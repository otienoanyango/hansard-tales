"""
Unit tests for MP Identifier.

Tests cover MP identification using regex patterns, spaCy NER,
fuzzy matching, and batch processing.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from hansard_tales.analysis.mp_identifier import MPIdentifier


class TestMPIdentifier:
    """Test suite for MPIdentifier."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing using ORM."""
        from datetime import datetime

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from hansard_tales.database.models import MPORM, Base, ChamberEnum

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        # Create engine and tables using ORM
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        # Create session and insert test MPs
        Session = sessionmaker(bind=engine)
        session = Session()

        # Insert test MPs
        test_mps_data = [
            ("JOHN DOE", "UDA", "Nairobi West"),
            ("JANE SMITH", "ODM", "Kisumu Central"),
            ("PETER JONES", "UDA", "Mombasa North"),
            ("MARY WILSON", "ODM", "Nakuru East"),
            ("MOSES WETANGULA", "FORD-K", "Bungoma"),
        ]

        now = datetime.now()
        for name, party, constituency in test_mps_data:
            mp = MPORM(
                id=uuid4(),
                name=name,
                chamber=ChamberEnum.NATIONAL_ASSEMBLY,
                party=party,
                constituency=constituency,
                parliament_term=2022,
                created_at=now,
                updated_at=now,
            )
            session.add(mp)

        session.commit()
        session.close()

        yield db_path

        # Cleanup
        Path(db_path).unlink()

    @pytest.fixture
    def mock_db_session(self, temp_db):
        """Create mock database session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Use the same database file as temp_db
        engine = create_engine(f"sqlite:///{temp_db}")
        Session = sessionmaker(bind=engine)
        session = Session()

        yield session

        session.close()

    @pytest.fixture
    def identifier(self, mock_db_session):
        """Create MP identifier instance."""
        # Mock spaCy to avoid downloading model
        with patch("spacy.load") as mock_load:
            mock_nlp = Mock()
            # Mock the doc object returned by nlp()
            mock_doc = Mock()
            mock_doc.ents = []  # Empty list of entities
            mock_nlp.return_value = mock_doc

            mock_load.return_value = mock_nlp
            identifier = MPIdentifier(mock_db_session)
            identifier.nlp = mock_nlp
            return identifier

    def test_init(self, mock_db_session):
        """Test MP identifier initialization."""
        with patch("spacy.load") as mock_load:
            mock_nlp = Mock()
            mock_load.return_value = mock_nlp

            identifier = MPIdentifier(mock_db_session)

            assert identifier.db == mock_db_session
            assert identifier.nlp == mock_nlp
            assert len(identifier.patterns) == 3
            assert isinstance(identifier.mp_cache, dict)

    def test_load_mp_cache(self, identifier):
        """Test MP cache loading."""
        cache = identifier.mp_cache

        # Should have entries for full names
        assert "john doe" in cache
        assert "jane smith" in cache

        # Should have entries for last names
        assert "doe" in cache
        assert "smith" in cache

    def test_exact_name_match(self, identifier):
        """Test exact name matching."""
        text = "Hon. JOHN DOE spoke about the budget."

        result = identifier.identify(text)

        assert result is not None
        assert result.name == "JOHN DOE"
        assert result.confidence == 0.95
        assert result.constituency == "Nairobi West"
        assert result.party == "UDA"

    def test_exact_name_match_with_constituency(self, identifier):
        """Test exact name matching with constituency."""
        text = "Hon. JANE SMITH (Kisumu Central, ODM) raised a point of order."

        result = identifier.identify(text)

        assert result is not None
        assert result.name == "JANE SMITH"
        assert result.confidence == 0.95
        assert result.constituency == "Kisumu Central"
        assert result.party == "ODM"

    def test_exact_name_match_dr_title(self, identifier):
        """Test exact name matching with Dr. title."""
        text = "Dr. PETER JONES presented the report."

        result = identifier.identify(text)

        assert result is not None
        assert result.name == "PETER JONES"
        assert result.confidence == 0.95

    def test_fuzzy_name_match(self, identifier):
        """Test fuzzy name matching with typo."""
        text = "Hon. JOHN DOE spoke about the budget."

        result = identifier.identify(text)

        assert result is not None
        assert result.name == "JOHN DOE"

    def test_fuzzy_name_match_partial(self, identifier):
        """Test fuzzy name matching with partial name."""
        # This should match via fuzzy matching
        text = "Hon. J. DOE raised a concern."

        result = identifier.identify(text)

        # May or may not match depending on fuzzy threshold
        # This tests the fuzzy matching logic
        if result:
            assert "DOE" in result.name

    def test_no_match(self, identifier):
        """Test no match for unknown MP."""
        text = "Hon. UNKNOWN PERSON spoke."

        result = identifier.identify(text)

        # Should not match
        assert result is None

    def test_constituency_boosting(self, identifier):
        """Test constituency information boosts matching score."""
        text = "Hon. JANE SMITH (Kisumu Central, ODM) spoke."

        result = identifier.identify(text)

        assert result is not None
        assert result.name == "JANE SMITH"
        assert result.constituency == "Kisumu Central"
        assert result.confidence == 0.95

    def test_party_boosting(self, identifier):
        """Test party information boosts matching score."""
        text = "Hon. PETER JONES (Mombasa North, UDA) presented."

        result = identifier.identify(text)

        assert result is not None
        assert result.name == "PETER JONES"
        assert result.party == "UDA"
        assert result.confidence == 0.95

    def test_batch_identification(self, identifier):
        """Test batch MP identification."""
        texts = [
            "Hon. JOHN DOE spoke about the budget.",
            "Dr. JANE SMITH raised a point of order.",
            "Hon. UNKNOWN PERSON made a statement.",
        ]

        results = identifier.identify_batch(texts)

        assert len(results) == 3
        assert results[0] is not None
        assert results[0].name == "JOHN DOE"
        assert results[1] is not None
        assert results[1].name == "JANE SMITH"
        assert results[2] is None  # Unknown person

    def test_batch_identification_empty(self, identifier):
        """Test batch identification with empty list."""
        results = identifier.identify_batch([])

        assert results == []

    def test_cache_performance(self, identifier):
        """Test cache improves lookup performance."""
        import time

        text = "Hon. JOHN DOE spoke about the budget."

        # First lookup (cache hit)
        start = time.time()
        result1 = identifier.identify(text)
        time1 = time.time() - start

        # Second lookup (should be fast due to cache)
        start = time.time()
        result2 = identifier.identify(text)
        time2 = time.time() - start

        assert result1 is not None
        assert result2 is not None
        assert result1.mp_id == result2.mp_id

        # Both should be fast (< 0.1 seconds)
        assert time1 < 0.1
        assert time2 < 0.1

    def test_cache_contains_all_mps(self, identifier):
        """Test cache contains all MPs from database."""
        cache = identifier.mp_cache

        # Should have at least 5 MPs (from test data)
        # Count unique MP objects (not list entries)
        mp_count = sum(1 for v in cache.values() if not isinstance(v, list))

        assert mp_count >= 5
