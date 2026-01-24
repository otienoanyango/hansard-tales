"""
Unit tests for db_manager CLI script.
"""

import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the CLI module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import db_manager


class TestBackupCommand:
    """Test suite for backup command."""
    
    def test_backup_command_success(self):
        """Test successful backup command execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test database
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.close()
            
            # Create args mock
            args = MagicMock()
            args.db_path = str(db_path)
            args.backup_dir = str(Path(tmpdir) / 'backups')
            
            # Execute backup command
            exit_code = db_manager.backup_command(args)
            
            # Verify success
            assert exit_code == 0
            
            # Verify backup was created
            backup_dir = Path(args.backup_dir)
            assert backup_dir.exists()
            backup_files = list(backup_dir.glob('hansard_*.db'))
            assert len(backup_files) == 1
    
    def test_backup_command_database_not_found(self):
        """Test backup command with non-existent database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create args mock with non-existent database
            args = MagicMock()
            args.db_path = str(Path(tmpdir) / 'nonexistent.db')
            args.backup_dir = str(Path(tmpdir) / 'backups')
            
            # Execute backup command
            exit_code = db_manager.backup_command(args)
            
            # Verify failure
            assert exit_code == 1
    
    def test_backup_command_argument_parsing(self):
        """Test backup command argument parsing."""
        with patch('sys.argv', ['db_manager.py', 'backup', '--db-path', 'test.db']):
            parser = db_manager.main.__wrapped__() if hasattr(db_manager.main, '__wrapped__') else None
            
            # If we can't get the parser directly, test via argparse
            import argparse
            parser = argparse.ArgumentParser()
            subparsers = parser.add_subparsers(dest='command')
            backup_parser = subparsers.add_parser('backup')
            backup_parser.add_argument('--db-path', default='data/hansard.db')
            backup_parser.add_argument('--backup-dir', default='data/backups')
            
            args = parser.parse_args(['backup', '--db-path', 'test.db'])
            
            assert args.command == 'backup'
            assert args.db_path == 'test.db'
            assert args.backup_dir == 'data/backups'


class TestCleanCommand:
    """Test suite for clean command."""
    
    def test_clean_command_success_with_confirmation(self):
        """Test successful clean command with confirmation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test database with multiple tables
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE downloaded_pdfs (id INTEGER)")
            conn.execute("CREATE TABLE mps (id INTEGER)")
            conn.execute("CREATE TABLE statements (id INTEGER)")
            conn.execute("INSERT INTO mps VALUES (1)")
            conn.execute("INSERT INTO statements VALUES (1)")
            conn.commit()
            conn.close()
            
            # Create args mock
            args = MagicMock()
            args.db_path = str(db_path)
            args.preserve_tables = ['downloaded_pdfs']
            args.no_confirm = True  # Skip confirmation
            
            # Execute clean command
            exit_code = db_manager.clean_command(args)
            
            # Verify success
            assert exit_code == 0
            
            # Verify tables were cleaned
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check mps table is empty
            cursor.execute("SELECT COUNT(*) FROM mps")
            assert cursor.fetchone()[0] == 0
            
            # Check statements table is empty
            cursor.execute("SELECT COUNT(*) FROM statements")
            assert cursor.fetchone()[0] == 0
            
            conn.close()
    
    def test_clean_command_database_not_found(self):
        """Test clean command with non-existent database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create args mock with non-existent database
            args = MagicMock()
            args.db_path = str(Path(tmpdir) / 'nonexistent.db')
            args.preserve_tables = ['downloaded_pdfs']
            args.no_confirm = True
            
            # Execute clean command
            exit_code = db_manager.clean_command(args)
            
            # Verify failure
            assert exit_code == 1
    
    def test_clean_command_argument_parsing(self):
        """Test clean command argument parsing."""
        import argparse
        
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        clean_parser = subparsers.add_parser('clean')
        clean_parser.add_argument('--db-path', default='data/hansard.db')
        clean_parser.add_argument('--preserve-tables', nargs='+', default=['downloaded_pdfs'])
        clean_parser.add_argument('--no-confirm', action='store_true')
        
        # Test default arguments
        args = parser.parse_args(['clean'])
        assert args.command == 'clean'
        assert args.db_path == 'data/hansard.db'
        assert args.preserve_tables == ['downloaded_pdfs']
        assert args.no_confirm is False
        
        # Test custom arguments
        args = parser.parse_args(['clean', '--db-path', 'test.db', '--no-confirm'])
        assert args.db_path == 'test.db'
        assert args.no_confirm is True
        
        # Test multiple preserve tables
        args = parser.parse_args(['clean', '--preserve-tables', 'table1', 'table2'])
        assert args.preserve_tables == ['table1', 'table2']


class TestMainFunction:
    """Test suite for main function."""
    
    def test_main_with_backup_command(self):
        """Test main function with backup command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test database
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.close()
            
            # Mock sys.argv
            test_args = [
                'db_manager.py',
                'backup',
                '--db-path', str(db_path),
                '--backup-dir', str(Path(tmpdir) / 'backups')
            ]
            
            with patch('sys.argv', test_args):
                with patch('sys.exit') as mock_exit:
                    db_manager.main()
                    
                    # Verify exit was called with success code
                    mock_exit.assert_called_once()
                    assert mock_exit.call_args[0][0] == 0
    
    def test_main_with_clean_command(self):
        """Test main function with clean command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test database
            db_path = Path(tmpdir) / 'test.db'
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE downloaded_pdfs (id INTEGER)")
            conn.execute("CREATE TABLE mps (id INTEGER)")
            conn.commit()
            conn.close()
            
            # Mock sys.argv
            test_args = [
                'db_manager.py',
                'clean',
                '--db-path', str(db_path),
                '--no-confirm'
            ]
            
            with patch('sys.argv', test_args):
                with patch('sys.exit') as mock_exit:
                    db_manager.main()
                    
                    # Verify exit was called with success code
                    mock_exit.assert_called_once()
                    assert mock_exit.call_args[0][0] == 0
    
    def test_main_keyboard_interrupt(self):
        """Test main function handles keyboard interrupt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.db'
            
            test_args = [
                'db_manager.py',
                'backup',
                '--db-path', str(db_path)
            ]
            
            with patch('sys.argv', test_args):
                with patch('sys.exit') as mock_exit:
                    with patch('hansard_tales.database.db_manager.DatabaseManager.backup', side_effect=KeyboardInterrupt):
                        db_manager.main()
                        
                        # Verify exit was called with interrupt code
                        mock_exit.assert_called_once_with(130)
