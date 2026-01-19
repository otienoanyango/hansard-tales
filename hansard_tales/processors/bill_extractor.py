#!/usr/bin/env python3
"""
Bill reference extraction for Hansard statements.

This module extracts bill references from Hansard text using regex patterns
to identify various bill formats used in Kenyan Parliament.

Usage:
    from scripts.bill_extractor import BillExtractor
    
    extractor = BillExtractor()
    bills = extractor.extract_bill_references(statement_text)
"""

import logging
import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BillReference:
    """Represents a bill reference found in text."""
    bill_number: str
    bill_year: Optional[str] = None
    full_text: str = ""
    position: int = 0
    bill_type: Optional[str] = None  # e.g., "Finance", "Appropriation"


class BillExtractor:
    """Extracts bill references from Hansard text."""
    
    # Common bill types to recognize (for validation)
    BILL_TYPES = {
        'Finance', 'Appropriation', 'Budget', 'Supplementary', 
        'Constitutional', 'Amendment', 'Revenue', 'Tax',
        'Health', 'Education', 'Agriculture', 'Security',
        'County', 'National', 'Public', 'Private', 'Water',
        'Energy', 'Housing', 'Transport', 'Employment'
    }
    
    # Common bill reference patterns in Kenyan Parliament
    BILL_PATTERNS = [
        # "The Finance Bill, 2024" - with "The" prefix
        r'The\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+Bill,?\s+(\d{4})',
        # "Finance Bill 2024" or "Finance Bill (2024)" - without "The"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+Bill[,\s]+\(?(\d{4})\)?',
        # "Bill No. 123" or "Bill No.123"
        r'Bill\s+No\.\s*(\d+)',
        # "Bill 2024/123" or "Bill 2024-123"
        r'Bill\s+(\d{4})[/-](\d+)',
        # "Bill Number 123"
        r'Bill\s+Number\s+(\d+)',
        # Just "Bill 123" (more permissive, 1-3 digits only) - must come last
        r'\bBill\s+(\d{1,3})\b',
    ]
    
    # Compile patterns for efficiency
    COMPILED_PATTERNS = [
        (re.compile(pattern, re.IGNORECASE), i) 
        for i, pattern in enumerate(BILL_PATTERNS)
    ]
    
    def __init__(self):
        """Initialize the bill extractor."""
        pass
    
    def normalize_bill_reference(self, bill_number: str, bill_year: Optional[str] = None) -> str:
        """
        Normalize bill reference to standard format.
        
        Args:
            bill_number: Bill number
            bill_year: Optional year
            
        Returns:
            Normalized bill reference (e.g., "Bill No. 123" or "Bill 2024/123")
        """
        # Remove leading zeros
        bill_number = bill_number.lstrip('0') or '0'
        
        if bill_year:
            return f"Bill {bill_year}/{bill_number}"
        else:
            return f"Bill No. {bill_number}"
    
    def extract_bill_references(self, text: str) -> List[BillReference]:
        """
        Extract all bill references from text.
        
        Args:
            text: Text to search for bill references
            
        Returns:
            List of BillReference objects
        """
        if not text:
            return []
        
        found_bills = []
        seen_positions = set()
        
        for pattern, pattern_idx in self.COMPILED_PATTERNS:
            for match in pattern.finditer(text):
                position = match.start()
                
                # Skip if we've already found a bill at this position
                if position in seen_positions:
                    continue
                
                seen_positions.add(position)
                
                # Extract bill information based on pattern
                bill_ref = self._parse_match(match, pattern_idx, text, position)
                
                if bill_ref:
                    found_bills.append(bill_ref)
                    logger.debug(f"Found bill: {bill_ref.full_text} at position {position}")
        
        # Sort by position
        found_bills.sort(key=lambda x: x.position)
        
        # Remove duplicates (same bill number mentioned multiple times)
        unique_bills = self._deduplicate_bills(found_bills)
        
        logger.info(f"Extracted {len(unique_bills)} unique bill references from text")
        
        return unique_bills
    
    def _parse_match(
        self, 
        match: re.Match, 
        pattern_idx: int, 
        text: str, 
        position: int
    ) -> Optional[BillReference]:
        """
        Parse a regex match into a BillReference object.
        
        Args:
            match: Regex match object
            pattern_idx: Index of the pattern that matched
            text: Full text
            position: Match position
            
        Returns:
            BillReference object or None
        """
        groups = match.groups()
        full_text = match.group(0)
        
        bill_number = None
        bill_year = None
        bill_type = None
        
        # Pattern 0: "The Finance Bill, 2024"
        if pattern_idx == 0:
            bill_type = groups[0]
            bill_year = groups[1]
            bill_number = None
            # Validate bill type
            if bill_type not in self.BILL_TYPES:
                return None
        
        # Pattern 1: "Finance Bill 2024"
        elif pattern_idx == 1:
            bill_type = groups[0]
            bill_year = groups[1]
            bill_number = None
            # Validate bill type
            if bill_type not in self.BILL_TYPES:
                return None
        
        # Pattern 2: "Bill No. 123"
        elif pattern_idx == 2:
            bill_number = groups[0]
        
        # Pattern 3: "Bill 2024/123"
        elif pattern_idx == 3:
            bill_year = groups[0]
            bill_number = groups[1]
        
        # Pattern 4: "Bill Number 123"
        elif pattern_idx == 4:
            bill_number = groups[0]
        
        # Pattern 5: "Bill 123"
        elif pattern_idx == 5:
            bill_number = groups[0]
        
        # Create normalized reference
        if bill_type and bill_year:
            # Named bill with year
            normalized = f"{bill_type} Bill {bill_year}"
        elif bill_number:
            normalized = self.normalize_bill_reference(bill_number, bill_year)
        else:
            # Couldn't extract enough info
            return None
        
        return BillReference(
            bill_number=bill_number or "",
            bill_year=bill_year,
            full_text=full_text,
            position=position,
            bill_type=bill_type
        )
    
    def _deduplicate_bills(self, bills: List[BillReference]) -> List[BillReference]:
        """
        Remove duplicate bill references.
        
        Args:
            bills: List of BillReference objects
            
        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []
        
        for bill in bills:
            # Create a key for deduplication
            if bill.bill_type and bill.bill_year:
                key = f"{bill.bill_type}_{bill.bill_year}"
            elif bill.bill_number and bill.bill_year:
                key = f"{bill.bill_year}_{bill.bill_number}"
            elif bill.bill_number:
                key = f"no_{bill.bill_number}"
            else:
                key = bill.full_text
            
            if key not in seen:
                seen.add(key)
                unique.append(bill)
        
        return unique
    
    def extract_from_statements(
        self, 
        statements: List[Dict]
    ) -> Dict[int, List[BillReference]]:
        """
        Extract bill references from a list of statements.
        
        Args:
            statements: List of statement dictionaries with 'text' field
            
        Returns:
            Dictionary mapping statement index to list of BillReference objects
        """
        results = {}
        
        for i, statement in enumerate(statements):
            text = statement.get('text', '')
            bills = self.extract_bill_references(text)
            
            if bills:
                results[i] = bills
        
        return results
    
    def get_statistics(self, bills: List[BillReference]) -> Dict:
        """
        Get statistics about extracted bill references.
        
        Args:
            bills: List of BillReference objects
            
        Returns:
            Dictionary with statistics
        """
        if not bills:
            return {
                'total_bills': 0,
                'bills_with_numbers': 0,
                'bills_with_years': 0,
                'bills_with_types': 0,
                'bill_types': []
            }
        
        bills_with_numbers = sum(1 for b in bills if b.bill_number)
        bills_with_years = sum(1 for b in bills if b.bill_year)
        bills_with_types = sum(1 for b in bills if b.bill_type)
        
        bill_types = list(set(b.bill_type for b in bills if b.bill_type))
        
        return {
            'total_bills': len(bills),
            'bills_with_numbers': bills_with_numbers,
            'bills_with_years': bills_with_years,
            'bills_with_types': bills_with_types,
            'bill_types': sorted(bill_types)
        }
    
    def format_bill_reference(self, bill: BillReference) -> str:
        """
        Format a bill reference for display.
        
        Args:
            bill: BillReference object
            
        Returns:
            Formatted string
        """
        if bill.bill_type and bill.bill_year:
            return f"{bill.bill_type} Bill {bill.bill_year}"
        elif bill.bill_number and bill.bill_year:
            return f"Bill {bill.bill_year}/{bill.bill_number}"
        elif bill.bill_number:
            return f"Bill No. {bill.bill_number}"
        else:
            return bill.full_text


def main():
    """Main entry point for testing."""
    import argparse
    import json
    from pathlib import Path
    
    parser = argparse.ArgumentParser(
        description="Extract bill references from Hansard text or statements"
    )
    parser.add_argument(
        "input_file",
        help="Path to text file or JSON file with statements"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file for bill references"
    )
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = BillExtractor()
    
    # Read input
    input_path = Path(args.input_file)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input_file}")
        return 1
    
    # Check if JSON or plain text
    if input_path.suffix == '.json':
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        if 'statements' in data:
            # Statements JSON format
            bills_by_statement = extractor.extract_from_statements(data['statements'])
            
            # Flatten to get all bills
            all_bills = []
            for bills in bills_by_statement.values():
                all_bills.extend(bills)
        else:
            logger.error("Invalid JSON format")
            return 1
    else:
        # Plain text file
        with open(input_path, 'r') as f:
            text = f.read()
        
        all_bills = extractor.extract_bill_references(text)
    
    # Print statistics
    stats = extractor.get_statistics(all_bills)
    
    print("\n" + "="*50)
    print("BILL EXTRACTION STATISTICS")
    print("="*50)
    print(f"Total bills found:      {stats['total_bills']}")
    print(f"Bills with numbers:     {stats['bills_with_numbers']}")
    print(f"Bills with years:       {stats['bills_with_years']}")
    print(f"Bills with types:       {stats['bills_with_types']}")
    
    if stats['bill_types']:
        print(f"\nBill types found:")
        for bill_type in stats['bill_types']:
            print(f"  - {bill_type}")
    
    print("="*50)
    
    # Print all bills
    if all_bills:
        print(f"\nBills found ({len(all_bills)}):")
        for bill in all_bills:
            formatted = extractor.format_bill_reference(bill)
            print(f"  - {formatted}")
    
    # Save output if requested
    if args.output:
        output_data = {
            'statistics': stats,
            'bills': [
                {
                    'bill_number': bill.bill_number,
                    'bill_year': bill.bill_year,
                    'bill_type': bill.bill_type,
                    'full_text': bill.full_text,
                    'position': bill.position,
                    'formatted': extractor.format_bill_reference(bill)
                }
                for bill in all_bills
            ]
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved to: {args.output}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
