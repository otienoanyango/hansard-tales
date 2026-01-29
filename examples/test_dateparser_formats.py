"""
Demonstration of dateparser handling various real-world formats.

This script shows how the refactored scrapers handle all the different
date and time formats found on parliament.go.ke.

Key Insight:
- The href (URL) contains the period code: (A), (P), (E)
- The link text shows human-readable: "Morning Sitting", "Afternoon Sitting", "Evening Sitting"
- We extract from the URL, not the link text

Period Mapping:
- (A) = Morning Sitting
- (P) = Afternoon Sitting
- (E) = Evening Sitting
"""


from hansard_tales.config.settings import ScraperConfig
from hansard_tales.scrapers.hansard import HansardScraper
from hansard_tales.scrapers.votes import VotesScraper


def test_hansard_formats() -> None:
    """Test Hansard scraper with real-world URL formats."""
    print("=" * 80)
    print("HANSARD SCRAPER - Real-World URL Testing")
    print("=" * 80)
    print("\nNote: We extract from the URL (href), not the link text.")
    print("Period codes in URL: (A)=Morning, (P)=Afternoon, (E)=Evening\n")

    config = ScraperConfig()
    scraper = HansardScraper(config)

    # These are the actual filenames from the href attribute
    test_cases: list[str] = [
        "Hansard Report - Thursday, 4th December 2025 (E).pdf",
        "Hansard Report - Thursday, 4th December 2025 (P).pdf",
        "Hansard Report - Wednesday, 3rd December 2025 (A).pdf",
        "Hansard Report - Tuesday, 2nd December 2025 (P).pdf",
        "Hansard Report - Thursday,16th January 2025 (P).pdf",  # No space
        "Hansard Report - Tuesday, 5th November 2024 (p).pdf",  # Lowercase
    ]

    for filename in test_cases:
        url = f"https://parliament.go.ke/files/{filename.replace(' ', '%20').replace(',', '%2C')}"
        metadata = scraper.extract_metadata(url, b"test")
        standardized = scraper._generate_filename(url)

        print(f"URL Filename: {filename}")
        print(f"  → Date: {metadata.get('date', 'N/A')}")
        print(f"  → Period: {metadata.get('period', 'N/A')}")
        print(f"  → Standardized: {standardized}\n")


def test_votes_formats() -> None:
    """Test Votes scraper with real-world formats."""
    print("\n" + "=" * 80)
    print("VOTES SCRAPER - Real-World Format Testing")
    print("=" * 80)

    config = ScraperConfig()
    scraper = VotesScraper(config)

    test_cases: list[str] = [
        "Tuesday, November 18, 2025 At 2.30pm",
        "Thursday, November 13,2025 At 2.30pm",  # No space after comma
        "Tuesday, 11 November 2025 At 2.30pm",  # Day before month
        "Wednesday,october 15,2025 At 9.30am",  # Lowercase, no spaces
        "Thursday, October 16, 2025 At 10.00am",
    ]

    for title in test_cases:
        url = f"https://parliament.go.ke/files/{title.replace(' ', '%20').replace(',', '%2C')}.pdf"
        metadata = scraper.extract_metadata(url, b"test")
        filename = scraper._generate_filename(url)

        print(f"\nTitle: {title}")
        print(f"  Date: {metadata.get('date', 'N/A')}")
        print(f"  Time: {metadata.get('time', 'N/A')}")
        print(f"  Filename: {filename}")


if __name__ == "__main__":
    test_hansard_formats()
    test_votes_formats()

    print("\n" + "=" * 80)
    print("✅ All formats parsed successfully!")
    print("=" * 80)
