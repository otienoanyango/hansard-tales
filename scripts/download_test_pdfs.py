"""
Download sample PDFs from parliament.go.ke for testing.

This script downloads a few real PDFs to use in tests instead of mocking.
"""

import re
import time
import urllib.parse
from pathlib import Path

import requests


def download_sample_pdfs():
    """Download sample PDFs for testing."""
    # Read sample HTML
    html_path = Path("tests/sample_html.txt")
    if not html_path.exists():
        print("Error: tests/sample_html.txt not found")
        return

    html = html_path.read_text()

    # Extract URLs
    urls = re.findall(r'href="(https://www\.parliament\.go\.ke/[^"]+\.pdf)"', html)

    print(f"Found {len(urls)} PDF URLs")

    # Download first 3 Hansard PDFs for testing
    hansard_dir = Path("tests/data/pdfs/hansard")
    hansard_dir.mkdir(parents=True, exist_ok=True)

    # Download first 3 PDFs
    for i, url in enumerate(urls[:3]):
        try:
            print(f"\nDownloading {i+1}/3: {url}")

            # Extract filename from URL
            filename = urllib.parse.unquote(url.split("/")[-1])

            # Generate standardized filename
            date_match = re.search(r"(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s*,?\s*\d{4})", filename)
            period_match = re.search(r"\(([APE])\)", filename, re.IGNORECASE)

            if date_match and period_match:
                import dateparser

                date_str = date_match.group(1)
                period = period_match.group(1).upper()

                parsed_date = dateparser.parse(
                    date_str,
                    settings={"TIMEZONE": "Africa/Nairobi", "RETURN_AS_TIMEZONE_AWARE": False},
                )

                if parsed_date:
                    standardized = f"hansard_{parsed_date.strftime('%Y%m%d')}_{period}.pdf"
                else:
                    standardized = filename
            else:
                standardized = filename

            # Download
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Save
            output_path = hansard_dir / standardized
            output_path.write_bytes(response.content)

            print(f"  Saved as: {standardized}")
            print(f"  Size: {len(response.content):,} bytes")

            # Be nice to the server
            time.sleep(1)

        except Exception as e:
            print(f"  Error: {e}")
            continue

    print(f"\n✅ Downloaded {len(list(hansard_dir.glob('*.pdf')))} PDFs to {hansard_dir}")


if __name__ == "__main__":
    download_sample_pdfs()
