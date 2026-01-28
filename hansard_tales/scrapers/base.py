"""
Base scraper framework for parliamentary documents.

This module provides the abstract base class for all document scrapers,
implementing common functionality like downloading, retry logic, and
duplicate detection.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import hashlib
import requests
import time

from hansard_tales.config.settings import ScraperConfig
from hansard_tales.models.base import Chamber


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
        self.session.headers.update({'User-Agent': config.user_agent})
    
    @abstractmethod
    def get_document_urls(
        self,
        chamber: Chamber,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[str]:
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
        
        This method implements exponential backoff retry logic for
        handling transient network errors.
        
        Args:
            url: Document URL to download
            
        Returns:
            ScrapedDocument with content and metadata
            
        Raises:
            requests.RequestException: If download fails after all retries
        """
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(
                    url,
                    timeout=self.config.timeout,
                    stream=True
                )
                response.raise_for_status()
                
                content = response.content
                doc_hash = hashlib.sha256(content).hexdigest()
                filename = self._generate_filename(url)
                metadata = self.extract_metadata(url, content)
                
                return ScrapedDocument(
                    url=url,
                    filename=filename,
                    content=content,
                    hash=doc_hash,
                    metadata=metadata
                )
            
            except requests.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise
                time.sleep(self.config.retry_delay * (2 ** attempt))
        
        # This should never be reached, but satisfies type checker
        raise requests.RequestException("Download failed after all retries")
    
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
        return url.split('/')[-1]
    
    def scrape(
        self,
        chamber: Chamber,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip_existing: bool = True,
        parliament_term: int = 2022
    ) -> List[ScrapedDocument]:
        """
        Scrape all documents in date range.
        
        This method orchestrates the complete scraping process:
        1. Get list of document URLs
        2. Download each document
        3. Skip duplicates if requested (checks downloaded_files table)
        4. Save document to filesystem
        5. Record download in database
        6. Continue on errors (log and skip failed documents)
        
        Args:
            chamber: Parliamentary chamber
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            skip_existing: Skip documents that already exist (by hash)
            parliament_term: Parliament term year for tracking
            
        Returns:
            List of successfully scraped documents
        """
        urls = self.get_document_urls(chamber, start_date, end_date)
        documents = []
        
        for url in urls:
            try:
                doc = self.download_document(url)
                
                # Skip if already downloaded (based on hash)
                if skip_existing and self._is_duplicate(doc.hash):
                    continue
                
                # Save document to filesystem
                file_path = self.save_document(doc, self.config.download_dir)
                
                # Record download in database
                self._record_download(doc, file_path, chamber, parliament_term)
                
                documents.append(doc)
                
            except Exception as e:
                # Log error but continue with remaining documents
                print(f"Error downloading {url}: {e}")
                continue
        
        return documents
        
        return documents
    
    def _is_duplicate(self, doc_hash: str) -> bool:
        """
        Check if document already exists (by hash).
        
        Queries the downloaded_files table to check if a document
        with the given hash has already been downloaded.
        
        Args:
            doc_hash: SHA256 hash of document
            
        Returns:
            True if document already exists in downloaded_files table
        """
        try:
            from hansard_tales.database.models import DownloadedFileORM
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from hansard_tales.config.settings import Config
            
            # Get database connection
            config = Config()
            engine = create_engine(config.database.connection_string)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                # Query for existing file
                existing = session.query(DownloadedFileORM).filter(
                    DownloadedFileORM.source_hash == doc_hash
                ).first()
                
                return existing is not None
            finally:
                session.close()
                
        except Exception:
            # If database is unavailable, assume not duplicate
            # This allows scraper to work without database
            return False
    
    def _record_download(
        self,
        doc: ScrapedDocument,
        file_path: Path,
        chamber: Chamber,
        parliament_term: int = 2022
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
            from hansard_tales.database.models import DownloadedFileORM
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from hansard_tales.config.settings import Config
            from datetime import datetime
            
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
                    original_filename=doc.metadata.get('original_filename', doc.filename),
                    file_size=len(doc.content),
                    document_type=doc.metadata['document_type'],
                    download_date=datetime.utcnow(),
                    file_path=str(file_path),
                    chamber=chamber.value,
                    parliament_term=parliament_term,
                    created_at=datetime.utcnow()
                )
                
                session.add(record)
                session.commit()
            finally:
                session.close()
                
        except Exception as e:
            # Log error but don't fail the download
            print(f"Warning: Failed to record download in database: {e}")
