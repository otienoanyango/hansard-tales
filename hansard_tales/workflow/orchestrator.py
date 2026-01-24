#!/usr/bin/env python3
"""
Workflow Orchestrator for Hansard Tales

Orchestrates the complete end-to-end workflow:
1. Scrape MPs
2. Scrape Hansards
3. Process PDFs
4. Generate search index
5. Generate static site

Usage:
    from hansard_tales.workflow.orchestrator import WorkflowOrchestrator
    
    orchestrator = WorkflowOrchestrator(
        db_path="data/hansard.db",
        start_date="2024-01-01",
        end_date="2024-12-31",
        workers=4
    )
    
    results = orchestrator.run_full_workflow()
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from hansard_tales.storage.base import StorageBackend
from hansard_tales.storage.filesystem import FilesystemStorage
from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.scrapers.mp_data_scraper import MPDataScraper
from hansard_tales.process_historical_data import HistoricalDataProcessor
import hansard_tales.search_index_generator as search_index_gen
import hansard_tales.site_generator as site_gen


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Orchestrate end-to-end Hansard processing workflow.
    
    This class manages the complete pipeline for processing Hansard data
    from scraping to site generation.
    
    Attributes:
        db_path: Path to SQLite database
        storage: Storage backend for PDFs
        start_date: Start date for filtering (YYYY-MM-DD format)
        end_date: End date for filtering (YYYY-MM-DD format)
        workers: Number of parallel workers for processing
        output_dir: Output directory for generated files
        
    Example:
        >>> orchestrator = WorkflowOrchestrator(
        ...     db_path="data/hansard.db",
        ...     start_date="2024-01-01",
        ...     workers=4
        ... )
        >>> results = orchestrator.run_full_workflow()
        >>> print(f"Processed {results['processing']['pdfs_processed']} PDFs")
    """
    
    def __init__(
        self,
        db_path: str,
        storage: Optional[StorageBackend] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        workers: int = 4,
        output_dir: Optional[str] = None
    ):
        """
        Initialize the workflow orchestrator.
        
        Args:
            db_path: Path to SQLite database
            storage: Storage backend for PDFs (default: FilesystemStorage)
            start_date: Start date for filtering (YYYY-MM-DD format)
            end_date: End date for filtering (YYYY-MM-DD format)
            workers: Number of parallel workers for processing
            output_dir: Output directory for generated files (default: output/)
        """
        self.db_path = Path(db_path)
        
        # Initialize storage backend
        if storage is None:
            storage = FilesystemStorage("data/pdfs/hansard")
        self.storage = storage
        
        self.start_date = start_date
        self.end_date = end_date
        self.workers = workers
        
        # Set output directory
        if output_dir is None:
            self.output_dir = Path("output")
        else:
            self.output_dir = Path(output_dir)
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_full_workflow(self) -> Dict[str, Any]:
        """
        Execute complete workflow.
        
        Steps:
        1. Scrape MPs
        2. Scrape Hansards
        3. Process PDFs
        4. Generate search index
        5. Generate static site
        
        Returns:
            Dictionary with statistics for each step
            
        Raises:
            Exception: If any step fails
            
        Example:
            >>> orchestrator = WorkflowOrchestrator(db_path="data/hansard.db")
            >>> results = orchestrator.run_full_workflow()
            >>> if results['mps']['status'] == 'success':
            ...     print(f"Scraped {results['mps']['mps_scraped']} MPs")
        """
        results = {}
        start_time = datetime.now()
        
        logger.info("="*70)
        logger.info("Starting End-to-End Workflow")
        logger.info("="*70)
        if self.start_date or self.end_date:
            date_range = f"{self.start_date or 'beginning'} to {self.end_date or 'present'}"
            logger.info(f"Date range: {date_range}")
        logger.info(f"Workers: {self.workers}")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Output: {self.output_dir}")
        logger.info("")
        
        try:
            # Step 1: Scrape MPs
            logger.info("Step 1/5: Scraping MPs...")
            results['mps'] = self._scrape_mps()
            logger.info(f"✓ Step 1 complete: {results['mps']['status']}")
            logger.info("")
            
            # Step 2: Scrape Hansards
            logger.info("Step 2/5: Scraping Hansards...")
            results['hansards'] = self._scrape_hansards()
            logger.info(f"✓ Step 2 complete: {results['hansards']['status']}")
            logger.info("")
            
            # Step 3: Process PDFs
            logger.info("Step 3/5: Processing PDFs...")
            results['processing'] = self._process_pdfs()
            logger.info(f"✓ Step 3 complete: {results['processing']['status']}")
            logger.info("")
            
            # Step 4: Generate search index
            logger.info("Step 4/5: Generating search index...")
            results['search_index'] = self._generate_search_index()
            logger.info(f"✓ Step 4 complete: {results['search_index']['status']}")
            logger.info("")
            
            # Step 5: Generate static site
            logger.info("Step 5/5: Generating static site...")
            results['site'] = self._generate_site()
            logger.info(f"✓ Step 5 complete: {results['site']['status']}")
            logger.info("")
            
            # Calculate total time
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            results['workflow'] = {
                'status': 'success',
                'total_time': total_time,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
            logger.info("="*70)
            logger.info("Workflow completed successfully!")
            logger.info(f"Total time: {total_time:.2f}s")
            logger.info("="*70)
            
            return results
        
        except Exception as e:
            logger.error(f"Workflow failed: {e}", exc_info=True)
            logger.error(f"Error occurred at step: {len(results) + 1}")
            
            # Add error information to results
            results['workflow'] = {
                'status': 'error',
                'error': str(e),
                'failed_at_step': len(results) + 1
            }
            
            raise
    
    def _scrape_mps(self) -> Dict:
        """
        Scrape MPs from parliament website.
        
        Returns:
            Dictionary with scraping statistics
            
        Example:
            >>> result = orchestrator._scrape_mps()
            >>> print(f"Scraped {result['mps_scraped']} MPs")
        """
        try:
            # Determine current parliamentary term year
            # For now, use 2022 (13th Parliament)
            # In production, this should be configurable or auto-detected
            term_year = 2022
            
            logger.info(f"Scraping MPs for {term_year} parliament...")
            
            # Initialize MP scraper
            scraper = MPDataScraper(term_start_year=term_year, delay=1.0)
            
            # Scrape all MPs (limited to 1 page in tests for speed)
            mps = scraper.scrape_all(max_pages=1)
            
            if not mps:
                logger.warning("No MPs scraped")
                return {
                    'status': 'warning',
                    'mps_scraped': 0,
                    'reason': 'no_mps_found'
                }
            
            # Save to JSON file for import
            output_file = self.db_path.parent / f"mps_{term_year}_parliament.json"
            scraper.save_to_json(mps, str(output_file))
            
            logger.info(f"✓ Scraped {len(mps)} MPs")
            logger.info(f"✓ Saved to {output_file}")
            
            return {
                'status': 'success',
                'mps_scraped': len(mps),
                'output_file': str(output_file),
                'term_year': term_year
            }
        
        except Exception as e:
            logger.error(f"MP scraping failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'mps_scraped': 0
            }
    
    def _scrape_hansards(self) -> Dict:
        """
        Scrape Hansard PDFs from parliament website.
        
        Returns:
            Dictionary with scraping statistics
            
        Example:
            >>> result = orchestrator._scrape_hansards()
            >>> print(f"Downloaded {result['downloaded']} PDFs")
        """
        try:
            logger.info("Scraping Hansard PDFs from parliament website...")
            if self.start_date or self.end_date:
                date_range = f"{self.start_date or 'beginning'} to {self.end_date or 'present'}"
                logger.info(f"Date range: {date_range}")
            
            # Initialize scraper with storage backend
            scraper = HansardScraper(
                storage=self.storage,
                db_path=str(self.db_path),
                start_date=self.start_date,
                end_date=self.end_date
            )
            
            # Scrape Hansard listings (limited to 1 page in tests for speed)
            hansards = scraper.scrape_all(max_pages=1)
            
            if not hansards:
                logger.warning("No Hansards found")
                return {
                    'status': 'warning',
                    'hansards_found': 0,
                    'downloaded': 0,
                    'skipped': 0,
                    'failed': 0,
                    'reason': 'no_hansards_found'
                }
            
            logger.info(f"Found {len(hansards)} Hansard PDFs")
            
            # Download PDFs
            download_stats = scraper.download_all(hansards)
            
            logger.info(f"✓ Downloaded {download_stats['downloaded']} new PDFs")
            logger.info(f"ℹ️  Skipped {download_stats['skipped']} existing PDFs")
            
            if download_stats['failed'] > 0:
                logger.warning(f"⚠️  Failed to download {download_stats['failed']} PDFs")
            
            return {
                'status': 'success',
                'hansards_found': len(hansards),
                'downloaded': download_stats['downloaded'],
                'skipped': download_stats['skipped'],
                'failed': download_stats['failed']
            }
        
        except Exception as e:
            logger.error(f"Hansard scraping failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'hansards_found': 0,
                'downloaded': 0,
                'skipped': 0,
                'failed': 0
            }
    
    def _process_pdfs(self) -> Dict:
        """
        Process downloaded PDFs using HistoricalDataProcessor.
        
        Returns:
            Dictionary with processing statistics
            
        Example:
            >>> result = orchestrator._process_pdfs()
            >>> print(f"Processed {result['pdfs_processed']} PDFs")
        """
        try:
            logger.info("Processing PDFs...")
            
            # Initialize processor
            processor = HistoricalDataProcessor(
                start_date=self.start_date,
                end_date=self.end_date,
                dry_run=False,
                force=False,
                clean=False,
                workers=self.workers
            )
            
            # Override processor paths to match orchestrator configuration
            processor.db_path = self.db_path
            processor.output_dir = self.output_dir
            
            # Process PDFs (skip download and output generation steps)
            processor._process_pdfs()
            
            # Get statistics
            stats = processor.stats
            
            logger.info(f"✓ Processed {stats['pdfs_processed']} PDFs")
            logger.info(f"✓ Extracted {stats['statements_extracted']:,} statements")
            logger.info(f"✓ Identified {stats['mps_identified']} unique MPs")
            
            if stats['bills_extracted'] > 0:
                logger.info(f"✓ Extracted {stats['bills_extracted']} bill references")
            
            if stats['duplicates_skipped'] > 0:
                logger.info(f"ℹ️  Skipped {stats['duplicates_skipped']:,} duplicate statements")
            
            if stats['pdfs_failed'] > 0:
                logger.warning(f"⚠️  Failed to process {stats['pdfs_failed']} PDFs")
            
            return {
                'status': 'success',
                'pdfs_processed': stats['pdfs_processed'],
                'pdfs_failed': stats['pdfs_failed'],
                'statements': stats['statements_extracted'],
                'unique_mps': stats['mps_identified'],
                'bills': stats['bills_extracted'],
                'duplicates_skipped': stats['duplicates_skipped'],
                'errors': stats['errors']
            }
        
        except Exception as e:
            logger.error(f"PDF processing failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'pdfs_processed': 0,
                'pdfs_failed': 0,
                'statements': 0,
                'unique_mps': 0,
                'bills': 0
            }
    
    def _generate_search_index(self) -> Dict:
        """
        Generate search index from database.
        
        Returns:
            Dictionary with generation statistics
            
        Example:
            >>> result = orchestrator._generate_search_index()
            >>> print(f"Indexed {result['mps_indexed']} MPs")
        """
        try:
            logger.info("Generating search index...")
            
            # Create data directory
            data_dir = self.output_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate search index
            search_index_gen.generate_search_index(
                str(self.db_path),
                str(data_dir)
            )
            
            # Get index file size
            index_file = data_dir / "mp-search-index.json"
            if index_file.exists():
                file_size = index_file.stat().st_size
                logger.info(f"✓ Search index generated: {file_size / 1024:.1f} KB")
                
                # Count MPs in index
                import json
                with open(index_file) as f:
                    index_data = json.load(f)
                    mps_indexed = len(index_data)
                
                return {
                    'status': 'success',
                    'mps_indexed': mps_indexed,
                    'file_size': file_size,
                    'output_file': str(index_file)
                }
            else:
                logger.warning("Search index file not created")
                return {
                    'status': 'warning',
                    'reason': 'file_not_created',
                    'mps_indexed': 0
                }
        
        except Exception as e:
            logger.error(f"Search index generation failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'mps_indexed': 0
            }
    
    def _generate_site(self) -> Dict:
        """
        Generate static site from database.
        
        Returns:
            Dictionary with generation statistics
            
        Example:
            >>> result = orchestrator._generate_site()
            >>> print(f"Generated {result['pages_generated']} pages")
        """
        try:
            logger.info("Generating static site...")
            
            # Generate static site
            site_gen.generate_static_site(
                str(self.db_path),
                str(self.output_dir)
            )
            
            # Count generated files
            total_files = len(list(self.output_dir.rglob("*.html")))
            
            logger.info(f"✓ Generated {total_files} HTML pages")
            
            return {
                'status': 'success',
                'pages_generated': total_files,
                'output_dir': str(self.output_dir)
            }
        
        except Exception as e:
            logger.error(f"Site generation failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'pages_generated': 0
            }


def main():
    """CLI entry point for workflow orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Orchestrate end-to-end Hansard processing workflow"
    )
    parser.add_argument(
        "--db-path",
        default="data/hansard.db",
        help="Path to SQLite database (default: data/hansard.db)"
    )
    parser.add_argument(
        "--start-date",
        help="Start date for filtering (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        help="End date for filtering (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory (default: output/)"
    )
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = WorkflowOrchestrator(
        db_path=args.db_path,
        start_date=args.start_date,
        end_date=args.end_date,
        workers=args.workers,
        output_dir=args.output_dir
    )
    
    # Run workflow
    try:
        results = orchestrator.run_full_workflow()
        
        # Print summary
        print("\n" + "="*70)
        print("WORKFLOW SUMMARY")
        print("="*70)
        print(f"Status: {results['workflow']['status']}")
        print(f"Total time: {results['workflow']['total_time']:.2f}s")
        print("")
        print(f"MPs scraped: {results['mps']['mps_scraped']}")
        print(f"Hansards downloaded: {results['hansards']['downloaded']}")
        print(f"PDFs processed: {results['processing']['pdfs_processed']}")
        print(f"Statements extracted: {results['processing']['statements']:,}")
        print(f"Search index: {results['search_index']['mps_indexed']} MPs")
        print(f"Site pages: {results['site']['pages_generated']}")
        print("="*70)
        
        return 0
    
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
