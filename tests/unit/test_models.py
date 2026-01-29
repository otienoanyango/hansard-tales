"""
Unit tests for Pydantic data models.

Tests model validation, serialization, and immutability constraints.
"""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from hansard_tales.models import (
    Bill,
    BillStatus,
    BillVersion,
    Chamber,
    Document,
    DocumentType,
    MPVote,
    Petition,
    Question,
    QuestionType,
    SourceReference,
    Statement,
    Vote,
    VoteDirection,
)


class TestSourceReference:
    """Test suite for SourceReference model."""

    def test_create_source_reference(self):
        """Test creating a source reference."""
        source = SourceReference(
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="abc123def456",
        )

        assert source.source_url == "https://parliament.go.ke/test.pdf"
        assert source.source_hash == "abc123def456"
        assert isinstance(source.download_date, datetime)

    def test_source_reference_immutability(self):
        """Test that source reference is immutable."""
        source = SourceReference(
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="abc123def456",
        )

        # Attempt to modify should raise error
        with pytest.raises((ValidationError, AttributeError)):
            source.source_url = "https://example.com/modified.pdf"

    def test_source_reference_with_page_line(self):
        """Test source reference with page and line numbers."""
        source = SourceReference(
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="abc123def456",
            page_number=5,
            line_number=10,
        )

        assert source.page_number == 5
        assert source.line_number == 10


class TestDocument:
    """Test suite for Document model."""

    def test_create_document(self):
        """Test creating a document."""
        source = SourceReference(
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="abc123def456",
        )

        doc = Document(
            type=DocumentType.HANSARD,
            chamber=Chamber.NATIONAL_ASSEMBLY,
            title="Test Hansard",
            date=date(2024, 1, 15),
            parliament_term=13,
            source=source,
            vector_doc_id="test_doc_1",
        )

        assert doc.type == DocumentType.HANSARD
        assert doc.chamber == Chamber.NATIONAL_ASSEMBLY
        assert doc.title == "Test Hansard"
        assert doc.date == date(2024, 1, 15)
        assert doc.parliament_term == 13
        assert doc.source.source_url == "https://parliament.go.ke/test.pdf"

    def test_document_with_metadata(self):
        """Test document with custom metadata."""
        source = SourceReference(
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="abc123def456",
        )

        doc = Document(
            type=DocumentType.HANSARD,
            chamber=Chamber.NATIONAL_ASSEMBLY,
            title="Test Hansard",
            date=date(2024, 1, 15),
            parliament_term=13,
            source=source,
            vector_doc_id="test_doc_1",
            metadata={"session": "Morning", "period": "A"},
        )

        assert doc.metadata["session"] == "Morning"
        assert doc.metadata["period"] == "A"

    def test_document_json_serialization(self):
        """Test document JSON serialization."""
        source = SourceReference(
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="abc123def456",
        )

        doc = Document(
            type=DocumentType.HANSARD,
            chamber=Chamber.NATIONAL_ASSEMBLY,
            title="Test Hansard",
            date=date(2024, 1, 15),
            parliament_term=13,
            source=source,
            vector_doc_id="test_doc_1",
        )

        # Serialize to JSON
        json_str = doc.model_dump_json()

        # Deserialize from JSON
        doc_restored = Document.model_validate_json(json_str)

        assert doc.title == doc_restored.title
        assert doc.type == doc_restored.type
        assert doc.chamber == doc_restored.chamber


class TestStatement:
    """Test suite for Statement model."""

    def test_create_statement(self):
        """Test creating a statement."""
        source = SourceReference(
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="abc123def456",
            page_number=5,
            line_number=10,
        )

        statement = Statement(
            document_id=uuid4(),
            mp_id=uuid4(),
            text="This is a test statement.",
            source=source,
            vector_doc_id="test_statement_1",
        )

        assert statement.text == "This is a test statement."
        assert statement.source.page_number == 5
        assert statement.source.line_number == 10

    def test_statement_with_analysis(self):
        """Test statement with analysis results."""
        source = SourceReference(
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="abc123def456",
        )

        statement = Statement(
            document_id=uuid4(),
            mp_id=uuid4(),
            text="This is a test statement.",
            source=source,
            vector_doc_id="test_statement_1",
            classification="substantive",
            sentiment="support",
            quality_score=85.5,
            topics=["healthcare", "budget"],
        )

        assert statement.classification == "substantive"
        assert statement.sentiment == "support"
        assert statement.quality_score == 85.5
        assert "healthcare" in statement.topics


class TestBill:
    """Test suite for Bill model."""

    def test_create_bill(self):
        """Test creating a bill."""
        bill = Bill(
            bill_number="Bill No. 1 of 2024",
            title="Test Bill",
            chamber=Chamber.NATIONAL_ASSEMBLY,
            status=BillStatus.PROPOSED,
            sponsor_id=uuid4(),
        )

        assert bill.bill_number == "Bill No. 1 of 2024"
        assert bill.title == "Test Bill"
        assert bill.status == BillStatus.PROPOSED
        assert bill.current_version == 1

    def test_bill_with_versions(self):
        """Test bill with multiple versions."""
        source = SourceReference(
            source_url="https://parliament.go.ke/bill.pdf",
            source_hash="abc123def456",
        )

        version1 = BillVersion(
            version_number=1,
            title="Test Bill v1",
            text="Original bill text",
            source=source,
            vector_doc_id="bill_v1",
        )

        version2 = BillVersion(
            version_number=2,
            title="Test Bill v2",
            text="Amended bill text",
            source=source,
            vector_doc_id="bill_v2",
            changes_summary="Added section 5",
        )

        bill = Bill(
            bill_number="Bill No. 1 of 2024",
            title="Test Bill",
            chamber=Chamber.NATIONAL_ASSEMBLY,
            status=BillStatus.COMMITTEE,
            sponsor_id=uuid4(),
            versions=[version1, version2],
            current_version=2,
        )

        assert len(bill.versions) == 2
        assert bill.current_version == 2
        assert bill.versions[1].changes_summary == "Added section 5"


class TestVote:
    """Test suite for Vote model."""

    def test_create_vote(self):
        """Test creating a vote."""
        source = SourceReference(
            source_url="https://parliament.go.ke/vote.pdf",
            source_hash="abc123def456",
        )

        vote = Vote(
            bill_id=uuid4(),
            vote_date=date(2024, 1, 15),
            chamber=Chamber.NATIONAL_ASSEMBLY,
            vote_type="division",
            ayes=150,
            noes=100,
            abstentions=10,
            result="passed",
            source=source,
        )

        assert vote.ayes == 150
        assert vote.noes == 100
        assert vote.result == "passed"

    def test_vote_with_individual_votes(self):
        """Test vote with individual MP votes."""
        source = SourceReference(
            source_url="https://parliament.go.ke/vote.pdf",
            source_hash="abc123def456",
        )

        mp_votes = [
            MPVote(mp_id=uuid4(), direction=VoteDirection.AYE),
            MPVote(mp_id=uuid4(), direction=VoteDirection.NO),
            MPVote(mp_id=uuid4(), direction=VoteDirection.ABSTAIN),
        ]

        vote = Vote(
            bill_id=uuid4(),
            vote_date=date(2024, 1, 15),
            chamber=Chamber.NATIONAL_ASSEMBLY,
            vote_type="division",
            votes=mp_votes,
            ayes=1,
            noes=1,
            abstentions=1,
            result="passed",
            source=source,
        )

        assert len(vote.votes) == 3
        assert vote.votes[0].direction == VoteDirection.AYE


class TestQuestion:
    """Test suite for Question model."""

    def test_create_question(self):
        """Test creating a question."""
        source = SourceReference(
            source_url="https://parliament.go.ke/question.pdf",
            source_hash="abc123def456",
        )

        question = Question(
            question_number="Q001/2024",
            asker_id=uuid4(),
            question_text="What is the budget allocation?",
            question_date=date(2024, 1, 15),
            chamber=Chamber.NATIONAL_ASSEMBLY,
            question_type=QuestionType.ORAL,
            source=source,
            vector_doc_id="question_1",
        )

        assert question.question_number == "Q001/2024"
        assert question.question_text == "What is the budget allocation?"
        assert question.question_type == QuestionType.ORAL

    def test_question_with_answer(self):
        """Test question with answer."""
        source = SourceReference(
            source_url="https://parliament.go.ke/question.pdf",
            source_hash="abc123def456",
        )

        question = Question(
            question_number="Q001/2024",
            asker_id=uuid4(),
            respondent_id=uuid4(),
            question_text="What is the budget allocation?",
            answer_text="The budget allocation is 100M.",
            question_date=date(2024, 1, 15),
            answer_date=date(2024, 1, 20),
            chamber=Chamber.NATIONAL_ASSEMBLY,
            question_type=QuestionType.WRITTEN,
            ministry="Treasury",
            source=source,
            vector_doc_id="question_1",
        )

        assert question.answer_text == "The budget allocation is 100M."
        assert question.answer_date == date(2024, 1, 20)
        assert question.ministry == "Treasury"


class TestPetition:
    """Test suite for Petition model."""

    def test_create_petition(self):
        """Test creating a petition."""
        source = SourceReference(
            source_url="https://parliament.go.ke/petition.pdf",
            source_hash="abc123def456",
        )

        petition = Petition(
            petition_number="P001/2024",
            title="Petition for Better Roads",
            petitioner="John Doe",
            sponsor_id=uuid4(),
            submission_date=date(2024, 1, 15),
            chamber=Chamber.NATIONAL_ASSEMBLY,
            petition_text="We petition for better roads in our area.",
            prayer="That the government allocates funds for road construction.",
            status="submitted",
            source=source,
            vector_doc_id="petition_1",
        )

        assert petition.petition_number == "P001/2024"
        assert petition.title == "Petition for Better Roads"
        assert petition.petitioner == "John Doe"
        assert petition.status == "submitted"

    def test_petition_with_response(self):
        """Test petition with committee response."""
        source = SourceReference(
            source_url="https://parliament.go.ke/petition.pdf",
            source_hash="abc123def456",
        )

        petition = Petition(
            petition_number="P001/2024",
            title="Petition for Better Roads",
            petitioner="John Doe",
            sponsor_id=uuid4(),
            submission_date=date(2024, 1, 15),
            chamber=Chamber.NATIONAL_ASSEMBLY,
            petition_text="We petition for better roads in our area.",
            prayer="That the government allocates funds for road construction.",
            status="committee_review",
            committee="Transport Committee",
            response="The committee has reviewed and recommends approval.",
            topics=["infrastructure", "transport"],
            source=source,
            vector_doc_id="petition_1",
        )

        assert petition.committee == "Transport Committee"
        assert petition.response == "The committee has reviewed and recommends approval."
        assert "infrastructure" in petition.topics
