"""
Unit tests for MP profile generator.

Tests the MPProfileGenerator class including:
- Statistics aggregation
- Topic aggregation
- Bill aggregation
- Summary generation
- Batch processing
"""

import sqlite3
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from hansard_tales.analysis.mp_profile_generator import MPProfile, MPProfileGenerator


@pytest.fixture
def temp_db():
    """Create temporary database with test data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute(
        """
        CREATE TABLE mps (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            chamber TEXT NOT NULL,
            party TEXT,
            constituency TEXT,
            parliament_term INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE statements (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            mp_id TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp TEXT,
            source_url TEXT NOT NULL,
            source_hash TEXT NOT NULL,
            page_number INTEGER,
            line_number INTEGER,
            vector_doc_id TEXT NOT NULL,
            classification TEXT,
            sentiment TEXT,
            quality_score REAL,
            topics TEXT,
            related_bill_ids TEXT,
            related_question_ids TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (mp_id) REFERENCES mps(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE mp_votes (
            id TEXT PRIMARY KEY,
            vote_id TEXT NOT NULL,
            mp_id TEXT NOT NULL,
            direction TEXT NOT NULL,
            FOREIGN KEY (mp_id) REFERENCES mps(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE bills (
            id TEXT PRIMARY KEY,
            bill_number TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            chamber TEXT NOT NULL,
            status TEXT NOT NULL,
            current_version INTEGER DEFAULT 1,
            sponsor_id TEXT NOT NULL,
            co_sponsor_ids TEXT,
            related_statement_ids TEXT,
            related_vote_ids TEXT,
            related_question_ids TEXT,
            related_petition_ids TEXT,
            topics TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (sponsor_id) REFERENCES mps(id)
        )
    """
    )

    conn.commit()
    conn.close()

    yield db_path

    Path(db_path).unlink()


@pytest.fixture
def db_session(temp_db):
    """Create SQLAlchemy session for testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(f"sqlite:///{temp_db}")
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def sample_mp_data(temp_db):
    """Insert sample MP data."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    mp_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    cursor.execute(
        """
        INSERT INTO mps (id, name, chamber, party, constituency, parliament_term, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (mp_id, "Hon. John Doe", "NATIONAL_ASSEMBLY", "UDA", "Nairobi West", 13, now, now),
    )

    # Add statements
    for i in range(10):
        stmt_id = str(uuid4())
        doc_id = str(uuid4())
        classification = "substantive" if i < 7 else "filler"
        sentiment = "positive" if i % 2 == 0 else "negative"
        quality_score = 75.0 if classification == "substantive" else 20.0
        topics = '["Healthcare", "Education"]' if i < 5 else '["Finance"]'

        cursor.execute(
            """
            INSERT INTO statements (
                id, document_id, mp_id, text, source_url, source_hash,
                vector_doc_id, classification, sentiment, quality_score,
                topics, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                stmt_id,
                doc_id,
                mp_id,
                f"Statement {i}",
                "http://example.com",
                "hash123",
                f"vec_{i}",
                classification,
                sentiment,
                quality_score,
                topics,
                now,
            ),
        )

    # Add votes
    for i in range(5):
        vote_id = str(uuid4())
        mp_vote_id = str(uuid4())
        direction = "aye" if i < 3 else "no"

        cursor.execute(
            """
            INSERT INTO mp_votes (id, vote_id, mp_id, direction)
            VALUES (?, ?, ?, ?)
        """,
            (mp_vote_id, vote_id, mp_id, direction),
        )

    # Add bills
    bill_id = str(uuid4())
    cursor.execute(
        """
        INSERT INTO bills (
            id, bill_number, title, chamber, status, sponsor_id,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            bill_id,
            "Bill-001",
            "Healthcare Bill 2024",
            "NATIONAL_ASSEMBLY",
            "active",
            mp_id,
            now,
            now,
        ),
    )

    conn.commit()
    conn.close()

    return mp_id


class TestMPProfile:
    """Test MPProfile dataclass."""

    def test_create_profile(self):
        """Test creating MP profile."""
        profile = MPProfile(
            mp_id="123",
            name="Hon. John Doe",
            constituency="Nairobi West",
            party="UDA",
            total_statements=100,
            substantive_statements=80,
            avg_quality_score=75.5,
        )

        assert profile.mp_id == "123"
        assert profile.name == "Hon. John Doe"
        assert profile.total_statements == 100
        assert profile.substantive_statements == 80

    def test_participation_rate(self):
        """Test participation rate calculation."""
        profile = MPProfile(
            mp_id="123",
            name="Test MP",
            constituency="Test",
            party="Test",
            total_statements=100,
            substantive_statements=80,
        )

        assert profile.participation_rate == 80.0

    def test_participation_rate_zero_statements(self):
        """Test participation rate with zero statements."""
        profile = MPProfile(
            mp_id="123", name="Test MP", constituency="Test", party="Test", total_statements=0
        )

        assert profile.participation_rate == 0.0

    def test_voting_alignment(self):
        """Test voting alignment calculation."""
        profile = MPProfile(
            mp_id="123",
            name="Test MP",
            constituency="Test",
            party="Test",
            votes_cast=10,
            votes_aye=6,
            votes_no=3,
            votes_abstain=1,
        )

        alignment = profile.voting_alignment
        assert alignment["aye"] == 60.0
        assert alignment["no"] == 30.0
        assert alignment["abstain"] == 10.0

    def test_voting_alignment_zero_votes(self):
        """Test voting alignment with zero votes."""
        profile = MPProfile(
            mp_id="123", name="Test MP", constituency="Test", party="Test", votes_cast=0
        )

        alignment = profile.voting_alignment
        assert alignment["aye"] == 0.0
        assert alignment["no"] == 0.0
        assert alignment["abstain"] == 0.0

    def test_post_init_validation(self):
        """Test post-init validation."""
        # Test negative quality score
        profile = MPProfile(
            mp_id="123",
            name="Test MP",
            constituency="Test",
            party="Test",
            avg_quality_score=-10.0,
        )
        assert profile.avg_quality_score == 0.0

        # Test quality score > 100
        profile = MPProfile(
            mp_id="123",
            name="Test MP",
            constituency="Test",
            party="Test",
            avg_quality_score=150.0,
        )
        assert profile.avg_quality_score == 100.0

        # Test substantive > total
        profile = MPProfile(
            mp_id="123",
            name="Test MP",
            constituency="Test",
            party="Test",
            total_statements=50,
            substantive_statements=100,
        )
        assert profile.substantive_statements == 50

    def test_to_dict(self):
        """Test converting profile to dictionary."""
        profile = MPProfile(
            mp_id="123",
            name="Test MP",
            constituency="Test",
            party="Test",
            total_statements=100,
            substantive_statements=80,
        )

        data = profile.to_dict()
        assert data["mp_id"] == "123"
        assert data["name"] == "Test MP"
        assert data["total_statements"] == 100
        assert "participation_rate" in data
        assert "voting_alignment" in data


class TestMPProfileGenerator:
    """Test MPProfileGenerator class."""

    def test_init(self, db_session):
        """Test generator initialization."""
        generator = MPProfileGenerator(db_session)
        assert generator.db == db_session
        assert generator.llm is None

    def test_init_with_llm(self, db_session):
        """Test generator initialization with LLM."""
        mock_llm = Mock()
        generator = MPProfileGenerator(db_session, llm_analyzer=mock_llm)
        assert generator.llm == mock_llm

    def test_aggregate_statistics(self, db_session, sample_mp_data):
        """Test statistics aggregation."""
        from unittest.mock import MagicMock

        generator = MPProfileGenerator(db_session)

        # Mock the database queries
        db_session.query = MagicMock()

        # Mock statement count
        count_mock = MagicMock()
        count_mock.scalar.return_value = 10
        db_session.query.return_value.filter.return_value = count_mock

        # Mock substantive count
        substantive_mock = MagicMock()
        substantive_mock.scalar.return_value = 7

        # Mock avg quality
        avg_mock = MagicMock()
        avg_mock.scalar.return_value = 75.0

        # Mock votes
        vote_mock1 = MagicMock()
        vote_mock1.direction = "aye"
        vote_mock2 = MagicMock()
        vote_mock2.direction = "no"
        db_session.query.return_value.filter.return_value.all.return_value = [
            vote_mock1,
            vote_mock2,
        ]

        # Mock topics
        db_session.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (["Healthcare"], 5)
        ]

        # Mock bills
        db_session.query.return_value.filter.return_value.all.return_value = [("Healthcare Bill",)]

        # Mock sentiment
        db_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("positive", 5)
        ]

        # Mock sessions
        db_session.query.return_value.filter.return_value.scalar.return_value = 3

        stats = generator._aggregate_statistics(sample_mp_data)

        assert "total_statements" in stats
        assert "substantive_statements" in stats
        assert "avg_quality_score" in stats
        assert "votes_cast" in stats

    def test_aggregate_statistics_no_data(self, db_session):
        """Test statistics aggregation with no data."""
        generator = MPProfileGenerator(db_session)
        fake_mp_id = str(uuid4())
        stats = generator._aggregate_statistics(fake_mp_id)

        assert stats["total_statements"] == 0
        assert stats["substantive_statements"] == 0
        assert stats["avg_quality_score"] == 0.0
        assert stats["votes_cast"] == 0

    def test_aggregate_topics(self, db_session, sample_mp_data):
        """Test topic aggregation."""
        generator = MPProfileGenerator(db_session)
        topics = generator._aggregate_topics(sample_mp_data, limit=5)

        assert len(topics) > 0
        assert all(isinstance(t, tuple) and len(t) == 2 for t in topics)
        assert all(isinstance(t[0], str) and isinstance(t[1], int) for t in topics)

    def test_aggregate_bills(self, db_session, sample_mp_data):
        """Test bill aggregation."""
        generator = MPProfileGenerator(db_session)
        bills = generator._aggregate_bills(sample_mp_data)

        assert "sponsored" in bills
        assert "discussed" in bills
        assert isinstance(bills["sponsored"], list)
        assert isinstance(bills["discussed"], list)

    def test_generate_basic_summary(self, db_session, sample_mp_data):
        """Test basic summary generation without LLM."""
        from hansard_tales.database.models import MPORM

        generator = MPProfileGenerator(db_session)
        mp = db_session.query(MPORM).filter(MPORM.id == sample_mp_data).first()
        stats = generator._aggregate_statistics(sample_mp_data)

        summary = generator._generate_basic_summary(mp, stats)

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert mp.name in summary

    def test_extract_key_positions(self, db_session, sample_mp_data):
        """Test key position extraction."""
        generator = MPProfileGenerator(db_session)
        positions = generator._extract_key_positions(sample_mp_data, limit=3)

        assert isinstance(positions, list)
        assert len(positions) <= 3

    def test_generate_profile(self, db_session, sample_mp_data):
        """Test complete profile generation."""
        generator = MPProfileGenerator(db_session)
        profile = generator.generate_profile(sample_mp_data)

        assert isinstance(profile, MPProfile)
        assert profile.mp_id == sample_mp_data
        assert profile.name == "Hon. John Doe"
        assert profile.constituency == "Nairobi West"
        assert profile.party == "UDA"
        assert profile.total_statements == 10
        assert profile.substantive_statements == 7

    def test_generate_profile_not_found(self, db_session):
        """Test profile generation for non-existent MP."""
        generator = MPProfileGenerator(db_session)
        fake_mp_id = str(uuid4())

        with pytest.raises(ValueError, match="MP not found"):
            generator.generate_profile(fake_mp_id)

    def test_generate_profiles_batch(self, db_session, sample_mp_data):
        """Test batch profile generation."""
        generator = MPProfileGenerator(db_session)
        profiles = generator.generate_profiles_batch(mp_ids=[sample_mp_data])

        assert len(profiles) == 1
        assert profiles[0].mp_id == sample_mp_data

    def test_generate_profiles_batch_all(self, db_session, sample_mp_data):
        """Test batch profile generation for all MPs."""
        generator = MPProfileGenerator(db_session)
        profiles = generator.generate_profiles_batch()

        assert len(profiles) >= 1

    def test_generate_profiles_by_party(self, db_session, sample_mp_data):
        """Test profile generation by party."""
        generator = MPProfileGenerator(db_session)
        profiles = generator.generate_profiles_by_party("UDA")

        assert len(profiles) >= 1
        assert all(p.party == "UDA" for p in profiles)

    def test_generate_profiles_by_constituency(self, db_session, sample_mp_data):
        """Test profile generation by constituency."""
        generator = MPProfileGenerator(db_session)
        profiles = generator.generate_profiles_by_constituency("Nairobi West")

        assert len(profiles) >= 1
        assert all(p.constituency == "Nairobi West" for p in profiles)
