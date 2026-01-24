#!/usr/bin/env python3
"""
Process existing PDFs in data/pdfs/hansard-report/ directory.

This script processes PDFs that have already been downloaded,
skipping the download step.
"""

from hansard_tales.process_historical_data import HistoricalDataProcessor

def main():
    print("="*70)
    print("Processing Existing Hansard PDFs")
    print("="*70)
    print()
    
    # Create processor
    processor = HistoricalDataProcessor(
        start_date='2024-01-01',
        end_date='2025-12-31',
        dry_run=False,
        force=False,
        clean=False,
        workers=4
    )
    
    # Skip download, just process existing PDFs
    print("Step 1: Processing PDFs...")
    processor._process_pdfs()
    
    # Quality assurance
    print("\nStep 2: Quality assurance checks...")
    processor._quality_assurance()
    
    # Generate outputs
    print("\nStep 3: Generating search index and static site...")
    processor._generate_outputs()
    
    # Print summary
    print("\n" + "="*70)
    print("Processing Complete!")
    print("="*70)
    processor._print_summary()
    
    # Emit metrics
    processor._emit_metrics()

if __name__ == "__main__":
    main()
