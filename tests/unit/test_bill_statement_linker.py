"""
Unit tests for Bill-Statement Linker.

Tests cover bill mention detection, pattern matching, bill resolution,
disambiguation, context extraction, and edge cases.
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import numpy as np
import pytest

from hansard_tales.analysis.bill_statement_linker import (
    BillMention,
    BillStatementLinker,
)
from hansard_tales.analysis.statement_segmenter import Statement
from hansard_tales.database.models import BillORM


class TestBillMention:
    """Test suite for BillMention dataclass."""

    def test_create_bill_mention(self):
        """Test creating a bill mention."""
        mention = BillMention(
            bill_id="bill-123",
            bill_title="Finance Bill, 2024",
            mention_text="The Finance Bill, 2024",
            confidence=0.95,
            context="...discussing the Finance Bill, 2024 provisions...",
        )

        assert mention.bill_id == "bill-123"
        assert mention.bill_title == "Finance Bill, 2024"
        assert mention.mention_text == "The Finance Bill, 2024"
        assert mention.confidence == 0.95
        assert "Finance Bill" in mention.context

    def test_bill_mention_validation_confidence(self):
        """Test bill mention confidence validation."""
        # Test invalid confidence (too high)
        with pytest.raises(ValueError, match="Confidence must be between"):
            BillMention(
                bill_id="bill-123",
                bill_title="Test Bill",
                mention_text="Test",
                confidence=1.5,
                context="Test context",
            )

        # Test invalid confidence (negative)
        with pytest.raises(ValueError, match="Confidence must be between"):
            BillMention(
                bill_id="bill-123",
                bill_title="Test Bill",
                mention_text="Test",
                confidence=-0.1,
                context="Test context",
            )

    def test_bill_mention_validation_empty_fields(self):
        """Test bill mention validation for empty fields."""
        # Test empty bill_id
        with pytest.raises(ValueError, match="bill_id cannot be empty"):
            BillMention(
                bill_id="",
                bill_title="Test Bill",
                mention_text="Test",
                confidence=0.9,
                context="Test context",
            )

        # Test empty mention_text
        with pytest.raises(ValueError, match="mention_text cannot be empty"):
            BillMention(
                bill_id="bill-123",
                bill_title="Test Bill",
                mention_text="",
                confidence=0.9,
                context="Test context",
            )


class TestBillStatementLinker:
    """Test suite for BillStatementLinker."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        mock_session = Mock()
        return mock_session

    @pytest.fixture
    def mock_vector_db(self):
        """Create mock vector database."""
        mock_db = Mock()
        return mock_db

    @pytest.fixture
    def linker(self, mock_db_session, mock_vector_db):
        """Create bill-statement linker instance."""
        return BillStatementLinker(db_session=mock_db_session, vector_db=mock_vector_db)

    @pytest.fixture
    def linker_no_vector_db(self, mock_db_session):
        """Create linker without vector DB."""
        return BillStatementLinker(db_session=mock_db_session, vector_db=None)

    @pytest.fixture
    def sample_statement(self):
        """Create sample statement for testing."""
        return Statement(
            text="We are discussing the Finance Bill, 2024 today.",
            mp_id="mp-123",
            start_pos=0,
            end_pos=100,
            page_number=1,
        )

    @pytest.fixture
    def sample_bill(self):
        """Create sample bill ORM object."""
        bill = Mock(spec=BillORM)
        bill.id = uuid4()
        bill.title = "Finance Bill, 2024"
        bill.bill_number = "Bill No. 15 of 2024"
        return bill

    def test_init(self, mock_db_session, mock_vector_db):
        """Test BillStatementLinker initialization."""
        linker = BillStatementLinker(db_session=mock_db_session, vector_db=mock_vector_db)

        assert linker.db == mock_db_session
        assert linker.vector_db == mock_vector_db
        assert len(linker.patterns) == 3  # Three regex patterns

    def test_init_without_vector_db(self, mock_db_session):
        """Test initialization without vector DB."""
        linker = BillStatementLinker(db_session=mock_db_session, vector_db=None)

        assert linker.db == mock_db_session
        assert linker.vector_db is None

    def test_pattern_matching_finance_bill(self, linker, sample_statement):
        """Test pattern matching for 'Finance Bill, 2024' format."""
        # Setup mock query
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        linker.db.query = Mock(return_value=mock_query)

        # Find mentions
        linker.find_bill_mentions(sample_statement)

        # Verify pattern was detected (even if not resolved)
        # The pattern should match "Finance Bill, 2024"
        linker.db.query.assert_called()

    def test_pattern_matching_bill_number(self, linker):
        """Test pattern matching for 'Bill No. X of YYYY' format."""
        statement = Statement(
            text="We are voting on Bill No. 15 of 2024.",
            mp_id="mp-123",
            start_pos=0,
            end_pos=100,
        )

        # Setup mock query
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        linker.db.query = Mock(return_value=mock_query)

        # Find mentions
        linker.find_bill_mentions(statement)

        # Verify query was called (pattern matched)
        linker.db.query.assert_called()

    def test_pattern_matching_the_bill(self, linker):
        """Test pattern matching for 'the Bill' contextual reference."""
        statement = Statement(
            text="I support the Bill and urge members to vote yes.",
            mp_id="mp-123",
            start_pos=0,
            end_pos=100,
        )

        # Setup mock query
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        linker.db.query = Mock(return_value=mock_query)

        # Find mentions
        linker.find_bill_mentions(statement)

        # Verify query was called (pattern matched)
        linker.db.query.assert_called()

    def test_bill_resolution_exact_match(self, linker, sample_statement, sample_bill):
        """Test bill resolution with exact match."""
        # Setup mock query to return one bill
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[sample_bill])
        linker.db.query = Mock(return_value=mock_query)

        # Find mentions
        mentions = linker.find_bill_mentions(sample_statement)

        # Verify
        assert len(mentions) == 1
        assert mentions[0].bill_id == str(sample_bill.id)
        assert mentions[0].bill_title == sample_bill.title
        assert mentions[0].confidence == 0.90

    def test_bill_resolution_no_match(self, linker, sample_statement):
        """Test bill resolution with no matching bills."""
        # Setup mock query to return no bills
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        linker.db.query = Mock(return_value=mock_query)

        # Find mentions
        mentions = linker.find_bill_mentions(sample_statement)

        # Verify no mentions found
        assert len(mentions) == 0

    def test_disambiguation_with_vector_db(self, linker, sample_statement, sample_bill):
        """Test disambiguation using vector similarity."""
        # Create two bills with similar titles
        bill1 = Mock(spec=BillORM)
        bill1.id = uuid4()
        bill1.title = "Finance Bill, 2024"

        bill2 = Mock(spec=BillORM)
        bill2.id = uuid4()
        bill2.title = "Finance Amendment Bill, 2024"

        # Setup mock query to return multiple bills
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[bill1, bill2])
        linker.db.query = Mock(return_value=mock_query)

        # Setup mock embedder
        mock_embedder = Mock()
        mock_embedder.encode = Mock(
            side_effect=[
                np.array([0.1, 0.2, 0.3]),  # Statement embedding
                np.array([0.1, 0.2, 0.3]),  # Bill1 embedding (high similarity)
                np.array([0.5, 0.6, 0.7]),  # Bill2 embedding (low similarity)
            ]
        )

        with patch(
            "sentence_transformers.SentenceTransformer",
            return_value=mock_embedder,
        ):
            # Find mentions
            mentions = linker.find_bill_mentions(sample_statement)

            # Verify bill1 was selected (higher similarity)
            assert len(mentions) == 1
            assert mentions[0].bill_id == str(bill1.id)

    def test_disambiguation_without_vector_db(self, linker_no_vector_db, sample_statement):
        """Test disambiguation without vector DB (fallback to first match)."""
        # Create two bills
        bill1 = Mock(spec=BillORM)
        bill1.id = uuid4()
        bill1.title = "Finance Bill, 2024"

        bill2 = Mock(spec=BillORM)
        bill2.id = uuid4()
        bill2.title = "Finance Amendment Bill, 2024"

        # Setup mock query to return multiple bills
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[bill1, bill2])
        linker_no_vector_db.db.query = Mock(return_value=mock_query)

        # Find mentions
        mentions = linker_no_vector_db.find_bill_mentions(sample_statement)

        # Verify first bill was selected (fallback)
        assert len(mentions) == 1
        assert mentions[0].bill_id == str(bill1.id)

    def test_disambiguation_low_similarity(self, linker, sample_statement):
        """Test disambiguation with low similarity scores (returns None)."""
        # Create two bills
        bill1 = Mock(spec=BillORM)
        bill1.id = uuid4()
        bill1.title = "Finance Bill, 2024"

        bill2 = Mock(spec=BillORM)
        bill2.id = uuid4()
        bill2.title = "Finance Amendment Bill, 2024"

        # Setup mock query
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[bill1, bill2])
        linker.db.query = Mock(return_value=mock_query)

        # Setup mock embedder with low similarity scores
        # Use very different vectors to ensure low similarity
        mock_embedder = Mock()
        statement_vec = np.array([1.0, 0.0, 0.0])
        bill1_vec = np.array([0.0, 1.0, 0.0])  # Orthogonal to statement
        bill2_vec = np.array([0.0, 0.0, 1.0])  # Orthogonal to statement

        mock_embedder.encode = Mock(side_effect=[statement_vec, bill1_vec, bill2_vec])

        # Patch the embedder initialization
        linker.embedder = mock_embedder

        # Find mentions
        mentions = linker.find_bill_mentions(sample_statement)

        # Verify no mentions when all below threshold (0.7)
        # With orthogonal vectors, similarity should be ~0.0
        assert len(mentions) == 0

    def test_context_extraction(self, linker):
        """Test context extraction around bill mention."""
        text = (
            "This is a long statement about various topics. "
            "We are discussing the Finance Bill, 2024 today. "
            "It has many important provisions for the economy."
        )
        position = text.index("Finance Bill")

        context = linker._extract_context(text, position, window=50)

        # Verify context includes mention and surrounding text
        assert "Finance Bill" in context
        assert len(context) <= 150  # 50 before + mention + 50 after + ellipsis

    def test_context_extraction_at_start(self, linker):
        """Test context extraction at start of text."""
        text = "Finance Bill, 2024 is important."
        position = 0

        context = linker._extract_context(text, position, window=50)

        # Verify no leading ellipsis
        assert not context.startswith("...")
        assert "Finance Bill" in context

    def test_context_extraction_at_end(self, linker):
        """Test context extraction at end of text."""
        text = "We are discussing the Finance Bill, 2024"
        position = text.index("Finance Bill")

        context = linker._extract_context(text, position, window=50)

        # Verify no trailing ellipsis
        assert not context.endswith("...")
        assert "Finance Bill" in context

    def test_deduplication(self, linker):
        """Test deduplication of bill mentions."""
        # Create duplicate mentions
        mention1 = BillMention(
            bill_id="bill-123",
            bill_title="Finance Bill, 2024",
            mention_text="Finance Bill, 2024",
            confidence=0.90,
            context="First mention",
        )
        mention2 = BillMention(
            bill_id="bill-123",
            bill_title="Finance Bill, 2024",
            mention_text="the Bill",
            confidence=0.85,
            context="Second mention",
        )
        mention3 = BillMention(
            bill_id="bill-456",
            bill_title="Health Bill, 2024",
            mention_text="Health Bill, 2024",
            confidence=0.92,
            context="Different bill",
        )

        mentions = [mention1, mention2, mention3]
        deduplicated = linker._deduplicate_mentions(mentions)

        # Verify only 2 unique bills
        assert len(deduplicated) == 2

        # Verify highest confidence mention kept for bill-123
        bill_123_mentions = [m for m in deduplicated if m.bill_id == "bill-123"]
        assert len(bill_123_mentions) == 1
        assert bill_123_mentions[0].confidence == 0.90  # Higher confidence

    def test_deduplication_empty_list(self, linker):
        """Test deduplication with empty list."""
        deduplicated = linker._deduplicate_mentions([])
        assert deduplicated == []

    def test_link_statement_to_bills(self, linker, sample_statement, sample_bill):
        """Test linking statement to bills (returns bill IDs)."""
        # Setup mock query
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[sample_bill])
        linker.db.query = Mock(return_value=mock_query)

        # Link statement
        bill_ids = linker.link_statement_to_bills(sample_statement)

        # Verify
        assert len(bill_ids) == 1
        assert bill_ids[0] == str(sample_bill.id)

    def test_link_statement_no_bills(self, linker, sample_statement):
        """Test linking statement with no bill mentions."""
        # Setup mock query to return no bills
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        linker.db.query = Mock(return_value=mock_query)

        # Link statement
        bill_ids = linker.link_statement_to_bills(sample_statement)

        # Verify empty list
        assert bill_ids == []

    def test_multiple_bill_mentions(self, linker):
        """Test statement with multiple bill mentions."""
        statement = Statement(
            text=("We are discussing the Finance Bill, 2024 and the Health Bill, 2024 today."),
            mp_id="mp-123",
            start_pos=0,
            end_pos=100,
        )

        # Create two bills
        bill1 = Mock(spec=BillORM)
        bill1.id = uuid4()
        bill1.title = "Finance Bill, 2024"

        bill2 = Mock(spec=BillORM)
        bill2.id = uuid4()
        bill2.title = "Health Bill, 2024"

        # Setup mock query to return appropriate bills based on filter
        call_count = [0]

        def mock_all():
            call_count[0] += 1
            # First call for Finance Bill, second for Health Bill
            if call_count[0] == 1:
                return [bill1]
            elif call_count[0] == 2:
                return [bill2]
            else:
                return []

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = mock_all
        linker.db.query = Mock(return_value=mock_query)

        # Find mentions
        mentions = linker.find_bill_mentions(statement)

        # Verify both bills found
        assert len(mentions) == 2
        bill_ids = [m.bill_id for m in mentions]
        assert str(bill1.id) in bill_ids
        assert str(bill2.id) in bill_ids

    def test_cosine_similarity(self, linker):
        """Test cosine similarity calculation."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        similarity = linker._cosine_similarity(vec1, vec2)

        # Identical vectors should have similarity of 1.0
        assert abs(similarity - 1.0) < 0.01

    def test_cosine_similarity_orthogonal(self, linker):
        """Test cosine similarity with orthogonal vectors."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])

        similarity = linker._cosine_similarity(vec1, vec2)

        # Orthogonal vectors should have similarity of 0.0
        assert abs(similarity - 0.0) < 0.01

    def test_edge_case_empty_statement(self, linker):
        """Test with empty statement text."""
        statement = Statement(text="", mp_id="mp-123", start_pos=0, end_pos=0)

        mentions = linker.find_bill_mentions(statement)

        # Should return empty list
        assert mentions == []

    def test_edge_case_no_bill_patterns(self, linker):
        """Test statement with no bill mention patterns."""
        statement = Statement(
            text="This is a general statement about healthcare policy.",
            mp_id="mp-123",
            start_pos=0,
            end_pos=100,
        )

        # Setup mock query
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        linker.db.query = Mock(return_value=mock_query)

        mentions = linker.find_bill_mentions(statement)

        # Should return empty list
        assert mentions == []

    def test_edge_case_case_insensitive_matching(self, linker, sample_bill):
        """Test case-insensitive bill matching."""
        statement = Statement(
            text="We are discussing the FINANCE BILL, 2024 today.",
            mp_id="mp-123",
            start_pos=0,
            end_pos=100,
        )

        # Setup mock query
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[sample_bill])
        linker.db.query = Mock(return_value=mock_query)

        mentions = linker.find_bill_mentions(statement)

        # Should match despite case difference
        assert len(mentions) == 1
