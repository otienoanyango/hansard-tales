"""
Unit tests for SQLAlchemy ORM models.

Tests database schema, relationships, and constraints.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import date, datetime
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from hansard_tales.database.models import (
    Base,
    DocumentTypeEnum,
    ChamberEnum,
    DocumentORM,
    MPORM,
    StatementORM,
    BillORM,
    BillVersionORM,
    VoteORM,
    MPVoteORM,
    QuestionORM,
    PetitionORM,
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    # Create engine and tables
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)
    Path(db_path).unlink()


class TestDocumentORM:
    """Test suite for DocumentORM model."""
    
    def test_create_document(self, temp_db):
        """Test creating a document in database."""
        doc = DocumentORM(
            id=uuid4(),
            type=DocumentTypeEnum.HANSARD,
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            title="Test Hansard",
            date=date(2024, 1, 15),
            parliament_term=13,
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="abc123def456" + "0" * 52,  # 64 chars
            download_date=datetime.utcnow(),
            vector_doc_id="test_doc_1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        temp_db.add(doc)
        temp_db.commit()
        
        # Verify document was created
        retrieved = temp_db.query(DocumentORM).filter_by(title="Test Hansard").first()
        assert retrieved is not None
        assert retrieved.type == DocumentTypeEnum.HANSARD
        assert retrieved.chamber == ChamberEnum.NATIONAL_ASSEMBLY
    
    def test_document_unique_source_hash(self, temp_db):
        """Test that source_hash must be unique."""
        doc1 = DocumentORM(
            id=uuid4(),
            type=DocumentTypeEnum.HANSARD,
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            title="Test Hansard 1",
            date=date(2024, 1, 15),
            parliament_term=13,
            source_url="https://parliament.go.ke/test1.pdf",
            source_hash="abc123def456" + "0" * 52,
            download_date=datetime.utcnow(),
            vector_doc_id="test_doc_1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        doc2 = DocumentORM(
            id=uuid4(),
            type=DocumentTypeEnum.HANSARD,
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            title="Test Hansard 2",
            date=date(2024, 1, 16),
            parliament_term=13,
            source_url="https://parliament.go.ke/test2.pdf",
            source_hash="abc123def456" + "0" * 52,  # Same hash
            download_date=datetime.utcnow(),
            vector_doc_id="test_doc_2",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        temp_db.add(doc1)
        temp_db.commit()
        
        # Attempt to add document with duplicate hash
        temp_db.add(doc2)
        with pytest.raises(IntegrityError):
            temp_db.commit()


class TestMPORM:
    """Test suite for MPORM model."""
    
    def test_create_mp(self, temp_db):
        """Test creating an MP in database."""
        mp = MPORM(
            id=uuid4(),
            name="John Doe",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            party="Test Party",
            constituency="Test Constituency",
            parliament_term=13,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        temp_db.add(mp)
        temp_db.commit()
        
        # Verify MP was created
        retrieved = temp_db.query(MPORM).filter_by(name="John Doe").first()
        assert retrieved is not None
        assert retrieved.party == "Test Party"
        assert retrieved.constituency == "Test Constituency"


class TestStatementORM:
    """Test suite for StatementORM model."""
    
    def test_create_statement_with_relationships(self, temp_db):
        """Test creating a statement with document and MP relationships."""
        # Create document
        doc = DocumentORM(
            id=uuid4(),
            type=DocumentTypeEnum.HANSARD,
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            title="Test Hansard",
            date=date(2024, 1, 15),
            parliament_term=13,
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="abc123def456" + "0" * 52,
            download_date=datetime.utcnow(),
            vector_doc_id="test_doc_1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Create MP
        mp = MPORM(
            id=uuid4(),
            name="John Doe",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            parliament_term=13,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        temp_db.add(doc)
        temp_db.add(mp)
        temp_db.commit()
        
        # Create statement
        statement = StatementORM(
            id=uuid4(),
            document_id=doc.id,
            mp_id=mp.id,
            text="This is a test statement.",
            source_url="https://parliament.go.ke/test.pdf",
            source_hash="abc123def456" + "0" * 52,
            page_number=5,
            line_number=10,
            vector_doc_id="test_statement_1",
            created_at=datetime.utcnow(),
        )
        
        temp_db.add(statement)
        temp_db.commit()
        
        # Verify relationships
        retrieved = temp_db.query(StatementORM).first()
        assert retrieved.document.title == "Test Hansard"
        assert retrieved.mp.name == "John Doe"


class TestBillORM:
    """Test suite for BillORM model."""
    
    def test_create_bill_with_sponsor(self, temp_db):
        """Test creating a bill with sponsor relationship."""
        # Create sponsor
        sponsor = MPORM(
            id=uuid4(),
            name="Jane Smith",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            parliament_term=13,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        temp_db.add(sponsor)
        temp_db.commit()
        
        # Create bill
        bill = BillORM(
            id=uuid4(),
            bill_number="Bill No. 1 of 2024",
            title="Test Bill",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            status="proposed",
            sponsor_id=sponsor.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        temp_db.add(bill)
        temp_db.commit()
        
        # Verify relationship
        retrieved = temp_db.query(BillORM).first()
        assert retrieved.sponsor.name == "Jane Smith"
    
    def test_bill_unique_bill_number(self, temp_db):
        """Test that bill_number must be unique."""
        sponsor = MPORM(
            id=uuid4(),
            name="Jane Smith",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            parliament_term=13,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        temp_db.add(sponsor)
        temp_db.commit()
        
        bill1 = BillORM(
            id=uuid4(),
            bill_number="Bill No. 1 of 2024",
            title="Test Bill 1",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            status="proposed",
            sponsor_id=sponsor.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        bill2 = BillORM(
            id=uuid4(),
            bill_number="Bill No. 1 of 2024",  # Same number
            title="Test Bill 2",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            status="proposed",
            sponsor_id=sponsor.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        temp_db.add(bill1)
        temp_db.commit()
        
        # Attempt to add bill with duplicate number
        temp_db.add(bill2)
        with pytest.raises(IntegrityError):
            temp_db.commit()


class TestVoteORM:
    """Test suite for VoteORM model."""
    
    def test_create_vote_with_bill(self, temp_db):
        """Test creating a vote with bill relationship."""
        # Create sponsor and bill
        sponsor = MPORM(
            id=uuid4(),
            name="Jane Smith",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            parliament_term=13,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        temp_db.add(sponsor)
        temp_db.commit()
        
        bill = BillORM(
            id=uuid4(),
            bill_number="Bill No. 1 of 2024",
            title="Test Bill",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            status="proposed",
            sponsor_id=sponsor.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        temp_db.add(bill)
        temp_db.commit()
        
        # Create vote
        vote = VoteORM(
            id=uuid4(),
            bill_id=bill.id,
            vote_date=date(2024, 1, 15),
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            vote_type="division",
            ayes=150,
            noes=100,
            abstentions=10,
            result="passed",
            source_url="https://parliament.go.ke/vote.pdf",
            source_hash="abc123def456" + "0" * 52,
            download_date=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        
        temp_db.add(vote)
        temp_db.commit()
        
        # Verify relationship
        retrieved = temp_db.query(VoteORM).first()
        assert retrieved.bill.title == "Test Bill"


class TestQuestionORM:
    """Test suite for QuestionORM model."""
    
    def test_create_question_with_asker(self, temp_db):
        """Test creating a question with asker relationship."""
        # Create asker
        asker = MPORM(
            id=uuid4(),
            name="John Doe",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            parliament_term=13,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        temp_db.add(asker)
        temp_db.commit()
        
        # Create question
        question = QuestionORM(
            id=uuid4(),
            question_number="Q001/2024",
            asker_id=asker.id,
            question_text="What is the budget allocation?",
            question_date=date(2024, 1, 15),
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            question_type="oral",
            source_url="https://parliament.go.ke/question.pdf",
            source_hash="abc123def456" + "0" * 52,
            download_date=datetime.utcnow(),
            vector_doc_id="question_1",
            created_at=datetime.utcnow(),
        )
        
        temp_db.add(question)
        temp_db.commit()
        
        # Verify relationship
        retrieved = temp_db.query(QuestionORM).first()
        assert retrieved.asker.name == "John Doe"


class TestPetitionORM:
    """Test suite for PetitionORM model."""
    
    def test_create_petition_with_sponsor(self, temp_db):
        """Test creating a petition with sponsor relationship."""
        # Create sponsor
        sponsor = MPORM(
            id=uuid4(),
            name="Jane Smith",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            parliament_term=13,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        temp_db.add(sponsor)
        temp_db.commit()
        
        # Create petition
        petition = PetitionORM(
            id=uuid4(),
            petition_number="P001/2024",
            title="Petition for Better Roads",
            petitioner="John Doe",
            sponsor_id=sponsor.id,
            submission_date=date(2024, 1, 15),
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            petition_text="We petition for better roads.",
            prayer="That the government allocates funds.",
            status="submitted",
            source_url="https://parliament.go.ke/petition.pdf",
            source_hash="abc123def456" + "0" * 52,
            download_date=datetime.utcnow(),
            vector_doc_id="petition_1",
            created_at=datetime.utcnow(),
        )
        
        temp_db.add(petition)
        temp_db.commit()
        
        # Verify relationship
        retrieved = temp_db.query(PetitionORM).first()
        assert retrieved.sponsor.name == "Jane Smith"
