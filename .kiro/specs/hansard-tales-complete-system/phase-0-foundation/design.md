# Phase 0: Foundation - Design

## Introduction

This document provides detailed component designs for Phase 0 of the Hansard Tales system. It translates the requirements into concrete technical specifications, interfaces, and implementation approaches.

**Design Principles**:
- **Simplicity First**: Start with SQLite and ChromaDB, migrate to PostgreSQL and Qdrant when needed
- **Type Safety**: Use Pydantic models and type hints throughout
- **Testability**: Design for easy unit and property-based testing
- **Extensibility**: Support all 22 document types from the start
- **Anti-Hallucination**: Immutable source tracking at every layer

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Configuration Layer                          │
│  config.yaml → Environment Variables → Validated Config Object  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Models Layer                           │
│  Pydantic Models: Document, Statement, Bill, Vote, Question...  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │  SQLAlchemy ORM  │         │  Vector DB       │             │
│  │  (PostgreSQL/    │         │  (Qdrant/        │             │
│  │   SQLite)        │         │   ChromaDB)      │             │
│  └──────────────────┘         └──────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Collection Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Hansard     │  │  Votes       │  │  Bills       │  ...    │
│  │  Scraper     │  │  Scraper     │  │  Scraper     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Processing Layer                              │
│  PDF Parser → Entity Extractor → Embedding Generator            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Observability Layer                           │
│  Structured Logging + Metrics + Error Tracking                  │
└─────────────────────────────────────────────────────────────────┘
```

## Design 1: Configuration Management

### Component Design

**Purpose**: Centralized configuration with validation and environment-specific overrides

**Technology**: Pydantic Settings + YAML


### Configuration Schema

```python
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Literal
from pathlib import Path

class DatabaseConfig(BaseSettings):
    """Database configuration"""
    engine: Literal["sqlite", "postgresql"] = "sqlite"
    host: str = "localhost"
    port: int = 5432
    database: str = "hansard_tales"
    user: str = "hansard"
    password: str = Field(default="", env="DB_PASSWORD")
    
    @property
    def connection_string(self) -> str:
        if self.engine == "sqlite":
            return f"sqlite:///{self.database}.db"
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

class VectorDBConfig(BaseSettings):
    """Vector database configuration"""
    engine: Literal["chromadb", "qdrant"] = "chromadb"
    host: str = "localhost"
    port: int = 6333
    collection_prefix: str = "hansard_tales"
    persist_directory: Path = Path("data/vector_db")
    
class EmbeddingConfig(BaseSettings):
    """Embedding model configuration"""
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32
    device: Literal["cpu", "cuda"] = "cpu"

class ScraperConfig(BaseSettings):
    """Web scraper configuration"""
    base_url: str = "https://parliament.go.ke"
    download_dir: Path = Path("data/pdfs")
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30
    user_agent: str = "HansardTales/1.0"

class LoggingConfig(BaseSettings):
    """Logging configuration"""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["json", "text"] = "json"
    output: Literal["stdout", "file", "both"] = "both"
    log_dir: Path = Path("logs")
    rotation: str = "1 day"
    retention: str = "30 days"

class MonitoringConfig(BaseSettings):
    """Monitoring configuration"""
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    sentry_enabled: bool = False
    sentry_dsn: str = Field(default="", env="SENTRY_DSN")

class Config(BaseSettings):
    """Main application configuration"""
    environment: Literal["development", "staging", "production"] = "development"
    database: DatabaseConfig = DatabaseConfig()
    vector_db: VectorDBConfig = VectorDBConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    scraper: ScraperConfig = ScraperConfig()
    logging: LoggingConfig = LoggingConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"

# Usage
config = Config()
```

### Configuration Files

**config/development.yaml**:
```yaml
environment: development
database:
  engine: sqlite
  database: data/hansard_dev
vector_db:
  engine: chromadb
  persist_directory: data/vector_db_dev
logging:
  level: DEBUG
  format: text
  output: stdout
monitoring:
  prometheus_enabled: false
  sentry_enabled: false
```

**config/production.yaml**:
```yaml
environment: production
database:
  engine: postgresql
  host: ${DB_HOST}
  port: 5432
  database: hansard_tales
  user: hansard
vector_db:
  engine: qdrant
  host: ${QDRANT_HOST}
  port: 6333
logging:
  level: INFO
  format: json
  output: both
monitoring:
  prometheus_enabled: true
  sentry_enabled: true
```

### Correctness Properties

**Property 1.1**: Configuration validation
- **Validates**: Requirements 6.1, 6.4
- **Property**: All required configuration fields must be present and valid
- **Test Strategy**: Generate random configurations, verify validation catches invalid ones

**Property 1.2**: Environment override
- **Validates**: Requirements 6.2
- **Property**: Environment variables must override file configuration
- **Test Strategy**: Set env vars, verify they take precedence



## Design 2: Data Models

### Component Design

**Purpose**: Type-safe data models for all parliamentary documents with immutable source tracking

**Technology**: Pydantic v2 for validation, SQLAlchemy for ORM

### Base Models

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID, uuid4

class Chamber(str, Enum):
    """Parliamentary chamber"""
    NATIONAL_ASSEMBLY = "national_assembly"
    SENATE = "senate"

class DocumentType(str, Enum):
    """Parliamentary document types"""
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

class SourceReference(BaseModel):
    """Immutable source tracking (anti-hallucination)"""
    model_config = ConfigDict(frozen=True)
    
    source_url: str = Field(..., description="Original document URL")
    source_hash: str = Field(..., description="SHA256 hash of original PDF")
    download_date: datetime = Field(default_factory=datetime.utcnow)
    page_number: Optional[int] = Field(None, description="Page in source PDF")
    line_number: Optional[int] = Field(None, description="Line on page")

class Document(BaseModel):
    """Base document model for all parliamentary documents"""
    id: UUID = Field(default_factory=uuid4)
    type: DocumentType
    chamber: Chamber
    title: str = Field(..., min_length=1, max_length=500)
    date: date
    session_id: Optional[str] = None
    parliament_term: int = Field(..., ge=1, le=20)
    
    # Source tracking (immutable)
    source: SourceReference
    
    # Vector DB reference
    vector_doc_id: str = Field(..., description="ID in vector database")
    
    # Metadata (varies by document type)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Statement(BaseModel):
    """Parliamentary statement from Hansard"""
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID = Field(..., description="Parent Hansard document")
    mp_id: UUID = Field(..., description="MP who made statement")
    text: str = Field(..., min_length=1)
    timestamp: Optional[datetime] = None
    
    # Source tracking (immutable)
    source: SourceReference
    
    # Vector DB reference
    vector_doc_id: str
    
    # Analysis results (populated by pipeline)
    classification: Optional[str] = Field(None, description="filler or substantive")
    sentiment: Optional[str] = Field(None, description="support, oppose, neutral")
    quality_score: Optional[float] = Field(None, ge=0, le=100)
    topics: List[str] = Field(default_factory=list)
    related_bill_ids: List[UUID] = Field(default_factory=list)
    related_question_ids: List[UUID] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BillStatus(str, Enum):
    """Bill lifecycle status"""
    PROPOSED = "proposed"
    FIRST_READING = "first_reading"
    SECOND_READING = "second_reading"
    COMMITTEE = "committee"
    THIRD_READING = "third_reading"
    PASSED = "passed"
    PRESIDENTIAL_ASSENT = "presidential_assent"
    ENACTED = "enacted"
    REJECTED = "rejected"

class BillVersion(BaseModel):
    """Version of a bill (for amendment tracking)"""
    version_number: int = Field(..., ge=1)
    title: str
    text: str
    source: SourceReference
    vector_doc_id: str
    changes_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Bill(BaseModel):
    """Parliamentary bill"""
    id: UUID = Field(default_factory=uuid4)
    bill_number: str = Field(..., description="Official bill number")
    title: str = Field(..., min_length=1, max_length=500)
    chamber: Chamber
    status: BillStatus
    
    # Version tracking
    versions: List[BillVersion] = Field(default_factory=list)
    current_version: int = Field(1, ge=1)
    
    # Sponsorship
    sponsor_id: UUID
    co_sponsor_ids: List[UUID] = Field(default_factory=list)
    
    # Related documents
    related_statement_ids: List[UUID] = Field(default_factory=list)
    related_vote_ids: List[UUID] = Field(default_factory=list)
    related_question_ids: List[UUID] = Field(default_factory=list)
    related_petition_ids: List[UUID] = Field(default_factory=list)
    
    # Categorization
    topics: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class VoteDirection(str, Enum):
    """Vote direction"""
    AYE = "aye"
    NO = "no"
    ABSTAIN = "abstain"
    ABSENT = "absent"

class MPVote(BaseModel):
    """Individual MP vote"""
    mp_id: UUID
    direction: VoteDirection

class Vote(BaseModel):
    """Parliamentary vote record"""
    id: UUID = Field(default_factory=uuid4)
    bill_id: UUID
    vote_date: date
    chamber: Chamber
    vote_type: str = Field(..., description="division, voice, etc.")
    
    # Individual votes
    votes: List[MPVote] = Field(default_factory=list)
    
    # Results
    ayes: int = Field(0, ge=0)
    noes: int = Field(0, ge=0)
    abstentions: int = Field(0, ge=0)
    result: str = Field(..., description="passed or failed")
    
    # Source tracking
    source: SourceReference
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

class QuestionType(str, Enum):
    """Question type"""
    ORAL = "oral"
    WRITTEN = "written"

class Question(BaseModel):
    """Parliamentary question"""
    id: UUID = Field(default_factory=uuid4)
    question_number: str
    asker_id: UUID = Field(..., description="MP/Senator who asked")
    respondent_id: Optional[UUID] = Field(None, description="Minister/official")
    question_text: str = Field(..., min_length=1)
    answer_text: Optional[str] = None
    question_date: date
    answer_date: Optional[date] = None
    chamber: Chamber
    
    # Categorization
    question_type: QuestionType
    ministry: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    
    # Source tracking
    source: SourceReference
    vector_doc_id: str
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Petition(BaseModel):
    """Public petition to parliament"""
    id: UUID = Field(default_factory=uuid4)
    petition_number: str
    title: str = Field(..., min_length=1, max_length=500)
    petitioner: str = Field(..., description="Name of petitioner")
    sponsor_id: UUID = Field(..., description="MP/Senator sponsor")
    submission_date: date
    chamber: Chamber
    
    # Content
    petition_text: str = Field(..., min_length=1)
    prayer: str = Field(..., description="What petitioners request")
    
    # Status tracking
    status: str = Field(..., description="submitted, committee_review, etc.")
    committee: Optional[str] = None
    response: Optional[str] = None
    
    # Categorization
    topics: List[str] = Field(default_factory=list)
    
    # Source tracking
    source: SourceReference
    vector_doc_id: str
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Correctness Properties

**Property 2.1**: Source immutability
- **Validates**: Requirements 15.3
- **Property**: SourceReference fields must be immutable after creation
- **Test Strategy**: Attempt to modify source fields, verify frozen model prevents it

**Property 2.2**: UUID uniqueness
- **Validates**: Requirements 3.4
- **Property**: All generated UUIDs must be unique
- **Test Strategy**: Generate 10k documents, verify no UUID collisions

**Property 2.3**: Model serialization
- **Validates**: Requirements 3.6
- **Property**: All models must serialize to/from JSON without data loss
- **Test Strategy**: Round-trip serialize/deserialize, verify equality



## Design 3: Database Schema (SQLAlchemy)

### Component Design

**Purpose**: Relational database schema for structured data with foreign key constraints

**Technology**: SQLAlchemy ORM with Alembic migrations

### Schema Definition

```python
from sqlalchemy import Column, String, Integer, Date, DateTime, Float, Text, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from uuid import uuid4
import enum

Base = declarative_base()

class DocumentTypeEnum(enum.Enum):
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
    NATIONAL_ASSEMBLY = "national_assembly"
    SENATE = "senate"

class DocumentORM(Base):
    """Documents table"""
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
    
    # Metadata (JSON)
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_documents_type_chamber_date', 'type', 'chamber', 'date'),
        Index('idx_documents_source_hash', 'source_hash'),
        Index('idx_documents_date', 'date'),
    )

class MPORM(Base):
    """MPs/Senators table"""
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
        Index('idx_mps_chamber_term', 'chamber', 'parliament_term'),
        Index('idx_mps_name', 'name'),
    )

class StatementORM(Base):
    """Statements table"""
    __tablename__ = "statements"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(PGUUID(as_uuid=True), ForeignKey('documents.id'), nullable=False)
    mp_id = Column(PGUUID(as_uuid=True), ForeignKey('mps.id'), nullable=False)
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
    document = relationship("DocumentORM", backref="statements")
    mp = relationship("MPORM", backref="statements")
    
    # Indexes
    __table_args__ = (
        Index('idx_statements_document_id', 'document_id'),
        Index('idx_statements_mp_id', 'mp_id'),
        Index('idx_statements_classification', 'classification'),
    )

class BillORM(Base):
    """Bills table"""
    __tablename__ = "bills"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bill_number = Column(String(50), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    chamber = Column(SQLEnum(ChamberEnum), nullable=False)
    status = Column(String(50), nullable=False)
    current_version = Column(Integer, default=1)
    
    # Sponsorship
    sponsor_id = Column(PGUUID(as_uuid=True), ForeignKey('mps.id'), nullable=False)
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
    sponsor = relationship("MPORM", backref="sponsored_bills")
    
    # Indexes
    __table_args__ = (
        Index('idx_bills_bill_number', 'bill_number'),
        Index('idx_bills_status', 'status'),
        Index('idx_bills_chamber', 'chamber'),
    )

class BillVersionORM(Base):
    """Bill versions table"""
    __tablename__ = "bill_versions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bill_id = Column(PGUUID(as_uuid=True), ForeignKey('bills.id'), nullable=False)
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
    bill = relationship("BillORM", backref="versions")
    
    # Indexes
    __table_args__ = (
        Index('idx_bill_versions_bill_id', 'bill_id'),
        Index('idx_bill_versions_version', 'bill_id', 'version_number'),
    )

class VoteORM(Base):
    """Votes table"""
    __tablename__ = "votes"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bill_id = Column(PGUUID(as_uuid=True), ForeignKey('bills.id'), nullable=False)
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
    bill = relationship("BillORM", backref="votes")
    
    # Indexes
    __table_args__ = (
        Index('idx_votes_bill_id', 'bill_id'),
        Index('idx_votes_date', 'vote_date'),
    )

class MPVoteORM(Base):
    """Individual MP votes table"""
    __tablename__ = "mp_votes"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    vote_id = Column(PGUUID(as_uuid=True), ForeignKey('votes.id'), nullable=False)
    mp_id = Column(PGUUID(as_uuid=True), ForeignKey('mps.id'), nullable=False)
    direction = Column(String(20), nullable=False)
    
    # Relationships
    vote = relationship("VoteORM", backref="mp_votes")
    mp = relationship("MPORM", backref="votes")
    
    # Indexes
    __table_args__ = (
        Index('idx_mp_votes_vote_id', 'vote_id'),
        Index('idx_mp_votes_mp_id', 'mp_id'),
    )

class QuestionORM(Base):
    """Questions table"""
    __tablename__ = "questions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    question_number = Column(String(50), nullable=False)
    asker_id = Column(PGUUID(as_uuid=True), ForeignKey('mps.id'), nullable=False)
    respondent_id = Column(PGUUID(as_uuid=True), ForeignKey('mps.id'))
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
    asker = relationship("MPORM", foreign_keys=[asker_id], backref="questions_asked")
    respondent = relationship("MPORM", foreign_keys=[respondent_id], backref="questions_answered")
    
    # Indexes
    __table_args__ = (
        Index('idx_questions_asker_id', 'asker_id'),
        Index('idx_questions_date', 'question_date'),
    )

class PetitionORM(Base):
    """Petitions table"""
    __tablename__ = "petitions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    petition_number = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    petitioner = Column(String(200), nullable=False)
    sponsor_id = Column(PGUUID(as_uuid=True), ForeignKey('mps.id'), nullable=False)
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
    sponsor = relationship("MPORM", backref="petitions_sponsored")
    
    # Indexes
    __table_args__ = (
        Index('idx_petitions_sponsor_id', 'sponsor_id'),
        Index('idx_petitions_date', 'submission_date'),
    )
```

### Migration Strategy

**Alembic Configuration**:
```python
# alembic/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from hansard_tales.models import Base

target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

### Correctness Properties

**Property 3.1**: Foreign key integrity
- **Validates**: Requirements 1.6
- **Property**: All foreign key references must point to existing records
- **Test Strategy**: Attempt to create records with invalid foreign keys, verify constraint violations

**Property 3.2**: Unique constraints
- **Validates**: Requirements 1.2
- **Property**: source_hash and bill_number must be unique
- **Test Strategy**: Attempt to insert duplicate values, verify constraint violations

**Property 3.3**: Migration reversibility
- **Validates**: Requirements 1.5
- **Property**: All migrations must be reversible (upgrade/downgrade)
- **Test Strategy**: Apply migration, verify data, downgrade, verify original state



## Design 4: Vector Database Integration

### Component Design

**Purpose**: Semantic search and RAG context retrieval using vector embeddings

**Technology**: ChromaDB (dev) / Qdrant (prod) with sentence-transformers

### Vector Database Interface

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class VectorSearchResult:
    """Result from vector search"""
    id: str
    score: float
    payload: Dict[str, Any]
    text: str

class VectorDB(ABC):
    """Abstract vector database interface"""
    
    @abstractmethod
    def create_collection(self, name: str, dimension: int) -> None:
        """Create a new collection"""
        pass
    
    @abstractmethod
    def insert(
        self,
        collection: str,
        id: str,
        vector: List[float],
        payload: Dict[str, Any],
        text: str
    ) -> None:
        """Insert a vector with metadata"""
        pass
    
    @abstractmethod
    def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Search for similar vectors"""
        pass
    
    @abstractmethod
    def delete(self, collection: str, id: str) -> None:
        """Delete a vector by ID"""
        pass
    
    @abstractmethod
    def get(self, collection: str, id: str) -> Optional[VectorSearchResult]:
        """Get a vector by ID"""
        pass

class ChromaDBAdapter(VectorDB):
    """ChromaDB implementation (development)"""
    
    def __init__(self, persist_directory: str):
        import chromadb
        self.client = chromadb.PersistentClient(path=persist_directory)
    
    def create_collection(self, name: str, dimension: int) -> None:
        self.client.get_or_create_collection(
            name=name,
            metadata={"dimension": dimension}
        )
    
    def insert(
        self,
        collection: str,
        id: str,
        vector: List[float],
        payload: Dict[str, Any],
        text: str
    ) -> None:
        coll = self.client.get_collection(collection)
        coll.add(
            ids=[id],
            embeddings=[vector],
            metadatas=[payload],
            documents=[text]
        )
    
    def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        coll = self.client.get_collection(collection)
        results = coll.query(
            query_embeddings=[query_vector],
            n_results=limit,
            where=filter
        )
        
        return [
            VectorSearchResult(
                id=results['ids'][0][i],
                score=results['distances'][0][i],
                payload=results['metadatas'][0][i],
                text=results['documents'][0][i]
            )
            for i in range(len(results['ids'][0]))
        ]
    
    def delete(self, collection: str, id: str) -> None:
        coll = self.client.get_collection(collection)
        coll.delete(ids=[id])
    
    def get(self, collection: str, id: str) -> Optional[VectorSearchResult]:
        coll = self.client.get_collection(collection)
        result = coll.get(ids=[id])
        if not result['ids']:
            return None
        return VectorSearchResult(
            id=result['ids'][0],
            score=1.0,
            payload=result['metadatas'][0],
            text=result['documents'][0]
        )

class QdrantAdapter(VectorDB):
    """Qdrant implementation (production)"""
    
    def __init__(self, host: str, port: int):
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        self.client = QdrantClient(host=host, port=port)
        self.Distance = Distance
        self.VectorParams = VectorParams
    
    def create_collection(self, name: str, dimension: int) -> None:
        from qdrant_client.models import Distance, VectorParams
        self.client.recreate_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=dimension,
                distance=Distance.COSINE
            )
        )
    
    def insert(
        self,
        collection: str,
        id: str,
        vector: List[float],
        payload: Dict[str, Any],
        text: str
    ) -> None:
        from qdrant_client.models import PointStruct
        payload['text'] = text
        self.client.upsert(
            collection_name=collection,
            points=[PointStruct(id=id, vector=vector, payload=payload)]
        )
    
    def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        qdrant_filter = None
        if filter:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter.items()
            ]
            qdrant_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter
        )
        
        return [
            VectorSearchResult(
                id=str(result.id),
                score=result.score,
                payload=result.payload,
                text=result.payload.get('text', '')
            )
            for result in results
        ]
    
    def delete(self, collection: str, id: str) -> None:
        self.client.delete(
            collection_name=collection,
            points_selector=[id]
        )
    
    def get(self, collection: str, id: str) -> Optional[VectorSearchResult]:
        results = self.client.retrieve(
            collection_name=collection,
            ids=[id]
        )
        if not results:
            return None
        result = results[0]
        return VectorSearchResult(
            id=str(result.id),
            score=1.0,
            payload=result.payload,
            text=result.payload.get('text', '')
        )

def create_vector_db(config: VectorDBConfig) -> VectorDB:
    """Factory function to create vector DB adapter"""
    if config.engine == "chromadb":
        return ChromaDBAdapter(str(config.persist_directory))
    elif config.engine == "qdrant":
        return QdrantAdapter(config.host, config.port)
    else:
        raise ValueError(f"Unknown vector DB engine: {config.engine}")
```

### Embedding Generator

```python
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

class EmbeddingGenerator:
    """Generate embeddings using sentence-transformers"""
    
    def __init__(self, config: EmbeddingConfig):
        self.model = SentenceTransformer(config.model_name, device=config.device)
        self.dimension = config.dimension
        self.batch_size = config.batch_size
    
    def generate(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            show_progress_bar=True
        )
        return embeddings.tolist()
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
```

### Collection Schema

```python
# Collection: documents
DOCUMENTS_COLLECTION = {
    "name": "documents",
    "dimension": 384,
    "payload_schema": {
        "document_id": "str",
        "document_type": "str",
        "chamber": "str",
        "date": "str",
        "session_id": "str",
        "parliament_term": "int",
        "source_url": "str",
        "source_hash": "str",
    }
}

# Collection: statements
STATEMENTS_COLLECTION = {
    "name": "statements",
    "dimension": 384,
    "payload_schema": {
        "statement_id": "str",
        "document_id": "str",
        "mp_id": "str",
        "chamber": "str",
        "date": "str",
        "classification": "str",
        "quality_score": "float",
        "topics": "list[str]",
        "source_url": "str",
        "source_hash": "str",
        "page_number": "int",
        "line_number": "int",
    }
}

# Collection: bills
BILLS_COLLECTION = {
    "name": "bills",
    "dimension": 384,
    "payload_schema": {
        "bill_id": "str",
        "bill_number": "str",
        "version_number": "int",
        "chamber": "str",
        "status": "str",
        "sponsor_id": "str",
        "topics": "list[str]",
        "source_url": "str",
        "source_hash": "str",
    }
}
```

### Correctness Properties

**Property 4.1**: Embedding consistency
- **Validates**: Requirements 2.4
- **Property**: Same text must always generate same embedding
- **Test Strategy**: Generate embeddings for same text multiple times, verify equality

**Property 4.2**: Vector persistence
- **Validates**: Requirements 2.5
- **Property**: Vectors must persist across restarts
- **Test Strategy**: Insert vectors, restart DB, verify vectors still exist

**Property 4.3**: Metadata filtering
- **Validates**: Requirements 2.3
- **Property**: Search with filters must only return matching results
- **Test Strategy**: Insert vectors with various metadata, search with filters, verify results



## Design 5: Web Scrapers

### Component Design

**Purpose**: Automated collection of parliamentary documents from parliament.go.ke

**Technology**: requests + BeautifulSoup4 with retry logic

### Base Scraper Interface

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import hashlib
import requests
from bs4 import BeautifulSoup
import time

@dataclass
class ScrapedDocument:
    """Result of scraping a single document"""
    url: str
    filename: str
    content: bytes
    hash: str
    metadata: dict

class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': config.user_agent})
    
    @abstractmethod
    def get_document_urls(
        self,
        chamber: Chamber,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[str]:
        """Get list of document URLs to download"""
        pass
    
    @abstractmethod
    def extract_metadata(self, url: str, content: bytes) -> dict:
        """Extract metadata from document"""
        pass
    
    def download_document(self, url: str) -> ScrapedDocument:
        """Download a single document with retry logic"""
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(
                    url,
                    timeout=self.config.timeout,
                    stream=True
                )
                response.raise_for_status()
                
                content = response.content
                doc_hash = hashlib.sha256(content).hexdigest()
                filename = self._generate_filename(url)
                metadata = self.extract_metadata(url, content)
                
                return ScrapedDocument(
                    url=url,
                    filename=filename,
                    content=content,
                    hash=doc_hash,
                    metadata=metadata
                )
            
            except requests.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise
                time.sleep(self.config.retry_delay * (2 ** attempt))
    
    def save_document(self, doc: ScrapedDocument, output_dir: Path) -> Path:
        """Save document to disk"""
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / doc.filename
        output_path.write_bytes(doc.content)
        return output_path
    
    def _generate_filename(self, url: str) -> str:
        """Generate filename from URL"""
        return url.split('/')[-1]
    
    def scrape(
        self,
        chamber: Chamber,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip_existing: bool = True
    ) -> List[ScrapedDocument]:
        """Scrape all documents in date range"""
        urls = self.get_document_urls(chamber, start_date, end_date)
        documents = []
        
        for url in urls:
            try:
                doc = self.download_document(url)
                
                # Skip if already downloaded (based on hash)
                if skip_existing and self._is_duplicate(doc.hash):
                    continue
                
                documents.append(doc)
                
            except Exception as e:
                # Log error but continue with remaining documents
                print(f"Error downloading {url}: {e}")
                continue
        
        return documents
    
    def _is_duplicate(self, doc_hash: str) -> bool:
        """Check if document already exists (by hash)"""
        # This will be implemented to check database
        return False

class HansardScraper(BaseScraper):
    """Scraper for Hansard documents"""
    
    def get_document_urls(
        self,
        chamber: Chamber,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[str]:
        """Get Hansard PDF URLs from parliament.go.ke"""
        base_url = f"{self.config.base_url}/the-national-assembly/house-business/hansard"
        if chamber == Chamber.SENATE:
            base_url = f"{self.config.base_url}/the-senate/house-business/hansard"
        
        response = self.session.get(base_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        urls = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.pdf') and 'hansard' in href.lower():
                full_url = href if href.startswith('http') else f"{self.config.base_url}{href}"
                urls.append(full_url)
        
        return urls
    
    def extract_metadata(self, url: str, content: bytes) -> dict:
        """Extract metadata from Hansard PDF"""
        # Extract date from filename (e.g., "hansard-2024-01-15.pdf")
        filename = url.split('/')[-1]
        
        metadata = {
            'document_type': 'hansard',
            'filename': filename,
        }
        
        # Try to extract date from filename
        import re
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
        if date_match:
            metadata['date'] = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
        
        return metadata

class VotesScraper(BaseScraper):
    """Scraper for Votes & Proceedings documents"""
    
    def get_document_urls(
        self,
        chamber: Chamber,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[str]:
        """Get Votes & Proceedings PDF URLs"""
        base_url = f"{self.config.base_url}/the-national-assembly/house-business/votes-and-proceedings"
        if chamber == Chamber.SENATE:
            base_url = f"{self.config.base_url}/the-senate/house-business/votes-and-proceedings"
        
        response = self.session.get(base_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        urls = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.pdf') and 'vote' in href.lower():
                full_url = href if href.startswith('http') else f"{self.config.base_url}{href}"
                urls.append(full_url)
        
        return urls
    
    def extract_metadata(self, url: str, content: bytes) -> dict:
        """Extract metadata from Votes PDF"""
        filename = url.split('/')[-1]
        
        metadata = {
            'document_type': 'votes',
            'filename': filename,
        }
        
        # Try to extract date from filename
        import re
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
        if date_match:
            metadata['date'] = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
        
        return metadata

def create_scraper(document_type: DocumentType, config: ScraperConfig) -> BaseScraper:
    """Factory function to create appropriate scraper"""
    scrapers = {
        DocumentType.HANSARD: HansardScraper,
        DocumentType.VOTES: VotesScraper,
        # More scrapers will be added in later phases
    }
    
    scraper_class = scrapers.get(document_type)
    if not scraper_class:
        raise ValueError(f"No scraper for document type: {document_type}")
    
    return scraper_class(config)
```

### Correctness Properties

**Property 5.1**: Hash uniqueness
- **Validates**: Requirements 4.5
- **Property**: Same PDF content must always generate same hash
- **Test Strategy**: Download same PDF multiple times, verify hash consistency

**Property 5.2**: Duplicate detection
- **Validates**: Requirements 4.6
- **Property**: Already-downloaded documents must be skipped
- **Test Strategy**: Download document, attempt to download again, verify skip

**Property 5.3**: Error resilience
- **Validates**: Requirements 4.7
- **Property**: Single document failure must not stop entire scrape
- **Test Strategy**: Mock failing downloads, verify scraper continues



## Design 6: PDF Processing Pipeline

### Component Design

**Purpose**: Extract text, tables, and metadata from PDF documents with source tracking

**Technology**: PyMuPDF (fitz) for text extraction, pdfplumber for tables

### PDF Processor

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import fitz  # PyMuPDF
import pdfplumber

@dataclass
class ExtractedText:
    """Text extracted from PDF with source tracking"""
    text: str
    page_number: int
    line_number: Optional[int] = None
    bbox: Optional[tuple] = None  # Bounding box (x0, y0, x1, y1)

@dataclass
class ExtractedTable:
    """Table extracted from PDF"""
    data: List[List[str]]
    page_number: int
    bbox: Optional[tuple] = None

@dataclass
class ProcessedPDF:
    """Result of PDF processing"""
    file_path: Path
    file_hash: str
    text_blocks: List[ExtractedText]
    tables: List[ExtractedTable]
    metadata: Dict[str, Any]
    page_count: int

class PDFProcessor:
    """Process PDF documents"""
    
    def __init__(self):
        pass
    
    def process(self, pdf_path: Path) -> ProcessedPDF:
        """Process a PDF file"""
        # Compute hash
        file_hash = self._compute_hash(pdf_path)
        
        # Extract text with source tracking
        text_blocks = self._extract_text(pdf_path)
        
        # Extract tables
        tables = self._extract_tables(pdf_path)
        
        # Extract metadata
        metadata = self._extract_metadata(pdf_path)
        
        # Get page count
        with fitz.open(pdf_path) as doc:
            page_count = len(doc)
        
        return ProcessedPDF(
            file_path=pdf_path,
            file_hash=file_hash,
            text_blocks=text_blocks,
            tables=tables,
            metadata=metadata,
            page_count=page_count
        )
    
    def _compute_hash(self, pdf_path: Path) -> str:
        """Compute SHA256 hash of PDF"""
        import hashlib
        return hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    
    def _extract_text(self, pdf_path: Path) -> List[ExtractedText]:
        """Extract text with page and line tracking"""
        text_blocks = []
        
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                # Get text blocks with bounding boxes
                blocks = page.get_text("blocks")
                
                for block_num, block in enumerate(blocks):
                    if block[6] == 0:  # Text block (not image)
                        text = block[4].strip()
                        if text:
                            text_blocks.append(ExtractedText(
                                text=text,
                                page_number=page_num,
                                line_number=block_num,
                                bbox=(block[0], block[1], block[2], block[3])
                            ))
        
        return text_blocks
    
    def _extract_tables(self, pdf_path: Path) -> List[ExtractedTable]:
        """Extract tables from PDF"""
        tables = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_tables = page.extract_tables()
                
                for table in page_tables:
                    if table:  # Skip empty tables
                        tables.append(ExtractedTable(
                            data=table,
                            page_number=page_num,
                            bbox=None  # pdfplumber doesn't provide bbox easily
                        ))
        
        return tables
    
    def _extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract PDF metadata"""
        with fitz.open(pdf_path) as doc:
            metadata = doc.metadata
            
            return {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
            }
    
    def extract_text_by_page(self, pdf_path: Path, page_number: int) -> str:
        """Extract text from specific page"""
        with fitz.open(pdf_path) as doc:
            if page_number < 1 or page_number > len(doc):
                raise ValueError(f"Invalid page number: {page_number}")
            
            page = doc[page_number - 1]
            return page.get_text()
    
    def search_text(self, pdf_path: Path, query: str) -> List[ExtractedText]:
        """Search for text in PDF"""
        results = []
        
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                text_instances = page.search_for(query)
                
                for inst in text_instances:
                    # Get surrounding text
                    text = page.get_text("text", clip=inst)
                    results.append(ExtractedText(
                        text=text,
                        page_number=page_num,
                        bbox=(inst.x0, inst.y0, inst.x1, inst.y1)
                    ))
        
        return results

class HansardProcessor(PDFProcessor):
    """Specialized processor for Hansard documents"""
    
    def process_hansard(self, pdf_path: Path) -> ProcessedPDF:
        """Process Hansard with MP identification"""
        base_result = self.process(pdf_path)
        
        # Additional Hansard-specific processing
        # This will be expanded in Phase 1
        
        return base_result

class VotesProcessor(PDFProcessor):
    """Specialized processor for Votes & Proceedings"""
    
    def process_votes(self, pdf_path: Path) -> ProcessedPDF:
        """Process Votes with structured data extraction"""
        base_result = self.process(pdf_path)
        
        # Extract vote tables
        # This will be expanded in Phase 1
        
        return base_result
```

### Document Storage Service

```python
from typing import Optional
from datetime import datetime

class DocumentStorageService:
    """Service for storing processed documents"""
    
    def __init__(
        self,
        db_session,
        vector_db: VectorDB,
        embedding_generator: EmbeddingGenerator
    ):
        self.db = db_session
        self.vector_db = vector_db
        self.embedding_generator = embedding_generator
    
    def store_document(
        self,
        processed_pdf: ProcessedPDF,
        document: Document
    ) -> str:
        """Store document in both SQL and vector DB"""
        # Store in SQL database
        doc_orm = DocumentORM(
            id=document.id,
            type=document.type.value,
            chamber=document.chamber.value,
            title=document.title,
            date=document.date,
            session_id=document.session_id,
            parliament_term=document.parliament_term,
            source_url=document.source.source_url,
            source_hash=document.source.source_hash,
            download_date=document.source.download_date,
            vector_doc_id=document.vector_doc_id,
            metadata=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        self.db.add(doc_orm)
        self.db.commit()
        
        # Generate embedding for full document text
        full_text = " ".join([block.text for block in processed_pdf.text_blocks])
        embedding = self.embedding_generator.generate(full_text)
        
        # Store in vector DB
        self.vector_db.insert(
            collection="documents",
            id=document.vector_doc_id,
            vector=embedding,
            payload={
                "document_id": str(document.id),
                "document_type": document.type.value,
                "chamber": document.chamber.value,
                "date": document.date.isoformat(),
                "session_id": document.session_id or "",
                "parliament_term": document.parliament_term,
                "source_url": document.source.source_url,
                "source_hash": document.source.source_hash,
            },
            text=full_text
        )
        
        return str(document.id)
    
    def is_duplicate(self, source_hash: str) -> bool:
        """Check if document already exists"""
        existing = self.db.query(DocumentORM).filter(
            DocumentORM.source_hash == source_hash
        ).first()
        return existing is not None
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """Retrieve document by ID"""
        doc_orm = self.db.query(DocumentORM).filter(
            DocumentORM.id == document_id
        ).first()
        
        if not doc_orm:
            return None
        
        return Document(
            id=doc_orm.id,
            type=DocumentType(doc_orm.type),
            chamber=Chamber(doc_orm.chamber),
            title=doc_orm.title,
            date=doc_orm.date,
            session_id=doc_orm.session_id,
            parliament_term=doc_orm.parliament_term,
            source=SourceReference(
                source_url=doc_orm.source_url,
                source_hash=doc_orm.source_hash,
                download_date=doc_orm.download_date
            ),
            vector_doc_id=doc_orm.vector_doc_id,
            metadata=doc_orm.metadata,
            created_at=doc_orm.created_at,
            updated_at=doc_orm.updated_at
        )
```

### Correctness Properties

**Property 6.1**: Text extraction completeness
- **Validates**: Requirements 5.1
- **Property**: All text in PDF must be extracted
- **Test Strategy**: Create test PDF with known text, verify all text extracted

**Property 6.2**: Source tracking preservation
- **Validates**: Requirements 5.2, 15.2
- **Property**: Page and line numbers must be accurate
- **Test Strategy**: Extract text, verify page/line numbers match PDF

**Property 6.3**: Hash consistency
- **Validates**: Requirements 15.1
- **Property**: Same PDF must always generate same hash
- **Test Strategy**: Process same PDF multiple times, verify hash consistency



## Design 7: Logging Infrastructure

### Component Design

**Purpose**: Structured logging with context tracking for debugging and monitoring

**Technology**: structlog with JSON formatting

### Logging Configuration

```python
import structlog
import logging
from typing import Any, Dict
from datetime import datetime
import sys

def configure_logging(config: LoggingConfig) -> None:
    """Configure structured logging"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout if config.output in ["stdout", "both"] else None,
        level=getattr(logging, config.level)
    )
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if config.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, config.level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

class Logger:
    """Structured logger wrapper"""
    
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message"""
        self.logger.critical(message, **kwargs)
    
    def bind(self, **kwargs: Any) -> 'Logger':
        """Bind context to logger"""
        bound_logger = self.logger.bind(**kwargs)
        new_logger = Logger(self.logger._name)
        new_logger.logger = bound_logger
        return new_logger

def get_logger(name: str) -> Logger:
    """Get logger instance"""
    return Logger(name)

# Usage example
logger = get_logger("hansard_tales.scraper")
logger.info(
    "document_downloaded",
    document_type="hansard",
    chamber="national_assembly",
    date="2024-01-15",
    file_size=1024000,
    duration_ms=1500
)
```

### Request ID Tracking

```python
import uuid
from contextvars import ContextVar

# Context variable for request ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

def generate_request_id() -> str:
    """Generate unique request ID"""
    return str(uuid.uuid4())

def set_request_id(request_id: str) -> None:
    """Set request ID for current context"""
    request_id_var.set(request_id)

def get_request_id() -> str:
    """Get request ID for current context"""
    return request_id_var.get()

# Middleware to add request ID to all logs
def add_request_id(logger, method_name, event_dict):
    """Add request ID to log event"""
    request_id = get_request_id()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict

# Add to structlog processors
structlog.configure(
    processors=[
        add_request_id,
        # ... other processors
    ]
)
```

### Log Rotation

```python
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

def setup_file_logging(config: LoggingConfig) -> None:
    """Setup file logging with rotation"""
    if config.output not in ["file", "both"]:
        return
    
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    handler = TimedRotatingFileHandler(
        filename=log_dir / "hansard_tales.log",
        when="midnight",
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding="utf-8"
    )
    
    handler.setFormatter(
        logging.Formatter('%(message)s')
    )
    
    logging.getLogger().addHandler(handler)
```

### Correctness Properties

**Property 7.1**: Log structure consistency
- **Validates**: Requirements 7.2
- **Property**: All log entries must include required fields
- **Test Strategy**: Generate logs, verify all have timestamp, level, component, message

**Property 7.2**: Request ID propagation
- **Validates**: Requirements 7.6
- **Property**: Request ID must be included in all logs within same operation
- **Test Strategy**: Set request ID, perform operations, verify all logs have same ID



## Design 8: Error Handling

### Component Design

**Purpose**: Consistent error handling with retry logic and graceful degradation

**Technology**: Custom exceptions with tenacity for retries

### Exception Hierarchy

```python
class HansardTalesError(Exception):
    """Base exception for all Hansard Tales errors"""
    pass

class DataCollectionError(HansardTalesError):
    """Error during data collection (scraping)"""
    pass

class ProcessingError(HansardTalesError):
    """Error during document processing"""
    pass

class StorageError(HansardTalesError):
    """Error during data storage"""
    pass

class ConfigurationError(HansardTalesError):
    """Error in configuration"""
    pass

class ValidationError(HansardTalesError):
    """Error in data validation"""
    pass
```

### Retry Logic

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import requests

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException)
)
def download_with_retry(url: str, timeout: int = 30) -> bytes:
    """Download with exponential backoff retry"""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((StorageError, ConnectionError))
)
def store_with_retry(data: Any, storage_func) -> None:
    """Store data with retry"""
    try:
        storage_func(data)
    except Exception as e:
        raise StorageError(f"Failed to store data: {e}") from e
```

### Error Context

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
import traceback

@dataclass
class ErrorContext:
    """Context information for errors"""
    error_type: str
    error_message: str
    stack_trace: str
    component: str
    operation: str
    input_data: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

def capture_error_context(
    error: Exception,
    component: str,
    operation: str,
    input_data: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None
) -> ErrorContext:
    """Capture full error context"""
    return ErrorContext(
        error_type=type(error).__name__,
        error_message=str(error),
        stack_trace=traceback.format_exc(),
        component=component,
        operation=operation,
        input_data=input_data,
        state=state,
        request_id=get_request_id()
    )

def log_error(logger: Logger, error_context: ErrorContext) -> None:
    """Log error with full context"""
    logger.error(
        "operation_failed",
        error_type=error_context.error_type,
        error_message=error_context.error_message,
        component=error_context.component,
        operation=error_context.operation,
        request_id=error_context.request_id,
        input_data=error_context.input_data,
        state=error_context.state,
        stack_trace=error_context.stack_trace
    )
```

### Graceful Degradation

```python
from typing import List, Callable, TypeVar, Generic

T = TypeVar('T')

class BatchProcessor(Generic[T]):
    """Process items in batch with error isolation"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def process_batch(
        self,
        items: List[T],
        process_func: Callable[[T], Any],
        continue_on_error: bool = True
    ) -> tuple[List[Any], List[tuple[T, Exception]]]:
        """Process batch of items, isolating errors"""
        results = []
        errors = []
        
        for item in items:
            try:
                result = process_func(item)
                results.append(result)
            except Exception as e:
                errors.append((item, e))
                
                error_context = capture_error_context(
                    error=e,
                    component="batch_processor",
                    operation="process_item",
                    input_data={"item": str(item)}
                )
                log_error(self.logger, error_context)
                
                if not continue_on_error:
                    raise
        
        return results, errors

# Usage
processor = BatchProcessor(logger)
results, errors = processor.process_batch(
    items=pdf_files,
    process_func=process_pdf,
    continue_on_error=True
)

logger.info(
    "batch_processing_complete",
    total_items=len(pdf_files),
    successful=len(results),
    failed=len(errors)
)
```

### Correctness Properties

**Property 8.1**: Retry exhaustion
- **Validates**: Requirements 8.2
- **Property**: Failed operations must retry exactly max_retries times
- **Test Strategy**: Mock failing operation, verify retry count

**Property 8.2**: Error isolation
- **Validates**: Requirements 8.3
- **Property**: Single item failure must not stop batch processing
- **Test Strategy**: Process batch with one failing item, verify others succeed

**Property 8.3**: Error context completeness
- **Validates**: Requirements 8.4
- **Property**: All errors must be logged with full context
- **Test Strategy**: Trigger errors, verify logs contain all required fields



## Design 9: Testing Infrastructure

### Component Design

**Purpose**: Comprehensive testing with unit, integration, and property-based tests

**Technology**: pytest + Hypothesis + pytest-cov

### Test Structure

```
tests/
├── unit/
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_scrapers.py
│   ├── test_pdf_processor.py
│   └── test_vector_db.py
├── integration/
│   ├── test_scrape_and_store.py
│   ├── test_process_and_embed.py
│   └── test_end_to_end.py
├── property/
│   ├── test_config_properties.py
│   ├── test_model_properties.py
│   ├── test_vector_properties.py
│   └── test_storage_properties.py
├── fixtures/
│   ├── sample_pdfs/
│   ├── sample_configs/
│   └── test_data.py
└── conftest.py
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from hansard_tales.models import Base
from hansard_tales.config import Config, DatabaseConfig, VectorDBConfig

@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def test_config(temp_dir):
    """Create test configuration"""
    return Config(
        environment="test",
        database=DatabaseConfig(
            engine="sqlite",
            database=str(temp_dir / "test.db")
        ),
        vector_db=VectorDBConfig(
            engine="chromadb",
            persist_directory=temp_dir / "vector_db"
        )
    )

@pytest.fixture
def db_session(test_config):
    """Create test database session"""
    engine = create_engine(test_config.database.connection_string)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def vector_db(test_config):
    """Create test vector database"""
    from hansard_tales.vector_db import create_vector_db
    vdb = create_vector_db(test_config.vector_db)
    vdb.create_collection("test_collection", dimension=384)
    yield vdb

@pytest.fixture
def sample_pdf(temp_dir):
    """Create sample PDF for testing"""
    from reportlab.pdfgen import canvas
    
    pdf_path = temp_dir / "sample.pdf"
    c = canvas.Canvas(str(pdf_path))
    c.drawString(100, 750, "Sample Hansard Document")
    c.drawString(100, 700, "This is a test statement by MP John Doe.")
    c.save()
    
    return pdf_path

@pytest.fixture
def sample_document():
    """Create sample document model"""
    from hansard_tales.models import Document, DocumentType, Chamber, SourceReference
    from datetime import date, datetime
    
    return Document(
        type=DocumentType.HANSARD,
        chamber=Chamber.NATIONAL_ASSEMBLY,
        title="Test Hansard",
        date=date(2024, 1, 15),
        parliament_term=13,
        source=SourceReference(
            source_url="https://example.com/test.pdf",
            source_hash="abc123",
            download_date=datetime.utcnow()
        ),
        vector_doc_id="test_doc_1"
    )
```

### Property-Based Tests

```python
# tests/property/test_model_properties.py
from hypothesis import given, strategies as st
from hansard_tales.models import Document, SourceReference
import json

@given(
    title=st.text(min_size=1, max_size=500),
    parliament_term=st.integers(min_value=1, max_value=20)
)
def test_document_serialization_roundtrip(title, parliament_term):
    """Property: Document serialization must be lossless"""
    from datetime import date, datetime
    
    doc = Document(
        type=DocumentType.HANSARD,
        chamber=Chamber.NATIONAL_ASSEMBLY,
        title=title,
        date=date(2024, 1, 15),
        parliament_term=parliament_term,
        source=SourceReference(
            source_url="https://example.com/test.pdf",
            source_hash="abc123",
            download_date=datetime.utcnow()
        ),
        vector_doc_id="test_doc"
    )
    
    # Serialize to JSON
    json_str = doc.model_dump_json()
    
    # Deserialize from JSON
    doc_restored = Document.model_validate_json(json_str)
    
    # Verify equality
    assert doc.title == doc_restored.title
    assert doc.parliament_term == doc_restored.parliament_term

@given(text=st.text(min_size=1))
def test_source_reference_immutability(text):
    """Property: SourceReference must be immutable"""
    from datetime import datetime
    
    source = SourceReference(
        source_url="https://example.com/test.pdf",
        source_hash="abc123",
        download_date=datetime.utcnow()
    )
    
    # Attempt to modify should raise error
    with pytest.raises(Exception):
        source.source_url = text

# tests/property/test_vector_properties.py
@given(
    text=st.text(min_size=10, max_size=1000),
    num_runs=st.integers(min_value=2, max_value=5)
)
def test_embedding_consistency(text, num_runs):
    """Property: Same text must generate same embedding"""
    from hansard_tales.embedding import EmbeddingGenerator
    from hansard_tales.config import EmbeddingConfig
    
    generator = EmbeddingGenerator(EmbeddingConfig())
    
    embeddings = [generator.generate(text) for _ in range(num_runs)]
    
    # All embeddings should be identical
    for i in range(1, num_runs):
        assert embeddings[0] == embeddings[i]

@given(
    texts=st.lists(st.text(min_size=10, max_size=100), min_size=2, max_size=10)
)
def test_vector_search_returns_most_similar(texts):
    """Property: Vector search must return most similar document"""
    from hansard_tales.vector_db import ChromaDBAdapter
    from hansard_tales.embedding import EmbeddingGenerator
    from hansard_tales.config import EmbeddingConfig
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vdb = ChromaDBAdapter(tmpdir)
        vdb.create_collection("test", dimension=384)
        
        generator = EmbeddingGenerator(EmbeddingConfig())
        
        # Insert all texts
        for i, text in enumerate(texts):
            embedding = generator.generate(text)
            vdb.insert(
                collection="test",
                id=f"doc_{i}",
                vector=embedding,
                payload={"index": i},
                text=text
            )
        
        # Search for first text
        query_embedding = generator.generate(texts[0])
        results = vdb.search(
            collection="test",
            query_vector=query_embedding,
            limit=1
        )
        
        # First result should be the query text itself
        assert results[0].text == texts[0]
```

### Coverage Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=hansard_tales
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=90
    -v
markers =
    unit: Unit tests
    integration: Integration tests
    property: Property-based tests
    slow: Slow tests
```

### Correctness Properties

**Property 9.1**: Test isolation
- **Validates**: Requirements 9.6
- **Property**: Tests must not affect each other
- **Test Strategy**: Run tests in random order, verify all pass

**Property 9.2**: Coverage threshold
- **Validates**: Requirements 9.3
- **Property**: Code coverage must be ≥90%
- **Test Strategy**: Run coverage report, verify threshold met



## Design 10: CI/CD Pipeline

### Component Design

**Purpose**: Automated testing, linting, and deployment on every commit

**Technology**: GitHub Actions

### Workflow Configuration

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install ruff mypy
          pip install -e .
      
      - name: Run ruff
        run: ruff check .
      
      - name: Run mypy
        run: mypy hansard_tales

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      
      - name: Run tests
        run: |
          pytest --cov=hansard_tales --cov-report=xml --cov-report=term
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  build:
    runs-on: ubuntu-latest
    needs: [lint, test]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Build package
        run: |
          pip install build
          python -m build
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/

  deploy:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to production
        run: |
          echo "Deployment will be configured in Phase 1"
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml
  
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Correctness Properties

**Property 10.1**: Test execution on commit
- **Validates**: Requirements 10.2
- **Property**: All tests must run on every commit
- **Test Strategy**: Push commit, verify CI runs all tests

**Property 10.2**: Coverage enforcement
- **Validates**: Requirements 10.4
- **Property**: CI must fail if coverage < 90%
- **Test Strategy**: Remove tests to drop coverage, verify CI fails



## Design 11: Development Environment

### Component Design

**Purpose**: Simple local development setup with all dependencies

**Technology**: Docker Compose + Makefile

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: hansard_tales
      POSTGRES_USER: hansard
      POSTGRES_PASSWORD: hansard_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hansard"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./config/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus

volumes:
  postgres_data:
  qdrant_data:
  prometheus_data:
  grafana_data:
```

### Makefile

```makefile
# Makefile
.PHONY: help install dev-setup test lint format clean migrate run

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev-setup    - Setup development environment"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make migrate      - Run database migrations"
	@echo "  make run          - Run application"

install:
	pip install -e .[dev]

dev-setup:
	docker-compose up -d
	sleep 10
	make migrate
	@echo "Development environment ready!"

test:
	pytest --cov=hansard_tales --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

test-property:
	pytest tests/property -v

lint:
	ruff check .
	mypy hansard_tales

format:
	ruff format .

clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

migrate:
	alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	alembic revision --autogenerate -m "$$name"

run:
	python -m hansard_tales.main

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
```

### Requirements Files

```txt
# requirements.txt
# Core dependencies
pydantic>=2.5.0
pydantic-settings>=2.1.0
sqlalchemy>=2.0.0
alembic>=1.13.0
psycopg2-binary>=2.9.0

# Vector DB
chromadb>=0.4.0
qdrant-client>=1.7.0

# Embeddings
sentence-transformers>=2.2.0
torch>=2.1.0

# PDF processing
PyMuPDF>=1.23.0
pdfplumber>=0.10.0

# Web scraping
requests>=2.31.0
beautifulsoup4>=4.12.0

# Logging
structlog>=23.2.0

# Retry logic
tenacity>=8.2.0

# Monitoring
prometheus-client>=0.19.0

# requirements-dev.txt
-r requirements.txt

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
hypothesis>=6.92.0

# Linting
ruff>=0.1.9
mypy>=1.8.0

# Type stubs
types-requests>=2.31.0
types-beautifulsoup4>=4.12.0

# Pre-commit
pre-commit>=3.6.0

# Documentation
mkdocs>=1.5.0
mkdocs-material>=9.5.0
```

### Setup Script

```bash
#!/bin/bash
# scripts/setup.sh

set -e

echo "Setting up Hansard Tales development environment..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version or higher required"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -e .[dev]

# Setup pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Run migrations
echo "Running database migrations..."
alembic upgrade head

echo "Setup complete! Activate virtual environment with: source venv/bin/activate"
```

### Correctness Properties

**Property 11.1**: Environment reproducibility
- **Validates**: Requirements 11.6
- **Property**: Setup script must create identical environments
- **Test Strategy**: Run setup on clean machine, verify all dependencies installed

**Property 11.2**: Service health
- **Validates**: Requirements 11.2
- **Property**: All Docker services must be healthy after startup
- **Test Strategy**: Start services, check health endpoints



## Design 12: Monitoring Setup

### Component Design

**Purpose**: Track system health and performance metrics

**Technology**: Prometheus + Grafana + Sentry

### Metrics Exporter

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from functools import wraps

# Define metrics
documents_processed = Counter(
    'documents_processed_total',
    'Total number of documents processed',
    ['document_type', 'chamber', 'status']
)

processing_time = Histogram(
    'document_processing_seconds',
    'Time spent processing documents',
    ['document_type', 'chamber']
)

error_count = Counter(
    'errors_total',
    'Total number of errors',
    ['component', 'error_type']
)

queue_depth = Gauge(
    'processing_queue_depth',
    'Number of documents in processing queue',
    ['document_type']
)

vector_db_size = Gauge(
    'vector_db_documents_total',
    'Total number of documents in vector DB',
    ['collection']
)

def track_processing_time(document_type: str, chamber: str):
    """Decorator to track processing time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                processing_time.labels(
                    document_type=document_type,
                    chamber=chamber
                ).observe(duration)
                documents_processed.labels(
                    document_type=document_type,
                    chamber=chamber,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                duration = time.time() - start
                processing_time.labels(
                    document_type=document_type,
                    chamber=chamber
                ).observe(duration)
                documents_processed.labels(
                    document_type=document_type,
                    chamber=chamber,
                    status='error'
                ).inc()
                error_count.labels(
                    component='processor',
                    error_type=type(e).__name__
                ).inc()
                raise
        return wrapper
    return decorator

# Usage
@track_processing_time('hansard', 'national_assembly')
def process_hansard(pdf_path: Path) -> ProcessedPDF:
    # Processing logic
    pass

def start_metrics_server(port: int = 9090):
    """Start Prometheus metrics server"""
    start_http_server(port)
```

### Prometheus Configuration

```yaml
# config/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'hansard_tales'
    static_configs:
      - targets: ['localhost:9090']
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    
  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Hansard Tales - System Overview",
    "panels": [
      {
        "title": "Documents Processed",
        "targets": [
          {
            "expr": "rate(documents_processed_total[5m])"
          }
        ]
      },
      {
        "title": "Processing Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(document_processing_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(errors_total[5m])"
          }
        ]
      },
      {
        "title": "Queue Depth",
        "targets": [
          {
            "expr": "processing_queue_depth"
          }
        ]
      }
    ]
  }
}
```

### Sentry Integration

```python
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

def configure_sentry(config: MonitoringConfig):
    """Configure Sentry error tracking"""
    if not config.sentry_enabled:
        return
    
    sentry_sdk.init(
        dsn=config.sentry_dsn,
        environment=config.environment,
        traces_sample_rate=0.1,
        integrations=[
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            )
        ]
    )

# Usage
try:
    process_document(pdf_path)
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```

### Health Check Endpoint

```python
from fastapi import FastAPI
from typing import Dict, Any

app = FastAPI()

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    checks = {
        "database": check_database_health(),
        "vector_db": check_vector_db_health(),
        "disk_space": check_disk_space(),
    }
    
    all_healthy = all(checks.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks
    }

def check_database_health() -> bool:
    """Check database connectivity"""
    try:
        # Attempt simple query
        return True
    except:
        return False

def check_vector_db_health() -> bool:
    """Check vector DB connectivity"""
    try:
        # Attempt simple query
        return True
    except:
        return False

def check_disk_space() -> bool:
    """Check available disk space"""
    import shutil
    stat = shutil.disk_usage("/")
    free_gb = stat.free / (1024**3)
    return free_gb > 10  # At least 10GB free
```

### Correctness Properties

**Property 12.1**: Metrics accuracy
- **Validates**: Requirements 12.2
- **Property**: Metrics must accurately reflect system state
- **Test Strategy**: Process documents, verify metrics match actual counts

**Property 12.2**: Health check reliability
- **Validates**: Requirements 12.4
- **Property**: Health check must detect service failures
- **Test Strategy**: Stop services, verify health check reports unhealthy



## Design 13: Documentation

### Component Design

**Purpose**: Comprehensive documentation for developers and operators

**Technology**: Markdown + MkDocs

### Documentation Structure

```
docs/
├── index.md                    # Overview
├── getting-started/
│   ├── installation.md
│   ├── quickstart.md
│   └── configuration.md
├── architecture/
│   ├── overview.md
│   ├── data-models.md
│   ├── storage.md
│   ├── processing-pipeline.md
│   └── adrs/                   # Architectural Decision Records
│       ├── 001-database-selection.md
│       ├── 002-vector-db-selection.md
│       └── ...
├── development/
│   ├── setup.md
│   ├── testing.md
│   ├── code-style.md
│   └── contributing.md
├── operations/
│   ├── deployment.md
│   ├── monitoring.md
│   ├── troubleshooting.md
│   └── maintenance.md
└── api/
    ├── models.md
    ├── scrapers.md
    ├── processors.md
    └── storage.md
```

### MkDocs Configuration

```yaml
# mkdocs.yml
site_name: Hansard Tales Documentation
site_description: Parliamentary accountability platform for Kenya
site_author: Hansard Tales Team
repo_url: https://github.com/hansard-tales/hansard-tales

theme:
  name: material
  palette:
    primary: indigo
    accent: indigo
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest
    - search.highlight

nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Quick Start: getting-started/quickstart.md
      - Configuration: getting-started/configuration.md
  - Architecture:
      - Overview: architecture/overview.md
      - Data Models: architecture/data-models.md
      - Storage: architecture/storage.md
      - Processing Pipeline: architecture/processing-pipeline.md
      - ADRs: architecture/adrs/
  - Development:
      - Setup: development/setup.md
      - Testing: development/testing.md
      - Code Style: development/code-style.md
      - Contributing: development/contributing.md
  - Operations:
      - Deployment: operations/deployment.md
      - Monitoring: operations/monitoring.md
      - Troubleshooting: operations/troubleshooting.md
      - Maintenance: operations/maintenance.md
  - API Reference:
      - Models: api/models.md
      - Scrapers: api/scrapers.md
      - Processors: api/processors.md
      - Storage: api/storage.md

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: true
            show_root_heading: true

markdown_extensions:
  - admonition
  - codehilite
  - pymdownx.superfences
  - pymdownx.tabbed
  - toc:
      permalink: true
```

### README Template

```markdown
# Hansard Tales

Parliamentary accountability platform for Kenya, tracking all activities from both the National Assembly and Senate.

## Features

- 📄 **22 Document Types**: Hansard, Bills, Votes, Questions, Petitions, and more
- 🤖 **AI-Powered Analysis**: Statement classification, sentiment analysis, quality scoring
- 🔍 **Semantic Search**: Find relevant context across all parliamentary documents
- 📊 **Comprehensive Tracking**: MP/Senator performance, party positions, bill lifecycle
- 🚫 **Anti-Hallucination**: Immutable source tracking with citation verification

## Quick Start

```bash
# Clone repository
git clone https://github.com/hansard-tales/hansard-tales.git
cd hansard-tales

# Run setup script
./scripts/setup.sh

# Activate virtual environment
source venv/bin/activate

# Start development environment
make dev-setup

# Run tests
make test
```

## Documentation

Full documentation available at: https://docs.hansard-tales.org

## Architecture

See [ARCHITECTURE.md](docs/architecture/overview.md) for detailed system design.

## Contributing

See [CONTRIBUTING.md](docs/development/contributing.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
```

### ADR Template

```markdown
# ADR-XXX: [Title]

## Status

[Proposed | Accepted | Deprecated | Superseded]

## Context

[Describe the problem and context]

## Decision

[Describe the decision]

## Consequences

### Positive

- [Benefit 1]
- [Benefit 2]

### Negative

- [Trade-off 1]
- [Trade-off 2]

## Alternatives Considered

### Option 1: [Name]

**Pros:**
- [Pro 1]

**Cons:**
- [Con 1]

**Cost:** [Cost analysis]

### Option 2: [Name]

[Same structure]

## Cost Analysis

[Detailed cost breakdown]

## References

- [Link 1]
- [Link 2]
```

### Correctness Properties

**Property 13.1**: Documentation completeness
- **Validates**: Requirements 13.1-13.5
- **Property**: All public APIs must have documentation
- **Test Strategy**: Check all public functions have docstrings

**Property 13.2**: ADR coverage
- **Validates**: Requirements 13.6
- **Property**: All major architectural decisions must have ADRs
- **Test Strategy**: Verify ADRs exist for all decisions in master architecture



## Implementation Strategy

### Phase 0 Implementation Order

The implementation should follow this order to minimize dependencies and enable incremental testing:

**Week 1: Core Infrastructure**

1. **Day 1-2: Configuration and Models**
   - Implement configuration management (Design 1)
   - Implement data models (Design 2)
   - Write unit tests for both
   - Property tests for model serialization

2. **Day 3-4: Database Setup**
   - Implement SQLAlchemy schema (Design 3)
   - Setup Alembic migrations
   - Write database tests
   - Property tests for foreign key integrity

3. **Day 5-7: Vector Database**
   - Implement vector DB adapters (Design 4)
   - Implement embedding generator
   - Write vector DB tests
   - Property tests for embedding consistency

**Week 2: Collection and Processing**

4. **Day 8-9: Web Scrapers**
   - Implement base scraper (Design 5)
   - Implement Hansard and Votes scrapers
   - Write scraper tests
   - Property tests for hash uniqueness

5. **Day 10-11: PDF Processing**
   - Implement PDF processor (Design 6)
   - Implement document storage service
   - Write processing tests
   - Property tests for source tracking

6. **Day 12-13: Infrastructure**
   - Implement logging (Design 7)
   - Implement error handling (Design 8)
   - Setup CI/CD (Design 10)
   - Setup development environment (Design 11)

7. **Day 14: Monitoring and Documentation**
   - Setup monitoring (Design 12)
   - Write documentation (Design 13)
   - Final integration tests
   - Review and polish

### Testing Strategy

**Unit Tests** (≥90% coverage):
- Test each component in isolation
- Mock external dependencies
- Fast execution (< 1 second per test)

**Integration Tests**:
- Test component interactions
- Use real databases (test instances)
- Test end-to-end workflows

**Property-Based Tests**:
- Test invariants and properties
- Generate random test cases
- Verify correctness properties

**Test Execution Order**:
1. Unit tests (fast feedback)
2. Property tests (thorough verification)
3. Integration tests (full system validation)

### Deployment Strategy

**Development Environment**:
- SQLite + ChromaDB (local files)
- Docker Compose for services
- Local Python virtual environment

**Staging Environment** (optional):
- PostgreSQL + Qdrant (Docker)
- Same infrastructure as production
- Test with production-like data

**Production Environment** (Phase 1+):
- PostgreSQL (self-hosted or RDS)
- Qdrant (self-hosted or cloud)
- GitHub Actions for processing
- Cloudflare Pages for static site

### Migration Path

**From SQLite to PostgreSQL**:
```python
# Export from SQLite
sqlite_engine = create_engine('sqlite:///data/hansard.db')
sqlite_session = sessionmaker(bind=sqlite_engine)()

# Import to PostgreSQL
pg_engine = create_engine('postgresql://...')
pg_session = sessionmaker(bind=pg_engine)()

# Copy data
for table in Base.metadata.sorted_tables:
    data = sqlite_session.execute(table.select()).fetchall()
    pg_session.execute(table.insert(), data)
    pg_session.commit()
```

**From ChromaDB to Qdrant**:
```python
# Export from ChromaDB
chroma = ChromaDBAdapter('data/vector_db')
collection = chroma.client.get_collection('documents')
all_docs = collection.get()

# Import to Qdrant
qdrant = QdrantAdapter('localhost', 6333)
qdrant.create_collection('documents', dimension=384)

for i, (id, embedding, metadata, text) in enumerate(zip(
    all_docs['ids'],
    all_docs['embeddings'],
    all_docs['metadatas'],
    all_docs['documents']
)):
    qdrant.insert('documents', id, embedding, metadata, text)
```

## Summary of Correctness Properties

This design includes 26 correctness properties across all components:

| Component | Properties | Test Strategy |
|-----------|-----------|---------------|
| Configuration | 2 | Validation, environment override |
| Data Models | 3 | Immutability, serialization, UUID uniqueness |
| Database | 3 | Foreign keys, unique constraints, migrations |
| Vector DB | 3 | Embedding consistency, persistence, filtering |
| Scrapers | 3 | Hash uniqueness, duplicate detection, error resilience |
| PDF Processing | 3 | Text extraction, source tracking, hash consistency |
| Logging | 2 | Structure consistency, request ID propagation |
| Error Handling | 3 | Retry exhaustion, error isolation, context completeness |
| Testing | 2 | Test isolation, coverage threshold |
| CI/CD | 2 | Test execution, coverage enforcement |
| Development | 2 | Environment reproducibility, service health |
| Monitoring | 2 | Metrics accuracy, health check reliability |
| Documentation | 2 | Completeness, ADR coverage |

**Total: 32 properties** to be validated through property-based testing.

## Next Steps

After completing Phase 0 design:

1. **Review Design**: Ensure all requirements are addressed
2. **Create Tasks**: Break down design into implementation tasks
3. **Implement**: Follow implementation order
4. **Test**: Verify all correctness properties
5. **Document**: Update documentation as implementation progresses
6. **Deploy**: Setup development environment
7. **Proceed to Phase 1**: Core analysis pipeline

## References

- [MASTER_ARCHITECTURE.md](../MASTER_ARCHITECTURE.md) - Complete system architecture
- [requirements.md](requirements.md) - Phase 0 requirements
- [DOCUMENT_FLOW.md](../DOCUMENT_FLOW.md) - Data flow architecture
- [README.md](../README.md) - Project overview

