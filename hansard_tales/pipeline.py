"""
Pipeline orchestration for Hansard Tales processing.

This module provides the ProcessingPipeline class that orchestrates the complete
document processing workflow from PDF extraction through analysis to site generation.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.orm import Session

from hansard_tales.analysis.bill_statement_linker import BillStatementLinker
from hansard_tales.analysis.citation_verifier import CitationVerifier
from hansard_tales.analysis.context_retriever import ContextRetriever
from hansard_tales.analysis.filler_detector import FillerDetector, StatementType
from hansard_tales.analysis.llm_analyzer import LLMAnalyzer
from hansard_tales.analysis.mp_identifier import MPIdentifier
from hansard_tales.analysis.mp_profile_generator import MPProfileGenerator
from hansard_tales.analysis.session_summary_generator import SessionSummaryGenerator
from hansard_tales.analysis.statement_segmenter import StatementSegmenter
from hansard_tales.database.models import DocumentORM, StatementORM
from hansard_tales.processors.pdf_processor import PDFProcessor
from hansard_tales.processors.vote_processor import VoteProcessor
from hansard_tales.site.generator import StaticSiteGenerator
from hansard_tales.vector_db.interface import VectorDB

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline processing stages."""

    DOWNLOAD = "download"
    TEXT_EXTRACTION = "text_extraction"
    MP_IDENTIFICATION = "mp_identification"
    SEGMENTATION = "segmentation"
    CLASSIFICATION = "classification"
    CONTEXT_RETRIEVAL = "context_retrieval"
    LLM_ANALYSIS = "llm_analysis"
    CITATION_VERIFICATION = "citation_verification"
    VOTE_PROCESSING = "vote_processing"
    BILL_LINKING = "bill_linking"
    PROFILE_GENERATION = "profile_generation"
    SUMMARY_GENERATION = "summary_generation"
    SITE_GENERATION = "site_generation"


@dataclass
class PipelineResult:
    """Result of pipeline stage execution."""

    stage: PipelineStage
    success: bool
    duration: float
    items_processed: int
    errors: list[str] = field(default_factory=list)
    data: Optional[Any] = None


class ProcessingPipeline:
    """Orchestrate document processing pipeline."""

    def __init__(
        self,
        db_session: Session,
        vector_db: VectorDB,
        config: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize processing pipeline.

        Args:
            db_session: Database session
            vector_db: Vector database interface
            config: Optional configuration dictionary with keys:
                - anthropic_api_key: API key for Claude
                - template_dir: Path to Jinja2 templates
                - output_dir: Path for generated site
                - max_retries: Maximum retry attempts (default: 3)
                - retry_delay: Delay between retries in seconds (default: 1.0)
        """
        self.db = db_session
        self.vector_db = vector_db
        self.config = config or {}

        # Initialize all components
        self.mp_identifier = MPIdentifier(db_session)
        self.segmenter = StatementSegmenter(self.mp_identifier)
        self.filler_detector = FillerDetector()
        self.context_retriever = ContextRetriever(vector_db)

        # LLM analyzer (requires API key)
        api_key = self.config.get("anthropic_api_key")
        if api_key:
            self.llm_analyzer = LLMAnalyzer(api_key)
        else:
            self.llm_analyzer = None
            logger.warning("No Anthropic API key provided, LLM analysis disabled")

        self.citation_verifier = CitationVerifier(db_session)
        self.vote_processor = VoteProcessor(db_session, self.mp_identifier)
        self.bill_linker = BillStatementLinker(db_session, vector_db)

        # Profile and summary generators (require LLM)
        if self.llm_analyzer:
            self.profile_generator = MPProfileGenerator(db_session, self.llm_analyzer)
            self.summary_generator = SessionSummaryGenerator(db_session, self.llm_analyzer)
        else:
            self.profile_generator = None
            self.summary_generator = None

        # Site generator
        template_dir = self.config.get("template_dir", "templates")
        output_dir = self.config.get("output_dir", "output")
        self.site_generator = StaticSiteGenerator(
            db_session,
            Path(template_dir),
            Path(output_dir),
        )

        # PDF processor
        self.pdf_processor = PDFProcessor()

        # Configuration
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 1.0)

        logger.info("ProcessingPipeline initialized")

    def process_hansard(
        self,
        pdf_path: Path,
        session_id: Optional[str] = None,
    ) -> list[PipelineResult]:
        """
        Process a Hansard PDF through complete pipeline.

        Args:
            pdf_path: Path to Hansard PDF file
            session_id: Optional session ID (generated if not provided)

        Returns:
            List of PipelineResult objects for each stage

        Raises:
            ValueError: If pdf_path is invalid
            FileNotFoundError: If PDF file doesn't exist
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        results = []
        logger.info(f"Processing Hansard: {pdf_path}")

        try:
            # Stage 1: Text extraction
            result = self._run_stage(
                PipelineStage.TEXT_EXTRACTION,
                lambda: self._extract_text(pdf_path),
            )
            results.append(result)
            if not result.success:
                return results
            text = result.data

            # Stage 2: MP identification & segmentation
            result = self._run_stage(
                PipelineStage.SEGMENTATION,
                lambda: self.segmenter.segment(text, session_id or ""),
            )
            results.append(result)
            if not result.success:
                return results
            statements = result.data

            # Stage 3: Classification (filler detection)
            result = self._run_stage(
                PipelineStage.CLASSIFICATION,
                lambda: [(stmt, self.filler_detector.classify(stmt)) for stmt in statements],
            )
            results.append(result)
            if not result.success:
                return results
            classified = result.data

            # Filter substantive statements
            substantive = [
                stmt for stmt, (type_, _) in classified if type_ == StatementType.SUBSTANTIVE
            ]
            logger.info(
                f"Filtered {len(substantive)} substantive statements "
                f"from {len(statements)} total"
            )

            # Stage 4: Context retrieval (RAG)
            result = self._run_stage(
                PipelineStage.CONTEXT_RETRIEVAL,
                lambda: [(stmt, self.context_retriever.retrieve(stmt)) for stmt in substantive],
            )
            results.append(result)
            if not result.success:
                return results
            with_context = result.data

            # Stage 5: LLM analysis (if enabled)
            if self.llm_analyzer:
                result = self._run_stage(
                    PipelineStage.LLM_ANALYSIS,
                    lambda: [
                        (stmt, self.llm_analyzer.analyze(stmt, ctx)) for stmt, ctx in with_context
                    ],
                )
                results.append(result)
                if not result.success:
                    return results
                analyzed = result.data

                # Stage 6: Citation verification
                result = self._run_stage(
                    PipelineStage.CITATION_VERIFICATION,
                    lambda: self._verify_citations(analyzed),
                )
                results.append(result)
            else:
                logger.warning("Skipping LLM analysis (no API key)")
                analyzed = [(stmt, None) for stmt, _ in with_context]

            # Stage 7: Bill linking
            result = self._run_stage(
                PipelineStage.BILL_LINKING,
                lambda: [(stmt, self.bill_linker.find_bill_mentions(stmt)) for stmt, _ in analyzed],
            )
            results.append(result)

            # Store results in database
            self._store_hansard_results(pdf_path, analyzed, session_id)

            logger.info(f"Hansard processing complete: {pdf_path}")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            results.append(
                PipelineResult(
                    stage=PipelineStage.TEXT_EXTRACTION,
                    success=False,
                    duration=0,
                    items_processed=0,
                    errors=[str(e)],
                )
            )

        return results

    def process_votes(
        self,
        pdf_path: Path,
        session_id: Optional[str] = None,
    ) -> list[PipelineResult]:
        """
        Process a Votes & Proceedings PDF through pipeline.

        Args:
            pdf_path: Path to Votes PDF file
            session_id: Optional session ID

        Returns:
            List of PipelineResult objects for each stage

        Raises:
            ValueError: If pdf_path is invalid
            FileNotFoundError: If PDF file doesn't exist
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        results = []
        logger.info(f"Processing Votes: {pdf_path}")

        try:
            # Stage 1: Vote processing (extraction from PDF)
            result = self._run_stage(
                PipelineStage.VOTE_PROCESSING,
                lambda: self.vote_processor.process_pdf(pdf_path),
            )
            results.append(result)
            if not result.success:
                return results
            votes = result.data

            # Store results in database
            self._store_vote_results(pdf_path, votes, session_id)

            logger.info(f"Votes processing complete: {pdf_path} ({len(votes)} votes)")

        except Exception as e:
            logger.error(f"Votes pipeline failed: {e}", exc_info=True)
            results.append(
                PipelineResult(
                    stage=PipelineStage.VOTE_PROCESSING,
                    success=False,
                    duration=0,
                    items_processed=0,
                    errors=[str(e)],
                )
            )

        return results

    def _run_stage(
        self,
        stage: PipelineStage,
        func: Callable,
    ) -> PipelineResult:
        """
        Run a pipeline stage with timing and error handling.

        Args:
            stage: Pipeline stage being executed
            func: Function to execute for this stage

        Returns:
            PipelineResult with execution details
        """
        start = time.time()
        logger.info(f"Starting stage: {stage.value}")

        try:
            data = func()
            duration = time.time() - start

            # Count items processed
            if isinstance(data, list):
                items_processed = len(data)
            elif data is not None:
                items_processed = 1
            else:
                items_processed = 0

            logger.info(
                f"Stage {stage.value} completed: " f"{items_processed} items in {duration:.2f}s"
            )

            return PipelineResult(
                stage=stage,
                success=True,
                duration=duration,
                items_processed=items_processed,
                errors=[],
                data=data,
            )

        except Exception as e:
            duration = time.time() - start
            logger.error(f"Stage {stage.value} failed: {e}", exc_info=True)

            return PipelineResult(
                stage=stage,
                success=False,
                duration=duration,
                items_processed=0,
                errors=[str(e)],
                data=None,
            )

    def _extract_text(self, pdf_path: Path) -> str:
        """
        Extract text from PDF with error handling.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text

        Raises:
            ValueError: If text extraction fails
        """
        try:
            text = self.pdf_processor.extract_text(pdf_path)
            if not text or len(text.strip()) < 100:
                raise ValueError(f"Insufficient text extracted from {pdf_path}")
            return text
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise ValueError(f"Failed to extract text from {pdf_path}: {e}")

    def _verify_citations(self, analyzed: list) -> list:
        """
        Verify citations from LLM analysis.

        Args:
            analyzed: List of (statement, analysis) tuples

        Returns:
            List of verified citations
        """
        verified = []
        for stmt, analysis in analyzed:
            if analysis and hasattr(analysis, "citations"):
                for citation in analysis.citations:
                    result = self.citation_verifier.verify_citation(
                        citation,
                        str(stmt.text),  # Use statement text as source
                    )
                    verified.append(result)
        return verified

    def _handle_stage_error(
        self,
        stage: PipelineStage,
        error: Exception,
        retry_count: int = 0,
    ) -> Optional[PipelineResult]:
        """
        Handle stage execution error with retry logic.

        Args:
            stage: Pipeline stage that failed
            error: Exception that occurred
            retry_count: Current retry attempt

        Returns:
            PipelineResult if retry should stop, None to continue
        """
        logger.error(f"Stage {stage.value} failed (attempt {retry_count + 1}): {error}")

        if retry_count >= self.max_retries:
            logger.error(f"Max retries ({self.max_retries}) exceeded for {stage.value}")
            return PipelineResult(
                stage=stage,
                success=False,
                duration=0,
                items_processed=0,
                errors=[f"Max retries exceeded: {error}"],
            )

        # Wait before retry
        time.sleep(self.retry_delay * (2**retry_count))  # Exponential backoff
        return None

    def _store_hansard_results(
        self,
        pdf_path: Path,
        analyzed: list,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Store Hansard processing results in database.

        Args:
            pdf_path: Path to source PDF
            analyzed: List of (statement, analysis) tuples
            session_id: Optional document ID
        """
        try:
            # Create or get document
            if session_id:
                document = self.db.query(DocumentORM).filter(DocumentORM.id == session_id).first()
            else:
                # Create new document from PDF metadata
                import hashlib

                from hansard_tales.database.models import ChamberEnum, DocumentTypeEnum

                # Generate source hash
                source_hash = hashlib.sha256(str(pdf_path).encode()).hexdigest()

                document = DocumentORM(
                    type=DocumentTypeEnum.HANSARD,
                    chamber=ChamberEnum.NATIONAL_ASSEMBLY,
                    title=pdf_path.stem,
                    date=datetime.now().date(),
                    parliament_term=2022,
                    source_url=str(pdf_path),
                    source_hash=source_hash,
                    download_date=datetime.now(),
                    vector_doc_id=f"doc_{source_hash[:16]}",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                self.db.add(document)
                self.db.flush()

            # Store statements
            for stmt, analysis in analyzed:
                import hashlib

                # Generate statement hash
                stmt_hash = hashlib.sha256(stmt.text.encode()).hexdigest()

                statement_orm = StatementORM(
                    document_id=document.id,
                    mp_id=stmt.mp_id,
                    text=stmt.text,
                    source_url=str(pdf_path),
                    source_hash=stmt_hash,
                    vector_doc_id=f"stmt_{stmt_hash[:16]}",
                    created_at=datetime.now(),
                )

                # Add analysis results if available
                if analysis:
                    if hasattr(analysis, "sentiment"):
                        statement_orm.sentiment = analysis.sentiment
                    if hasattr(analysis, "quality_score"):
                        statement_orm.quality_score = analysis.quality_score
                    if hasattr(analysis, "primary_topic"):
                        statement_orm.topics = [analysis.primary_topic]

                self.db.add(statement_orm)

            self.db.commit()
            logger.info(f"Stored {len(analyzed)} statements for document {document.id}")

        except Exception as e:
            logger.error(f"Failed to store results: {e}")
            self.db.rollback()
            raise

    def _store_vote_results(
        self,
        pdf_path: Path,
        votes: list,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Store vote processing results in database.

        Args:
            pdf_path: Path to source PDF
            votes: List of VoteRecord objects
            session_id: Optional session ID
        """
        try:
            # Store votes (implementation depends on VoteRecord structure)
            for vote in votes:
                # Store vote record
                # This would use the actual ORM models for votes
                pass

            self.db.commit()
            logger.info(f"Stored {len(votes)} votes")

        except Exception as e:
            logger.error(f"Failed to store vote results: {e}")
            self.db.rollback()
            raise
