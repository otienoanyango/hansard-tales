#!/usr/bin/env python3
"""
Period-of-Day extractor for Hansard documents.

This module extracts the period-of-day (A=Afternoon, P=Morning, E=Evening)
from PDF metadata and content.
"""

import logging
from pathlib import Path
from typing import Optional

import pdfplumber


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PeriodOfDayExtractor:
    """Extract period-of-day from PDF title and content."""
    
    # Keyword mapping for period-of-day detection
    KEYWORDS = {
        'A': ['afternoon'],
        'P': ['morning', 'plenary'],
        'E': ['evening']
    }
    
    def extract_from_title(self, title: str) -> Optional[str]:
        """
        Extract period-of-day from PDF title.
        
        Searches for keywords in the title (case-insensitive):
        - "afternoon" maps to 'A'
        - "morning" or "plenary" map to 'P'
        - "evening" maps to 'E'
        
        Args:
            title: PDF title or filename
            
        Returns:
            'A', 'P', or 'E' if keyword found, None otherwise
            
        Example:
            >>> extractor = PeriodOfDayExtractor()
            >>> extractor.extract_from_title("Hansard Report - Afternoon Session")
            'A'
            >>> extractor.extract_from_title("Morning Plenary")
            'P'
        """
        if not title:
            return None
        
        # Convert to lowercase for case-insensitive matching
        title_lower = title.lower()
        
        # Search for keywords in order (A, P, E)
        for period, keywords in self.KEYWORDS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    logger.debug(f"Found keyword '{keyword}' in title, mapped to '{period}'")
                    return period
        
        return None
    
    def extract_from_content(self, pdf_path: str) -> Optional[str]:
        """
        Extract period-of-day from first page of PDF.
        
        Reads the first page of the PDF and searches for period-of-day
        keywords in the text content.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            'A', 'P', or 'E' if keyword found, None otherwise
            
        Example:
            >>> extractor = PeriodOfDayExtractor()
            >>> extractor.extract_from_content("hansard_20240101.pdf")
            'P'
        """
        pdf_file = Path(pdf_path)
        
        if not pdf_file.exists():
            logger.warning(f"PDF file not found: {pdf_path}")
            return None
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Check if PDF has pages
                if not pdf.pages:
                    logger.warning(f"PDF has no pages: {pdf_path}")
                    return None
                
                # Extract text from first page
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                if not text:
                    logger.warning(f"No text extracted from first page: {pdf_path}")
                    return None
                
                # Convert to lowercase for case-insensitive matching
                text_lower = text.lower()
                
                # Search for keywords in order (A, P, E)
                for period, keywords in self.KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in text_lower:
                            logger.debug(
                                f"Found keyword '{keyword}' in first page, mapped to '{period}'"
                            )
                            return period
                
                return None
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return None
    
    def extract(self, pdf_path: str, title: Optional[str] = None) -> str:
        """
        Extract period-of-day with fallback logic.
        
        Extraction strategy:
        1. Try to extract from title (if provided)
        2. If not found, try to extract from first page of PDF
        3. If still not found, default to 'P' (Morning)
        
        Args:
            pdf_path: Path to PDF file
            title: Optional PDF title or filename
            
        Returns:
            'A', 'P', or 'E' (defaults to 'P' if not found)
            
        Example:
            >>> extractor = PeriodOfDayExtractor()
            >>> extractor.extract("hansard.pdf", "Afternoon Session")
            'A'
            >>> extractor.extract("hansard.pdf")  # No keywords found
            'P'
        """
        # Try title first
        if title:
            period = self.extract_from_title(title)
            if period:
                logger.info(f"Extracted period '{period}' from title")
                return period
        
        # Try PDF content
        period = self.extract_from_content(pdf_path)
        if period:
            logger.info(f"Extracted period '{period}' from PDF content")
            return period
        
        # Default to 'P' (Morning)
        logger.info("No period-of-day keywords found, defaulting to 'P' (Morning)")
        return 'P'
