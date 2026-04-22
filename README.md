Document Summarization System (DocSummarize)

An AI-powered web application that automatically summarizes PDF documents using Natural Language Processing (NLP) and transformer-based models.

🚀 Overview

DocSummarize is a Flask-based web application that enables users to upload PDF files and instantly generate concise, human-readable summaries. The system uses advanced NLP techniques to extract text, process large documents efficiently, and generate abstractive summaries.

✨ Features
📂 Upload single or multiple PDF files
🧠 Abstractive text summarization using DistilBART
📊 Automatic table extraction from PDFs
⚡ Chunk-based processing for large documents
🌐 Clean and responsive web interface
📥 Download summaries as text files
🔒 Stateless processing (no data stored permanently)

🛠️ Tech Stack:
Backend:
Python
Flask
Hugging Face Transformers
PyTorch

NLP Model:
DistilBART-CNN-12-6 (pre-trained summarization model)

PDF Processing:
pdfplumber

Frontend:
HTML5
CSS3
JavaScript
Jinja2 Templates

🏗️ Project Structure
document-summarization-system/
│
├── app.py              # Flask application (routes & logic)
├── model.py            # NLP summarization pipeline
├── pdfutils.py         # PDF text & table extraction
├── requirements.txt    # Dependencies
├── README.md           # Project documentation
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── error.html
│   └── components/
│       ├── summarycard.html
│       ├── tablecomponent.html
│       └── upload.html
│
└── static/
    ├── css/style.css
    └── js/script.js
    
⚙️ How It Works
User uploads PDF files
System extracts text and tables using pdfplumber
Text is split into chunks (to handle long documents)
Each chunk is summarized using DistilBART
Summaries are combined into a final output
Results are displayed and available for download

▶️ Installation & Setup:

1. Clone the Repository
git clone https://github.com/your-username/document-summarization-system.git
cd document-summarization-system

2. Create Virtual Environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

3. Install Dependencies
pip install -r requirements.txt

5. Run the Application
python app.py

7. Open in Browser
http://localhost:5001

📊 Model Details
Model: DistilBART-CNN-12-6
Type: Abstractive summarization
Max input: ~1024 tokens (handled via chunking)
Output length: 40–120 tokens per chunk

📈 Performance
Generates fluent and coherent summaries
Handles large documents efficiently
Works well on academic, technical, and business PDFs

🔮 Future Enhancements
OCR support for scanned PDFs
Multilingual summarization
Domain-specific fine-tuned models
User authentication & history
Real-time streaming summaries
Support for DOCX, TXT, HTML files

📚 References
Hugging Face Transformers
BART & DistilBART research papers
pdfplumber documentation

👨‍💻 Authors:
Rishika Arisetty
Bhumika Yanamala
Chetan Ram Nandamuri
Sai Venkata Sandeep Garlapati
