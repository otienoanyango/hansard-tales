#!/usr/bin/env python3
"""
Workflow Orchestrator CLI for Hansard Tales.

This script orchestrates the complete end-to-end workflow:
1. Scrape MPs from parliament website
2. Scrape Hansard PDFs
3. Process PDFs to extract statements
4. Generate search index
5. Generate static site

Usage:
    # Run complete workflow
    python scripts/run_workflow.py
    
    # Run with date range
    python scripts/run_workflow.py --start-date 2024-01-01 --end-date 2024-12-31
    
    # Run with custom workers
    python scripts/run_workflow.py --workers 8
    
    # Run with custom database and output directory
    python scripts/run_workflow.py --db-path data/hansard.db --output-dir output/
"""

import argparse
import logging
import sys
from pathlib import Path

from hansard_tales.workflow.orchestrator import WorkflowOrchestrator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Orchestrate end-to-end Hansard processing workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow Steps:
  1. Scrape MPs from parliament website
  2. Scrape Hansard PDFs
  3. Process PDFs to extract statements
  4. Generate search index
  5. Generate static site

Examples:
  # Run complete workflow
  %(prog)s
  
  # Run with date range
  %(prog)s --start-date 2024-01-01 --end-date 2024-12-31
  
  # Run with more workers for faster processing
  %(prog)s --workers 8
  
  # Run with custom paths
  %(prog)s --db-path data/hansard.db --output-dir output/
        """
    )
    
    parser.add_argument(
        '--db-path',
        default='data/hansard.db',
        help='Path to SQLite database (default: data/hansard.db)'
    )
    parser.add_argument(
        '--start-date',
        help='Start date for filtering (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--end-date',
        help='End date for filtering (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of parallel workers for processing (default: 4)'
    )
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for generated files (default: output/)'
    )
    parser.add_argument(
        '--storage-dir',
        default='data/pdfs/hansard',
        help='Storage directory for PDFs (default: data/pdfs/hansard)'
    )
    
    args = parser.parse_args()
    
    try:
        # Display configuration
        print("="*70)
        print("HANSARD TALES - WORKFLOW ORCHESTRATOR")
        print("="*70)
        print(f"Database: {args.db_path}")
        print(f"Output: {args.output_dir}")
        print(f"Storage: {args.storage_dir}")
        if args.start_date or args.end_date:
            date_range = f"{args.start_date or 'beginning'} to {args.end_date or 'present'}"
            print(f"Date range: {date_range}")
        print(f"Workers: {args.workers}")
        print("="*70)
        print()
        
        # Create orchestrator
        from hansard_tales.storage.filesystem import FilesystemStorage
        storage = FilesystemStorage(args.storage_dir)
        
        orchestrator = WorkflowOrchestrator(
            db_path=args.db_path,
            storage=storage,
            start_date=args.start_date,
            end_date=args.end_date,
            workers=args.workers,
            output_dir=args.output_dir
        )
        
        # Run workflow
        results = orchestrator.run_full_workflow()
        
        # Print summary
        print()
        print("="*70)
        print("WORKFLOW SUMMARY")
        print("="*70)
        print(f"Status: {results['workflow']['status'].upper()}")
        print(f"Total time: {results['workflow']['total_time']:.2f}s")
        print()
        
        # MPs
        if 'mps' in results:
            mps_status = results['mps']['status']
            mps_count = results['mps'].get('mps_scraped', 0)
            print(f"✓ MPs scraped: {mps_count} ({mps_status})")
        
        # Hansards
        if 'hansards' in results:
            hansards_status = results['hansards']['status']
            downloaded = results['hansards'].get('downloaded', 0)
            skipped = results['hansards'].get('skipped', 0)
            failed = results['hansards'].get('failed', 0)
            print(f"✓ Hansards downloaded: {downloaded} ({skipped} skipped, {failed} failed) ({hansards_status})")
        
        # Processing
        if 'processing' in results:
            proc_status = results['processing']['status']
            pdfs = results['processing'].get('pdfs_processed', 0)
            statements = results['processing'].get('statements', 0)
            print(f"✓ PDFs processed: {pdfs} ({proc_status})")
            print(f"  └─ Statements extracted: {statements:,}")
        
        # Search index
        if 'search_index' in results:
            index_status = results['search_index']['status']
            mps_indexed = results['search_index'].get('mps_indexed', 0)
            print(f"✓ Search index: {mps_indexed} MPs indexed ({index_status})")
        
        # Site
        if 'site' in results:
            site_status = results['site']['status']
            pages = results['site'].get('pages_generated', 0)
            print(f"✓ Site generated: {pages} pages ({site_status})")
        
        print("="*70)
        print()
        print(f"✓ Workflow completed successfully!")
        print(f"  Output directory: {args.output_dir}")
        print()
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\n✗ Workflow cancelled by user")
        logger.info("Workflow cancelled by user")
        return 130
    
    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        logger.error(f"Workflow failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
