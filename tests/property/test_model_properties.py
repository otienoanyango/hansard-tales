"""
Property-based tests for data models.

Tests universal properties that must hold for all valid inputs.
"""

import pytest
from hypothesis import given, strategies as st
from datetime import date, datetime
from uuid import uuid4

from hansard_tales.models import (
    Chamber,
    DocumentType,
    SourceReference,
    Document,
    Statement,
    BillStatus,
    Bill,
    Question,
    QuestionType,
)


# Custom strategies
@st.composite
def source_reference_strategy(draw):
    """Generate valid SourceReference instances."""
    return SourceReference(
        source_url=draw(st.text(min_size=10, max_size=200)),
        source_hash=draw(st.text(min_size=64, max_size=64, alphabet="0123456789abcdef")),
        page_number=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=1000))),
        line_number=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=100))),
    )


@st.composite
def document_strategy(draw):
    """Generate valid Document instances."""
    return Document(
        type=draw(st.sampled_from(DocumentType)),
        chamber=draw(st.sampled_from(Chamber)),
        title=draw(st.text(min_size=1, max_size=500)),
        date=draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31))),
        parliament_term=draw(st.integers(min_value=1, max_value=20)),
        source=draw(source_reference_strategy()),
        vector_doc_id=draw(st.text(min_size=1, max_size=100)),
    )


class TestSourceReferenceProperties:
    """Property-based tests for SourceReference."""
    
    @given(source_reference_strategy())
    def test_source_reference_immutability(self, source):
        """
        Property: SourceReference must be immutable.
        
        **Validates: Requirements 15.3**
        """
        # Attempt to modify should raise error
        with pytest.raises(Exception):
            source.source_url = "modified"
    
    @given(source_reference_strategy())
    def test_source_reference_serialization_roundtrip(self, source):
        """
        Property: SourceReference serialization must be lossless.
        
        **Validates: Requirements 3.6**
        """
        # Serialize to dict
        data = source.model_dump()
        
        # Deserialize from dict
        restored = SourceReference.model_validate(data)
        
        # Verify equality
        assert source.source_url == restored.source_url
        assert source.source_hash == restored.source_hash
        assert source.page_number == restored.page_number
        assert source.line_number == restored.line_number


class TestDocumentProperties:
    """Property-based tests for Document."""
    
    @given(document_strategy())
    def test_document_has_valid_id(self, doc):
        """
        Property: All documents must have valid UUID.
        
        **Validates: Requirements 3.4**
        """
        assert doc.id is not None
        assert isinstance(doc.id, type(uuid4()))
    
    @given(document_strategy())
    def test_document_serialization_roundtrip(self, doc):
        """
        Property: Document serialization must be lossless.
        
        **Validates: Requirements 3.6**
        """
        # Serialize to JSON
        json_str = doc.model_dump_json()
        
        # Deserialize from JSON
        restored = Document.model_validate_json(json_str)
        
        # Verify key fields
        assert doc.title == restored.title
        assert doc.type == restored.type
        assert doc.chamber == restored.chamber
        assert doc.date == restored.date
        assert doc.parliament_term == restored.parliament_term
    
    @given(
        title=st.text(min_size=1, max_size=500),
        parliament_term=st.integers(min_value=1, max_value=20),
    )
    def test_document_validation_accepts_valid_data(self, title, parliament_term):
        """
        Property: Valid document data must pass validation.
        
        **Validates: Requirements 3.1, 3.2**
        """
        source = SourceReference(
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="a" * 64,
        )
        
        doc = Document(
            type=DocumentType.HANSARD,
            chamber=Chamber.NATIONAL_ASSEMBLY,
            title=title,
            date=date(2024, 1, 15),
            parliament_term=parliament_term,
            source=source,
            vector_doc_id="test_doc",
        )
        
        assert doc.title == title
        assert doc.parliament_term == parliament_term
    
    @given(st.integers(min_value=-100, max_value=0))
    def test_document_rejects_invalid_parliament_term(self, invalid_term):
        """
        Property: Invalid parliament terms must be rejected.
        
        **Validates: Requirements 3.2**
        """
        source = SourceReference(
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="a" * 64,
        )
        
        with pytest.raises(Exception):
            Document(
                type=DocumentType.HANSARD,
                chamber=Chamber.NATIONAL_ASSEMBLY,
                title="Test",
                date=date(2024, 1, 15),
                parliament_term=invalid_term,
                source=source,
                vector_doc_id="test_doc",
            )


class TestStatementProperties:
    """Property-based tests for Statement."""
    
    @given(
        text=st.text(min_size=1, max_size=10000),
        quality_score=st.one_of(st.none(), st.floats(min_value=0, max_value=100)),
    )
    def test_statement_validation(self, text, quality_score):
        """
        Property: Valid statement data must pass validation.
        
        **Validates: Requirements 3.2**
        """
        source = SourceReference(
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="a" * 64,
        )
        
        statement = Statement(
            document_id=uuid4(),
            mp_id=uuid4(),
            text=text,
            source=source,
            vector_doc_id="test_statement",
            quality_score=quality_score,
        )
        
        assert statement.text == text
        assert statement.quality_score == quality_score


class TestBillProperties:
    """Property-based tests for Bill."""
    
    @given(
        bill_number=st.text(min_size=1, max_size=50),
        title=st.text(min_size=1, max_size=500),
    )
    def test_bill_validation(self, bill_number, title):
        """
        Property: Valid bill data must pass validation.
        
        **Validates: Requirements 3.2**
        """
        bill = Bill(
            bill_number=bill_number,
            title=title,
            chamber=Chamber.NATIONAL_ASSEMBLY,
            status=BillStatus.PROPOSED,
            sponsor_id=uuid4(),
        )
        
        assert bill.bill_number == bill_number
        assert bill.title == title
        assert bill.current_version == 1


class TestQuestionProperties:
    """Property-based tests for Question."""
    
    @given(
        question_number=st.text(min_size=1, max_size=50),
        question_text=st.text(min_size=1, max_size=10000),
    )
    def test_question_validation(self, question_number, question_text):
        """
        Property: Valid question data must pass validation.
        
        **Validates: Requirements 3.2**
        """
        source = SourceReference(
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="a" * 64,
        )
        
        question = Question(
            question_number=question_number,
            asker_id=uuid4(),
            question_text=question_text,
            question_date=date(2024, 1, 15),
            chamber=Chamber.NATIONAL_ASSEMBLY,
            question_type=QuestionType.ORAL,
            source=source,
            vector_doc_id="test_question",
        )
        
        assert question.question_number == question_number
        assert question.question_text == question_text
