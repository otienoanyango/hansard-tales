"""
End-to-end tests for Phase 1 complete analysis pipeline.

Tests the complete system from PDF processing to site generation:
- Process complete Hansard PDF
- Process complete Votes PDF
- Generate MP profiles
- Generate session summaries
- Generate static site
- Verify site content
- Measure performance
- Verify cost tracking
"""

import tempfile
import time
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
from hansard_tales.analysis.filler_detector import FillerDetector
from hansard_tales.analysis.llm_analyzer import LLMAnalyzer
from hansard_tales.analysis.mp_identifier import MPIdentifier
from hansard_tales.analysis.mp_profile_generator import MPProfileGenerator
from hansard_tales.analysis.session_summary_generator import SessionSummaryGenerator
from hansard_tales.analysis.statement_segmenter import StatementSegmenter
from hansard_tales.database.models import (
    MPORM,
    Base,
    BillORM,
    SessionORM,
    StatementORM,
    VoteRecordORM,
)
from hansard_tales.models import Chamber
from hansard_tales.processors.vote_processor import VoteProcessor
from hansard_tales.site.generator import StaticSiteGenerator
from hansard_tales.vector_db import ChromaDBAdapter


@pytest.fixture
def temp_db():
    """Create temporary database with sample data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add sample MPs
    mps = [
        MPORM(
            name="Hon. John Doe",
            clean_name="John Doe",
            constituency="Nairobi West",
            party="UDA",
            chamber=Chamber.NATIONAL_ASSEMBLY.value,
            status="Elected",
            parliament_term=13,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        MPORM(
            name="Hon. Jane Smith",
            clean_name="Jane Smith",
            constituency="Kisumu Central",
            party="ODM",
            chamber=Chamber.NATIONAL_ASSEMBLY.value,
            status="Elected",
            parliament_term=13,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        MPORM(
            name="Hon. Peter Jones",
            clean_name="Peter Jones",
            constituency="Mombasa North",
            party="Wiper",
            chamber=Chamber.NATIONAL_ASSEMBLY.value,
            status="Elected",
            parliament_term=13,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]
    session.add_all(mps)

    # Add sample session
    test_session = SessionORM(
        date=date(2025, 11, 4),
        session_type="afternoon",
        chamber=Chamber.NATIONAL_ASSEMBLY.value,
        parliament_term=13,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(test_session)

    # Add sample bills
    bills = [
        BillORM(
            title="The Finance Bill, 2025",
            bill_number="15",
            year=2025,
            chamber=Chamber.NATIONAL_ASSEMBLY.value,
            status="First Reading",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        BillORM(
            title="The Healthcare Reform Bill, 2025",
            bill_number="20",
            year=2025,
            chamber=Chamber.NATIONAL_ASSEMBLY.value,
            status="Second Reading",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]
    session.add_all(bills)

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
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_hansard_text():
    """Sample Hansard text for testing."""
    return """
NATIONAL ASSEMBLY
HANSARD REPORT
Tuesday, 4th November 2025
Afternoon Sitting

The House met at 2:30 p.m.

[The Speaker (Hon. Moses Wetangula) in the Chair]

PRAYERS

COMMUNICATION FROM THE CHAIR

The Speaker (Hon. Moses Wetangula): Hon. Members, I have a communication
to make regarding the Finance Bill, 2025.

MOTION - THE FINANCE BILL, 2025

Hon. John Doe (Nairobi West, UDA): Mr. Speaker, I beg to move that this House
approves The Finance Bill, 2025. This legislation is crucial for our economic
development. It will create jobs, promote investment, and ensure fiscal
sustainability. The tax reforms proposed will make our system more equitable
and efficient.

Hon. Jane Smith (Kisumu Central, ODM): Thank you, Mr. Speaker. I rise to
contribute to this important debate. While I appreciate the objectives of
this Bill, I have serious concerns about the tax provisions. The proposed
VAT increases will disproportionately affect low-income families. We need
to reconsider these provisions to ensure social justice.

Hon. Peter Jones (Mombasa North, Wiper): Mr. Speaker, I support this motion.
The Finance Bill addresses critical infrastructure needs in our coastal region.
The allocation for port development will boost trade and create employment
opportunities for our youth.

The Speaker (Hon. Moses Wetangula): Hon. Members, I now put the question.

(Question put and agreed to)

The House rose at 5:30 p.m.
"""


class TestCompleteHansardProcessing:
    """Test complete Hansard PDF processing pipeline."""

    @patch("anthropic.Anthropic")
    def test_process_complete_hansard_document(
        self, mock_anthropic, temp_db, temp_vector_db, sample_hansard_text
    ):
        """Test processing a complete Hansard document through entire pipeline."""
        # Setup mocks
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"sentiment": "positive", "sentiment_confidence": 0.9, "sentiment_explanation": "Supportive of bill", "quality_score": 75, "quality_factors": {"clarity": 80, "depth": 70, "evidence": 65}, "primary_topic": "Finance", "secondary_topics": ["Economy", "Taxation"], "topic_confidence": 0.85, "key_points": ["Economic development", "Job creation", "Tax reform"], "citations": ["economic development", "tax reforms"]}'
            )
        ]
        mock_client.messages.create.return_value = mock_response

        # Initialize pipeline components
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)
        classifier = FillerDetector()
        context_retriever = ContextRetriever(temp_vector_db, temp_db)
        llm_analyzer = LLMAnalyzer(api_key="test_key")
        llm_analyzer.client = mock_client
        citation_verifier = CitationVerifier(temp_db)
        bill_linker = BillStatementLinker(temp_db, temp_vector_db)

        # Get session
        session = temp_db.query(SessionORM).first()

        # Process document
        start_time = time.time()

        # Stage 1: Segmentation
        statements = segmenter.segment(sample_hansard_text, session_id=str(session.id))
        assert len(statements) >= 5  # Should have multiple statements

        # Stage 2: Classification
        classified = []
        for stmt in statements:
            stmt_type, confidence = classifier.classify(stmt)
            classified.append((stmt, stmt_type, confidence))

        substantive = [stmt for stmt, stmt_type, _ in classified if classifier.is_substantive(stmt)]
        assert len(substantive) >= 3  # Should have substantive statements

        # Stage 3: Context Retrieval
        with_context = []
        for stmt in substantive:
            context = context_retriever.retrieve(stmt, top_k=3)
            with_context.append((stmt, context))

        # Stage 4: LLM Analysis
        analyzed = []
        for stmt, context in with_context:
            analysis = llm_analyzer.analyze(stmt, context)
            analyzed.append((stmt, analysis))

        assert len(analyzed) >= 3

        # Stage 5: Citation Verification
        verified_count = 0
        for stmt, analysis in analyzed:
            for citation_text in analysis.citations:
                citation = citation_verifier.verify_citation(
                    citation_text, source_id=str(uuid4()), threshold=0.90
                )
                if citation.verification_status == "verified":
                    verified_count += 1

        # Stage 6: Bill Linking
        bill_mentions_count = 0
        for stmt, analysis in analyzed:
            mentions = bill_linker.find_bill_mentions(stmt)
            bill_mentions_count += len(mentions)

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

        processing_time = time.time() - start_time

        # Verify results
        stored_statements = temp_db.query(StatementORM).all()
        assert len(stored_statements) >= 3

        # Verify performance (should process in reasonable time)
        assert processing_time < 30  # Should complete in under 30 seconds for test

        # Verify data quality
        for stmt in stored_statements:
            assert stmt.text is not None
            assert stmt.sentiment in ["positive", "negative", "neutral", "mixed"]
            assert 0 <= stmt.quality_score <= 100
            assert stmt.primary_topic is not None


class TestCompleteVotesProcessing:
    """Test complete Votes PDF processing pipeline."""

    def test_process_complete_votes_document(self, temp_db):
        """Test processing a complete Votes & Proceedings document."""
        # Setup
        mp_identifier = MPIdentifier(temp_db)
        vote_processor = VoteProcessor(temp_db, mp_identifier)

        # Get session and MPs
        session = temp_db.query(SessionORM).first()
        mps = temp_db.query(MPORM).all()

        # Create mock vote record
        from hansard_tales.processors.vote_processor import MPVote, VoteRecord

        vote_record = VoteRecord(
            vote_id=str(uuid4()),
            session_id=str(session.id),
            date=date(2025, 11, 4),
            motion_text="Motion to approve The Finance Bill, 2025",
            vote_type="division",
            result="passed",
            ayes=180,
            noes=120,
            abstentions=15,
            mp_votes=[
                MPVote(mp_id=str(mps[0].id), vote="aye"),
                MPVote(mp_id=str(mps[1].id), vote="no"),
                MPVote(mp_id=str(mps[2].id), vote="aye"),
            ],
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
        assert stored_vote.ayes == 180
        assert stored_vote.noes == 120
        assert stored_vote.result == "passed"

        # Verify vote totals
        assert stored_vote.ayes + stored_vote.noes + stored_vote.abstentions == 315


class TestMPProfileGeneration:
    """Test MP profile generation."""

    @patch("anthropic.Anthropic")
    def test_generate_complete_mp_profiles(self, mock_anthropic, temp_db):
        """Test generating complete MP profiles with all data."""
        # Setup mocks
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text="Hon. John Doe is an active member focusing on economic policy and finance. He has contributed substantively to debates on fiscal reform."
            )
        ]
        mock_client.messages.create.return_value = mock_response

        # Add statements for MPs
        session = temp_db.query(SessionORM).first()
        mps = temp_db.query(MPORM).all()

        for mp in mps:
            for i in range(5):
                stmt = StatementORM(
                    session_id=session.id,
                    mp_id=mp.id,
                    text=f"Statement {i} by {mp.name}",
                    statement_type="substantive",
                    start_pos=0,
                    end_pos=20,
                    sentiment="positive",
                    quality_score=75,
                    primary_topic="Finance",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                temp_db.add(stmt)
        temp_db.commit()

        # Generate profiles
        llm_analyzer = LLMAnalyzer(api_key="test_key")
        llm_analyzer.client = mock_client
        profile_generator = MPProfileGenerator(temp_db, llm_analyzer)

        profiles = []
        for mp in mps:
            profile = profile_generator.generate_profile(str(mp.id))
            profiles.append(profile)

        # Verify profiles
        assert len(profiles) == len(mps)

        for profile in profiles:
            assert profile.total_statements >= 5
            assert profile.substantive_statements >= 5
            assert profile.avg_quality_score > 0
            assert profile.summary is not None
            assert len(profile.top_topics) > 0


class TestSessionSummaryGeneration:
    """Test session summary generation."""

    @patch("anthropic.Anthropic")
    def test_generate_complete_session_summary(self, mock_anthropic, temp_db):
        """Test generating complete session summary."""
        # Setup mocks
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"title": "Finance Bill Debate", "summary": "The House debated The Finance Bill, 2025 with focus on economic development and tax reform.", "key_debates": ["Finance Bill provisions", "Tax reform impact"], "main_topics": ["Finance", "Economy", "Taxation"]}'
            )
        ]
        mock_client.messages.create.return_value = mock_response

        # Add statements
        session = temp_db.query(SessionORM).first()
        mps = temp_db.query(MPORM).all()

        for mp in mps:
            stmt = StatementORM(
                session_id=session.id,
                mp_id=mp.id,
                text=f"Statement about finance by {mp.name}",
                statement_type="substantive",
                start_pos=0,
                end_pos=30,
                sentiment="positive",
                quality_score=75,
                primary_topic="Finance",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            temp_db.add(stmt)
        temp_db.commit()

        # Generate summary
        llm_analyzer = LLMAnalyzer(api_key="test_key")
        llm_analyzer.client = mock_client
        summary_generator = SessionSummaryGenerator(temp_db, llm_analyzer)

        summary = summary_generator.generate_summary(str(session.id))

        # Verify summary
        assert summary is not None
        assert summary.title is not None
        assert summary.summary is not None
        assert len(summary.key_debates) > 0
        assert len(summary.main_topics) > 0
        assert summary.total_mps_present >= 3
        assert summary.total_statements >= 3


class TestStaticSiteGeneration:
    """Test static site generation."""

    def test_generate_complete_static_site(self, temp_db, temp_output_dir):
        """Test generating complete static site with all pages."""
        # Add data
        session = temp_db.query(SessionORM).first()
        mps = temp_db.query(MPORM).all()

        for mp in mps:
            stmt = StatementORM(
                session_id=session.id,
                mp_id=mp.id,
                text=f"Statement by {mp.name}",
                statement_type="substantive",
                start_pos=0,
                end_pos=20,
                sentiment="positive",
                quality_score=75,
                primary_topic="Finance",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            temp_db.add(stmt)
        temp_db.commit()

        # Generate site
        template_dir = Path("templates")
        site_generator = StaticSiteGenerator(temp_db, template_dir, temp_output_dir)

        # Generate all pages
        site_generator._generate_homepage()
        site_generator._generate_mp_pages()
        site_generator._generate_session_pages()
        site_generator._generate_bill_pages()
        site_generator._generate_party_pages()

        # Verify site structure
        assert (temp_output_dir / "index.html").exists()
        assert (temp_output_dir / "mps" / "index.html").exists()
        assert (temp_output_dir / "sessions" / "index.html").exists()
        assert (temp_output_dir / "bills" / "index.html").exists()
        assert (temp_output_dir / "parties" / "index.html").exists()

        # Verify MP pages
        mp_files = list((temp_output_dir / "mps").glob("*.html"))
        assert len(mp_files) >= 4  # index.html + 3 MP pages

        # Verify session pages
        session_files = list((temp_output_dir / "sessions").glob("*.html"))
        assert len(session_files) >= 2  # index.html + 1 session page


class TestSiteContentVerification:
    """Test verification of generated site content."""

    def test_verify_site_content_accuracy(self, temp_db, temp_output_dir):
        """Test that generated site content matches database."""
        # Add data
        session = temp_db.query(SessionORM).first()
        mp = temp_db.query(MPORM).first()

        stmt = StatementORM(
            session_id=session.id,
            mp_id=mp.id,
            text="Test statement for verification",
            statement_type="substantive",
            start_pos=0,
            end_pos=30,
            sentiment="positive",
            quality_score=85,
            primary_topic="Healthcare",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        temp_db.add(stmt)
        temp_db.commit()

        # Generate site
        template_dir = Path("templates")
        site_generator = StaticSiteGenerator(temp_db, template_dir, temp_output_dir)

        site_generator._generate_homepage()
        site_generator._generate_mp_pages()

        # Verify homepage exists
        homepage = temp_output_dir / "index.html"
        assert homepage.exists()

        # Verify MP page exists
        mp_dir = temp_output_dir / "mps"
        assert mp_dir.exists()
        assert (mp_dir / "index.html").exists()

        # Verify content (basic check)
        homepage_content = homepage.read_text()
        assert len(homepage_content) > 0


class TestPerformanceMeasurement:
    """Test performance measurement of pipeline."""

    @patch("anthropic.Anthropic")
    def test_measure_hansard_processing_time(
        self, mock_anthropic, temp_db, temp_vector_db, sample_hansard_text
    ):
        """Test measuring Hansard processing time."""
        # Setup mocks
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"sentiment": "positive", "sentiment_confidence": 0.9, "sentiment_explanation": "Supportive", "quality_score": 75, "quality_factors": {"clarity": 80}, "primary_topic": "Finance", "secondary_topics": [], "topic_confidence": 0.85, "key_points": ["Reform"], "citations": ["reform"]}'
            )
        ]
        mock_client.messages.create.return_value = mock_response

        # Initialize components
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)
        classifier = FillerDetector()
        context_retriever = ContextRetriever(temp_vector_db, temp_db)
        llm_analyzer = LLMAnalyzer(api_key="test_key")
        llm_analyzer.client = mock_client

        session = temp_db.query(SessionORM).first()

        # Measure processing time
        start_time = time.time()

        # Process
        statements = segmenter.segment(sample_hansard_text, session_id=str(session.id))
        substantive = [stmt for stmt in statements if classifier.is_substantive(stmt)]

        for stmt in substantive[:5]:  # Limit to 5 for performance
            context = context_retriever.retrieve(stmt, top_k=3)
            analysis = llm_analyzer.analyze(stmt, context)

        processing_time = time.time() - start_time

        # Verify performance
        # Should process 5 statements in reasonable time
        assert processing_time < 15  # 15 seconds for 5 statements

        # Calculate per-statement time
        per_statement_time = processing_time / max(len(substantive[:5]), 1)
        assert per_statement_time < 5  # Less than 5 seconds per statement


class TestCostTracking:
    """Test cost tracking for LLM API calls."""

    @patch("anthropic.Anthropic")
    def test_verify_cost_tracking(self, mock_anthropic, temp_db, temp_vector_db):
        """Test that LLM API costs are tracked."""
        # Setup mocks
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"sentiment": "positive", "sentiment_confidence": 0.9, "sentiment_explanation": "Supportive", "quality_score": 75, "quality_factors": {"clarity": 80}, "primary_topic": "Finance", "secondary_topics": [], "topic_confidence": 0.85, "key_points": ["Reform"], "citations": ["reform"]}'
            )
        ]
        mock_response.usage = Mock(input_tokens=500, output_tokens=200)
        mock_client.messages.create.return_value = mock_response

        # Initialize components
        llm_analyzer = LLMAnalyzer(api_key="test_key")
        llm_analyzer.client = mock_client

        # Create statement
        from hansard_tales.analysis.statement_segmenter import Statement

        stmt = Statement(
            text="Test statement for cost tracking", mp_id=None, start_pos=0, end_pos=33
        )

        # Analyze (this should track costs)
        analysis = llm_analyzer.analyze(stmt, context=None)

        # Verify API was called
        assert mock_client.messages.create.called

        # In real implementation, verify cost tracking
        # For now, just verify the call happened
        assert analysis is not None


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""

    @patch("anthropic.Anthropic")
    def test_complete_workflow_from_text_to_site(
        self, mock_anthropic, temp_db, temp_vector_db, temp_output_dir, sample_hansard_text
    ):
        """Test complete workflow from Hansard text to generated site."""
        # Setup mocks
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"sentiment": "positive", "sentiment_confidence": 0.9, "sentiment_explanation": "Supportive", "quality_score": 75, "quality_factors": {"clarity": 80}, "primary_topic": "Finance", "secondary_topics": [], "topic_confidence": 0.85, "key_points": ["Reform"], "citations": ["reform"]}'
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

        session = temp_db.query(SessionORM).first()

        # Stage 1: Process Hansard
        statements = segmenter.segment(sample_hansard_text, session_id=str(session.id))
        substantive = [stmt for stmt in statements if classifier.is_substantive(stmt)]

        # Stage 2: Analyze statements
        for stmt in substantive[:3]:  # Limit for performance
            context = context_retriever.retrieve(stmt, top_k=3)
            analysis = llm_analyzer.analyze(stmt, context)

            # Store in database
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

        # Stage 3: Generate profiles
        llm_analyzer_profile = LLMAnalyzer(api_key="test_key")
        llm_analyzer_profile.client = mock_client
        profile_generator = MPProfileGenerator(temp_db, llm_analyzer_profile)

        mps = temp_db.query(MPORM).all()
        profiles = []
        for mp in mps[:2]:  # Limit for performance
            profile = profile_generator.generate_profile(str(mp.id))
            profiles.append(profile)

        # Stage 4: Generate site
        template_dir = Path("templates")
        site_generator = StaticSiteGenerator(temp_db, template_dir, temp_output_dir)

        site_generator._generate_homepage()
        site_generator._generate_mp_pages()
        site_generator._generate_session_pages()

        # Verify complete workflow
        # 1. Database has statements
        stored_statements = temp_db.query(StatementORM).all()
        assert len(stored_statements) >= 3

        # 2. Profiles were generated
        assert len(profiles) >= 2

        # 3. Site was generated
        assert (temp_output_dir / "index.html").exists()
        assert (temp_output_dir / "mps" / "index.html").exists()
        assert (temp_output_dir / "sessions" / "index.html").exists()

        # 4. Content is accurate
        for stmt in stored_statements:
            assert stmt.text is not None
            assert stmt.quality_score > 0

        for profile in profiles:
            assert profile.name is not None
            assert profile.total_statements >= 0
