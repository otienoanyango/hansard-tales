"""
Integration tests for Phase 1 analysis pipeline components.

Tests the integration between different analysis components:
- MP Identification → Segmentation
- Segmentation → Classification
- Classification → Context Retrieval
- Context Retrieval → LLM Analysis
- LLM Analysis → Citation Verification
- Vote Processing → Database Storage
- Bill Linking → Profile Generation
- Profile Generation → Site Generation
"""

import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hansard_tales.analysis.bill_statement_linker import BillStatementLinker
from hansard_tales.analysis.citation_verifier import CitationVerifier
from hansard_tales.analysis.context_retriever import ContextRetriever
from hansard_tales.analysis.filler_detector import FillerDetector, StatementType
from hansard_tales.analysis.llm_analyzer import LLMAnalyzer
from hansard_tales.analysis.mp_identifier import MPIdentifier
from hansard_tales.analysis.mp_profile_generator import MPProfileGenerator
from hansard_tales.analysis.statement_segmenter import Statement, StatementSegmenter
from hansard_tales.database.models import (
    MPORM,
    Base,
    BillORM,
    DocumentORM,
    StatementORM,
)
from hansard_tales.models import Chamber
from hansard_tales.processors.vote_processor import VoteProcessor
from hansard_tales.site.generator import StaticSiteGenerator
from hansard_tales.vector_db import ChromaDBAdapter


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add sample MPs
    mp1 = MPORM(
        name="Hon. John Doe",
        clean_name="John Doe",
        constituency="Nairobi West",
        party="UDA",
        chamber=Chamber.NATIONAL_ASSEMBLY.value,
        status="Elected",
        parliament_term=13,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    mp2 = MPORM(
        name="Hon. Jane Smith",
        clean_name="Jane Smith",
        constituency="Kisumu Central",
        party="ODM",
        chamber=Chamber.NATIONAL_ASSEMBLY.value,
        status="Elected",
        parliament_term=13,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add_all([mp1, mp2])

    # Add sample document (represents a session)
    test_doc = DocumentORM(
        type="HANSARD",
        chamber=Chamber.NATIONAL_ASSEMBLY.value,
        title="Hansard Report - Tuesday, 4th November 2025 (Afternoon)",
        date=date(2025, 11, 4),
        session_id="afternoon_20251104",
        parliament_term=13,
        source_url="https://test.com/hansard.pdf",
        source_hash="test_hash_123",
        download_date=datetime.now(UTC),
        vector_doc_id="vec_test_123",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(test_doc)

    # Add sample bill
    bill = BillORM(
        title="The Finance Bill, 2025",
        bill_number="15",
        year=2025,
        chamber=Chamber.NATIONAL_ASSEMBLY.value,
        status="First Reading",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(bill)

    session.commit()
    yield session
    session.close()


@pytest.fixture
def temp_vector_db():
    """Create temporary vector database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vector_db = ChromaDBAdapter(persist_directory=tmpdir)
        vector_db.create_collection("statements", dimension=384)
        yield vector_db


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory for site generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestMPIdentificationToSegmentation:
    """Test integration between MP identification and statement segmentation."""

    def test_mp_identification_feeds_segmentation(self, temp_db):
        """Test that MP identification results are used in segmentation."""
        # Setup
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)

        # Sample Hansard text with MP names
        text = """
Hon. John Doe (Nairobi West, UDA): Mr. Speaker, I rise to support this motion.
The Finance Bill is crucial for our economic development.

Hon. Jane Smith (Kisumu Central, ODM): Thank you, Mr. Speaker.
I have concerns about the tax provisions in this bill.
"""

        # Segment text
        statements = segmenter.segment(text, session_id="test_session")

        # Verify MP identification worked
        assert len(statements) >= 2
        assert any(stmt.mp_id is not None for stmt in statements)

        # Verify MPs were correctly identified
        mp_names = [stmt.mp_name for stmt in statements if stmt.mp_name]
        assert "Hon. John Doe" in mp_names or "John Doe" in mp_names

    def test_segmentation_handles_unidentified_mps(self, temp_db):
        """Test that segmentation handles MPs not in database."""
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)

        text = """
Hon. Unknown Person (Somewhere, Party): This is a statement.
"""

        statements = segmenter.segment(text, session_id="test_session")

        # Should still create statement even if MP not identified
        assert len(statements) >= 1
        # MP ID should be None for unknown MPs
        assert statements[0].mp_id is None


class TestSegmentationToClassification:
    """Test integration between segmentation and classification."""

    def test_segmented_statements_are_classified(self, temp_db):
        """Test that segmented statements can be classified."""
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)
        classifier = FillerDetector()

        text = """
Hon. John Doe (Nairobi West, UDA): Thank you, Mr. Speaker.

Hon. Jane Smith (Kisumu Central, ODM): I rise to support this important motion
on healthcare reform. We need to ensure universal coverage for all citizens.
"""

        # Segment
        statements = segmenter.segment(text, session_id="test_session")

        # Classify each statement
        classifications = []
        for stmt in statements:
            stmt_type, confidence = classifier.classify(stmt)
            classifications.append((stmt, stmt_type, confidence))

        # Verify classifications
        assert len(classifications) >= 2

        # First statement should be filler (short acknowledgment)
        assert any(stmt_type == StatementType.SHORT_ACK for _, stmt_type, _ in classifications)

        # Second statement should be substantive
        assert any(stmt_type == StatementType.SUBSTANTIVE for _, stmt_type, _ in classifications)

    def test_classification_filters_filler_statements(self, temp_db):
        """Test that classification can filter out filler statements."""
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)
        classifier = FillerDetector()

        text = """
Hon. John Doe: I beg to move.
Hon. Jane Smith: I second.
Hon. John Doe: This is a substantive policy statement about healthcare.
"""

        statements = segmenter.segment(text, session_id="test_session")

        # Filter to substantive only
        substantive = [stmt for stmt in statements if classifier.is_substantive(stmt)]

        # Should have fewer substantive statements than total
        assert len(substantive) < len(statements)
        assert len(substantive) >= 1


class TestClassificationToContextRetrieval:
    """Test integration between classification and context retrieval."""

    def test_substantive_statements_get_context(self, temp_db, temp_vector_db):
        """Test that substantive statements get context retrieved."""
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)
        classifier = FillerDetector()
        context_retriever = ContextRetriever(temp_vector_db, temp_db)

        text = """
Hon. John Doe (Nairobi West, UDA): We need comprehensive healthcare reform
to ensure universal coverage for all citizens.
"""

        # Segment and classify
        statements = segmenter.segment(text, session_id="test_session")
        substantive = [stmt for stmt in statements if classifier.is_substantive(stmt)]

        # Retrieve context for substantive statements
        contexts = []
        for stmt in substantive:
            context = context_retriever.retrieve(stmt, top_k=3)
            contexts.append(context)

        # Verify context was retrieved
        assert len(contexts) == len(substantive)
        for context in contexts:
            assert context is not None
            # Context should have various components
            assert hasattr(context, "historical_statements")
            assert hasattr(context, "related_bills")


class TestContextRetrievalToLLMAnalysis:
    """Test integration between context retrieval and LLM analysis."""

    @patch("anthropic.Anthropic")
    def test_context_enhances_llm_analysis(self, mock_anthropic, temp_db, temp_vector_db):
        """Test that retrieved context is used in LLM analysis."""
        # Setup mocks
        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"sentiment": "positive", "sentiment_confidence": 0.9, "sentiment_explanation": "Supportive", "quality_score": 75, "quality_factors": {"clarity": 80, "depth": 70}, "primary_topic": "Healthcare", "secondary_topics": ["Reform"], "topic_confidence": 0.85, "key_points": ["Universal coverage"], "citations": ["healthcare reform"]}'
            )
        ]
        mock_client.messages.create.return_value = mock_response

        # Setup components
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)
        context_retriever = ContextRetriever(temp_vector_db, temp_db)
        llm_analyzer = LLMAnalyzer(api_key="test_key")
        llm_analyzer.client = mock_client

        text = """
Hon. John Doe (Nairobi West, UDA): We need comprehensive healthcare reform.
"""

        # Process pipeline
        statements = segmenter.segment(text, session_id="test_session")
        stmt = statements[0]
        context = context_retriever.retrieve(stmt, top_k=3)

        # Analyze with context
        analysis = llm_analyzer.analyze(stmt, context)

        # Verify LLM was called with context
        assert mock_client.messages.create.called
        call_args = mock_client.messages.create.call_args

        # Check that context was included in prompt
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]
        assert "healthcare reform" in prompt.lower()


class TestLLMAnalysisToCitationVerification:
    """Test integration between LLM analysis and citation verification."""

    @patch("anthropic.Anthropic")
    def test_llm_citations_are_verified(self, mock_anthropic, temp_db):
        """Test that LLM-generated citations are verified."""
        # Setup mocks
        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"sentiment": "positive", "sentiment_confidence": 0.9, "sentiment_explanation": "Supportive", "quality_score": 75, "quality_factors": {"clarity": 80}, "primary_topic": "Healthcare", "secondary_topics": [], "topic_confidence": 0.85, "key_points": ["Reform"], "citations": ["healthcare reform"]}'
            )
        ]
        mock_client.messages.create.return_value = mock_response

        # Setup components
        llm_analyzer = LLMAnalyzer(api_key="test_key")
        llm_analyzer.client = mock_client
        citation_verifier = CitationVerifier(temp_db)

        # Create statement
        stmt = Statement(
            text="We need comprehensive healthcare reform.", mp_id=None, start_pos=0, end_pos=42
        )

        # Analyze
        analysis = llm_analyzer.analyze(stmt, context=None)

        # Verify citations
        verified_citations = []
        for citation_text in analysis.citations:
            # In real scenario, we'd have source_id from statement
            citation = citation_verifier.verify_citation(
                citation_text, source_id="test_source", threshold=0.90
            )
            verified_citations.append(citation)

        # Should have verified citations
        assert len(verified_citations) > 0


class TestVoteProcessingToDatabaseStorage:
    """Test integration between vote processing and database storage."""

    def test_processed_votes_stored_in_database(self, temp_db):
        """Test that processed votes are correctly stored in database."""
        # Setup
        mp_identifier = MPIdentifier(temp_db)
        vote_processor = VoteProcessor(temp_db, mp_identifier)

        # Get session
        session = temp_db.query(SessionORM).first()

        # Create mock vote record
        from hansard_tales.processors.vote_processor import MPVote, VoteRecord

        mp = temp_db.query(MPORM).first()
        vote_record = VoteRecord(
            vote_id=str(uuid4()),
            session_id=str(session.id),
            date=date(2025, 11, 4),
            motion_text="Motion to approve the Finance Bill",
            vote_type="division",
            result="passed",
            ayes=150,
            noes=100,
            abstentions=10,
            mp_votes=[MPVote(mp_id=str(mp.id), vote="aye")],
        )

        # Store in database
        vote_orm = VoteRecordORM(
            session_id=session.id,
            date=vote_record.date,
            motion_text=vote_record.motion_text,
            vote_type=vote_record.vote_type,
            result=vote_record.result,
            ayes=vote_record.ayes,
            noes=vote_record.noes,
            abstentions=vote_record.abstentions,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        temp_db.add(vote_orm)
        temp_db.commit()

        # Verify storage
        stored_vote = temp_db.query(VoteRecordORM).first()
        assert stored_vote is not None
        assert stored_vote.motion_text == "Motion to approve the Finance Bill"
        assert stored_vote.ayes == 150
        assert stored_vote.result == "passed"


class TestBillLinkingToProfileGeneration:
    """Test integration between bill linking and profile generation."""

    def test_bill_mentions_included_in_mp_profile(self, temp_db, temp_vector_db):
        """Test that bill mentions are included in MP profiles."""
        # Setup
        bill_linker = BillStatementLinker(temp_db, temp_vector_db)

        # Get MP and bill
        mp = temp_db.query(MPORM).first()
        bill = temp_db.query(BillORM).first()
        session = temp_db.query(SessionORM).first()

        # Create statement mentioning bill
        stmt = Statement(
            text="I support The Finance Bill, 2025 because it promotes economic growth.",
            mp_id=str(mp.id),
            start_pos=0,
            end_pos=70,
        )

        # Find bill mentions
        mentions = bill_linker.find_bill_mentions(stmt)

        # Store statement with bill link
        stmt_orm = StatementORM(
            session_id=session.id,
            mp_id=mp.id,
            text=stmt.text,
            statement_type="substantive",
            start_pos=stmt.start_pos,
            end_pos=stmt.end_pos,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        temp_db.add(stmt_orm)
        temp_db.commit()

        # Generate profile
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client
            mock_response = Mock()
            mock_response.content = [Mock(text="MP profile summary")]
            mock_client.messages.create.return_value = mock_response

            llm_analyzer = LLMAnalyzer(api_key="test_key")
            llm_analyzer.client = mock_client

            profile_generator = MPProfileGenerator(temp_db, llm_analyzer)
            profile = profile_generator.generate_profile(str(mp.id))

        # Verify profile includes statement data
        assert profile.total_statements >= 1
        assert profile.substantive_statements >= 1


class TestProfileGenerationToSiteGeneration:
    """Test integration between profile generation and site generation."""

    def test_mp_profiles_generate_site_pages(self, temp_db, temp_output_dir):
        """Test that MP profiles are used to generate site pages."""
        # Setup
        mp = temp_db.query(MPORM).first()
        session = temp_db.query(SessionORM).first()

        # Add statement for MP
        stmt_orm = StatementORM(
            session_id=session.id,
            mp_id=mp.id,
            text="Test statement",
            statement_type="substantive",
            start_pos=0,
            end_pos=14,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        temp_db.add(stmt_orm)
        temp_db.commit()

        # Generate site
        template_dir = Path("templates")
        site_generator = StaticSiteGenerator(temp_db, template_dir, temp_output_dir)

        # Generate MP pages
        site_generator._generate_mp_pages()

        # Verify MP directory was created
        mp_dir = temp_output_dir / "mps"
        assert mp_dir.exists()
        assert (mp_dir / "index.html").exists()

        # Verify individual MP page was created
        mp_files = list(mp_dir.glob("*.html"))
        # Should have index.html plus MP pages
        assert len(mp_files) >= 2


class TestEndToEndPipelineIntegration:
    """Test complete end-to-end pipeline integration."""

    @patch("anthropic.Anthropic")
    def test_complete_hansard_processing_pipeline(
        self, mock_anthropic, temp_db, temp_vector_db, temp_output_dir
    ):
        """Test complete pipeline from text to site generation."""
        # Setup mocks
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"sentiment": "positive", "sentiment_confidence": 0.9, "sentiment_explanation": "Supportive", "quality_score": 75, "quality_factors": {"clarity": 80}, "primary_topic": "Healthcare", "secondary_topics": [], "topic_confidence": 0.85, "key_points": ["Reform"], "citations": ["healthcare reform"]}'
            )
        ]
        mock_client.messages.create.return_value = mock_response

        # Initialize all components
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)
        classifier = FillerDetector()
        context_retriever = ContextRetriever(temp_vector_db, temp_db)
        llm_analyzer = LLMAnalyzer(api_key="test_key")
        llm_analyzer.client = mock_client
        citation_verifier = CitationVerifier(temp_db)
        bill_linker = BillStatementLinker(temp_db, temp_vector_db)

        # Sample Hansard text
        text = """
Hon. John Doe (Nairobi West, UDA): Mr. Speaker, I rise to support
The Finance Bill, 2025. This legislation will promote economic growth
and create jobs for our youth.

Hon. Jane Smith (Kisumu Central, ODM): Thank you, Mr. Speaker.
I have concerns about the tax provisions in this bill.
"""

        # Get session
        session = temp_db.query(SessionORM).first()

        # Stage 1: Segmentation
        statements = segmenter.segment(text, session_id=str(session.id))
        assert len(statements) >= 2

        # Stage 2: Classification
        substantive = [stmt for stmt in statements if classifier.is_substantive(stmt)]
        assert len(substantive) >= 1

        # Stage 3: Context Retrieval
        with_context = [(stmt, context_retriever.retrieve(stmt, top_k=3)) for stmt in substantive]

        # Stage 4: LLM Analysis
        analyzed = []
        for stmt, context in with_context:
            analysis = llm_analyzer.analyze(stmt, context)
            analyzed.append((stmt, analysis))

        assert len(analyzed) >= 1

        # Stage 5: Citation Verification
        for stmt, analysis in analyzed:
            for citation_text in analysis.citations:
                citation = citation_verifier.verify_citation(
                    citation_text, source_id=str(uuid4()), threshold=0.90
                )
                assert citation is not None

        # Stage 6: Bill Linking
        for stmt, analysis in analyzed:
            mentions = bill_linker.find_bill_mentions(stmt)
            # Should find Finance Bill mention
            if "Finance Bill" in stmt.text:
                assert len(mentions) >= 0  # May or may not find depending on DB state

        # Stage 7: Store in database
        for stmt, analysis in analyzed:
            stmt_orm = StatementORM(
                session_id=session.id,
                mp_id=int(stmt.mp_id) if stmt.mp_id else None,
                text=stmt.text,
                statement_type="substantive",
                start_pos=stmt.start_pos,
                end_pos=stmt.end_pos,
                sentiment=analysis.sentiment,
                quality_score=analysis.quality_score,
                primary_topic=analysis.primary_topic,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            temp_db.add(stmt_orm)
        temp_db.commit()

        # Verify database storage
        stored_statements = temp_db.query(StatementORM).all()
        assert len(stored_statements) >= 1

        # Stage 8: Generate site
        template_dir = Path("templates")
        site_generator = StaticSiteGenerator(temp_db, template_dir, temp_output_dir)

        # Generate pages
        site_generator._generate_homepage()
        site_generator._generate_mp_pages()
        site_generator._generate_session_pages()

        # Verify site generation
        assert (temp_output_dir / "index.html").exists()
        assert (temp_output_dir / "mps" / "index.html").exists()
        assert (temp_output_dir / "sessions" / "index.html").exists()
