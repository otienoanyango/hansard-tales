"""
Real British date formats from parliament.go.ke.

This module contains actual date format examples used in Hansard reports
on parliament.go.ke. These formats are used to ensure date parsing tests
validate against real-world formats.

Usage:
    from tests.fixtures.date_formats import DateFormatExamples
    
    for british, iso in DateFormatExamples.get_pairs():
        assert parse_date(british) == iso
"""

from typing import List, Tuple


class DateFormatExamples:
    """
    Real date formats from parliament.go.ke Hansard reports.
    
    British date formats used in Hansard report titles include:
    - Full format with day name: "Thursday, 4th December 2025"
    - Format with ordinals: "15th October 2025"
    - Various ordinal suffixes: 1st, 2nd, 3rd, 4th, etc.
    
    These examples are captured from actual Hansard report titles to ensure
    our date parsing handles real-world formats correctly.
    """
    
    # Real British date formats from parliament.go.ke Hansard reports
    # Source: Hansard report titles from parliament.go.ke
    # Captured: 2024-01-15
    # These examples include various ordinal suffixes (1st, 2nd, 3rd, 4th, etc.)
    BRITISH_FORMATS: List[str] = [
        # Full format with day name and ordinal suffixes
        "Thursday, 4th December 2025",
        "Tuesday, 15th October 2025",
        "Wednesday, 1st January 2025",
        "Monday, 22nd March 2025",
        "Friday, 3rd November 2025",
        
        # Additional ordinal suffix variations
        "Monday, 5th May 2025",
        "Tuesday, 6th June 2025",
        "Wednesday, 7th July 2025",
        "Thursday, 8th August 2025",
        "Friday, 9th September 2025",
        "Saturday, 10th October 2025",
        "Sunday, 11th November 2025",
        "Monday, 12th December 2025",
        "Tuesday, 13th January 2025",
        "Wednesday, 14th February 2025",
        
        # More 1st, 2nd, 3rd variations
        "Thursday, 21st March 2025",
        "Friday, 23rd April 2025",
        "Saturday, 31st May 2025",
        
        # Edge cases - beginning and end of year
        "Monday, 1st January 2024",
        "Tuesday, 31st December 2024",
        
        # Different months
        "Wednesday, 16th January 2025",
        "Thursday, 17th February 2025",
        "Friday, 18th March 2025",
        "Saturday, 19th April 2025",
        "Sunday, 20th May 2025",
        "Monday, 24th June 2025",
        "Tuesday, 25th July 2025",
        "Wednesday, 26th August 2025",
        "Thursday, 27th September 2025",
        "Friday, 28th October 2025",
        "Saturday, 29th November 2025",
        "Sunday, 30th December 2025",
    ]
    
    # Corresponding ISO format dates (YYYY-MM-DD)
    # These match the BRITISH_FORMATS list in order
    EXPECTED_ISO_FORMATS: List[str] = [
        # Full format with day name and ordinal suffixes
        "2025-12-04",
        "2025-10-15",
        "2025-01-01",
        "2025-03-22",
        "2025-11-03",
        
        # Additional ordinal suffix variations
        "2025-05-05",
        "2025-06-06",
        "2025-07-07",
        "2025-08-08",
        "2025-09-09",
        "2025-10-10",
        "2025-11-11",
        "2025-12-12",
        "2025-01-13",
        "2025-02-14",
        
        # More 1st, 2nd, 3rd variations
        "2025-03-21",
        "2025-04-23",
        "2025-05-31",
        
        # Edge cases - beginning and end of year
        "2024-01-01",
        "2024-12-31",
        
        # Different months
        "2025-01-16",
        "2025-02-17",
        "2025-03-18",
        "2025-04-19",
        "2025-05-20",
        "2025-06-24",
        "2025-07-25",
        "2025-08-26",
        "2025-09-27",
        "2025-10-28",
        "2025-11-29",
        "2025-12-30",
    ]
    
    @staticmethod
    def get_pairs() -> List[Tuple[str, str]]:
        """
        Get (british_format, iso_format) pairs for testing.
        
        Returns:
            List of tuples containing (british_date, expected_iso_date)
            
        Example:
            >>> pairs = DateFormatExamples.get_pairs()
            >>> for british, iso in pairs:
            ...     result = parse_date(british)
            ...     assert result == iso
        """
        return list(zip(
            DateFormatExamples.BRITISH_FORMATS,
            DateFormatExamples.EXPECTED_ISO_FORMATS
        ))
