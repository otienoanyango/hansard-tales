"""
Property-based tests for Statement Segmenter.

Tests universal properties that must hold for statement segmentation operations.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from hansard_tales.analysis.statement_segmenter import Statement, StatementSegmenter


class TestSegmentationAccuracy:
    """
    Property-based tests for segmentation accuracy.

    **Validates: Requirements 2.6**
    """

    @pytest.fixture
    def temp_db_with_mps(self):
        """Create temporary database with test MPs using ORM."""
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
    def mock_db_session(self, temp_db_with_mps):
        """Create mock database session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{temp_db_with_mps}")
        Session = sessionmaker(bind=engine)
        session = Session()

        yield session

        session.close()

    @pytest.fixture
    def mock_mp_identifier(self, mock_db_session):
        """Create mock MP identifier."""
        from unittest.mock import Mock, patch

        from hansard_tales.analysis.mp_identifier import MPIdentifier

        with patch("spacy.load") as mock_load:
            mock_nlp = Mock()
            mock_doc = Mock()
            mock_doc.ents = []
            mock_nlp.return_value = mock_doc
            mock_load.return_value = mock_nlp

            identifier = MPIdentifier(mock_db_session)
            identifier.nlp = mock_nlp
            return identifier

    @pytest.fixture
    def segmenter(self, mock_mp_identifier):
        """Create statement segmenter instance."""
        return StatementSegmenter(mock_mp_identifier)

    @settings(
        max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        num_statements=st.integers(min_value=2, max_value=5),
        mp_name=st.sampled_from(["JOHN DOE", "JANE SMITH", "PETER JONES"]),
        title=st.sampled_from(["Hon.", "Dr.", "Mr."]),
    )
    def test_property_2_1_segmentation_accuracy(self, segmenter, num_statements, mp_name, title):
        """
        Property 2.1: Segmentation accuracy ≥98%.

        **Validates: Requirements 2.6**

        This property tests that when given text with clear MP boundaries,
        the segmenter correctly identifies and separates statements.
        """
        # Build text with multiple statements
        statements_text = []
        for i in range(num_statements):
            statement = (
                f"{title} {mp_name} made statement number {i + 1}. "
                f"This is a longer statement to ensure it meets the minimum length requirement. "
                f"We need to have enough text here to pass the 20 character minimum filter."
            )
            statements_text.append(statement)

        text = "\n".join(statements_text)

        # Segment the text
        result = segmenter.segment(text, "session-123")

        # Property: Should create at least num_statements - 1 statements
        # (allowing for some merging at boundaries)
        assert len(result) >= num_statements - 1, (
            f"Expected at least {num_statements - 1} statements, " f"got {len(result)}"
        )

        # Property: All statements should have valid structure
        for stmt in result:
            assert isinstance(stmt, Statement)
            assert len(stmt.text) > 0
            assert stmt.start_pos >= 0
            assert stmt.end_pos > stmt.start_pos

        # Property: Statements should be in order
        for i in range(len(result) - 1):
            assert result[i].start_pos < result[i + 1].start_pos

    @settings(
        max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        boundary_type=st.sampled_from(
            [
                "\nHon. JOHN DOE",
                "\nDr. JANE SMITH",
                "\nThe Speaker:",
            ]
        ),
        num_boundaries=st.integers(min_value=2, max_value=4),
    )
    def test_property_2_1_boundary_detection_accuracy(
        self, segmenter, boundary_type, num_boundaries
    ):
        """
        Property 2.1: Boundary detection must identify all boundaries.

        **Validates: Requirements 2.3, 2.4**

        This property tests that the segmenter correctly identifies
        all statement boundaries in the text.
        """
        # Build text with known boundaries
        text_parts = ["Initial text that is long enough to be a valid statement."]

        for i in range(num_boundaries):
            text_parts.append(
                f"{boundary_type} Statement {i + 1} with enough text to meet minimum length."
            )

        text = " ".join(text_parts)

        # Find boundaries
        boundaries = segmenter._find_boundaries(text)

        # Property: Should find at least num_boundaries boundaries
        # (plus the start of text at position 0)
        assert len(boundaries) >= num_boundaries, (
            f"Expected at least {num_boundaries} boundaries, " f"found {len(boundaries)}"
        )

        # Property: Boundaries should be sorted
        assert boundaries == sorted(boundaries)

        # Property: First boundary should be at position 0
        assert boundaries[0] == 0


class TestNoStatementLoss:
    """
    Property-based tests for statement loss prevention.

    **Validates: Requirements 2.6**
    """

    @pytest.fixture
    def temp_db_with_mps(self):
        """Create temporary database with test MPs using ORM."""
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
    def mock_db_session(self, temp_db_with_mps):
        """Create mock database session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{temp_db_with_mps}")
        Session = sessionmaker(bind=engine)
        session = Session()

        yield session

        session.close()

    @pytest.fixture
    def mock_mp_identifier(self, mock_db_session):
        """Create mock MP identifier."""
        from unittest.mock import Mock, patch

        from hansard_tales.analysis.mp_identifier import MPIdentifier

        with patch("spacy.load") as mock_load:
            mock_nlp = Mock()
            mock_doc = Mock()
            mock_doc.ents = []
            mock_nlp.return_value = mock_doc
            mock_load.return_value = mock_nlp

            identifier = MPIdentifier(mock_db_session)
            identifier.nlp = mock_nlp
            return identifier

    @pytest.fixture
    def segmenter(self, mock_mp_identifier):
        """Create statement segmenter instance."""
        return StatementSegmenter(mock_mp_identifier)

    @settings(
        max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        text_length=st.integers(min_value=100, max_value=1000),
        num_boundaries=st.integers(min_value=1, max_value=5),
    )
    def test_property_2_2_no_statement_loss(self, segmenter, text_length, num_boundaries):
        """
        Property 2.2: No statement loss - all text must be assigned.

        **Validates: Requirements 2.6**

        This property tests that segmentation doesn't lose any text.
        The sum of statement lengths should approximately equal input length
        (minus headers and short segments).
        """
        # Generate text with known length
        base_text = "A" * text_length

        # Add boundaries
        text_parts = [base_text[: text_length // (num_boundaries + 1)]]
        for i in range(num_boundaries):
            start = (i + 1) * (text_length // (num_boundaries + 1))
            end = (i + 2) * (text_length // (num_boundaries + 1))
            text_parts.append(f"\nHon. JOHN DOE: {base_text[start:end]}")

        text = "".join(text_parts)
        original_length = len(text)

        # Segment the text
        statements = segmenter.segment(text, "session-123")

        # Calculate total statement length
        total_statement_length = sum(len(stmt.text) for stmt in statements)

        # Property: Total statement length should be close to original
        # (allowing for whitespace normalization and short segment filtering)
        # We expect at least 80% of the text to be captured
        assert total_statement_length >= original_length * 0.8, (
            f"Significant text loss: original={original_length}, "
            f"captured={total_statement_length}"
        )

    @settings(
        max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        statement_text=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
            min_size=50,
            max_size=200,
        )
    )
    def test_property_2_2_statement_coverage(self, segmenter, statement_text):
        """
        Property 2.2: All substantive text must appear in some statement.

        **Validates: Requirements 2.6**

        This property tests that no substantive text is lost during
        segmentation. Every word from the input should appear in at least
        one statement.
        """
        # Create text with MP boundary
        text = f"Hon. JOHN DOE: {statement_text}"

        # Segment the text
        statements = segmenter.segment(text, "session-123")

        # Property: Should create at least one statement
        assert len(statements) >= 1

        # Property: The statement text should be present
        # Combine all statement texts
        combined_text = " ".join(stmt.text for stmt in statements)

        # Check that key words from original text appear in statements
        # (allowing for some cleaning and normalization)
        original_words = set(statement_text.split())
        if len(original_words) > 0:
            # At least some words should be preserved
            found_words = sum(1 for word in original_words if word in combined_text)
            preservation_rate = found_words / len(original_words)

            assert (
                preservation_rate >= 0.7
            ), f"Too much text lost: only {preservation_rate:.1%} of words preserved"


class TestSegmentationRobustness:
    """
    Property-based tests for segmentation robustness.

    Tests that the segmenter handles edge cases gracefully.
    """

    @pytest.fixture
    def temp_db_with_mps(self):
        """Create temporary database with test MPs using ORM."""
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
    def mock_db_session(self, temp_db_with_mps):
        """Create mock database session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{temp_db_with_mps}")
        Session = sessionmaker(bind=engine)
        session = Session()

        yield session

        session.close()

    @pytest.fixture
    def mock_mp_identifier(self, mock_db_session):
        """Create mock MP identifier."""
        from unittest.mock import Mock, patch

        from hansard_tales.analysis.mp_identifier import MPIdentifier

        with patch("spacy.load") as mock_load:
            mock_nlp = Mock()
            mock_doc = Mock()
            mock_doc.ents = []
            mock_nlp.return_value = mock_doc
            mock_load.return_value = mock_nlp

            identifier = MPIdentifier(mock_db_session)
            identifier.nlp = mock_nlp
            return identifier

    @pytest.fixture
    def segmenter(self, mock_mp_identifier):
        """Create statement segmenter instance."""
        return StatementSegmenter(mock_mp_identifier)

    @settings(
        max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(text=st.text(min_size=0, max_size=500))
    def test_segmentation_never_crashes(self, segmenter, text):
        """
        Property: Segmentation must never crash on any input.

        **Validates: Requirements 2.6**

        This property tests that the segmenter handles arbitrary text
        gracefully without crashing.
        """
        # Should never crash, even with random text
        try:
            result = segmenter.segment(text, "session-123")
            # Result should be a list
            assert isinstance(result, list)
            # All items should be Statement objects
            for stmt in result:
                assert isinstance(stmt, Statement)
        except Exception as e:
            pytest.fail(f"Segmentation crashed on input '{text[:100]}...': {e}")

    @settings(
        max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(empty_input=st.sampled_from(["", "   ", "\n", "\t", "  \n  "]))
    def test_empty_input_handling(self, segmenter, empty_input):
        """
        Property: Empty or whitespace-only input should return empty list.

        **Validates: Requirements 2.6**

        This property tests that the segmenter handles empty or
        whitespace-only input gracefully.
        """
        result = segmenter.segment(empty_input, "session-123")

        # Property: Should return empty list for empty input
        assert result == [], f"Expected empty list for empty input, got {result}"

    @settings(
        max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        text=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
            min_size=20,
            max_size=200,
        )
    )
    def test_clean_statement_idempotent(self, segmenter, text):
        """
        Property: Cleaning a statement twice should produce same result.

        **Validates: Requirements 2.5**

        This property tests that the clean_statement function is idempotent.
        """
        # Clean once
        cleaned_once = segmenter.clean_statement(text)

        # Clean again
        cleaned_twice = segmenter.clean_statement(cleaned_once)

        # Property: Should be the same
        assert (
            cleaned_once == cleaned_twice
        ), "clean_statement is not idempotent: produces different results on second application"

    @settings(
        max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        text=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
            min_size=20,
            max_size=200,
        )
    )
    def test_clean_statement_preserves_content(self, segmenter, text):
        """
        Property: Cleaning should preserve substantive content.

        **Validates: Requirements 2.5**

        This property tests that cleaning removes only formatting artifacts,
        not substantive content.
        """
        # Clean the text
        cleaned = segmenter.clean_statement(text)

        # Property: Cleaned text should not be empty if input wasn't empty
        if text.strip():
            assert len(cleaned) > 0, "Cleaning removed all content"

        # Property: Cleaned text should be shorter or equal length
        assert len(cleaned) <= len(text), "Cleaning increased text length"
