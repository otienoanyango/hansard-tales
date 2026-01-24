"""
Filename generator for standardized Hansard PDF filenames.

This module provides functionality to generate and parse standardized
Hansard PDF filenames with the format: hansard_YYYYMMDD_{A|P|E}.pdf

The filename format includes:
- Date in YYYYMMDD format
- Period-of-day indicator (A=Afternoon, P=Morning, E=Evening)
- Optional numeric suffix for duplicate dates/periods
"""

import re
from typing import Dict, List, Optional


class FilenameGenerator:
    """
    Generate and parse standardized Hansard filenames.
    
    This class handles the generation of filenames in the format:
    hansard_YYYYMMDD_{A|P|E}.pdf
    
    When a file with the same date and period already exists, a numeric
    suffix is appended: hansard_YYYYMMDD_A_2.pdf
    
    Example:
        >>> generator = FilenameGenerator()
        >>> filename = generator.generate("2024-01-01", "A", [])
        >>> print(filename)
        'hansard_20240101_A.pdf'
        
        >>> # With existing file
        >>> existing = ["hansard_20240101_A.pdf"]
        >>> filename = generator.generate("2024-01-01", "A", existing)
        >>> print(filename)
        'hansard_20240101_A_2.pdf'
    """
    
    # Regex pattern for parsing standardized filenames
    FILENAME_PATTERN = re.compile(r'^hansard_(\d{8})_([APE])(?:_(\d+))?\.pdf$')
    
    def generate(
        self,
        date: str,
        period_of_day: str,
        existing_files: List[str]
    ) -> str:
        """
        Generate standardized filename: hansard_YYYYMMDD_{A|P|E}.pdf
        
        If a file with the same date and period already exists, append a
        numeric suffix starting from 2: hansard_YYYYMMDD_A_2.pdf
        
        Args:
            date: Date in YYYY-MM-DD format
            period_of_day: Period code ('A', 'P', or 'E')
            existing_files: List of existing filenames to check for conflicts
            
        Returns:
            Standardized filename string
            
        Raises:
            ValueError: If date format is invalid or period_of_day is not A/P/E
            
        Example:
            >>> generator = FilenameGenerator()
            >>> generator.generate("2024-01-01", "A", [])
            'hansard_20240101_A.pdf'
            
            >>> existing = ["hansard_20240101_A.pdf"]
            >>> generator.generate("2024-01-01", "A", existing)
            'hansard_20240101_A_2.pdf'
        """
        # Validate period_of_day
        if period_of_day not in ('A', 'P', 'E'):
            raise ValueError(
                f"Invalid period_of_day: {period_of_day}. "
                "Must be 'A', 'P', or 'E'"
            )
        
        # Convert date from YYYY-MM-DD to YYYYMMDD
        date_compact = self._convert_date_to_compact(date)
        
        # Generate base filename
        base_filename = f"hansard_{date_compact}_{period_of_day}.pdf"
        
        # Check if base filename exists
        if base_filename not in existing_files:
            return base_filename
        
        # Find the next available suffix
        suffix = 2
        while True:
            filename_with_suffix = f"hansard_{date_compact}_{period_of_day}_{suffix}.pdf"
            if filename_with_suffix not in existing_files:
                return filename_with_suffix
            suffix += 1
    
    def parse(self, filename: str) -> Dict[str, Optional[str]]:
        """
        Parse standardized filename to extract components.
        
        Extracts date, period_of_day, and suffix from a filename in the
        format: hansard_YYYYMMDD_{A|P|E}[_N].pdf
        
        Args:
            filename: Filename to parse
            
        Returns:
            Dictionary with keys:
            - 'date': Date in YYYY-MM-DD format (or None if invalid)
            - 'period_of_day': Period code 'A', 'P', or 'E' (or None if invalid)
            - 'suffix': Numeric suffix as string (or None if no suffix)
            
        Example:
            >>> generator = FilenameGenerator()
            >>> result = generator.parse("hansard_20240101_A.pdf")
            >>> print(result)
            {'date': '2024-01-01', 'period_of_day': 'A', 'suffix': None}
            
            >>> result = generator.parse("hansard_20240101_A_2.pdf")
            >>> print(result)
            {'date': '2024-01-01', 'period_of_day': 'A', 'suffix': '2'}
        """
        match = self.FILENAME_PATTERN.match(filename)
        
        if not match:
            return {
                'date': None,
                'period_of_day': None,
                'suffix': None
            }
        
        date_compact = match.group(1)
        period_of_day = match.group(2)
        suffix = match.group(3)
        
        # Convert date from YYYYMMDD to YYYY-MM-DD
        date = self._convert_date_from_compact(date_compact)
        
        return {
            'date': date,
            'period_of_day': period_of_day,
            'suffix': suffix
        }
    
    def _convert_date_to_compact(self, date: str) -> str:
        """
        Convert date from YYYY-MM-DD to YYYYMMDD format.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            Date string in YYYYMMDD format
            
        Raises:
            ValueError: If date format is invalid
        """
        # Validate date format
        date_pattern = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')
        match = date_pattern.match(date)
        
        if not match:
            raise ValueError(
                f"Invalid date format: {date}. Expected YYYY-MM-DD"
            )
        
        year, month, day = match.groups()
        
        # Validate month and day ranges
        month_int = int(month)
        day_int = int(day)
        
        if not (1 <= month_int <= 12):
            raise ValueError(
                f"Invalid month: {month}. Must be between 01 and 12"
            )
        
        if not (1 <= day_int <= 31):
            raise ValueError(
                f"Invalid day: {day}. Must be between 01 and 31"
            )
        
        return f"{year}{month}{day}"
    
    def _convert_date_from_compact(self, date_compact: str) -> str:
        """
        Convert date from YYYYMMDD to YYYY-MM-DD format.
        
        Args:
            date_compact: Date string in YYYYMMDD format
            
        Returns:
            Date string in YYYY-MM-DD format
        """
        year = date_compact[:4]
        month = date_compact[4:6]
        day = date_compact[6:8]
        
        return f"{year}-{month}-{day}"
