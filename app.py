"""
Flask application for Document Summarization System.
Handles routes, file uploads, and orchestrates summarization.
"""

import os
import uuid
from flask import (
    Flask, render_template, request, jsonify, 
    send_file, session, redirect, url_for, flash
)
from werkzeug.utils import secure_filename
from model import Summarizer
from pdfutils import PDFExtractor
import tempfile
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize components
summarizer = Summarizer()
pdf_extractor = PDFExtractor()

ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_files():
    """Remove files older than 1 hour from uploads folder."""
    import time
    current_time = time.time()
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(filepath):
            file_age = current_time - os.path.getmtime(filepath)
            if file_age > 3600:  # 1 hour
                try:
                    os.remove(filepath)
                except OSError:
                    pass


@app.route('/')
def index():
    """Render main upload page."""
    cleanup_old_files()
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle multiple file uploads."""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'No files selected'}), 400
    
    uploaded_files = []
    errors = []
    
    for file in files:
        if file.filename == '':
            continue
            
        if not allowed_file(file.filename):
            errors.append(f'{file.filename}: Only PDF files are allowed')
            continue
        
        # Generate unique filename to prevent collisions
        original_name = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{unique_id}_{original_name}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            uploaded_files.append({
                'original_name': file.filename,
                'stored_name': filename,
                'filepath': filepath,
                'size': os.path.getsize(filepath)
            })
        except Exception as e:
            errors.append(f'{file.filename}: Upload failed - {str(e)}')
    
    if not uploaded_files:
        return jsonify({'error': 'No valid files uploaded', 'details': errors}), 400
    
    return jsonify({
        'success': True,
        'files': uploaded_files,
        'errors': errors if errors else None
    })


@app.route('/summarize', methods=['POST'])
def summarize():
    """Generate summaries for uploaded files."""
    data = request.get_json()
    
    if not data or 'files' not in data:
        return jsonify({'error': 'No files specified'}), 400
    
    files_info = data['files']
    results = []
    
    for file_info in files_info:
        filepath = file_info.get('filepath')
        original_name = file_info.get('original_name', 'Unknown')
        
        if not filepath or not os.path.exists(filepath):
            results.append({
                'filename': original_name,
                'error': 'File not found',
                'success': False
            })
            continue
        
        try:
            # Extract text and tables from PDF
            extraction_result = pdf_extractor.extract(filepath)
            
            if extraction_result['error']:
                results.append({
                    'filename': original_name,
                    'error': extraction_result['error'],
                    'success': False
                })
                continue
            
            text = extraction_result['text']
            tables = extraction_result['tables']
            
            if not text or len(text.strip()) < 50:
                results.append({
                    'filename': original_name,
                    'error': 'Insufficient text content for summarization',
                    'success': False
                })
                continue
            
            # Generate summary
            summary = summarizer.summarize(text)
            
            results.append({
                'filename': original_name,
                'summary': summary,
                'tables': tables,
                'word_count': len(text.split()),
                'page_count': extraction_result.get('page_count', 0),
                'success': True
            })
            
        except Exception as e:
            results.append({
                'filename': original_name,
                'error': f'Processing error: {str(e)}',
                'success': False
            })
    
    return jsonify({'results': results})


@app.route('/download-summary', methods=['POST'])
def download_summary():
    """Generate and download summary as text file."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    filename = data.get('filename', 'document')
    summary = data.get('summary', '')
    tables = data.get('tables', [])
    
    # Create summary content
    content_lines = [
        f"Document Summary: {filename}",
        "=" * 50,
        "",
        "SUMMARY",
        "-" * 30,
        summary,
        ""
    ]
    
    if tables:
        content_lines.extend([
            "",
            "EXTRACTED TABLES",
            "-" * 30
        ])
        
        for i, table in enumerate(tables, 1):
            content_lines.append(f"\nTable {i}:")
            for row in table:
                content_lines.append(" | ".join(str(cell) for cell in row))
            content_lines.append("")
    
    content = "\n".join(content_lines)
    
    # Create temporary file
    base_filename = os.path.splitext(filename)[0]
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.txt', 
        delete=False,
        encoding='utf-8'
    )
    temp_file.write(content)
    temp_file.close()
    
    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name=f"{base_filename}_summary.txt",
        mimetype='text/plain'
    )


@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up uploaded files after processing."""
    data = request.get_json()
    
    if data and 'files' in data:
        for file_info in data['files']:
            filepath = file_info.get('filepath')
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
    
    return jsonify({'success': True})


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return render_template('error.html', 
                         error_code=413,
                         error_message='File too large. Maximum size is 50MB.'), 413


@app.errorhandler(404)
def not_found(e):
    """Handle 404 error."""
    return render_template('error.html',
                         error_code=404,
                         error_message='Page not found.'), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 error."""
    return render_template('error.html',
                         error_code=500,
                         error_message='Internal server error. Please try again.'), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
