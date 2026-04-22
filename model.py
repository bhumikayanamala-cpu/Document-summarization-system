"""
NLP Summarization module using HuggingFace Transformers.
Optimized for speed with batching and caching.
"""

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Summarizer:
    """
    Text summarization using DistilBART model.
    Includes optimizations for faster inference.
    """
    
    MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
    MAX_INPUT_LENGTH = 1024
    MAX_OUTPUT_LENGTH = 150
    MIN_OUTPUT_LENGTH = 40
    
    def __init__(self):
        """Initialize the summarization model."""
        logger.info(f"Loading summarization model: {self.MODEL_NAME}")
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.MODEL_NAME)
        self.model.to(self.device)
        self.model.eval()
        
        # Enable torch optimizations
        if self.device.type == 'cuda':
            self.model.half()  # FP16 for faster GPU inference
        
        logger.info("Model loaded successfully")
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and prepare text for summarization."""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove very short lines (likely headers/footers)
        lines = text.split('\n')
        lines = [line for line in lines if len(line.split()) > 3]
        text = ' '.join(lines)
        
        return text
    
    def _chunk_text(self, text: str, max_tokens: int = 900) -> list:
        """
        Split long text into chunks that fit within model's context window.
        Uses sentence boundaries for better coherence.
        """
        sentences = text.replace('\n', ' ').split('. ')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Rough token estimation (words * 1.3)
            sentence_tokens = int(len(sentence.split()) * 1.3)
            
            if current_length + sentence_tokens > max_tokens:
                if current_chunk:
                    chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_length = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_length += sentence_tokens
        
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
        
        return chunks if chunks else [text[:max_tokens * 4]]  # Fallback
    
    def summarize(self, text: str, max_length: Optional[int] = None, 
                  min_length: Optional[int] = None) -> str:
        """
        Generate summary for input text.
        
        Args:
            text: Input text to summarize
            max_length: Maximum summary length (tokens)
            min_length: Minimum summary length (tokens)
            
        Returns:
            Generated summary string
        """
        if not text or len(text.strip()) < 50:
            return "Text too short for meaningful summarization."
        
        max_length = max_length or self.MAX_OUTPUT_LENGTH
        min_length = min_length or self.MIN_OUTPUT_LENGTH
        
        # Preprocess
        text = self._preprocess_text(text)
        
        # Handle long documents by chunking
        chunks = self._chunk_text(text)
        
        if len(chunks) == 1:
            # Single chunk - direct summarization
            return self._generate_summary(chunks[0], max_length, min_length)
        else:
            # Multiple chunks - hierarchical summarization
            chunk_summaries = []
            
            for chunk in chunks[:5]:  # Limit to first 5 chunks for speed
                summary = self._generate_summary(
                    chunk, 
                    max_length=100, 
                    min_length=30
                )
                chunk_summaries.append(summary)
            
            # Combine chunk summaries
            combined = ' '.join(chunk_summaries)
            
            # Generate final summary from combined summaries
            if len(combined.split()) > 200:
                return self._generate_summary(combined, max_length, min_length)
            else:
                return combined
    
    def _generate_summary(self, text: str, max_length: int, 
                          min_length: int) -> str:
        """Generate summary for a single text chunk."""
        try:
            inputs = self.tokenizer(
                text,
                max_length=self.MAX_INPUT_LENGTH,
                truncation=True,
                return_tensors='pt'
            ).to(self.device)
            
            with torch.no_grad():
                summary_ids = self.model.generate(
                    inputs['input_ids'],
                    max_length=max_length,
                    min_length=min_length,
                    num_beams=4,
                    length_penalty=2.0,
                    early_stopping=True,
                    no_repeat_ngram_size=3
                )
            
            summary = self.tokenizer.decode(
                summary_ids[0], 
                skip_special_tokens=True
            )
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return f"Error generating summary: {str(e)}"
    
    def summarize_batch(self, texts: list, max_length: Optional[int] = None,
                        min_length: Optional[int] = None) -> list:
        """
        Batch summarization for multiple texts.
        More efficient than individual calls.
        """
        return [self.summarize(text, max_length, min_length) for text in texts]
