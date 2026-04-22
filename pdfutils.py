"""
PDF extraction utilities using pdfplumber.
Handles text extraction and intelligent table detection.
"""

import pdfplumber
import logging
from typing import Dict, List, Any, Optional
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extract text and tables from PDF documents.
    Includes intelligent table detection to avoid false positives.
    """
    
    # Minimum requirements for a valid table
    MIN_TABLE_ROWS = 2
    MIN_TABLE_COLS = 2
    MAX_TABLE_COLS = 20
    MIN_CELL_DENSITY = 0.5  # At least 50% of cells should have content
    
    def __init__(self):
        """Initialize PDF extractor."""
        pass
    
    def extract(self, filepath: str) -> Dict[str, Any]:
        """
        Extract text and tables from a PDF file.
        
        Args:
            filepath: Path to PDF file
            
        Returns:
            Dictionary with 'text', 'tables', 'page_count', and 'error' keys
        """
        result = {
            'text': '',
            'tables': [],
            'page_count': 0,
            'error': None
        }
        
        try:
            with pdfplumber.open(filepath) as pdf:
                result['page_count'] = len(pdf.pages)
                
                all_text = []
                all_tables = []
                
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = self._extract_page_text(page)
                    if page_text:
                        all_text.append(page_text)
                    
                    # Extract tables
                    page_tables = self._extract_page_tables(page)
                    all_tables.extend(page_tables)
                
                result['text'] = '\n\n'.join(all_text)
                result['tables'] = all_tables
                
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            result['error'] = f"Failed to process PDF: {str(e)}"
        
        return result
    
    def _extract_page_text(self, page) -> str:
        """Extract and clean text from a single page."""
        try:
            text = page.extract_text() or ''
            
            # Clean up the text
            text = self._clean_text(text)
            
            return text
        except Exception as e:
            logger.warning(f"Text extraction error: {e}")
            return ''
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ''
        
        # Remove excessive whitespace while preserving paragraph breaks
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Remove lines that are just numbers (page numbers)
                if re.match(r'^\d+$', line):
                    continue
                # Remove lines that are just special characters
                if re.match(r'^[\W_]+$', line):
                    continue
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_page_tables(self, page) -> List[List[List[str]]]:
        """
        Extract valid tables from a page.
        Filters out paragraph text incorrectly detected as tables.
        """
        valid_tables = []
        
        try:
            tables = page.extract_tables() or []
            
            for table in tables:
                if self._is_valid_table(table):
                    cleaned_table = self._clean_table(table)
                    if cleaned_table:
                        valid_tables.append(cleaned_table)
                        
        except Exception as e:
            logger.warning(f"Table extraction error: {e}")
        
        return valid_tables
    
    def _is_valid_table(self, table: List[List]) -> bool:
        """
        Determine if extracted data is a genuine table.
        Filters out paragraph text detected as single-column tables.
        """
        if not table:
            return False
        
        # Check minimum dimensions
        num_rows = len(table)
        if num_rows < self.MIN_TABLE_ROWS:
            return False
        
        # Get column count (use max to handle ragged tables)
        num_cols = max(len(row) for row in table if row)
        
        if num_cols < self.MIN_TABLE_COLS:
            return False
        
        if num_cols > self.MAX_TABLE_COLS:
            return False
        
        # Check cell density (non-empty cells)
        total_cells = 0
        filled_cells = 0
        
        for row in table:
            if not row:
                continue
            for cell in row:
                total_cells += 1
                if cell and str(cell).strip():
                    filled_cells += 1
        
        if total_cells == 0:
            return False
        
        density = filled_cells / total_cells
        if density < self.MIN_CELL_DENSITY:
            return False
        
        # Check if it's actually paragraph text in disguise
        if self._is_paragraph_text(table):
            return False
        
        return True
    
    def _is_paragraph_text(self, table: List[List]) -> bool:
        """
        Detect if table is actually paragraph text.
        Paragraph text often appears as single-column with long text cells.
        """
        # Check if most cells contain long text (>50 words)
        long_text_cells = 0
        total_cells = 0
        
        for row in table:
            if not row:
                continue
            for cell in row:
                if cell and str(cell).strip():
                    total_cells += 1
                    words = str(cell).split()
                    if len(words) > 50:
                        long_text_cells += 1
        
        if total_cells == 0:
            return False
        
        # If more than 30% of cells have very long text, it's likely paragraph text
        if long_text_cells / total_cells > 0.3:
            return True
        
        # Check for single-column structure with narrative text
        col_counts = [len(row) for row in table if row]
        if col_counts and max(col_counts) <= 2:
            # Check if cells contain sentence-like text
            sentence_pattern = re.compile(r'[A-Z][^.!?]*[.!?]')
            sentence_cells = 0
            
            for row in table:
                if not row:
                    continue
                for cell in row:
                    if cell and sentence_pattern.search(str(cell)):
                        sentence_cells += 1
            
            if total_cells > 0 and sentence_cells / total_cells > 0.5:
                return True
        
        return False
    
    def _clean_table(self, table: List[List]) -> List[List[str]]:
        """Clean and normalize table data."""
        cleaned = []
        
        for row in table:
            if not row:
                continue
            
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_row.append('')
                else:
                    # Clean cell content
                    cell_text = str(cell).strip()
                    # Replace newlines within cells
                    cell_text = ' '.join(cell_text.split())
                    # Limit cell length for display
                    if len(cell_text) > 200:
                        cell_text = cell_text[:197] + '...'
                    cleaned_row.append(cell_text)
            
            # Skip rows that are completely empty
            if any(cell for cell in cleaned_row):
                cleaned.append(cleaned_row)
        
        return cleaned if len(cleaned) >= self.MIN_TABLE_ROWS else []
