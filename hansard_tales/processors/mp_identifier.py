#!/usr/bin/env python3
"""
MP identification and statement extraction for Hansard documents.

This module identifies MPs from Hansard text using regex patterns and
extracts their statements for database storage.

Usage:
    from scripts.mp_identifier import MPIdentifier
    
    identifier = MPIdentifier()
    statements = identifier.extract_statements(hansard_text)
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Statement:
    """Represents a statement made by an MP in Hansard."""
    mp_name: str
    text: str
    start_position: int
    end_position: int
    page_number: Optional[int] = None
    confidence: float = 1.0


class MPIdentifier:
    """Identifies MPs and extracts their statements from Hansard text."""
    
    # Common speaker patterns in Kenyan Hansard
    SPEAKER_PATTERNS = [
        # "Hon. John Doe:" or "Hon. John Doe (MP):"
        r'Hon\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:\([^)]*\))?\s*:',
        # "The Speaker:" or "The Deputy Speaker:"
        r'(The\s+(?:Deputy\s+)?Speaker)\s*:',
        # "Mr. Speaker:" or "Madam Speaker:"
        r'((?:Mr\.|Madam)\s+Speaker)\s*:',
        # "The Chairperson:" or "The Temporary Speaker:"
        r'(The\s+(?:Temporary\s+)?(?:Chairperson|Speaker))\s*:',
    ]
    
    # Compile patterns for efficiency
    COMPILED_PATTERNS = [re.compile(pattern, re.MULTILINE) for pattern in SPEAKER_PATTERNS]
    
    # Common non-MP speakers to filter out
    NON_MP_SPEAKERS = {
        'The Speaker',
        'The Deputy Speaker',
        'Mr. Speaker',
        'Madam Speaker',
        'The Chairperson',
        'The Temporary Speaker',
        'The Temporary Chairperson',
    }
    
    def __init__(self, use_spacy: bool = False):
        """
        Initialize the MP identifier.
        
        Args:
            use_spacy: Whether to use spaCy for name validation (optional)
        """
        self.use_spacy = use_spacy
        self.nlp = None
        
        if use_spacy:
            try:
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded for name validation")
            except (ImportError, OSError) as e:
                logger.warning(f"Could not load spaCy model: {e}")
                self.use_spacy = False
    
    def normalize_mp_name(self, name: str) -> str:
        """
        Normalize MP name for consistent database storage.
        
        Args:
            name: Raw MP name from text
            
        Returns:
            Normalized name
        """
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove common prefixes/suffixes
        name = re.sub(r'\s*\([^)]*\)\s*', '', name)  # Remove parenthetical content
        name = re.sub(r'\s*,\s*MP\s*$', '', name, flags=re.IGNORECASE)  # Remove ", MP"
        
        # Title case
        name = name.title()
        
        return name.strip()
    
    def validate_name_with_spacy(self, name: str) -> bool:
        """
        Validate that a name looks like a person name using spaCy NER.
        
        Args:
            name: Name to validate
            
        Returns:
            True if name appears to be a person name
        """
        if not self.use_spacy or not self.nlp:
            return True  # Skip validation if spaCy not available
        
        doc = self.nlp(name)
        
        # Check if any entity is recognized as a PERSON
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                return True
        
        # Also accept if it looks like a name (capitalized words)
        words = name.split()
        if len(words) >= 2 and all(w[0].isupper() for w in words if w):
            return True
        
        return False
    
    def find_all_speakers(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Find all speaker mentions in text.
        
        Args:
            text: Hansard text to search
            
        Returns:
            List of (speaker_name, start_position, end_position) tuples
        """
        speakers = []
        seen_positions = set()
        
        for pattern in self.COMPILED_PATTERNS:
            for match in pattern.finditer(text):
                speaker_name = match.group(1)
                start_pos = match.start()
                end_pos = match.end()
                
                # Skip if we've already found a speaker at this position
                if start_pos in seen_positions:
                    continue
                
                seen_positions.add(start_pos)
                speakers.append((speaker_name, start_pos, end_pos))
        
        # Sort by position
        speakers.sort(key=lambda x: x[1])
        
        return speakers
    
    def extract_statement_text(
        self,
        text: str,
        start_pos: int,
        next_speaker_pos: Optional[int] = None
    ) -> str:
        """
        Extract statement text from start position to next speaker.
        
        Args:
            text: Full Hansard text
            start_pos: Start position (after speaker name)
            next_speaker_pos: Position of next speaker (or None for end of text)
            
        Returns:
            Statement text
        """
        if next_speaker_pos is None:
            statement = text[start_pos:]
        else:
            statement = text[start_pos:next_speaker_pos]
        
        # Clean up the statement
        statement = statement.strip()
        
        # Remove leading colon if present
        if statement.startswith(':'):
            statement = statement[1:].strip()
        
        return statement
    
    def extract_statements(
        self,
        text: str,
        page_number: Optional[int] = None,
        filter_non_mps: bool = True
    ) -> List[Statement]:
        """
        Extract all MP statements from Hansard text.
        
        Args:
            text: Hansard text to process
            page_number: Optional page number for attribution
            filter_non_mps: Whether to filter out non-MP speakers
            
        Returns:
            List of Statement objects
        """
        speakers = self.find_all_speakers(text)
        
        if not speakers:
            logger.warning("No speakers found in text")
            return []
        
        statements = []
        
        for i, (speaker_name, start_pos, end_pos) in enumerate(speakers):
            # Normalize the name
            normalized_name = self.normalize_mp_name(speaker_name)
            
            # Filter out non-MP speakers if requested
            if filter_non_mps and normalized_name in self.NON_MP_SPEAKERS:
                logger.debug(f"Skipping non-MP speaker: {normalized_name}")
                continue
            
            # Validate name with spaCy if available
            if self.use_spacy and not self.validate_name_with_spacy(normalized_name):
                logger.debug(f"Name validation failed: {normalized_name}")
                continue
            
            # Find the end position (next speaker or end of text)
            next_start_pos = speakers[i + 1][1] if i + 1 < len(speakers) else None
            
            # Extract statement text (start after the speaker pattern)
            statement_text = self.extract_statement_text(text, end_pos, next_start_pos)
            
            # Skip empty statements
            if not statement_text or len(statement_text) < 10:
                logger.debug(f"Skipping empty/short statement for {normalized_name}")
                continue
            
            # Create statement object
            statement = Statement(
                mp_name=normalized_name,
                text=statement_text,
                start_position=start_pos,
                end_position=next_start_pos or len(text),
                page_number=page_number,
                confidence=1.0
            )
            
            statements.append(statement)
            logger.debug(f"Extracted statement for {normalized_name}: {len(statement_text)} chars")
        
        logger.info(f"Extracted {len(statements)} statements from text")
        
        return statements
    
    def extract_statements_from_pages(
        self,
        pages_data: List[Dict],
        filter_non_mps: bool = True
    ) -> List[Statement]:
        """
        Extract statements from PDF pages data (from PDFProcessor).
        
        Args:
            pages_data: List of page dictionaries with 'page_number' and 'text'
            filter_non_mps: Whether to filter out non-MP speakers
            
        Returns:
            List of Statement objects with page numbers
        """
        all_statements = []
        
        for page in pages_data:
            page_num = page.get('page_number')
            page_text = page.get('text', '')
            
            if not page_text:
                continue
            
            statements = self.extract_statements(
                page_text,
                page_number=page_num,
                filter_non_mps=filter_non_mps
            )
            
            all_statements.extend(statements)
        
        return all_statements
    
    def get_unique_mp_names(self, statements: List[Statement]) -> List[str]:
        """
        Get list of unique MP names from statements.
        
        Args:
            statements: List of Statement objects
            
        Returns:
            Sorted list of unique MP names
        """
        names = set(stmt.mp_name for stmt in statements)
        return sorted(names)
    
    def get_statements_by_mp(self, statements: List[Statement]) -> Dict[str, List[Statement]]:
        """
        Group statements by MP name.
        
        Args:
            statements: List of Statement objects
            
        Returns:
            Dictionary mapping MP names to their statements
        """
        by_mp = {}
        
        for stmt in statements:
            if stmt.mp_name not in by_mp:
                by_mp[stmt.mp_name] = []
            by_mp[stmt.mp_name].append(stmt)
        
        return by_mp
    
    def get_statistics(self, statements: List[Statement]) -> Dict:
        """
        Get statistics about extracted statements.
        
        Args:
            statements: List of Statement objects
            
        Returns:
            Dictionary with statistics
        """
        if not statements:
            return {
                'total_statements': 0,
                'unique_mps': 0,
                'avg_statement_length': 0,
                'total_characters': 0
            }
        
        by_mp = self.get_statements_by_mp(statements)
        total_chars = sum(len(stmt.text) for stmt in statements)
        
        return {
            'total_statements': len(statements),
            'unique_mps': len(by_mp),
            'avg_statement_length': total_chars / len(statements),
            'total_characters': total_chars,
            'statements_per_mp': {
                name: len(stmts) for name, stmts in by_mp.items()
            }
        }


def main():
    """Main entry point for testing."""
    import argparse
    import json
    from pathlib import Path
    
    parser = argparse.ArgumentParser(
        description="Extract MP statements from Hansard text"
    )
    parser.add_argument(
        "input_file",
        help="Path to text file or JSON file from PDFProcessor"
    )
    parser.add_argument(
        "--use-spacy",
        action="store_true",
        help="Use spaCy for name validation"
    )
    parser.add_argument(
        "--include-non-mps",
        action="store_true",
        help="Include non-MP speakers (Speaker, Chairperson, etc.)"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file for statements"
    )
    
    args = parser.parse_args()
    
    # Initialize identifier
    identifier = MPIdentifier(use_spacy=args.use_spacy)
    
    # Read input
    input_path = Path(args.input_file)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input_file}")
        return 1
    
    # Check if JSON (from PDFProcessor) or plain text
    if input_path.suffix == '.json':
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        if 'pages' in data:
            # PDFProcessor format
            statements = identifier.extract_statements_from_pages(
                data['pages'],
                filter_non_mps=not args.include_non_mps
            )
        else:
            logger.error("Invalid JSON format")
            return 1
    else:
        # Plain text file
        with open(input_path, 'r') as f:
            text = f.read()
        
        statements = identifier.extract_statements(
            text,
            filter_non_mps=not args.include_non_mps
        )
    
    # Print statistics
    stats = identifier.get_statistics(statements)
    
    print("\n" + "="*50)
    print("EXTRACTION STATISTICS")
    print("="*50)
    print(f"Total statements:     {stats['total_statements']}")
    print(f"Unique MPs:           {stats['unique_mps']}")
    print(f"Avg statement length: {stats['avg_statement_length']:.0f} chars")
    print(f"Total characters:     {stats['total_characters']:,}")
    print("="*50)
    
    # Print MP list
    unique_mps = identifier.get_unique_mp_names(statements)
    print(f"\nUnique MPs found ({len(unique_mps)}):")
    for mp in unique_mps:
        by_mp = identifier.get_statements_by_mp(statements)
        count = len(by_mp[mp])
        print(f"  - {mp}: {count} statement(s)")
    
    # Save output if requested
    if args.output:
        output_data = {
            'statistics': stats,
            'statements': [
                {
                    'mp_name': stmt.mp_name,
                    'text': stmt.text,
                    'page_number': stmt.page_number,
                    'start_position': stmt.start_position,
                    'end_position': stmt.end_position,
                    'confidence': stmt.confidence
                }
                for stmt in statements
            ]
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved to: {args.output}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
