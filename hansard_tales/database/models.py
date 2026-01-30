"""
SQLAlchemy ORM models for database schema.

This module defines the database schema using SQLAlchemy ORM,
mapping to the Pydantic models for data validation.
"""

import enum
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DocumentTypeEnum(enum.Enum):
    """Document type enumeration."""

    HANSARD = "hansard"
    VOTES = "votes"
    BILL = "bill"
    QUESTION = "question"
    PETITION = "petition"
    STATEMENT_TRACKER = "statement_tracker"
    MOTION_TRACKER = "motion_tracker"
    BILL_TRACKER = "bill_tracker"
    ORDER_PAPER = "order_paper"
    LEGISLATIVE_PROPOSAL = "legislative_proposal"
    AUDITOR_REPORT = "auditor_report"


class ChamberEnum(enum.Enum):
    """Chamber enumeration."""

    NATIONAL_ASSEMBLY = "national_assembly"
    SENATE = "senate"


class DocumentORM(Base):
    """
    Documents table.

    Stores all parliamentary documents with immutable source tracking.
    """

    __tablename__ = "documents"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(SQLEnum(DocumentTypeEnum), nullable=False)
    chamber = Column(SQLEnum(ChamberEnum), nullable=False)
    title = Column(String(500), nullable=False)
    date = Column(Date, nullable=False)
    session_id = Column(String(100))
    parliament_term = Column(Integer, nullable=False)

    # Source tracking (immutable)
    source_url = Column(Text, nullable=False)
    source_hash = Column(String(64), nullable=False, unique=True)
    download_date = Column(DateTime, nullable=False)

    # Vector DB reference
    vector_doc_id = Column(String(100), nullable=False)

    # Document metadata (JSON)
    doc_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_documents_type_chamber_date", "type", "chamber", "date"),
        Index("idx_documents_source_hash", "source_hash"),
        Index("idx_documents_date", "date"),
    )


class MPORM(Base):
    """
    MPs/Senators table.

    Stores information about Members of Parliament and Senators.
    """

    __tablename__ = "mps"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    chamber = Column(SQLEnum(ChamberEnum), nullable=False)
    party = Column(String(100))
    constituency = Column(String(200))
    parliament_term = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_mps_chamber_term", "chamber", "parliament_term"),
        Index("idx_mps_name", "name"),
    )


class StatementORM(Base):
    """
    Statements table.

    Stores individual statements from Hansard with source tracking.
    """

    __tablename__ = "statements"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(PGUUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    mp_id = Column(PGUUID(as_uuid=True), ForeignKey("mps.id"), nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime)

    # Source tracking (immutable)
    source_url = Column(Text, nullable=False)
    source_hash = Column(String(64), nullable=False)
    page_number = Column(Integer)
    line_number = Column(Integer)

    # Vector DB reference
    vector_doc_id = Column(String(100), nullable=False)

    # Analysis results
    classification = Column(String(50))
    sentiment = Column(String(50))
    quality_score = Column(Float)
    topics = Column(JSON, default=[])
    related_bill_ids = Column(JSON, default=[])
    related_question_ids = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime, nullable=False)

    # Relationships
    document = relationship("DocumentORM", backref="statements")  # type: ignore[assignment]
    mp = relationship("MPORM", backref="statements")  # type: ignore[assignment]

    # Indexes
    __table_args__ = (
        Index("idx_statements_document_id", "document_id"),
        Index("idx_statements_mp_id", "mp_id"),
        Index("idx_statements_classification", "classification"),
    )


class BillORM(Base):
    """
    Bills table.

    Stores parliamentary bills with version tracking.
    """

    __tablename__ = "bills"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bill_number = Column(String(50), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    chamber = Column(SQLEnum(ChamberEnum), nullable=False)
    status = Column(String(50), nullable=False)
    current_version = Column(Integer, default=1)

    # Sponsorship
    sponsor_id = Column(PGUUID(as_uuid=True), ForeignKey("mps.id"), nullable=False)
    co_sponsor_ids = Column(JSON, default=[])

    # Related documents
    related_statement_ids = Column(JSON, default=[])
    related_vote_ids = Column(JSON, default=[])
    related_question_ids = Column(JSON, default=[])
    related_petition_ids = Column(JSON, default=[])

    # Categorization
    topics = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Relationships
    sponsor = relationship("MPORM", backref="sponsored_bills")  # type: ignore[assignment]

    # Indexes
    __table_args__ = (
        Index("idx_bills_bill_number", "bill_number"),
        Index("idx_bills_status", "status"),
        Index("idx_bills_chamber", "chamber"),
    )


class BillVersionORM(Base):
    """
    Bill versions table.

    Stores different versions of bills for amendment tracking.
    """

    __tablename__ = "bill_versions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bill_id = Column(PGUUID(as_uuid=True), ForeignKey("bills.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    text = Column(Text, nullable=False)

    # Source tracking
    source_url = Column(Text, nullable=False)
    source_hash = Column(String(64), nullable=False)
    download_date = Column(DateTime, nullable=False)

    # Vector DB reference
    vector_doc_id = Column(String(100), nullable=False)

    changes_summary = Column(Text)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    bill = relationship("BillORM", backref="versions")  # type: ignore[assignment]

    # Indexes
    __table_args__ = (
        Index("idx_bill_versions_bill_id", "bill_id"),
        Index("idx_bill_versions_version", "bill_id", "version_number"),
    )


class VoteORM(Base):
    """
    Votes table.

    Stores parliamentary vote records.
    """

    __tablename__ = "votes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bill_id = Column(PGUUID(as_uuid=True), ForeignKey("bills.id"), nullable=False)
    vote_date = Column(Date, nullable=False)
    chamber = Column(SQLEnum(ChamberEnum), nullable=False)
    vote_type = Column(String(50), nullable=False)

    # Results
    ayes = Column(Integer, default=0)
    noes = Column(Integer, default=0)
    abstentions = Column(Integer, default=0)
    result = Column(String(50), nullable=False)

    # Source tracking
    source_url = Column(Text, nullable=False)
    source_hash = Column(String(64), nullable=False)
    download_date = Column(DateTime, nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False)

    # Relationships
    bill = relationship("BillORM", backref="votes")  # type: ignore[assignment]

    # Indexes
    __table_args__ = (
        Index("idx_votes_bill_id", "bill_id"),
        Index("idx_votes_date", "vote_date"),
    )


class MPVoteORM(Base):
    """
    Individual MP votes table.

    Stores how each MP voted on a particular vote.
    """

    __tablename__ = "mp_votes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    vote_id = Column(PGUUID(as_uuid=True), ForeignKey("votes.id"), nullable=False)
    mp_id = Column(PGUUID(as_uuid=True), ForeignKey("mps.id"), nullable=False)
    direction = Column(String(20), nullable=False)

    # Relationships
    vote = relationship("VoteORM", backref="mp_votes")  # type: ignore[assignment]
    mp = relationship("MPORM", backref="votes")  # type: ignore[assignment]

    # Indexes
    __table_args__ = (
        Index("idx_mp_votes_vote_id", "vote_id"),
        Index("idx_mp_votes_mp_id", "mp_id"),
    )


class QuestionORM(Base):
    """
    Questions table.

    Stores parliamentary questions and answers.
    """

    __tablename__ = "questions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    question_number = Column(String(50), nullable=False)
    asker_id = Column(PGUUID(as_uuid=True), ForeignKey("mps.id"), nullable=False)
    respondent_id = Column(PGUUID(as_uuid=True), ForeignKey("mps.id"))
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text)
    question_date = Column(Date, nullable=False)
    answer_date = Column(Date)
    chamber = Column(SQLEnum(ChamberEnum), nullable=False)

    # Categorization
    question_type = Column(String(20), nullable=False)
    ministry = Column(String(200))
    topics = Column(JSON, default=[])

    # Source tracking
    source_url = Column(Text, nullable=False)
    source_hash = Column(String(64), nullable=False)
    download_date = Column(DateTime, nullable=False)
    vector_doc_id = Column(String(100), nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False)

    # Relationships
    asker = relationship("MPORM", foreign_keys=[asker_id], backref="questions_asked")  # type: ignore[assignment]
    respondent = relationship("MPORM", foreign_keys=[respondent_id], backref="questions_answered")  # type: ignore[assignment]

    # Indexes
    __table_args__ = (
        Index("idx_questions_asker_id", "asker_id"),
        Index("idx_questions_date", "question_date"),
    )


class PetitionORM(Base):
    """
    Petitions table.

    Stores public petitions to parliament.
    """

    __tablename__ = "petitions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    petition_number = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    petitioner = Column(String(200), nullable=False)
    sponsor_id = Column(PGUUID(as_uuid=True), ForeignKey("mps.id"), nullable=False)
    submission_date = Column(Date, nullable=False)
    chamber = Column(SQLEnum(ChamberEnum), nullable=False)

    # Content
    petition_text = Column(Text, nullable=False)
    prayer = Column(Text, nullable=False)

    # Status tracking
    status = Column(String(50), nullable=False)
    committee = Column(String(200))
    response = Column(Text)

    # Categorization
    topics = Column(JSON, default=[])

    # Source tracking
    source_url = Column(Text, nullable=False)
    source_hash = Column(String(64), nullable=False)
    download_date = Column(DateTime, nullable=False)
    vector_doc_id = Column(String(100), nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False)

    # Relationships
    sponsor = relationship("MPORM", backref="petitions_sponsored")  # type: ignore[assignment]

    # Indexes
    __table_args__ = (
        Index("idx_petitions_sponsor_id", "sponsor_id"),
        Index("idx_petitions_date", "submission_date"),
    )


class DownloadedFileORM(Base):
    """
    Downloaded files tracking table for duplicate prevention.

    This table tracks all downloaded PDFs to prevent redownloading
    the same files. Uses SHA256 hash for deduplication.
    """

    __tablename__ = "downloaded_files"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Source tracking
    source_url = Column(Text, nullable=False)
    source_hash = Column(String(64), nullable=False, unique=True)

    # File information
    standardized_filename = Column(String(255), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    document_type = Column(String(50), nullable=False)

    # Download tracking
    download_date = Column(DateTime, nullable=False)
    file_path = Column(Text, nullable=False)

    # Metadata
    chamber = Column(String(50))
    parliament_term = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_downloaded_files_hash", "source_hash"),
        Index("idx_downloaded_files_type", "document_type"),
        Index("idx_downloaded_files_date", "download_date"),
    )


class APIUsageORM(Base):
    """
    API usage tracking table for cost management.

    This table tracks API calls (LLM, embeddings, etc.) to monitor
    and enforce budget constraints.
    """

    __tablename__ = "api_usage"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Date and model tracking
    date = Column(Date, nullable=False)
    model = Column(String(100), nullable=False)

    # Token counts
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)

    # Cost tracking
    cost_usd = Column(Float, nullable=False, default=0.0)

    # Request count
    requests = Column(Integer, nullable=False, default=1)

    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_api_usage_date", "date"),
        Index("idx_api_usage_model", "model"),
        Index("idx_api_usage_date_model", "date", "model"),
    )
