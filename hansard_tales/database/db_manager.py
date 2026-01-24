"""
Database management utilities for Hansard Tales.

This module provides utilities for database maintenance including:
- Backup: Create timestamped backups of the database
- Clean: Remove all data except the downloaded_pdfs table

Usage:
    from hansard_tales.database.db_manager import DatabaseManager
    
    manager = DatabaseManager()
    
    # Create backup
    backup_path = manager.backup("data/hansard.db")
    
    # Clean database (preserves downloaded_pdfs)
    manager.clean("data/hansard.db", confirm=True)
"""

import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database backup and maintenance utilities."""
    
    def backup(
        self,
        db_path: str,
        backup_dir: str = "data/backups"
    ) -> str:
        """
        Create timestamped backup of database.
        
        The backup filename follows the format: hansard_YYYYMMDD_HHMMSS.db
        where the timestamp reflects the backup creation time.
        
        Args:
            db_path: Path to the database file to backup
            backup_dir: Directory to store backups (default: data/backups)
            
        Returns:
            Path to the created backup file
            
        Raises:
            FileNotFoundError: If the database file doesn't exist
            OSError: If backup directory cannot be created or file cannot be copied
            
        Example:
            >>> manager = DatabaseManager()
            >>> backup_path = manager.backup("data/hansard.db")
            >>> print(f"Backup created: {backup_path}")
            Backup created: data/backups/hansard_20240122_143052.db
        """
        db_file = Path(db_path)
        
        # Verify database exists
        if not db_file.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        # Create backup directory
        backup_path_obj = Path(backup_dir)
        backup_path_obj.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"hansard_{timestamp}.db"
        backup_file = backup_path_obj / backup_filename
        
        # Copy database file
        shutil.copy2(db_path, backup_file)
        
        logger.info(f"Created backup: {backup_file}")
        
        return str(backup_file)
    
    def clean(
        self,
        db_path: str,
        preserve_tables: Optional[List[str]] = None,
        confirm: bool = True
    ) -> None:
        """
        Clean database while preserving specified tables.
        
        This operation deletes all data from tables except those in the
        preserve_tables list. By default, it preserves the downloaded_pdfs
        table to maintain download history.
        
        Args:
            db_path: Path to the database file
            preserve_tables: Tables to preserve (default: ['downloaded_pdfs'])
            confirm: Require user confirmation before cleaning (default: True)
            
        Raises:
            FileNotFoundError: If the database file doesn't exist
            sqlite3.Error: If database operations fail
            
        Example:
            >>> manager = DatabaseManager()
            >>> manager.clean("data/hansard.db", confirm=True)
            This will delete all data except ['downloaded_pdfs']. Continue? (yes/no): yes
            ✓ Cleaned table: parliamentary_terms
            ✓ Cleaned table: mps
            ...
            ✓ Database cleaned successfully
        """
        if preserve_tables is None:
            preserve_tables = ['downloaded_pdfs']
        
        db_file = Path(db_path)
        
        # Verify database exists
        if not db_file.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        # Confirmation prompt
        if confirm:
            response = input(
                f"This will delete all data except {preserve_tables}. "
                "Continue? (yes/no): "
            )
            if response.lower() != 'yes':
                logger.info("Clean operation cancelled")
                print("✗ Clean operation cancelled")
                return
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Get all tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            all_tables = [row[0] for row in cursor.fetchall()]
            
            # Delete from tables not in preserve list
            cleaned_count = 0
            for table in all_tables:
                if table not in preserve_tables and not table.startswith('sqlite_'):
                    logger.info(f"Database operation: DELETE from table={table}")
                    cursor.execute(f"DELETE FROM {table}")
                    logger.info(f"Cleaned table: {table}")
                    print(f"✓ Cleaned table: {table}")
                    cleaned_count += 1
            
            conn.commit()
            
            logger.info(f"Database cleaned successfully ({cleaned_count} tables)")
            print(f"\n✓ Database cleaned successfully ({cleaned_count} tables)")
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error during clean: {e}", exc_info=True)
            raise
        finally:
            conn.close()
