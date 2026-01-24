"""
Unit tests for run_workflow CLI script.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the CLI module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import run_workflow


class TestArgumentParsing:
    """Test suite for argument parsing."""
    
    def test_default_arguments(self):
        """Test default argument values."""
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--db-path', default='data/hansard.db')
        parser.add_argument('--start-date')
        parser.add_argument('--end-date')
        parser.add_argument('--workers', type=int, default=4)
        parser.add_argument('--output-dir', default='output')
        parser.add_argument('--storage-dir', default='data/pdfs/hansard')
        
        args = parser.parse_args([])
        
        assert args.db_path == 'data/hansard.db'
        assert args.start_date is None
        assert args.end_date is None
        assert args.workers == 4
        assert args.output_dir == 'output'
        assert args.storage_dir == 'data/pdfs/hansard'
    
    def test_custom_arguments(self):
        """Test custom argument values."""
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--db-path', default='data/hansard.db')
        parser.add_argument('--start-date')
        parser.add_argument('--end-date')
        parser.add_argument('--workers', type=int, default=4)
        parser.add_argument('--output-dir', default='output')
        parser.add_argument('--storage-dir', default='data/pdfs/hansard')
        
        args = parser.parse_args([
            '--db-path', 'custom.db',
            '--start-date', '2024-01-01',
            '--end-date', '2024-12-31',
            '--workers', '8',
            '--output-dir', 'custom_output',
            '--storage-dir', 'custom_storage'
        ])
        
        assert args.db_path == 'custom.db'
        assert args.start_date == '2024-01-01'
        assert args.end_date == '2024-12-31'
        assert args.workers == 8
        assert args.output_dir == 'custom_output'
        assert args.storage_dir == 'custom_storage'
    
    def test_date_range_arguments(self):
        """Test date range argument parsing."""
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--start-date')
        parser.add_argument('--end-date')
        
        # Test with both dates
        args = parser.parse_args(['--start-date', '2024-01-01', '--end-date', '2024-12-31'])
        assert args.start_date == '2024-01-01'
        assert args.end_date == '2024-12-31'
        
        # Test with only start date
        args = parser.parse_args(['--start-date', '2024-01-01'])
        assert args.start_date == '2024-01-01'
        assert args.end_date is None
        
        # Test with only end date
        args = parser.parse_args(['--end-date', '2024-12-31'])
        assert args.start_date is None
        assert args.end_date == '2024-12-31'


class TestMainFunction:
    """Test suite for main function."""
    
    def test_main_success(self):
        """Test successful workflow execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock sys.argv
            test_args = [
                'run_workflow.py',
                '--db-path', str(Path(tmpdir) / 'test.db'),
                '--output-dir', str(Path(tmpdir) / 'output'),
                '--storage-dir', str(Path(tmpdir) / 'storage')
            ]
            
            # Mock WorkflowOrchestrator
            mock_results = {
                'workflow': {
                    'status': 'success',
                    'total_time': 10.5
                },
                'mps': {
                    'status': 'success',
                    'mps_scraped': 10
                },
                'hansards': {
                    'status': 'success',
                    'downloaded': 5,
                    'skipped': 2,
                    'failed': 0
                },
                'processing': {
                    'status': 'success',
                    'pdfs_processed': 5,
                    'statements': 100
                },
                'search_index': {
                    'status': 'success',
                    'mps_indexed': 10
                },
                'site': {
                    'status': 'success',
                    'pages_generated': 50
                }
            }
            
            with patch('sys.argv', test_args):
                with patch('run_workflow.WorkflowOrchestrator') as mock_orchestrator:
                    # Setup mock
                    mock_instance = MagicMock()
                    mock_instance.run_full_workflow.return_value = mock_results
                    mock_orchestrator.return_value = mock_instance
                    
                    # Run main
                    exit_code = run_workflow.main()
                    
                    # Verify orchestrator was created with correct args
                    mock_orchestrator.assert_called_once()
                    call_kwargs = mock_orchestrator.call_args[1]
                    assert call_kwargs['db_path'] == str(Path(tmpdir) / 'test.db')
                    assert call_kwargs['output_dir'] == str(Path(tmpdir) / 'output')
                    assert call_kwargs['workers'] == 4
                    
                    # Verify workflow was run
                    mock_instance.run_full_workflow.assert_called_once()
                    
                    # Verify exit code
                    assert exit_code == 0
    
    def test_main_with_date_range(self):
        """Test workflow execution with date range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_args = [
                'run_workflow.py',
                '--db-path', str(Path(tmpdir) / 'test.db'),
                '--start-date', '2024-01-01',
                '--end-date', '2024-12-31',
                '--workers', '8'
            ]
            
            mock_results = {
                'workflow': {'status': 'success', 'total_time': 10.5},
                'mps': {'status': 'success', 'mps_scraped': 10},
                'hansards': {'status': 'success', 'downloaded': 5, 'skipped': 0, 'failed': 0},
                'processing': {'status': 'success', 'pdfs_processed': 5, 'statements': 100},
                'search_index': {'status': 'success', 'mps_indexed': 10},
                'site': {'status': 'success', 'pages_generated': 50}
            }
            
            with patch('sys.argv', test_args):
                with patch('run_workflow.WorkflowOrchestrator') as mock_orchestrator:
                    mock_instance = MagicMock()
                    mock_instance.run_full_workflow.return_value = mock_results
                    mock_orchestrator.return_value = mock_instance
                    
                    exit_code = run_workflow.main()
                    
                    # Verify date range was passed
                    call_kwargs = mock_orchestrator.call_args[1]
                    assert call_kwargs['start_date'] == '2024-01-01'
                    assert call_kwargs['end_date'] == '2024-12-31'
                    assert call_kwargs['workers'] == 8
                    
                    assert exit_code == 0
    
    def test_main_workflow_failure(self):
        """Test workflow execution with failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_args = [
                'run_workflow.py',
                '--db-path', str(Path(tmpdir) / 'test.db')
            ]
            
            with patch('sys.argv', test_args):
                with patch('run_workflow.WorkflowOrchestrator') as mock_orchestrator:
                    # Setup mock to raise exception
                    mock_instance = MagicMock()
                    mock_instance.run_full_workflow.side_effect = Exception("Workflow failed")
                    mock_orchestrator.return_value = mock_instance
                    
                    exit_code = run_workflow.main()
                    
                    # Verify exit code indicates failure
                    assert exit_code == 1
    
    def test_main_keyboard_interrupt(self):
        """Test workflow handles keyboard interrupt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_args = [
                'run_workflow.py',
                '--db-path', str(Path(tmpdir) / 'test.db')
            ]
            
            with patch('sys.argv', test_args):
                with patch('run_workflow.WorkflowOrchestrator') as mock_orchestrator:
                    # Setup mock to raise KeyboardInterrupt
                    mock_instance = MagicMock()
                    mock_instance.run_full_workflow.side_effect = KeyboardInterrupt()
                    mock_orchestrator.return_value = mock_instance
                    
                    exit_code = run_workflow.main()
                    
                    # Verify exit code indicates interrupt
                    assert exit_code == 130


class TestWorkflowIntegration:
    """Test suite for workflow integration."""
    
    def test_orchestrator_initialization(self):
        """Test WorkflowOrchestrator is initialized correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_args = [
                'run_workflow.py',
                '--db-path', str(Path(tmpdir) / 'test.db'),
                '--output-dir', str(Path(tmpdir) / 'output'),
                '--storage-dir', str(Path(tmpdir) / 'storage'),
                '--workers', '8'
            ]
            
            mock_results = {
                'workflow': {'status': 'success', 'total_time': 10.5},
                'mps': {'status': 'success', 'mps_scraped': 10},
                'hansards': {'status': 'success', 'downloaded': 5, 'skipped': 0, 'failed': 0},
                'processing': {'status': 'success', 'pdfs_processed': 5, 'statements': 100},
                'search_index': {'status': 'success', 'mps_indexed': 10},
                'site': {'status': 'success', 'pages_generated': 50}
            }
            
            with patch('sys.argv', test_args):
                with patch('run_workflow.WorkflowOrchestrator') as mock_orchestrator:
                    mock_instance = MagicMock()
                    mock_instance.run_full_workflow.return_value = mock_results
                    mock_orchestrator.return_value = mock_instance
                    
                    exit_code = run_workflow.main()
                    
                    # Verify all parameters were passed correctly
                    call_kwargs = mock_orchestrator.call_args[1]
                    assert 'db_path' in call_kwargs
                    assert 'storage' in call_kwargs
                    assert 'start_date' in call_kwargs
                    assert 'end_date' in call_kwargs
                    assert 'workers' in call_kwargs
                    assert 'output_dir' in call_kwargs
                    
                    assert call_kwargs['workers'] == 8
                    assert exit_code == 0
