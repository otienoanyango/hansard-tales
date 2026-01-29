"""
Base scraper framework for parliamentary documents.

This module provides the abstract base class for all document scrapers,
implementing common functionality like downloading, retry logic, and
duplicate detection.
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, date
from pathlib import Path

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from hansard_tales.config.settings import ScraperConfig
from hansard_tales.models.base import Chamber
from hansard_tales.utils.logging import get_logger

logger = get_logger(__name__)
# Create a standard logger for tenacity (it doesn't work with structlog)
_retry_logger = logging.getLogger(__name__)


@dataclass
class ScrapedDocument:
    """Result of scraping a single document."""

    url: str
    filename: str
    content: bytes
    hash: str
    metadata: dict


class DataCollectionError(Exception):
    """Exception raised when data collection fails."""

    pass


class BaseScraper(ABC):
    """
    Base class for all parliamentary document scrapers.

    This class provides common functionality for downloading documents
    from parliament.go.ke, including retry logic, duplicate detection,
    and error handling.

    Attributes:
        config: Scraper configuration
        session: HTTP session for making requests

    Example:
        >>> scraper = HansardScraper(config)
        >>> documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY)
    """

    def __init__(self, config: ScraperConfig):
        """
        Initialize scraper with configuration.

        Args:
            config: Scraper configuration
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})
        self.logger = get_logger(self.__class__.__name__)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError)),
        before_sleep=before_sleep_log(_retry_logger, logging.WARNING),
    )
    def _fetch_page_with_retry(self, url: str, timeout: int = 30) -> requests.Response:
        """
        Fetch a page with exponential backoff retry logic.

        Uses tenacity to retry up to 5 times with exponential backoff:
        - Attempt 1: immediate
        - Attempt 2: wait 1s
        - Attempt 3: wait 2s
        - Attempt 4: wait 4s
        - Attempt 5: wait 8s

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            Response object

        Raises:
            requests.RequestException: If all retries fail
        """
        self.logger.debug(f"Fetching: {url}")
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        return response

    @abstractmethod
    def get_document_urls(
        self, chamber: Chamber, start_date: date | None = None, end_date: date | None = None
    ) -> list[str]:
        """
        Get list of document URLs to download.

        This method must be implemented by subclasses to extract
        document URLs from parliament.go.ke pages.

        Args:
            chamber: Parliamentary chamber
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            List of document URLs

        Raises:
            DataCollectionError: If no documents found (indicates HTML/CSS changes)
        """
        pass

    @abstractmethod
    def extract_metadata(self, url: str, content: bytes) -> dict:
        """
        Extract metadata from document.

        Args:
            url: Document URL
            content: Document content

        Returns:
            Dictionary of metadata
        """
        pass

    def download_document(self, url: str) -> ScrapedDocument:
        """
        Download a single document with retry logic.

        This method uses tenacity for exponential backoff retry logic
        to handle transient network errors and slow server responses.

        Args:
            url: Document URL to download

        Returns:
            ScrapedDocument with content and metadata

        Raises:
            requests.RequestException: If download fails after all retries
        """
        response = self._fetch_page_with_retry(url, timeout=self.config.timeout)

        content = response.content
        doc_hash = hashlib.sha256(content).hexdigest()
        filename = self._generate_filename(url)
        metadata = self.extract_metadata(url, content)

        return ScrapedDocument(
            url=url, filename=filename, content=content, hash=doc_hash, metadata=metadata
        )

    def save_document(self, doc: ScrapedDocument, output_dir: Path) -> Path:
        """
        Save document to disk.

        Args:
            doc: Scraped document to save
            output_dir: Directory to save document in

        Returns:
            Path to saved document
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / doc.filename
        output_path.write_bytes(doc.content)
        return output_path

    def _generate_filename(self, url: str) -> str:
        """
        Generate filename from URL.

        Args:
            url: Document URL

        Returns:
            Filename extracted from URL
        """
        return url.split("/")[-1]

    def scrape(
        self,
        chamber: Chamber,
        start_date: date | None = None,
        end_date: date | None = None,
        skip_existing: bool = True,
        parliament_term: int = 2022,
    ) -> list[ScrapedDocument]:
        """
        Scrape all documents in date range using batch URL checking.

        Optimized workflow with batch database queries:
        1. Get list of all document URLs
        2. Batch query database to check which URLs exist (single query)
        3. For each URL:
           - If URL exists in DB and file exists in storage, skip
           - If URL exists in DB but file missing, download and update
           - If URL not in DB, download and insert new record
        4. Continue on errors (log and skip failed documents)

        Args:
            chamber: Parliamentary chamber
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            skip_existing: Skip documents that already exist (by URL)
            parliament_term: Parliament term year for tracking

        Returns:
            List of successfully scraped documents
        """
        urls = self.get_document_urls(chamber, start_date, end_date)
        documents = []

        # Batch check all URLs in database at once (more efficient)
        if skip_existing:
            url_status = self._batch_check_urls_in_db(urls)
        else:
            url_status = dict.fromkeys(urls, (False, None))

        for url in urls:
            try:
                exists_in_db, file_path = url_status.get(url, (False, None))

                if skip_existing and exists_in_db:
                    # URL exists in database, verify file exists in storage
                    if file_path and self._verify_file_exists(file_path):
                        # File exists in both database and storage, skip
                        continue
                    else:
                        # File in database but not storage, download and update
                        doc = self.download_document(url)
                        saved_path = self.save_document(doc, self.config.download_dir)
                        self._update_download_record(doc, saved_path, chamber, parliament_term)
                        documents.append(doc)
                else:
                    # URL not in database, download and insert new record
                    doc = self.download_document(url)
                    saved_path = self.save_document(doc, self.config.download_dir)
                    self._record_download(doc, saved_path, chamber, parliament_term)
                    documents.append(doc)

            except Exception as e:
                # Log error but continue with remaining documents
                print(f"Error downloading {url}: {e}")
                continue

        return documents

    def _batch_check_urls_in_db(self, urls: list[str]) -> dict[str, tuple[bool, Path | None]]:
        """
        Batch check if URLs exist in database and get their file paths.

        This is more efficient than checking URLs one at a time.

        Args:
            urls: List of URLs to check

        Returns:
            Dictionary mapping URL to (exists_in_db, file_path)
            where exists_in_db is True if URL is in database,
            and file_path is the Path if available, None otherwise
        """
        if not urls:
            return {}

        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            from hansard_tales.config.settings import Config
            from hansard_tales.database.models import DownloadedFileORM

            # Get database connection
            config = Config()
            engine = create_engine(config.database.connection_string)
            Session = sessionmaker(bind=engine)
            session = Session()

            try:
                # Batch query all URLs at once
                records = (
                    session.query(DownloadedFileORM)
                    .filter(DownloadedFileORM.source_url.in_(urls))
                    .all()
                )

                # Build result dictionary
                result = {}
                url_to_record = {record.source_url: record for record in records}

                for url in urls:
                    if url in url_to_record:
                        record = url_to_record[url]
                        file_path = Path(record.file_path) if record.file_path else None
                        result[url] = (True, file_path)
                    else:
                        result[url] = (False, None)

                return result
            finally:
                session.close()

        except Exception:
            # If database is unavailable, assume no URLs exist
            return dict.fromkeys(urls, (False, None))

    def _verify_file_exists(self, file_path: Path) -> bool:
        """
        Verify that a file exists in storage.

        Args:
            file_path: Path to file to check

        Returns:
            True if file exists, False otherwise
        """
        return file_path.exists() and file_path.is_file()

    def _is_duplicate(self, doc_hash: str) -> bool:
        """
        Check if document already exists (by hash).

        Queries the downloaded_files table to check if a document
        with the given hash has already been downloaded.

        Args:
            doc_hash: SHA256 hash of document

        Returns:
            True if document already exists in downloaded_files table

        Note:
            This method is deprecated in favor of _is_duplicate_by_url()
            which checks before downloading. Kept for backward compatibility.
        """
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            from hansard_tales.config.settings import Config
            from hansard_tales.database.models import DownloadedFileORM

            # Get database connection
            config = Config()
            engine = create_engine(config.database.connection_string)
            Session = sessionmaker(bind=engine)
            session = Session()

            try:
                # Query for existing file
                existing = (
                    session.query(DownloadedFileORM)
                    .filter(DownloadedFileORM.source_hash == doc_hash)
                    .first()
                )

                return existing is not None
            finally:
                session.close()

        except Exception:
            # If database is unavailable, assume not duplicate
            # This allows scraper to work without database
            return False

    def _record_download(
        self, doc: ScrapedDocument, file_path: Path, chamber: Chamber, parliament_term: int = 2022
    ) -> None:
        """
        Record downloaded file in database for duplicate tracking.

        Args:
            doc: Scraped document to record
            file_path: Path where file was saved
            chamber: Parliamentary chamber
            parliament_term: Parliament term year
        """
        try:
            from datetime import datetime

            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            from hansard_tales.config.settings import Config
            from hansard_tales.database.models import DownloadedFileORM

            # Get database connection
            config = Config()
            engine = create_engine(config.database.connection_string)
            Session = sessionmaker(bind=engine)
            session = Session()

            try:
                # Create record
                record = DownloadedFileORM(
                    source_url=doc.url,
                    source_hash=doc.hash,
                    standardized_filename=doc.filename,
                    original_filename=doc.metadata.get("original_filename", doc.filename),
                    file_size=len(doc.content),
                    document_type=doc.metadata["document_type"],
                    download_date=datetime.now(UTC),
                    file_path=str(file_path),
                    chamber=chamber.value,
                    parliament_term=parliament_term,
                    created_at=datetime.now(UTC),
                )

                session.add(record)
                session.commit()
            finally:
                session.close()

        except Exception as e:
            # Log error but don't fail the download
            print(f"Warning: Failed to record download in database: {e}")

    def _update_download_record(
        self, doc: ScrapedDocument, file_path: Path, chamber: Chamber, parliament_term: int = 2022
    ) -> None:
        """
        Update existing download record in database.

        Used when a file exists in the database but not in storage,
        so we re-download it and update the record.

        Args:
            doc: Scraped document to update
            file_path: Path where file was saved
            chamber: Parliamentary chamber
            parliament_term: Parliament term year
        """
        try:
            from datetime import datetime

            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            from hansard_tales.config.settings import Config
            from hansard_tales.database.models import DownloadedFileORM

            # Get database connection
            config = Config()
            engine = create_engine(config.database.connection_string)
            Session = sessionmaker(bind=engine)
            session = Session()

            try:
                # Find existing record by URL
                existing = (
                    session.query(DownloadedFileORM)
                    .filter(DownloadedFileORM.source_url == doc.url)
                    .first()
                )

                if existing:
                    # Update record
                    existing.source_hash = doc.hash
                    existing.file_size = len(doc.content)
                    existing.file_path = str(file_path)
                    existing.download_date = datetime.now(UTC)

                    session.commit()
            finally:
                session.close()

        except Exception as e:
            # Log error but don't fail the download
            print(f"Warning: Failed to update download record in database: {e}")
