/**
 * Document Summarization System - Client-Side JavaScript
 * Handles file selection, uploads, and summary generation
 */

(function() {
    'use strict';
    
    // ==================== State Management ====================
    const state = {
        selectedFiles: new Map(), // Map<uniqueId, {file, originalName, size}>
        uploadedFiles: [],        // Server-side file info after upload
        isProcessing: false
    };
    
    // ==================== DOM Elements ====================
    const elements = {
        uploadArea: document.getElementById('upload-area'),
        fileInput: document.getElementById('file-input'),
        fileList: document.getElementById('file-list'),
        selectedFiles: document.getElementById('selected-files'),
        fileCount: document.getElementById('file-count'),
        generateBtn: document.getElementById('generate-btn'),
        clearBtn: document.getElementById('clear-btn'),
        summariesContainer: document.getElementById('summaries-container'),
        emptyState: document.getElementById('empty-state'),
        selectedCount: document.getElementById('selected-count'),
        summaryCount: document.getElementById('summary-count'),
        statusText: document.getElementById('status-text')
    };
    
    // ==================== Initialization ====================
    function init() {
        setupEventListeners();
        updateUI();
    }
    
    function setupEventListeners() {
        // File input change
        elements.fileInput.addEventListener('change', handleFileSelect);
        
        // Drag and drop
        elements.uploadArea.addEventListener('dragover', handleDragOver);
        elements.uploadArea.addEventListener('dragleave', handleDragLeave);
        elements.uploadArea.addEventListener('drop', handleDrop);
        elements.uploadArea.addEventListener('click', () => elements.fileInput.click());
        
        // Buttons
        elements.generateBtn.addEventListener('click', handleGenerate);
        elements.clearBtn.addEventListener('click', handleClear);
        
        // Delegate download button clicks
        elements.summariesContainer.addEventListener('click', handleDownloadClick);
    }
    
    // ==================== File Handling ====================
    function handleFileSelect(event) {
        const files = Array.from(event.target.files);
        addFiles(files);
        event.target.value = ''; // Reset to allow re-selecting same files
    }
    
    function handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        elements.uploadArea.classList.add('dragover');
    }
    
    function handleDragLeave(event) {
        event.preventDefault();
        event.stopPropagation();
        elements.uploadArea.classList.remove('dragover');
    }
    
    function handleDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        elements.uploadArea.classList.remove('dragover');
        
        const files = Array.from(event.dataTransfer.files);
        addFiles(files);
    }
    
    function addFiles(files) {
        files.forEach(file => {
            // Only accept PDF files
            if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
                showNotification(`${file.name} is not a PDF file`, 'error');
                return;
            }
            
            // Check for duplicates by name and size
            const isDuplicate = Array.from(state.selectedFiles.values()).some(
                f => f.file.name === file.name && f.file.size === file.size
            );
            
            if (isDuplicate) {
                showNotification(`${file.name} is already selected`, 'warning');
                return;
            }
            
            // Generate unique ID for this file
            const uniqueId = generateUniqueId();
            state.selectedFiles.set(uniqueId, {
                file: file,
                originalName: file.name,
                size: file.size
            });
        });
        
        updateUI();
    }
    
    function removeFile(uniqueId) {
        state.selectedFiles.delete(uniqueId);
        updateUI();
    }
    
    function handleClear() {
        state.selectedFiles.clear();
        state.uploadedFiles = [];
        updateUI();
    }
    
    // ==================== Upload & Summarization ====================
    async function handleGenerate() {
        if (state.selectedFiles.size === 0 || state.isProcessing) return;
        
        state.isProcessing = true;
        updateUI();
        setStatus('Uploading files...');
        
        try {
            // Step 1: Upload files
            const uploadResult = await uploadFiles();
            
            if (!uploadResult.success || uploadResult.files.length === 0) {
                throw new Error(uploadResult.error || 'No files were uploaded successfully');
            }
            
            state.uploadedFiles = uploadResult.files;
            setStatus('Generating summaries...');
            
            // Step 2: Generate summaries
            const summaryResult = await generateSummaries(uploadResult.files);
            
            if (!summaryResult.results) {
                throw new Error('Failed to generate summaries');
            }
            
            // Step 3: Display results
            displaySummaries(summaryResult.results);
            
            // Step 4: Cleanup
            await cleanupFiles(uploadResult.files);
            
            setStatus('Completed');
            state.selectedFiles.clear();
            
        } catch (error) {
            console.error('Processing error:', error);
            showNotification(error.message, 'error');
            setStatus('Error occurred');
        } finally {
            state.isProcessing = false;
            updateUI();
        }
    }
    
    async function uploadFiles() {
        const formData = new FormData();
        
        state.selectedFiles.forEach(({file}) => {
            formData.append('files', file);
        });
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        return response.json();
    }
    
    async function generateSummaries(files) {
        const response = await fetch('/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ files })
        });
        
        return response.json();
    }
    
    async function cleanupFiles(files) {
        try {
            await fetch('/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ files })
            });
        } catch (e) {
            console.warn('Cleanup failed:', e);
        }
    }
    
    // ==================== Display Summaries ====================
    function displaySummaries(results) {
        elements.emptyState.hidden = true;
        
        // Clear existing summaries (except empty state)
        const existingCards = elements.summariesContainer.querySelectorAll('.summary-card');
        existingCards.forEach(card => card.remove());
        
        results.forEach(result => {
            const card = createSummaryCard(result);
            elements.summariesContainer.appendChild(card);
        });
        
        elements.summaryCount.textContent = results.filter(r => r.success).length;
        
        // Scroll to summaries
        elements.summariesContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    function createSummaryCard(result) {
        const card = document.createElement('article');
        card.className = `summary-card ${result.success ? '' : 'error'}`;
        
        const tablesJson = result.tables ? JSON.stringify(result.tables) : '[]';
        
        card.innerHTML = `
            <header class="card-header">
                <div class="card-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                    <h3>${escapeHtml(result.filename)}</h3>
                </div>
                <div class="card-meta">
                    ${result.success 
                        ? `<span class="badge success">Completed</span>
                           ${result.word_count ? `<span class="meta-item">${result.word_count} words</span>` : ''}
                           ${result.page_count ? `<span class="meta-item">${result.page_count} pages</span>` : ''}`
                        : '<span class="badge error">Error</span>'
                    }
                </div>
            </header>
            <div class="card-body">
                ${result.success 
                    ? `<div class="summary-content">
                           <h4>Summary</h4>
                           <p>${escapeHtml(result.summary)}</p>
                       </div>
                       ${result.tables && result.tables.length > 0 
                           ? `<div class="tables-content">
                                  <h4>Extracted Tables</h4>
                                  ${result.tables.map(table => createTableHTML(table)).join('')}
                              </div>` 
                           : ''}`
                    : `<div class="error-content">
                           <p>${escapeHtml(result.error)}</p>
                       </div>`
                }
            </div>
            ${result.success 
                ? `<footer class="card-footer">
                       <button type="button" class="btn btn-outline download-btn" 
                               data-filename="${escapeHtml(result.filename)}"
                               data-summary="${escapeHtml(result.summary)}"
                               data-tables='${escapeHtml(tablesJson)}'>
                           <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                               <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                               <polyline points="7 10 12 15 17 10"></polyline>
                               <line x1="12" y1="15" x2="12" y2="3"></line>
                           </svg>
                           Download Summary
                       </button>
                   </footer>` 
                : ''
            }
        `;
        
        return card;
    }
    
    function createTableHTML(table) {
        if (!table || table.length === 0) return '';
        
        let html = '<div class="table-wrapper"><div class="table-scroll"><table class="data-table">';
        
        table.forEach((row, index) => {
            if (index === 0) {
                html += '<thead><tr>';
                row.forEach(cell => {
                    html += `<th>${escapeHtml(cell || '')}</th>`;
                });
                html += '</tr></thead><tbody>';
            } else {
                html += '<tr>';
                row.forEach(cell => {
                    html += `<td>${escapeHtml(cell || '')}</td>`;
                });
                html += '</tr>';
            }
        });
        
        html += '</tbody></table></div></div>';
        return html;
    }
    
    // ==================== Download Handler ====================
    async function handleDownloadClick(event) {
        const btn = event.target.closest('.download-btn');
        if (!btn) return;
        
        const filename = btn.dataset.filename;
        const summary = btn.dataset.summary;
        let tables = [];
        
        try {
            tables = JSON.parse(btn.dataset.tables || '[]');
        } catch (e) {
            console.warn('Failed to parse tables:', e);
        }
        
        try {
            const response = await fetch('/download-summary', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filename, summary, tables })
            });
            
            if (!response.ok) throw new Error('Download failed');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${filename.replace('.pdf', '')}_summary.txt`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            
        } catch (error) {
            showNotification('Download failed: ' + error.message, 'error');
        }
    }
    
    // ==================== UI Updates ====================
    function updateUI() {
        const fileCount = state.selectedFiles.size;
        const hasFiles = fileCount > 0;
        
        // Update file list
        elements.fileList.innerHTML = '';
        state.selectedFiles.forEach((fileData, uniqueId) => {
            const li = createFileListItem(uniqueId, fileData);
            elements.fileList.appendChild(li);
        });
        
        // Toggle visibility
        elements.selectedFiles.classList.toggle('visible', hasFiles);
        
        // Update counts
        elements.fileCount.textContent = `(${fileCount})`;
        elements.selectedCount.textContent = fileCount;
        
        // Update buttons
        elements.generateBtn.disabled = !hasFiles || state.isProcessing;
        elements.clearBtn.disabled = !hasFiles || state.isProcessing;
        
        // Update button text
        const btnText = elements.generateBtn.querySelector('.btn-text');
        const btnLoading = elements.generateBtn.querySelector('.btn-loading');
        
        if (state.isProcessing) {
            btnText.hidden = true;
            btnLoading.hidden = false;
        } else {
            btnText.hidden = false;
            btnLoading.hidden = true;
        }
    }
    
    function createFileListItem(uniqueId, fileData) {
        const li = document.createElement('li');
        li.className = 'file-item';
        li.innerHTML = `
            <div class="file-info">
                <div class="file-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                </div>
                <div class="file-details">
                    <span class="file-name">${escapeHtml(fileData.originalName)}</span>
                    <span class="file-size">${formatFileSize(fileData.size)}</span>
                </div>
            </div>
            <button type="button" class="remove-file" title="Remove file">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        `;
        
        li.querySelector('.remove-file').addEventListener('click', () => removeFile(uniqueId));
        return li;
    }
    
    function setStatus(text) {
        elements.statusText.textContent = text;
    }
    
    // ==================== Utilities ====================
    function generateUniqueId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function showNotification(message, type = 'info') {
        // Simple notification - could be enhanced with a toast library
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // For now, use alert for errors
        if (type === 'error') {
            alert(message);
        }
    }
    
    // ==================== Initialize ====================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
