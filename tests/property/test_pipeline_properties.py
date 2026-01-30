"""Property-based tests for ProcessingPipeline."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

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


class TestPipelineCompletenessProperties:
    """
    Property 12.1: Pipeline completeness.

    **Validates**: Requirements 1.13
    **Property**: All stages must execute for each document
    **Test Strategy**: Verify all stages run for multiple documents
    """

    @settings(max_examples=10, deadline=None)
    @given(
        num_statements=st.integers(min_value=1, max_value=10),
        has_llm=st.booleans(),
    )
    def test_all_stages_execute_for_document(
        self,
        mock_pipeline,
        num_statements,
        has_llm,
    ):
        """
        Test that all required stages execute for any document.

        Property: For any valid document, all pipeline stages must execute
        """
        # Configure LLM availability
        if has_llm:
            mock_pipeline.llm_analyzer = Mock()
        else:
            mock_pipeline.llm_analyzer = None

        # Mock PDF file existence
        with patch("hansard_tales.pipeline.Path.exists", return_value=True):
            # Mock text extraction
            mock_pipeline.pdf_processor = Mock()
            mock_pipeline.pdf_processor.extract_text.return_value = "Long text " * 50

            # Mock segmentation
            from hansard_tales.analysis.filler_detector import StatementType
            from hansard_tales.analysis.statement_segmenter import Statement

            statements = [
                Statement(
                    text=f"Statement {i}",
                    mp_id=f"mp{i}",
                    start_pos=i * 100,
                    end_pos=(i + 1) * 100,
                )
                for i in range(num_statements)
            ]
            mock_pipeline.segmenter = Mock()
            mock_pipeline.segmenter.segment.return_value = statements

            # Mock classification
            mock_pipeline.filler_detector = Mock()
            mock_pipeline.filler_detector.classify.return_value = (
                StatementType.SUBSTANTIVE,
                0.95,
            )

            # Mock context retrieval
            mock_pipeline.context_retriever = Mock()
            mock_pipeline.context_retriever.retrieve.return_value = Mock()

            # Mock bill linking
            mock_pipeline.bill_linker = Mock()
            mock_pipeline.bill_linker.find_bill_mentions.return_value = []

            # Mock database operations
            mock_pipeline.db.query.return_value.filter.return_value.first.return_value = None
            mock_pipeline.db.commit = Mock()

            # Process document
            results = mock_pipeline.process_hansard(Path("test.pdf"))

            # Verify all required stages executed
            stage_names = [r.stage for r in results]

            # These stages must always execute
            assert PipelineStage.TEXT_EXTRACTION in stage_names
            assert PipelineStage.SEGMENTATION in stage_names
            assert PipelineStage.CLASSIFICATION in stage_names
            assert PipelineStage.CONTEXT_RETRIEVAL in stage_names
            assert PipelineStage.BILL_LINKING in stage_names

            # LLM stages only if LLM is available
            if has_llm:
                assert PipelineStage.LLM_ANALYSIS in stage_names
                assert PipelineStage.CITATION_VERIFICATION in stage_names

            # All stages should succeed
            assert all(r.success for r in results)

    @settings(max_examples=10, deadline=None)
    @given(
        num_votes=st.integers(min_value=1, max_value=10),
    )
    def test_votes_pipeline_completeness(
        self,
        mock_pipeline,
        num_votes,
    ):
        """
        Test that votes pipeline executes completely.

        Property: For any valid votes document, all stages must execute
        """
        # Mock PDF file existence
        with patch("hansard_tales.pipeline.Path.exists", return_value=True):
            # Mock vote processing
            mock_votes = [Mock() for _ in range(num_votes)]
            mock_pipeline.vote_processor = Mock()
            mock_pipeline.vote_processor.process_pdf.return_value = mock_votes

            # Mock database operations
            mock_pipeline.db.commit = Mock()

            # Process document
            results = mock_pipeline.process_votes(Path("test.pdf"))

            # Verify vote processing stage executed
            assert len(results) >= 1
            assert any(r.stage == PipelineStage.VOTE_PROCESSING for r in results)

            # Verify success
            assert all(r.success for r in results)

            # Verify correct number of items processed
            vote_result = next(r for r in results if r.stage == PipelineStage.VOTE_PROCESSING)
            assert vote_result.items_processed == num_votes


class TestErrorRecoveryProperties:
    """
    Property 12.2: Error recovery.

    **Validates**: Requirements 1.13
    **Property**: Pipeline failures must not corrupt database
    **Test Strategy**: Inject errors, verify database consistency
    """

    @settings(max_examples=10, deadline=None)
    @given(
        failure_stage=st.sampled_from(
            [
                PipelineStage.TEXT_EXTRACTION,
                PipelineStage.SEGMENTATION,
                PipelineStage.CLASSIFICATION,
            ]
        ),
    )
    def test_database_rollback_on_failure(
        self,
        mock_pipeline,
        failure_stage,
    ):
        """
        Test that database is rolled back on pipeline failure.

        Property: Any pipeline failure must trigger database rollback
        """
        # Mock PDF file existence
        with patch("hansard_tales.pipeline.Path.exists", return_value=True):
            # Configure pipeline to fail at specific stage
            if failure_stage == PipelineStage.TEXT_EXTRACTION:
                mock_pipeline.pdf_processor = Mock()
                mock_pipeline.pdf_processor.extract_text.side_effect = Exception(
                    "Extraction failed"
                )
            elif failure_stage == PipelineStage.SEGMENTATION:
                mock_pipeline.pdf_processor = Mock()
                mock_pipeline.pdf_processor.extract_text.return_value = "Long text " * 50
                mock_pipeline.segmenter = Mock()
                mock_pipeline.segmenter.segment.side_effect = Exception("Segmentation failed")
            elif failure_stage == PipelineStage.CLASSIFICATION:
                mock_pipeline.pdf_processor = Mock()
                mock_pipeline.pdf_processor.extract_text.return_value = "Long text " * 50

                from hansard_tales.analysis.statement_segmenter import Statement

                statements = [Statement(text="Test", mp_id="mp1", start_pos=0, end_pos=100)]
                mock_pipeline.segmenter = Mock()
                mock_pipeline.segmenter.segment.return_value = statements

                mock_pipeline.filler_detector = Mock()
                mock_pipeline.filler_detector.classify.side_effect = Exception(
                    "Classification failed"
                )

            # Mock database operations
            mock_pipeline.db.rollback = Mock()
            mock_pipeline.db.commit = Mock()

            # Process document (should fail)
            results = mock_pipeline.process_hansard(Path("test.pdf"))

            # Verify at least one stage failed
            assert any(not r.success for r in results)

            # Verify database was not committed after failure
            # (commit should only be called if all stages succeed)
            if any(not r.success for r in results):
                # If there was a failure, commit should not have been called
                # or rollback should have been called
                assert mock_pipeline.db.commit.call_count == 0 or mock_pipeline.db.rollback.called

    @settings(max_examples=10, deadline=None)
    @given(
        num_retries=st.integers(min_value=1, max_value=5),
    )
    def test_retry_logic_respects_max_retries(
        self,
        mock_pipeline,
        num_retries,
    ):
        """
        Test that retry logic respects maximum retry count.

        Property: Error handling must respect configured max retries
        """
        # Configure retry settings
        mock_pipeline.max_retries = num_retries
        mock_pipeline.retry_delay = 0.01

        error = ValueError("Test error")

        # Test retries within limit
        for retry_count in range(num_retries):
            result = mock_pipeline._handle_stage_error(
                PipelineStage.TEXT_EXTRACTION,
                error,
                retry_count=retry_count,
            )
            # Should return None to continue retrying
            assert result is None

        # Test retry at limit
        result = mock_pipeline._handle_stage_error(
            PipelineStage.TEXT_EXTRACTION,
            error,
            retry_count=num_retries,
        )
        # Should return PipelineResult indicating failure
        assert result is not None
        assert result.success is False
        assert "Max retries exceeded" in result.errors[0]

    @settings(max_examples=10, deadline=None)
    @given(
        text_length=st.integers(min_value=0, max_value=200),
    )
    def test_text_extraction_validation(
        self,
        mock_pipeline,
        text_length,
    ):
        """
        Test that text extraction validates content length.

        Property: Insufficient text must be rejected
        """
        mock_pipeline.pdf_processor = Mock()
        test_text = "x" * text_length
        mock_pipeline.pdf_processor.extract_text.return_value = test_text

        if text_length < 100:
            # Should raise error for insufficient text
            with pytest.raises(ValueError, match="Insufficient text extracted"):
                mock_pipeline._extract_text(Path("test.pdf"))
        else:
            # Should succeed for sufficient text
            result = mock_pipeline._extract_text(Path("test.pdf"))
            assert result == test_text
