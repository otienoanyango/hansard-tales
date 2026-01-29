#!/usr/bin/env python3
"""Fix BeautifulSoup AttributeValueList type issues."""

import re
from pathlib import Path


def fix_href_type_checks(file_path: Path) -> None:
    """Add isinstance checks for href attributes."""
    content = file_path.read_text()

    # Pattern 1: href = link["href"] or link.get("href")
    # Add type check after getting href
    patterns = [
        # After href = link["href"]
        (
            r'(\s+)href = link\["href"\]\n(\s+)\n(\s+)# Validate',
            r'\1href = link["href"]\n\1\n\1# Type narrow: href can be str or list, ensure it\'s str\n\1if not isinstance(href, str):\n\1    continue\n\1\n\3# Validate',
        ),
        # After href = link.get("href", "")
        (
            r'(\s+)href = link\.get\("href", ""\)\n(\s+)match = re\.search',
            r'\1href = link.get("href", "")\n\1# Type narrow: ensure href is str\n\1if not isinstance(href, str):\n\1    continue\n\2match = re.search',
        ),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    file_path.write_text(content)
    print(f"Fixed {file_path}")


def main() -> None:
    """Fix all scraper files."""
    scraper_files = [
        Path("hansard_tales/scrapers/hansard.py"),
        Path("hansard_tales/scrapers/mp.py"),
    ]

    for file_path in scraper_files:
        if file_path.exists():
            fix_href_type_checks(file_path)


if __name__ == "__main__":
    main()
