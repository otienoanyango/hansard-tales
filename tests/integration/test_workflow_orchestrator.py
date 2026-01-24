#!/usr/bin/env python3
"""
Unit tests for WorkflowOrchestrator.

Tests workflow orchestration including:
- Workflow executes all steps in sequence
- Workflow stops on step failure
- Workflow returns statistics
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from hansard_tales.workflow.orchestrator import WorkflowOrchestrator
from hansard_tales.storage.filesystem import FilesystemStorage


class TestWorkflowOrchestrator:
    """Test suite for WorkflowOrchestrator."""
    
    # Use production_db fixture from conftest.py instead of creating custom schema
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_orchestrator_initialization(self, production_db, temp_storage_dir, temp_output_dir):
        """Test WorkflowOrchestrator initialization."""
        storage = FilesystemStorage(temp_storage_dir)
        
        orchestrator = WorkflowOrchestrator(
            db_path=production_db,
            storage=storage,
            start_date="2024-01-01",
            end_date="2024-12-31",
            workers=4,
            output_dir=temp_output_dir
        )
        
        assert orchestrator.db_path == Path(production_db)
        assert orchestrator.storage == storage
        assert orchestrator.start_date == "2024-01-01"
        assert orchestrator.end_date == "2024-12-31"
        assert orchestrator.workers == 4
        assert orchestrator.output_dir == Path(temp_output_dir)
    
    def test_orchestrator_default_storage(self, production_db):
        """Test WorkflowOrchestrator with default storage."""
        orchestrator = WorkflowOrchestrator(db_path=production_db)
        
        assert orchestrator.storage is not None
        assert isinstance(orchestrator.storage, FilesystemStorage)
    
    @patch('hansard_tales.workflow.orchestrator.MPDataScraper')
    def test_scrape_mps_success(self, mock_scraper_class, production_db):
        """Test successful MP scraping."""
        # Setup mock
        try:
            mock_scraper = Mock()
            mock_scraper.scrape_all.return_value = [
                {'name': 'John Doe', 'constituency': 'Test', 'party': 'TestParty'},
                {'name': 'Jane Smith', 'constituency': 'Test2', 'party': 'TestParty2'}
            ]
            mock_scraper.save_to_json = Mock()
            mock_scraper_class.return_value = mock_scraper
        except Exception as e:
            raise AssertionError(f"[MPDataScraper] Failed to setup mock: {e}") from e
        
        try:
            orchestrator = WorkflowOrchestrator(db_path=production_db)
            result = orchestrator._scrape_mps()
        except Exception as e:
            raise AssertionError(f"[WorkflowOrchestrator] Failed to scrape MPs: {e}") from e
        
        try:
            assert result['status'] == 'success'
            assert result['mps_scraped'] == 2
            assert 'output_file' in result
            assert result['term_year'] == 2022
        except (AssertionError, KeyError) as e:
            raise AssertionError(f"[WorkflowOrchestrator] MP scraping result verification failed: {e}") from e
        
        # Verify scraper was called correctly
        try:
            mock_scraper.scrape_all.assert_called_once_with(max_pages=1)
            mock_scraper.save_to_json.assert_called_once()
        except AssertionError as e:
            raise AssertionError(f"[MPDataScraper] Mock call verification failed: {e}") from e
    
    @patch('hansard_tales.workflow.orchestrator.MPDataScraper')
    def test_scrape_mps_no_results(self, mock_scraper_class, production_db):
        """Test MP scraping with no results."""
        # Setup mock to return empty list
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = []
        mock_scraper_class.return_value = mock_scraper
        
        orchestrator = WorkflowOrchestrator(db_path=production_db)
        result = orchestrator._scrape_mps()
        
        assert result['status'] == 'warning'
        assert result['mps_scraped'] == 0
        assert result['reason'] == 'no_mps_found'
    
    @patch('hansard_tales.workflow.orchestrator.MPDataScraper')
    def test_scrape_mps_error(self, mock_scraper_class, production_db):
        """Test MP scraping with error."""
        # Setup mock to raise exception
        mock_scraper = Mock()
        mock_scraper.scrape_all.side_effect = Exception("Network error")
        mock_scraper_class.return_value = mock_scraper
        
        orchestrator = WorkflowOrchestrator(db_path=production_db)
        result = orchestrator._scrape_mps()
        
        assert result['status'] == 'error'
        assert result['mps_scraped'] == 0
        assert 'error' in result
        assert 'Network error' in result['error']
    
    @patch('hansard_tales.workflow.orchestrator.HansardScraper')
    def test_scrape_hansards_success(self, mock_scraper_class, production_db, temp_storage_dir):
        """Test successful Hansard scraping."""
        # Setup mock
        try:
            mock_scraper = Mock()
            mock_scraper.scrape_all.return_value = [
                {'url': 'http://test.com/1.pdf', 'title': 'Test 1', 'date': '2024-01-01'},
                {'url': 'http://test.com/2.pdf', 'title': 'Test 2', 'date': '2024-01-02'}
            ]
            mock_scraper.download_all.return_value = {
                'total': 2,
                'downloaded': 2,
                'skipped': 0,
                'failed': 0
            }
            mock_scraper_class.return_value = mock_scraper
        except Exception as e:
            raise AssertionError(f"[HansardScraper] Failed to setup mock: {e}") from e
        
        try:
            storage = FilesystemStorage(temp_storage_dir)
            orchestrator = WorkflowOrchestrator(db_path=production_db, storage=storage)
            result = orchestrator._scrape_hansards()
        except Exception as e:
            raise AssertionError(f"[WorkflowOrchestrator] Failed to scrape Hansards: {e}") from e
        
        try:
            assert result['status'] == 'success'
            assert result['hansards_found'] == 2
            assert result['downloaded'] == 2
            assert result['skipped'] == 0
            assert result['failed'] == 0
        except (AssertionError, KeyError) as e:
            raise AssertionError(f"[WorkflowOrchestrator] Hansard scraping result verification failed: {e}") from e
        
        # Verify scraper was called correctly
        try:
            mock_scraper.scrape_all.assert_called_once_with(max_pages=1)
            mock_scraper.download_all.assert_called_once()
        except AssertionError as e:
            raise AssertionError(f"[HansardScraper] Mock call verification failed: {e}") from e
    
    @patch('hansard_tales.workflow.orchestrator.HansardScraper')
    def test_scrape_hansards_no_results(self, mock_scraper_class, production_db):
        """Test Hansard scraping with no results."""
        # Setup mock to return empty list
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = []
        mock_scraper_class.return_value = mock_scraper
        
        orchestrator = WorkflowOrchestrator(db_path=production_db)
        result = orchestrator._scrape_hansards()
        
        assert result['status'] == 'warning'
        assert result['hansards_found'] == 0
        assert result['downloaded'] == 0
        assert result['reason'] == 'no_hansards_found'
    
    @patch('hansard_tales.workflow.orchestrator.HansardScraper')
    def test_scrape_hansards_error(self, mock_scraper_class, production_db):
        """Test Hansard scraping with error."""
        # Setup mock to raise exception
        mock_scraper = Mock()
        mock_scraper.scrape_all.side_effect = Exception("Network error")
        mock_scraper_class.return_value = mock_scraper
        
        orchestrator = WorkflowOrchestrator(db_path=production_db)
        result = orchestrator._scrape_hansards()
        
        assert result['status'] == 'error'
        assert result['hansards_found'] == 0
        assert 'error' in result
        assert 'Network error' in result['error']
    
    @patch('hansard_tales.workflow.orchestrator.HistoricalDataProcessor')
    def test_process_pdfs_success(self, mock_processor_class, production_db):
        """Test successful PDF processing."""
        # Setup mock
        try:
            mock_processor = Mock()
            mock_processor.stats = {
                'pdfs_processed': 5,
                'pdfs_failed': 0,
                'statements_extracted': 100,
                'mps_identified': 10,
                'bills_extracted': 5,
                'duplicates_skipped': 2,
                'errors': []
            }
            mock_processor._process_pdfs = Mock()
            mock_processor_class.return_value = mock_processor
        except Exception as e:
            raise AssertionError(f"[HistoricalDataProcessor] Failed to setup mock: {e}") from e
        
        try:
            orchestrator = WorkflowOrchestrator(db_path=production_db)
            result = orchestrator._process_pdfs()
        except Exception as e:
            raise AssertionError(f"[WorkflowOrchestrator] Failed to process PDFs: {e}") from e
        
        try:
            assert result['status'] == 'success'
            assert result['pdfs_processed'] == 5
            assert result['pdfs_failed'] == 0
            assert result['statements'] == 100
            assert result['unique_mps'] == 10
            assert result['bills'] == 5
            assert result['duplicates_skipped'] == 2
        except (AssertionError, KeyError) as e:
            raise AssertionError(f"[WorkflowOrchestrator] PDF processing result verification failed: {e}") from e
        
        # Verify processor was called
        try:
            mock_processor._process_pdfs.assert_called_once()
        except AssertionError as e:
            raise AssertionError(f"[HistoricalDataProcessor] Mock call verification failed: {e}") from e
    
    @patch('hansard_tales.workflow.orchestrator.HistoricalDataProcessor')
    def test_process_pdfs_error(self, mock_processor_class, production_db):
        """Test PDF processing with error."""
        # Setup mock to raise exception
        mock_processor = Mock()
        mock_processor._process_pdfs.side_effect = Exception("Processing error")
        mock_processor_class.return_value = mock_processor
        
        orchestrator = WorkflowOrchestrator(db_path=production_db)
        result = orchestrator._process_pdfs()
        
        assert result['status'] == 'error'
        assert result['pdfs_processed'] == 0
        assert 'error' in result
        assert 'Processing error' in result['error']
    
    @patch('hansard_tales.workflow.orchestrator.search_index_gen')
    def test_generate_search_index_success(self, mock_search_gen, production_db, temp_output_dir):
        """Test successful search index generation."""
        # Create mock index file
        try:
            data_dir = Path(temp_output_dir) / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            index_file = data_dir / "mp-search-index.json"
            
            # Write mock index data
            import json
            mock_data = [
                {'id': 1, 'name': 'John Doe'},
                {'id': 2, 'name': 'Jane Smith'}
            ]
            with open(index_file, 'w') as f:
                json.dump(mock_data, f)
        except Exception as e:
            raise AssertionError(f"[SearchIndexGenerator] Failed to create mock index file: {e}") from e
        
        try:
            orchestrator = WorkflowOrchestrator(db_path=production_db, output_dir=temp_output_dir)
            result = orchestrator._generate_search_index()
        except Exception as e:
            raise AssertionError(f"[WorkflowOrchestrator] Failed to generate search index: {e}") from e
        
        try:
            assert result['status'] == 'success'
            assert result['mps_indexed'] == 2
            assert result['file_size'] > 0
            assert 'output_file' in result
        except (AssertionError, KeyError) as e:
            raise AssertionError(f"[SearchIndexGenerator] Search index result verification failed: {e}") from e
    
    @patch('hansard_tales.workflow.orchestrator.search_index_gen')
    def test_generate_search_index_error(self, mock_search_gen, production_db, temp_output_dir):
        """Test search index generation with error."""
        # Setup mock to raise exception
        mock_search_gen.generate_search_index.side_effect = Exception("Index error")
        
        orchestrator = WorkflowOrchestrator(db_path=production_db, output_dir=temp_output_dir)
        result = orchestrator._generate_search_index()
        
        assert result['status'] == 'error'
        assert result['mps_indexed'] == 0
        assert 'error' in result
        assert 'Index error' in result['error']
    
    @patch('hansard_tales.workflow.orchestrator.site_gen')
    def test_generate_site_success(self, mock_site_gen, production_db, temp_output_dir):
        """Test successful site generation."""
        # Create mock HTML files
        try:
            (Path(temp_output_dir) / "index.html").write_text("<html></html>")
            (Path(temp_output_dir) / "about.html").write_text("<html></html>")
        except Exception as e:
            raise AssertionError(f"[SiteGenerator] Failed to create mock HTML files: {e}") from e
        
        try:
            orchestrator = WorkflowOrchestrator(db_path=production_db, output_dir=temp_output_dir)
            result = orchestrator._generate_site()
        except Exception as e:
            raise AssertionError(f"[WorkflowOrchestrator] Failed to generate site: {e}") from e
        
        try:
            assert result['status'] == 'success'
            assert result['pages_generated'] >= 2
            assert 'output_dir' in result
        except (AssertionError, KeyError) as e:
            raise AssertionError(f"[SiteGenerator] Site generation result verification failed: {e}") from e
    
    @patch('hansard_tales.workflow.orchestrator.site_gen')
    def test_generate_site_error(self, mock_site_gen, production_db, temp_output_dir):
        """Test site generation with error."""
        # Setup mock to raise exception
        mock_site_gen.generate_static_site.side_effect = Exception("Site error")
        
        orchestrator = WorkflowOrchestrator(db_path=production_db, output_dir=temp_output_dir)
        result = orchestrator._generate_site()
        
        assert result['status'] == 'error'
        assert result['pages_generated'] == 0
        assert 'error' in result
        assert 'Site error' in result['error']
    
    @patch('hansard_tales.workflow.orchestrator.WorkflowOrchestrator._generate_site')
    @patch('hansard_tales.workflow.orchestrator.WorkflowOrchestrator._generate_search_index')
    @patch('hansard_tales.workflow.orchestrator.WorkflowOrchestrator._process_pdfs')
    @patch('hansard_tales.workflow.orchestrator.WorkflowOrchestrator._scrape_hansards')
    @patch('hansard_tales.workflow.orchestrator.WorkflowOrchestrator._scrape_mps')
    def test_run_full_workflow_success(
        self,
        mock_scrape_mps,
        mock_scrape_hansards,
        mock_process_pdfs,
        mock_generate_index,
        mock_generate_site,
        production_db
    ):
        """Test complete workflow executes all steps in sequence."""
        # Setup mocks to return success
        mock_scrape_mps.return_value = {'status': 'success', 'mps_scraped': 10}
        mock_scrape_hansards.return_value = {'status': 'success', 'downloaded': 5}
        mock_process_pdfs.return_value = {'status': 'success', 'pdfs_processed': 5, 'statements': 100}
        mock_generate_index.return_value = {'status': 'success', 'mps_indexed': 10}
        mock_generate_site.return_value = {'status': 'success', 'pages_generated': 50}
        
        orchestrator = WorkflowOrchestrator(db_path=production_db)
        results = orchestrator.run_full_workflow()
        
        # Verify all steps were called in sequence
        mock_scrape_mps.assert_called_once()
        mock_scrape_hansards.assert_called_once()
        mock_process_pdfs.assert_called_once()
        mock_generate_index.assert_called_once()
        mock_generate_site.assert_called_once()
        
        # Verify results structure
        assert 'mps' in results
        assert 'hansards' in results
        assert 'processing' in results
        assert 'search_index' in results
        assert 'site' in results
        assert 'workflow' in results
        
        # Verify workflow status
        assert results['workflow']['status'] == 'success'
        assert 'total_time' in results['workflow']
        assert 'start_time' in results['workflow']
        assert 'end_time' in results['workflow']
    
    @patch('hansard_tales.workflow.orchestrator.WorkflowOrchestrator._scrape_hansards')
    @patch('hansard_tales.workflow.orchestrator.WorkflowOrchestrator._scrape_mps')
    def test_run_full_workflow_stops_on_failure(
        self,
        mock_scrape_mps,
        mock_scrape_hansards,
        production_db
    ):
        """Test workflow stops on step failure."""
        # Setup first step to succeed, second to fail
        mock_scrape_mps.return_value = {'status': 'success', 'mps_scraped': 10}
        mock_scrape_hansards.side_effect = Exception("Network error")
        
        orchestrator = WorkflowOrchestrator(db_path=production_db)
        
        # Workflow should raise exception
        with pytest.raises(Exception) as exc_info:
            orchestrator.run_full_workflow()
        
        assert "Network error" in str(exc_info.value)
        
        # Verify only first two steps were called
        mock_scrape_mps.assert_called_once()
        mock_scrape_hansards.assert_called_once()
    
    @patch('hansard_tales.workflow.orchestrator.WorkflowOrchestrator._generate_site')
    @patch('hansard_tales.workflow.orchestrator.WorkflowOrchestrator._generate_search_index')
    @patch('hansard_tales.workflow.orchestrator.WorkflowOrchestrator._process_pdfs')
    @patch('hansard_tales.workflow.orchestrator.WorkflowOrchestrator._scrape_hansards')
    @patch('hansard_tales.workflow.orchestrator.WorkflowOrchestrator._scrape_mps')
    def test_run_full_workflow_returns_statistics(
        self,
        mock_scrape_mps,
        mock_scrape_hansards,
        mock_process_pdfs,
        mock_generate_index,
        mock_generate_site,
        production_db
    ):
        """Test workflow returns comprehensive statistics."""
        # Setup mocks with detailed statistics
        mock_scrape_mps.return_value = {
            'status': 'success',
            'mps_scraped': 349,
            'term_year': 2022
        }
        mock_scrape_hansards.return_value = {
            'status': 'success',
            'hansards_found': 100,
            'downloaded': 50,
            'skipped': 45,
            'failed': 5
        }
        mock_process_pdfs.return_value = {
            'status': 'success',
            'pdfs_processed': 50,
            'pdfs_failed': 0,
            'statements': 5000,
            'unique_mps': 200,
            'bills': 150,
            'duplicates_skipped': 10,
            'errors': []
        }
        mock_generate_index.return_value = {
            'status': 'success',
            'mps_indexed': 349,
            'file_size': 102400
        }
        mock_generate_site.return_value = {
            'status': 'success',
            'pages_generated': 500
        }
        
        orchestrator = WorkflowOrchestrator(db_path=production_db)
        results = orchestrator.run_full_workflow()
        
        # Verify statistics are returned
        assert results['mps']['mps_scraped'] == 349
        assert results['hansards']['downloaded'] == 50
        assert results['processing']['statements'] == 5000
        assert results['search_index']['mps_indexed'] == 349
        assert results['site']['pages_generated'] == 500
        
        # Verify workflow metadata
        assert results['workflow']['status'] == 'success'
        assert isinstance(results['workflow']['total_time'], float)
        assert results['workflow']['total_time'] >= 0


class TestWorkflowOrchestratorEdgeCases:
    """Test edge cases for WorkflowOrchestrator."""
    
    @pytest.fixture
    # Use production_db fixture from conftest.py
    
    def test_orchestrator_with_date_range(self, production_db):
        """Test orchestrator with date range filtering."""
        orchestrator = WorkflowOrchestrator(
            db_path=production_db,
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        
        assert orchestrator.start_date == "2024-01-01"
        assert orchestrator.end_date == "2024-12-31"
    
    def test_orchestrator_with_custom_workers(self, production_db):
        """Test orchestrator with custom worker count."""
        orchestrator = WorkflowOrchestrator(
            db_path=production_db,
            workers=8
        )
        
        assert orchestrator.workers == 8
    
    def test_orchestrator_creates_directories(self, production_db):
        """Test orchestrator creates necessary directories."""
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        try:
            db_path = Path(temp_dir) / "subdir" / "test.db"
            output_dir = Path(temp_dir) / "output"
            
            orchestrator = WorkflowOrchestrator(
                db_path=str(db_path),
                output_dir=str(output_dir)
            )
            
            # Verify directories were created
            assert db_path.parent.exists()
            assert output_dir.exists()
        
        finally:
            import shutil
            shutil.rmtree(temp_dir)
