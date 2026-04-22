# Document Summarization System

AI-powered document summarization using Flask, HuggingFace Transformers, and pdfplumber.

## Features

- **Multi-file Upload**: Select multiple PDF files without losing previous selections
- **AI Summarization**: Uses DistilBART model for fast, accurate summaries
- **Table Extraction**: Intelligently extracts real tables, ignoring paragraph text
- **Download Summaries**: Export summaries as text files
- **Modern UI**: Clean, responsive design with soft colors

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd document-summarization-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
