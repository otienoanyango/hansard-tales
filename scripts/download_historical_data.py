#!/usr/bin/env python3
"""
Download historical parliamentary data from parliament.go.ke.

This script downloads Hansard, Votes & Proceedings, and MP data
for specified date ranges and parliament terms with progress tracking,
resume capability, and comprehensive error handling.

Usage:
    # Download all data for 2024
    python scripts/download_historical_data.py --year 2024

    # Download specific date range
    python scripts/download_historical_data.py --start-date 2024-01-01 --end-date 2024-12-31

    # Download specific document types
    python scripts/download_historical_data.py --year 2024 --types hansard votes

    # Download with custom workers
    python scripts/download_historical_data.py --year 2024 --workers 8

    # Resume interrupted download
    python scripts/download_historical_data.py --year 2024 --resume
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

from tqdm import tqdm

from hansard_tales.config.settings import Config
from hansard_tales.models.base import Chamber
from hansard_tales.scrapers.hansard import HansardScraper
from hansard_tales.scrapers.mp import MPScraper
from hansard_tales.scrapers.votes import VotesScraper
from hansard_tales.utils.logging import get_logger

logger = get_logger(__name__)


class HistoricalDataDownloader:
    """
    Download historical parliamentary data with progress tracking.

    This class manages downloading Hansard, Votes & Proceedings, and MP data
    for specified date ranges and parliament terms.

    Attributes:
        config: Application configuration
        scraper_config: Scraper configuration
        output_dir: Directory to save downloaded files
        resume: Whether to skip already downloaded files
    """

    # Parliament term mapping (start year -> term info)
    PARLIAMENT_TERMS = {
        2013: {"term": 11, "start": date(2013, 3, 28), "end": date(2017, 8, 8)},
        2017: {"term": 12, "start": date(2017, 8, 31), "end": date(2022, 9, 12)},
        2022: {"term": 13, "start": date(2022, 9, 13), "end": date(2027, 8, 31)},
    }

    def __init__(
        self,
        output_dir: Path | None = None,
        resume: bool = True,
        workers: int = 4,
        max_pages: int | None = None,
    ):
        """
        Initialize downloader.

        Args:
            output_dir: Directory to save downloaded files (default: data/pdfs)
            resume: Skip already downloaded files (default: True)
            workers: Number of parallel workers (not used yet, for future)
            max_pages: Maximum pages to scrape for MPs (None = all pages)
        """
        self.config = Config()
        self.scraper_config = self.config.scraper
        self.output_dir = output_dir or self.scraper_config.download_dir
        self.resume = resume
        self.workers = workers
        self.max_pages = max_pages

        # Statistics
        self.stats = {
            "hansard": {"total": 0, "downloaded": 0, "skipped": 0, "failed": 0},
            "votes": {"total": 0, "downloaded": 0, "skipped": 0, "failed": 0},
            "mps": {"total": 0, "downloaded": 0, "skipped": 0, "failed": 0},
        }

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_hansard(
        self,
        chamber: Chamber,
        start_date: date | None = None,
        end_date: date | None = None,
        parliament_term: int = 2022,
    ) -> int:
        """
        Download Hansard documents for date range.

        Args:
            chamber: Parliamentary chamber
            start_date: Start date for filtering
            end_date: End date for filtering
            parliament_term: Parliament term year

        Returns:
            Number of documents downloaded
        """
        logger.info(
            f"Downloading Hansard documents for {chamber.value} "
            f"(term: {parliament_term}, dates: {start_date} to {end_date})"
        )

        try:
            scraper = HansardScraper(config=self.scraper_config)
            documents = scraper.scrape(
                chamber=chamber,
                start_date=start_date,
                end_date=end_date,
                skip_existing=self.resume,
                parliament_term=parliament_term,
            )

            self.stats["hansard"]["downloaded"] += len(documents)
            return len(documents)

        except Exception as e:
            logger.error(f"Error downloading Hansard: {e}")
            self.stats["hansard"]["failed"] += 1
            return 0

    def download_votes(
        self,
        chamber: Chamber,
        start_date: date | None = None,
        end_date: date | None = None,
        parliament_term: int = 2022,
    ) -> int:
        """
        Download Votes & Proceedings documents for date range.

        Args:
            chamber: Parliamentary chamber
            start_date: Start date for filtering
            end_date: End date for filtering
            parliament_term: Parliament term year

        Returns:
            Number of documents downloaded
        """
        logger.info(
            f"Downloading Votes & Proceedings for {chamber.value} "
            f"(term: {parliament_term}, dates: {start_date} to {end_date})"
        )

        try:
            scraper = VotesScraper(config=self.scraper_config)
            documents = scraper.scrape(
                chamber=chamber,
                start_date=start_date,
                end_date=end_date,
                skip_existing=self.resume,
                parliament_term=parliament_term,
            )

            self.stats["votes"]["downloaded"] += len(documents)
            return len(documents)

        except Exception as e:
            logger.error(f"Error downloading Votes: {e}")
            self.stats["votes"]["failed"] += 1
            return 0

    def download_mps(
        self,
        chamber: Chamber,
        parliament_term: int = 2022,
        max_pages: int | None = None,
    ) -> int:
        """
        Download MP data for parliament term.

        Args:
            chamber: Parliamentary chamber
            parliament_term: Parliament term year
            max_pages: Maximum pages to scrape (None = all pages)

        Returns:
            Number of MPs downloaded
        """
        logger.info(f"Downloading MPs for {chamber.value} (term: {parliament_term})")

        try:
            scraper = MPScraper(chamber=chamber, config=self.scraper_config)
            mps = scraper.scrape_mps(parliament_term=parliament_term, max_pages=max_pages)

            # Store MPs in database
            stored = scraper.store_mps(mps)

            self.stats["mps"]["downloaded"] += stored
            return stored

        except Exception as e:
            logger.error(f"Error downloading MPs: {e}")
            self.stats["mps"]["failed"] += 1
            return 0

    def download_for_year(
        self,
        year: int,
        document_types: list[str],
        chamber: Chamber = Chamber.NATIONAL_ASSEMBLY,
    ) -> dict:
        """
        Download all documents for a specific year.

        Args:
            year: Year to download
            document_types: List of document types to download
            chamber: Parliamentary chamber

        Returns:
            Dictionary with download statistics
        """
        # Get parliament term for year
        term_info = self._get_parliament_term(year)
        if not term_info:
            logger.error(f"No parliament term found for year {year}")
            return self.stats

        parliament_term = term_info["term_start_year"]
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Ensure dates are within term bounds
        if start_date < term_info["start"]:
            start_date = term_info["start"]
        if end_date > term_info["end"]:
            end_date = term_info["end"]

        logger.info(f"Downloading data for year {year} (term {parliament_term})")
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Document types: {', '.join(document_types)}")

        # Download each document type
        with tqdm(total=len(document_types), desc=f"Year {year}") as pbar:
            if "hansard" in document_types:
                self.download_hansard(chamber, start_date, end_date, parliament_term)
                pbar.update(1)

            if "votes" in document_types:
                self.download_votes(chamber, start_date, end_date, parliament_term)
                pbar.update(1)

            if "mps" in document_types:
                self.download_mps(chamber, parliament_term, max_pages=self.max_pages)
                pbar.update(1)

        return self.stats

    def download_for_date_range(
        self,
        start_date: date,
        end_date: date,
        document_types: list[str],
        chamber: Chamber = Chamber.NATIONAL_ASSEMBLY,
    ) -> dict:
        """
        Download documents for specific date range.

        Args:
            start_date: Start date
            end_date: End date
            document_types: List of document types to download
            chamber: Parliamentary chamber

        Returns:
            Dictionary with download statistics
        """
        # Get parliament term for date range
        term_info = self._get_parliament_term(start_date.year)
        if not term_info:
            logger.error(f"No parliament term found for date {start_date}")
            return self.stats

        parliament_term = term_info["term_start_year"]

        logger.info(f"Downloading data for date range {start_date} to {end_date}")
        logger.info(f"Parliament term: {parliament_term}")
        logger.info(f"Document types: {', '.join(document_types)}")

        # Download each document type
        with tqdm(total=len(document_types), desc="Date range") as pbar:
            if "hansard" in document_types:
                self.download_hansard(chamber, start_date, end_date, parliament_term)
                pbar.update(1)

            if "votes" in document_types:
                self.download_votes(chamber, start_date, end_date, parliament_term)
                pbar.update(1)

            if "mps" in document_types:
                self.download_mps(chamber, parliament_term, max_pages=self.max_pages)
                pbar.update(1)

        return self.stats

    def download_for_parliament_terms(
        self,
        start_year: int,
        end_year: int,
        document_types: list[str],
        chamber: Chamber = Chamber.NATIONAL_ASSEMBLY,
    ) -> dict:
        """
        Download documents for multiple parliament terms.

        Args:
            start_year: Start year (inclusive)
            end_year: End year (inclusive)
            document_types: List of document types to download
            chamber: Parliamentary chamber

        Returns:
            Dictionary with download statistics
        """
        logger.info(f"Downloading data for years {start_year} to {end_year}")

        # Get all parliament terms in range
        terms = []
        for term_start_year in self.PARLIAMENT_TERMS:
            if start_year <= term_start_year <= end_year:
                terms.append(term_start_year)

        if not terms:
            logger.error(f"No parliament terms found for years {start_year}-{end_year}")
            return self.stats

        # Download for each term
        with tqdm(total=len(terms), desc="Parliament terms") as pbar:
            for term_start_year in terms:
                term_info = self.PARLIAMENT_TERMS[term_start_year]

                # Calculate date range for this term within requested years
                start_date = max(term_info["start"], date(start_year, 1, 1))
                end_date = min(term_info["end"], date(end_year, 12, 31))

                logger.info(
                    f"Processing term {term_info['term']} "
                    f"({term_start_year}): {start_date} to {end_date}"
                )

                # Download for this term
                if "hansard" in document_types:
                    self.download_hansard(chamber, start_date, end_date, term_start_year)

                if "votes" in document_types:
                    self.download_votes(chamber, start_date, end_date, term_start_year)

                if "mps" in document_types:
                    self.download_mps(chamber, term_start_year, max_pages=self.max_pages)

                pbar.update(1)

        return self.stats

    def _get_parliament_term(self, year: int) -> dict | None:
        """
        Get parliament term info for a given year.

        Args:
            year: Year to look up

        Returns:
            Dictionary with term info or None if not found
        """
        for term_start_year, term_info in self.PARLIAMENT_TERMS.items():
            if term_info["start"].year <= year <= term_info["end"].year:
                return {
                    "term": term_info["term"],
                    "term_start_year": term_start_year,
                    "start": term_info["start"],
                    "end": term_info["end"],
                }
        return None

    def print_summary(self) -> None:
        """Print download summary statistics."""
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)

        for doc_type, stats in self.stats.items():
            print(f"\n{doc_type.upper()}:")
            print(f"  Downloaded: {stats['downloaded']}")
            print(f"  Skipped:    {stats['skipped']}")
            print(f"  Failed:     {stats['failed']}")
            print(f"  Total:      {stats['total']}")

        total_downloaded = sum(s["downloaded"] for s in self.stats.values())
        total_failed = sum(s["failed"] for s in self.stats.values())

        print(f"\nTOTAL DOWNLOADED: {total_downloaded}")
        print(f"TOTAL FAILED:     {total_failed}")
        print("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Download historical parliamentary data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Date range options
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        "--year",
        type=int,
        help="Download data for specific year (e.g., 2024)",
    )
    date_group.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD)",
    )
    date_group.add_argument(
        "--parliament-terms",
        type=str,
        help="Parliament term range (e.g., 2013-2024)",
    )

    parser.add_argument(
        "--end-date",
        type=str,
        help="End date (YYYY-MM-DD), required with --start-date",
    )

    # Document types
    parser.add_argument(
        "--types",
        nargs="+",
        choices=["hansard", "votes", "mps", "all"],
        default=["all"],
        help="Document types to download (default: all)",
    )

    # Chamber
    parser.add_argument(
        "--chamber",
        choices=["national_assembly", "senate"],
        default="national_assembly",
        help="Parliamentary chamber (default: national_assembly)",
    )

    # Options
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Skip already downloaded files (default: True)",
    )
    parser.add_argument(
        "--no-resume",
        action="store_false",
        dest="resume",
        help="Redownload all files",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for downloaded files",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Maximum pages to scrape for MPs (for testing, default: all pages)",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.start_date and not args.end_date:
        parser.error("--end-date is required when using --start-date")

    return args


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Parse document types
    document_types = args.types
    if "all" in document_types:
        document_types = ["hansard", "votes", "mps"]

    # Parse chamber
    chamber = Chamber.NATIONAL_ASSEMBLY
    if args.chamber == "senate":
        chamber = Chamber.SENATE

    # Create downloader
    downloader = HistoricalDataDownloader(
        output_dir=args.output_dir,
        resume=args.resume,
        workers=args.workers,
        max_pages=args.max_pages,
    )

    try:
        # Download based on arguments
        if args.year:
            downloader.download_for_year(args.year, document_types, chamber)

        elif args.start_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
            downloader.download_for_date_range(start_date, end_date, document_types, chamber)

        elif args.parliament_terms:
            start_year, end_year = map(int, args.parliament_terms.split("-"))
            downloader.download_for_parliament_terms(start_year, end_year, document_types, chamber)

        # Print summary
        downloader.print_summary()

        return 0

    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
        downloader.print_summary()
        return 1

    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
