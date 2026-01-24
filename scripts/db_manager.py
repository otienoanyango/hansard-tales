#!/usr/bin/env python3
"""
Database management CLI for Hansard Tales.

This script provides command-line access to database maintenance operations:
- backup: Create timestamped backups of the database
- clean: Remove all data except the downloaded_pdfs table

Usage:
    # Create a backup
    python scripts/db_manager.py backup --db-path data/hansard.db
    
    # Clean database (with confirmation)
    python scripts/db_manager.py clean --db-path data/hansard.db
    
    # Clean database (skip confirmation)
    python scripts/db_manager.py clean --db-path data/hansard.db --no-confirm
    
    # Specify custom backup directory
    python scripts/db_manager.py backup --db-path data/hansard.db --backup-dir backups/
"""

import argparse
import logging
import sys
from pathlib import Path

from hansard_tales.database.db_manager import DatabaseManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backup_command(args):
    """Execute backup command."""
    try:
        manager = DatabaseManager()
        
        print(f"Creating backup of {args.db_path}...")
        backup_path = manager.backup(
            db_path=args.db_path,
            backup_dir=args.backup_dir
        )
        
        print(f"\n✓ Backup created successfully!")
        print(f"  Location: {backup_path}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        logger.error(f"Backup failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Backup failed: {e}")
        logger.error(f"Backup failed: {e}", exc_info=True)
        return 1


def clean_command(args):
    """Execute clean command."""
    try:
        manager = DatabaseManager()
        
        print(f"Cleaning database: {args.db_path}")
        print(f"Preserving tables: {args.preserve_tables}")
        print()
        
        manager.clean(
            db_path=args.db_path,
            preserve_tables=args.preserve_tables,
            confirm=not args.no_confirm
        )
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        logger.error(f"Clean failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Clean failed: {e}")
        logger.error(f"Clean failed: {e}", exc_info=True)
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Database management utilities for Hansard Tales",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a backup
  %(prog)s backup --db-path data/hansard.db
  
  # Clean database with confirmation
  %(prog)s clean --db-path data/hansard.db
  
  # Clean database without confirmation
  %(prog)s clean --db-path data/hansard.db --no-confirm
  
  # Preserve additional tables during clean
  %(prog)s clean --db-path data/hansard.db --preserve-tables downloaded_pdfs,mps
        """
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Command to execute',
        required=True
    )
    
    # Backup command
    backup_parser = subparsers.add_parser(
        'backup',
        help='Create a timestamped backup of the database'
    )
    backup_parser.add_argument(
        '--db-path',
        default='data/hansard.db',
        help='Path to database file (default: data/hansard.db)'
    )
    backup_parser.add_argument(
        '--backup-dir',
        default='data/backups',
        help='Directory to store backups (default: data/backups)'
    )
    backup_parser.set_defaults(func=backup_command)
    
    # Clean command
    clean_parser = subparsers.add_parser(
        'clean',
        help='Remove all data except specified tables'
    )
    clean_parser.add_argument(
        '--db-path',
        default='data/hansard.db',
        help='Path to database file (default: data/hansard.db)'
    )
    clean_parser.add_argument(
        '--preserve-tables',
        default=['downloaded_pdfs'],
        nargs='+',
        help='Tables to preserve (default: downloaded_pdfs)'
    )
    clean_parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompt'
    )
    clean_parser.set_defaults(func=clean_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    try:
        exit_code = args.func(args)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n✗ Operation cancelled by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
