"""Unit tests for ProcessingPipeline."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from hansard_tales.analysis.filler_detector import StatementType
from hansard_tales.analysis.statement_segmenter import Statement
from hansard_tales.pipeline import (
    PipelineStage,
    ProcessingPipeline,
)


@pytest.fixture
def mock_pipeline():
    """Create a pipeline with all components mocked."""
    db_session = Mock()
    vector_db = Mock()

    with patch("hansard_tales.pipeline.MPIdentifier"), patch(
        "hansard_tales.pipeline.StatementSegmenter"
    ), patch("hansard_tales.pipeline.FillerDetector"), patch(
        "hansard_tales.pipeline.ContextRetriever"
    ), patch("hansard_tales.pipeline.CitationVerifier"), patch(
        "hansard_tales.pipeline.VoteProcessor"
    ), patch("hansard_tales.pipeline.BillStatementLinker"), patch(
        "hansard_tales.pipeline.StaticSiteGenerator"
    ), patch("hansard_tales.pipeline.PDFProcessor"):
        pipeline = ProcessingPipeline(db_session, vector_db)
        yield pipeline


class TestPipelineStageExecution:
    """Test pipeline stage execution."""

    def test_run_stage_success(self, mock_pipeline):
        """Test successful stage execution."""

        # Test function that returns data
        def test_func():
            return ["item1", "item2", "item3"]

        result = mock_pipeline._run_stage(PipelineStage.TEXT_EXTRACTION, test_func)

        assert result.success is True
        assert result.stage == PipelineStage.TEXT_EXTRACTION
        assert result.items_processed == 3
        assert result.duration > 0
        assert len(result.errors) == 0
        assert result.data == ["item1", "item2", "item3"]

    def test_run_stage_failure(self, mock_pipeline):
        """Test stage execution with error."""

        # Test function that raises error
        def test_func():
            raise ValueError("Test error")

        result = mock_pipeline._run_stage(PipelineStage.TEXT_EXTRACTION, test_func)

        assert result.success is False
        assert result.stage == PipelineStage.TEXT_EXTRACTION
        assert result.items_processed == 0
        assert result.duration > 0
        assert len(result.errors) == 1
        assert "Test error" in result.errors[0]
        assert result.data is None

    def test_run_stage_with_none_data(self, mock_pipeline):
        """Test stage execution that returns None."""

        def test_func():
            return None

        result = mock_pipeline._run_stage(PipelineStage.TEXT_EXTRACTION, test_func)

        assert result.success is True
        assert result.items_processed == 0
        assert result.data is None

    def test_run_stage_with_single_item(self, mock_pipeline):
        """Test stage execution that returns single item."""

        def test_func():
            return "single_item"

        result = mock_pipeline._run_stage(PipelineStage.TEXT_EXTRACTION, test_func)

        assert result.success is True
        assert result.items_processed == 1
        assert result.data == "single_item"

    def test_run_stage_timing(self, mock_pipeline):
        """Test that stage execution tracks timing."""
        import time

        def slow_func():
            time.sleep(0.1)
            return ["data"]

        result = mock_pipeline._run_stage(PipelineStage.TEXT_EXTRACTION, slow_func)

        assert result.success is True
        assert result.duration >= 0.1


class TestErrorHandling:
    """Test pipeline error handling."""

    def test_extract_text_with_invalid_pdf(self, mock_pipeline):
        """Test text extraction with invalid PDF."""
        mock_pipeline.pdf_processor = Mock()
        mock_pipeline.pdf_processor.extract_text.side_effect = Exception("PDF error")

        with pytest.raises(ValueError, match="Failed to extract text"):
            mock_pipeline._extract_text(Path("test.pdf"))

    def test_extract_text_with_insufficient_content(self, mock_pipeline):
        """Test text extraction with insufficient content."""
        mock_pipeline.pdf_processor = Mock()
        mock_pipeline.pdf_processor.extract_text.return_value = "short"

        with pytest.raises(ValueError, match="Insufficient text extracted"):
            mock_pipeline._extract_text(Path("test.pdf"))

    def test_extract_text_success(self, mock_pipeline):
        """Test successful text extraction."""
        mock_pipeline.pdf_processor = Mock()
        long_text = "This is a long text " * 20
        mock_pipeline.pdf_processor.extract_text.return_value = long_text

        result = mock_pipeline._extract_text(Path("test.pdf"))

        assert result == long_text

    def test_handle_stage_error_with_retries(self):
        """Test error handling with retry logic."""
        db_session = Mock()
        vector_db = Mock()
        config = {"max_retries": 3, "retry_delay": 0.01}

        with patch("hansard_tales.pipeline.MPIdentifier"), patch(
            "hansard_tales.pipeline.StatementSegmenter"
        ), patch("hansard_tales.pipeline.FillerDetector"), patch(
            "hansard_tales.pipeline.ContextRetriever"
        ), patch("hansard_tales.pipeline.CitationVerifier"), patch(
            "hansard_tales.pipeline.VoteProcessor"
        ), patch("hansard_tales.pipeline.BillStatementLinker"), patch(
            "hansard_tales.pipeline.StaticSiteGenerator"
        ), patch("hansard_tales.pipeline.PDFProcessor"):
            pipeline = ProcessingPipeline(db_session, vector_db, config)

            error = ValueError("Test error")

            # First retry (should return None to continue)
            result = pipeline._handle_stage_error(
                PipelineStage.TEXT_EXTRACTION, error, retry_count=0
            )
            assert result is None

            # Max retries exceeded (should return PipelineResult)
            result = pipeline._handle_stage_error(
                PipelineStage.TEXT_EXTRACTION, error, retry_count=3
            )
            assert result is not None
            assert result.success is False
            assert "Max retries exceeded" in result.errors[0]

    def test_process_hansard_with_missing_file(self, mock_pipeline):
        """Test Hansard processing with missing file."""
        with pytest.raises(FileNotFoundError):
            mock_pipeline.process_hansard(Path("nonexistent.pdf"))

    def test_process_votes_with_missing_file(self, mock_pipeline):
        """Test Votes processing with missing file."""
        with pytest.raises(FileNotFoundError):
            mock_pipeline.process_votes(Path("nonexistent.pdf"))


class TestResultStorage:
    """Test pipeline result storage."""

    def test_store_hansard_results_with_new_session(self, mock_pipeline):
        """Test storing Hansard results with new session."""
        # Create mock statement and analysis
        stmt = Statement(
            text="Test statement",
            mp_id="mp123",
            start_pos=0,
            end_pos=100,
        )
        analysis = Mock()
        analysis.sentiment = "positive"
        analysis.quality_score = 85
        analysis.primary_topic = "Healthcare"

        analyzed = [(stmt, analysis)]

        # Mock database operations
        mock_pipeline.db.query.return_value.filter.return_value.first.return_value = None
        mock_pipeline.db.flush = Mock()
        mock_pipeline.db.commit = Mock()

        mock_pipeline._store_hansard_results(Path("test.pdf"), analyzed)

        # Verify session was created
        assert mock_pipeline.db.add.called
        assert mock_pipeline.db.commit.called

    def test_store_hansard_results_with_existing_session(self, mock_pipeline):
        """Test storing Hansard results with existing session."""
        # Create mock statement
        stmt = Statement(
            text="Test statement",
            mp_id="mp123",
            start_pos=0,
            end_pos=100,
        )
        analyzed = [(stmt, None)]

        # Mock existing session
        mock_session = Mock()
        mock_session.id = "session123"
        mock_pipeline.db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_pipeline.db.commit = Mock()

        mock_pipeline._store_hansard_results(Path("test.pdf"), analyzed, "session123")

        # Verify statement was added
        assert mock_pipeline.db.add.called
        assert mock_pipeline.db.commit.called

    def test_store_hansard_results_rollback_on_error(self, mock_pipeline):
        """Test that storage errors trigger rollback."""
        stmt = Statement(
            text="Test statement",
            mp_id="mp123",
            start_pos=0,
            end_pos=100,
        )
        analyzed = [(stmt, None)]

        # Mock database error
        mock_pipeline.db.query.return_value.filter.return_value.first.return_value = None
        mock_pipeline.db.commit.side_effect = Exception("Database error")
        mock_pipeline.db.rollback = Mock()

        with pytest.raises(Exception):
            mock_pipeline._store_hansard_results(Path("test.pdf"), analyzed)

        # Verify rollback was called
        assert mock_pipeline.db.rollback.called

    def test_store_vote_results(self, mock_pipeline):
        """Test storing vote results."""
        votes = [Mock(), Mock()]
        mock_pipeline.db.commit = Mock()

        mock_pipeline._store_vote_results(Path("test.pdf"), votes)

        # Verify commit was called
        assert mock_pipeline.db.commit.called

    def test_verify_citations(self, mock_pipeline):
        """Test citation verification."""
        mock_pipeline.citation_verifier = Mock()

        # Create mock statement and analysis with citations
        stmt = Statement(
            text="Test statement with citation",
            mp_id="mp123",
            start_pos=0,
            end_pos=100,
        )
        analysis = Mock()
        analysis.citations = ["citation1", "citation2"]

        analyzed = [(stmt, analysis)]

        # Mock citation verification
        mock_citation = Mock()
        mock_pipeline.citation_verifier.verify_citation.return_value = mock_citation

        result = mock_pipeline._verify_citations(analyzed)

        # Verify citations were verified
        assert len(result) == 2
        assert mock_pipeline.citation_verifier.verify_citation.call_count == 2


class TestPipelineCompletion:
    """Test complete pipeline execution."""

    @patch("hansard_tales.pipeline.Path.exists")
    def test_process_hansard_complete_pipeline(self, mock_exists):
        """Test complete Hansard processing pipeline."""
        mock_exists.return_value = True

        db_session = Mock()
        vector_db = Mock()

        pipeline = ProcessingPipeline(db_session, vector_db)

        # Mock all components
        pipeline.pdf_processor = Mock()
        pipeline.pdf_processor.extract_text.return_value = "Long text " * 50

        pipeline.segmenter = Mock()
        mock_stmt = Statement(
            text="Test statement",
            mp_id="mp123",
            start_pos=0,
            end_pos=100,
        )
        pipeline.segmenter.segment.return_value = [mock_stmt]

        pipeline.filler_detector = Mock()
        pipeline.filler_detector.classify.return_value = (
            StatementType.SUBSTANTIVE,
            0.95,
        )

        pipeline.context_retriever = Mock()
        pipeline.context_retriever.retrieve.return_value = Mock()

        pipeline.bill_linker = Mock()
        pipeline.bill_linker.find_bill_mentions.return_value = []

        # Mock database operations
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.commit = Mock()

        results = pipeline.process_hansard(Path("test.pdf"))

        # Verify all stages executed
        stage_names = [r.stage for r in results]
        assert PipelineStage.TEXT_EXTRACTION in stage_names
        assert PipelineStage.SEGMENTATION in stage_names
        assert PipelineStage.CLASSIFICATION in stage_names
        assert PipelineStage.CONTEXT_RETRIEVAL in stage_names
        assert PipelineStage.BILL_LINKING in stage_names

        # Verify all stages succeeded
        assert all(r.success for r in results)

    @patch("hansard_tales.pipeline.Path.exists")
    def test_process_hansard_early_failure(self, mock_exists):
        """Test Hansard pipeline with early stage failure."""
        mock_exists.return_value = True

        db_session = Mock()
        vector_db = Mock()

        pipeline = ProcessingPipeline(db_session, vector_db)

        # Mock text extraction failure
        pipeline.pdf_processor = Mock()
        pipeline.pdf_processor.extract_text.side_effect = Exception("Extraction failed")

        results = pipeline.process_hansard(Path("test.pdf"))

        # Verify pipeline stopped after first failure
        assert len(results) == 1
        assert results[0].stage == PipelineStage.TEXT_EXTRACTION
        assert results[0].success is False

    @patch("hansard_tales.pipeline.Path.exists")
    def test_process_votes_complete_pipeline(self, mock_exists):
        """Test complete Votes processing pipeline."""
        mock_exists.return_value = True

        db_session = Mock()
        vector_db = Mock()

        pipeline = ProcessingPipeline(db_session, vector_db)

        # Mock vote processor
        pipeline.vote_processor = Mock()
        mock_votes = [Mock(), Mock()]
        pipeline.vote_processor.process_pdf.return_value = mock_votes

        # Mock database operations
        db_session.commit = Mock()

        results = pipeline.process_votes(Path("test.pdf"))

        # Verify vote processing stage executed
        assert len(results) == 1
        assert results[0].stage == PipelineStage.VOTE_PROCESSING
        assert results[0].success is True
        assert results[0].items_processed == 2

    def test_pipeline_without_llm_analyzer(self):
        """Test pipeline execution without LLM analyzer."""
        db_session = Mock()
        vector_db = Mock()
        config = {}  # No API key

        pipeline = ProcessingPipeline(db_session, vector_db, config)

        # Verify LLM-dependent components are None
        assert pipeline.llm_analyzer is None
        assert pipeline.profile_generator is None
        assert pipeline.summary_generator is None


class TestParallelProcessing:
    """Test parallel processing capabilities."""

    def test_pipeline_initialization_with_config(self):
        """Test pipeline initialization with custom config."""
        db_session = Mock()
        vector_db = Mock()
        config = {
            "anthropic_api_key": "test_key",
            "template_dir": "custom_templates",
            "output_dir": "custom_output",
            "max_retries": 5,
            "retry_delay": 2.0,
        }

        pipeline = ProcessingPipeline(db_session, vector_db, config)

        assert pipeline.max_retries == 5
        assert pipeline.retry_delay == 2.0
        assert pipeline.llm_analyzer is not None

    def test_multiple_statements_processing(self):
        """Test processing multiple statements in batch."""
        db_session = Mock()
        vector_db = Mock()

        pipeline = ProcessingPipeline(db_session, vector_db)

        # Create multiple statements
        statements = [
            Statement(
                text=f"Statement {i}",
                mp_id=f"mp{i}",
                start_pos=i * 100,
                end_pos=(i + 1) * 100,
            )
            for i in range(10)
        ]

        # Mock classification
        pipeline.filler_detector = Mock()
        pipeline.filler_detector.classify.return_value = (
            StatementType.SUBSTANTIVE,
            0.95,
        )

        # Test batch classification
        result = pipeline._run_stage(
            PipelineStage.CLASSIFICATION,
            lambda: [(stmt, pipeline.filler_detector.classify(stmt)) for stmt in statements],
        )

        assert result.success is True
        assert result.items_processed == 10
        assert len(result.data) == 10

    def test_context_retrieval_for_multiple_statements(self):
        """Test context retrieval for multiple statements."""
        db_session = Mock()
        vector_db = Mock()

        pipeline = ProcessingPipeline(db_session, vector_db)

        # Create multiple statements
        statements = [
            Statement(
                text=f"Statement {i}",
                mp_id=f"mp{i}",
                start_pos=i * 100,
                end_pos=(i + 1) * 100,
            )
            for i in range(5)
        ]

        # Mock context retrieval
        pipeline.context_retriever = Mock()
        mock_context = Mock()
        pipeline.context_retriever.retrieve.return_value = mock_context

        # Test batch context retrieval
        result = pipeline._run_stage(
            PipelineStage.CONTEXT_RETRIEVAL,
            lambda: [(stmt, pipeline.context_retriever.retrieve(stmt)) for stmt in statements],
        )

        assert result.success is True
        assert result.items_processed == 5
        assert pipeline.context_retriever.retrieve.call_count == 5

    def test_bill_linking_for_multiple_statements(self):
        """Test bill linking for multiple statements."""
        db_session = Mock()
        vector_db = Mock()

        pipeline = ProcessingPipeline(db_session, vector_db)

        # Create multiple statements
        statements = [
            Statement(
                text=f"Statement about Bill {i}",
                mp_id=f"mp{i}",
                start_pos=i * 100,
                end_pos=(i + 1) * 100,
            )
            for i in range(5)
        ]

        # Mock bill linking
        pipeline.bill_linker = Mock()
        pipeline.bill_linker.find_bill_mentions.return_value = []

        # Test batch bill linking
        result = pipeline._run_stage(
            PipelineStage.BILL_LINKING,
            lambda: [pipeline.bill_linker.find_bill_mentions(stmt) for stmt in statements],
        )

        assert result.success is True
        assert result.items_processed == 5
        assert pipeline.bill_linker.find_bill_mentions.call_count == 5
