#!/usr/bin/env python3
"""
PDF text extraction processor for Hansard documents.

This script extracts text from Hansard PDF files using pdfplumber,
preserving page numbers for source attribution.

Usage:
    python scripts/pdf_processor.py <pdf_file> [--output-dir PATH]
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pdfplumber


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Processor for extracting text from Hansard PDF files."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the PDF processor.
        
        Args:
            output_dir: Optional directory to save extracted text
        """
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_text_from_pdf(self, pdf_path: str) -> Optional[Dict]:
        """
        Extract text from a PDF file with page numbers.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with extracted text and metadata, or None if failed
        """
        pdf_file = Path(pdf_path)
        
        if not pdf_file.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        try:
            logger.info(f"Processing: {pdf_file.name}")
            
            with pdfplumber.open(pdf_path) as pdf:
                # Extract metadata
                metadata = {
                    'filename': pdf_file.name,
                    'num_pages': len(pdf.pages),
                    'metadata': pdf.metadata or {}
                }
                
                # Extract text from each page
                pages = []
                for page_num, page in enumerate(pdf.pages, start=1):
                    try:
                        text = page.extract_text()
                        
                        if text:
                            pages.append({
                                'page_number': page_num,
                                'text': text.strip(),
                                'char_count': len(text)
                            })
                            logger.debug(f"  Page {page_num}: {len(text)} characters")
                        else:
                            logger.warning(f"  Page {page_num}: No text extracted (possibly scanned)")
                            pages.append({
                                'page_number': page_num,
                                'text': '',
                                'char_count': 0,
                                'warning': 'No text extracted - possibly scanned image'
                            })
                    
                    except Exception as e:
                        logger.error(f"  Page {page_num}: Extraction failed - {e}")
                        pages.append({
                            'page_number': page_num,
                            'text': '',
                            'char_count': 0,
                            'error': str(e)
                        })
                
                # Calculate statistics
                total_chars = sum(p['char_count'] for p in pages)
                pages_with_text = sum(1 for p in pages if p['char_count'] > 0)
                
                result = {
                    'metadata': metadata,
                    'pages': pages,
                    'statistics': {
                        'total_pages': len(pages),
                        'pages_with_text': pages_with_text,
                        'pages_without_text': len(pages) - pages_with_text,
                        'total_characters': total_chars,
                        'avg_chars_per_page': total_chars / len(pages) if pages else 0
                    }
                }
                
                logger.info(f"✓ Extracted {total_chars} characters from {pages_with_text}/{len(pages)} pages")
                
                return result
        
        except pdfplumber.pdfminer.pdfparser.PDFSyntaxError as e:
            logger.error(f"✗ Malformed PDF: {e}")
            return None
        
        except Exception as e:
            logger.error(f"✗ Unexpected error: {e}")
            return None
    
    def get_full_text(self, extracted_data: Dict) -> str:
        """
        Get full text from extracted data.
        
        Args:
            extracted_data: Dictionary from extract_text_from_pdf
            
        Returns:
            Full text concatenated from all pages
        """
        if not extracted_data or 'pages' not in extracted_data:
            return ""
        
        return "\n\n".join(
            page['text'] 
            for page in extracted_data['pages'] 
            if page['text']
        )
    
    def get_page_text(self, extracted_data: Dict, page_number: int) -> Optional[str]:
        """
        Get text from a specific page.
        
        Args:
            extracted_data: Dictionary from extract_text_from_pdf
            page_number: Page number (1-indexed)
            
        Returns:
            Text from the specified page, or None if not found
        """
        if not extracted_data or 'pages' not in extracted_data:
            return None
        
        for page in extracted_data['pages']:
            if page['page_number'] == page_number:
                return page['text']
        
        return None
    
    def save_extracted_text(self, extracted_data: Dict, output_path: Optional[str] = None) -> bool:
        """
        Save extracted text to a JSON file.
        
        Args:
            extracted_data: Dictionary from extract_text_from_pdf
            output_path: Optional output file path
            
        Returns:
            True if successful, False otherwise
        """
        if not extracted_data:
            logger.error("No data to save")
            return False
        
        # Determine output path
        if output_path:
            out_file = Path(output_path)
        elif self.output_dir:
            filename = extracted_data['metadata']['filename']
            out_file = self.output_dir / f"{Path(filename).stem}.json"
        else:
            logger.error("No output path specified")
            return False
        
        try:
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Saved to: {out_file}")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed to save: {e}")
            return False
    
    def process_pdf(self, pdf_path: str, save_output: bool = True) -> Optional[Dict]:
        """
        Process a PDF file: extract text and optionally save.
        
        Args:
            pdf_path: Path to the PDF file
            save_output: Whether to save extracted text to file
            
        Returns:
            Extracted data dictionary, or None if failed
        """
        # Extract text
        extracted_data = self.extract_text_from_pdf(pdf_path)
        
        if not extracted_data:
            return None
        
        # Save if requested
        if save_output and self.output_dir:
            self.save_extracted_text(extracted_data)
        
        return extracted_data
    
    def process_directory(self, pdf_dir: str, pattern: str = "*.pdf") -> List[Dict]:
        """
        Process all PDF files in a directory.
        
        Args:
            pdf_dir: Directory containing PDF files
            pattern: Glob pattern for PDF files
            
        Returns:
            List of extracted data dictionaries
        """
        pdf_directory = Path(pdf_dir)
        
        if not pdf_directory.exists():
            logger.error(f"Directory not found: {pdf_dir}")
            return []
        
        pdf_files = list(pdf_directory.glob(pattern))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_dir}")
            return []
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        results = []
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"\nProcessing {i}/{len(pdf_files)}: {pdf_file.name}")
            
            extracted_data = self.process_pdf(str(pdf_file))
            if extracted_data:
                results.append(extracted_data)
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("PROCESSING SUMMARY")
        logger.info("="*50)
        logger.info(f"Total PDFs:           {len(pdf_files)}")
        logger.info(f"Successfully processed: {len(results)}")
        logger.info(f"Failed:               {len(pdf_files) - len(results)}")
        
        if results:
            total_pages = sum(r['statistics']['total_pages'] for r in results)
            total_chars = sum(r['statistics']['total_characters'] for r in results)
            logger.info(f"Total pages:          {total_pages}")
            logger.info(f"Total characters:     {total_chars:,}")
        
        logger.info("="*50)
        
        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract text from Hansard PDF files"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to PDF file or directory"
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save extracted text (JSON format)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save extracted text to file"
    )
    parser.add_argument(
        "--print-text",
        action="store_true",
        help="Print extracted text to console"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show statistics, don't save or print text"
    )
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = PDFProcessor(output_dir=args.output_dir)
    
    # Check if path is file or directory
    path = Path(args.pdf_path)
    
    if path.is_file():
        # Process single file
        extracted_data = processor.process_pdf(
            str(path),
            save_output=not args.no_save and not args.stats_only
        )
        
        if not extracted_data:
            sys.exit(1)
        
        # Print text if requested
        if args.print_text and not args.stats_only:
            print("\n" + "="*50)
            print("EXTRACTED TEXT")
            print("="*50)
            print(processor.get_full_text(extracted_data))
            print("="*50)
    
    elif path.is_dir():
        # Process directory
        results = processor.process_directory(str(path))
        
        if not results:
            sys.exit(1)
    
    else:
        logger.error(f"Path not found: {args.pdf_path}")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
