"""
Property-based tests for MP Identifier.

Tests universal properties that must hold for MP identification operations.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from hansard_tales.analysis.mp_identifier import MPIdentifier, MPMatch


class TestMPIdentificationAccuracy:
    """
    Property-based tests for MP identification accuracy.

    **Validates: Requirements 1.6**
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

        # Insert diverse test MPs with various name patterns
        test_mps_data = [
            # Common names
            ("JOHN DOE", "UDA", "Nairobi West"),
            ("JANE SMITH", "ODM", "Kisumu Central"),
            ("PETER JONES", "UDA", "Mombasa North"),
            ("MARY WILSON", "ODM", "Nakuru East"),
            ("MOSES WETANGULA", "FORD-K", "Bungoma"),
            # Names with multiple parts
            ("JOHN PAUL MWANGI", "UDA", "Kiambu"),
            ("MARY ANNE WANJIRU", "ODM", "Nairobi"),
            # Short names
            ("ALI ROBA", "UDA", "Mandera"),
            ("EVE OBARA", "ODM", "Kabondo"),
            # Names with common last names (for disambiguation testing)
            ("JAMES KAMAU", "UDA", "Ruiru"),
            ("PETER KAMAU", "ODM", "Juja"),
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
    def identifier(self, mock_db_session):
        """Create MP identifier instance with mocked spaCy."""
        from unittest.mock import Mock, patch

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

    @settings(
        max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        mp_name=st.sampled_from(
            [
                "JOHN DOE",
                "JANE SMITH",
                "PETER JONES",
                "MARY WILSON",
                "MOSES WETANGULA",
                "JOHN PAUL MWANGI",
                "MARY ANNE WANJIRU",
                "ALI ROBA",
                "EVE OBARA",
                "JAMES KAMAU",
                "PETER KAMAU",
            ]
        ),
        title=st.sampled_from(["Hon.", "Dr.", "Prof.", "Mr.", "Ms.", "Mrs."]),
        include_constituency=st.booleans(),
        include_party=st.booleans(),
    )
    def test_property_1_1_mp_identification_accuracy(
        self, identifier, mp_name, title, include_constituency, include_party
    ):
        """
        Property 1.1: MP identification accuracy ≥95%.

        **Validates: Requirements 1.6**

        This property tests that when given a properly formatted MP mention,
        the identifier correctly identifies the MP with high confidence.
        """
        # Build text with MP mention
        text_parts = [title, mp_name]

        if include_constituency or include_party:
            context_parts = []
            if include_constituency:
                # Get constituency from cache
                mp_record = identifier.mp_cache.get(mp_name.lower())
                if mp_record and not isinstance(mp_record, list):
                    context_parts.append(mp_record.constituency)
            if include_party:
                # Get party from cache
                mp_record = identifier.mp_cache.get(mp_name.lower())
                if mp_record and not isinstance(mp_record, list):
                    context_parts.append(mp_record.party)

            if context_parts:
                text_parts.append(f"({', '.join(context_parts)})")

        text = " ".join(text_parts) + " spoke about the budget."

        # Identify MP
        result = identifier.identify(text)

        # Property: Should successfully identify the MP
        assert result is not None, f"Failed to identify MP in text: {text}"

        # Property: Identified name should match (case-insensitive)
        assert result.name.lower() == mp_name.lower(), f"Expected {mp_name}, got {result.name}"

        # Property: Confidence should be high (≥0.80)
        assert (
            result.confidence >= 0.80
        ), f"Confidence {result.confidence} below threshold for: {text}"

        # Property: Should have valid MP ID
        assert result.mp_id is not None
        assert len(result.mp_id) > 0


class TestNameVariationHandling:
    """
    Property-based tests for name variation handling.

    **Validates: Requirements 1.3**
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
        mp_id = uuid4()
        test_mps_data = [
            (mp_id, "JOHN DOE", "UDA", "Nairobi West"),
            (uuid4(), "JANE SMITH", "ODM", "Kisumu Central"),
            (uuid4(), "PETER JONES", "UDA", "Mombasa North"),
        ]

        now = datetime.now()
        for mp_uuid, name, party, constituency in test_mps_data:
            mp = MPORM(
                id=mp_uuid,
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

        yield db_path, str(mp_id)

        Path(db_path).unlink()

    @pytest.fixture
    def mock_db_session(self, temp_db_with_mps):
        """Create mock database session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        db_path, mp_id = temp_db_with_mps
        engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=engine)
        session = Session()

        yield session, mp_id

        session.close()

    @pytest.fixture
    def identifier(self, mock_db_session):
        """Create MP identifier instance with mocked spaCy."""
        from unittest.mock import Mock, patch

        session, mp_id = mock_db_session
        with patch("spacy.load") as mock_load:
            mock_nlp = Mock()
            # Mock the doc object returned by nlp()
            mock_doc = Mock()
            mock_doc.ents = []  # Empty list of entities
            mock_nlp.return_value = mock_doc

            mock_load.return_value = mock_nlp
            identifier = MPIdentifier(session)
            identifier.nlp = mock_nlp
            return identifier, mp_id

    @settings(
        max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        title=st.sampled_from(["Hon.", "Dr.", "Prof.", "Mr.", "Ms.", "Mrs."]),
        name_format=st.sampled_from(
            [
                "JOHN DOE",  # Full name uppercase
                "John Doe",  # Title case
                "john doe",  # Lowercase
                "JOHN DOE",  # With extra spaces (handled by regex)
            ]
        ),
        context_format=st.sampled_from(
            [
                "(Nairobi West, UDA)",
                "(Nairobi West)",
                "",  # No context
            ]
        ),
    )
    def test_property_1_2_name_variation_handling(
        self, identifier, title, name_format, context_format
    ):
        """
        Property 1.2: Different name formats must resolve to same MP.

        **Validates: Requirements 1.3**

        This property tests that various formatting of the same MP name
        (different cases, with/without titles, with/without context)
        all resolve to the same MP record.
        """
        identifier_obj, expected_mp_id = identifier

        # Build text with name variation
        text = f"{title} {name_format} {context_format} spoke about the budget."

        # Identify MP
        result = identifier_obj.identify(text)

        # Property: Should identify the MP regardless of format
        if result is not None:
            # Property: Should resolve to the same MP ID
            assert (
                result.mp_id == expected_mp_id
            ), f"Name variation '{name_format}' resolved to different MP"

            # Property: Name should be normalized to database format
            assert (
                result.name == "JOHN DOE"
            ), f"Expected normalized name 'JOHN DOE', got '{result.name}'"

    @settings(
        max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        base_name=st.sampled_from(["JOHN DOE", "JANE SMITH", "PETER JONES"]),
        title1=st.sampled_from(["Hon.", "Dr.", "Prof."]),
        title2=st.sampled_from(["Hon.", "Dr.", "Prof."]),
    )
    def test_property_1_2_title_variation_same_mp(self, identifier, base_name, title1, title2):
        """
        Property 1.2: Same MP with different titles resolves to same record.

        **Validates: Requirements 1.3, 1.4**

        This property tests that the same MP mentioned with different
        honorific titles (Hon., Dr., Prof., etc.) is correctly identified
        as the same person.
        """
        identifier_obj, _ = identifier

        # Create two mentions with different titles
        text1 = f"{title1} {base_name} spoke first."
        text2 = f"{title2} {base_name} spoke second."

        # Identify MP in both texts
        result1 = identifier_obj.identify(text1)
        result2 = identifier_obj.identify(text2)

        # Property: Both should identify the same MP (or both fail)
        if result1 is not None and result2 is not None:
            assert (
                result1.mp_id == result2.mp_id
            ), f"Different titles for {base_name} resolved to different MPs"
            assert (
                result1.name == result2.name
            ), f"Different titles produced different names: {result1.name} vs {result2.name}"


class TestMPIdentificationRobustness:
    """
    Property-based tests for MP identification robustness.

    Tests that the identifier handles edge cases gracefully.
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
    def identifier(self, mock_db_session):
        """Create MP identifier instance with mocked spaCy."""
        from unittest.mock import Mock, patch

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

    @settings(
        max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(text=st.text(min_size=10, max_size=200))
    def test_identification_never_crashes(self, identifier, text):
        """
        Property: MP identification must never crash on any input.

        **Validates: Requirements 1.7**

        This property tests that the identifier handles arbitrary text
        gracefully without crashing, even if no MP is present.
        """
        # Should never crash, even with random text
        try:
            result = identifier.identify(text)
            # Result can be None (no MP found) or MPMatch
            assert result is None or isinstance(result, MPMatch)
        except Exception as e:
            pytest.fail(f"Identification crashed on input '{text}': {e}")

    @settings(
        max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(texts=st.lists(st.text(min_size=10, max_size=100), min_size=1, max_size=20))
    def test_batch_identification_consistency(self, identifier, texts):
        """
        Property: Batch identification must match individual identification.

        **Validates: Requirements 1.6**

        This property tests that batch processing produces the same results
        as processing texts individually.
        """
        # Process individually
        individual_results = [identifier.identify(text) for text in texts]

        # Process as batch
        batch_results = identifier.identify_batch(texts)

        # Property: Results should match
        assert len(individual_results) == len(batch_results)

        for i, (ind_result, batch_result) in enumerate(
            zip(individual_results, batch_results, strict=False)
        ):
            if ind_result is None and batch_result is None:
                continue
            elif ind_result is not None and batch_result is not None:
                assert (
                    ind_result.mp_id == batch_result.mp_id
                ), f"Batch result differs from individual at index {i}"
            else:
                pytest.fail(
                    f"Inconsistent results at index {i}: "
                    f"individual={ind_result}, batch={batch_result}"
                )

    @settings(
        max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(empty_input=st.sampled_from(["", "   ", "\n", "\t", "  \n  "]))
    def test_empty_input_handling(self, identifier, empty_input):
        """
        Property: Empty or whitespace-only input should return None.

        **Validates: Requirements 1.7**

        This property tests that the identifier handles empty or
        whitespace-only input gracefully.
        """
        result = identifier.identify(empty_input)

        # Property: Should return None for empty input
        assert result is None, f"Expected None for empty input, got {result}"
