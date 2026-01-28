"""
Base data models for parliamentary documents.

This module defines the core Pydantic models used throughout the system,
including immutable source tracking for anti-hallucination.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID, uuid4


class Chamber(str, Enum):
    """Parliamentary chamber."""
    
    NATIONAL_ASSEMBLY = "national_assembly"
    SENATE = "senate"


class DocumentType(str, Enum):
    """Parliamentary document types."""
    
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
    """
    Immutable source tracking (anti-hallucination).
    
    This model ensures all data can be traced back to original documents.
    Fields are frozen to prevent modification after creation.
    """
    
    model_config = ConfigDict(frozen=True)
    
    source_url: str = Field(..., description="Original document URL")
    source_hash: str = Field(..., description="SHA256 hash of original PDF")
    download_date: datetime = Field(default_factory=datetime.utcnow)
    page_number: Optional[int] = Field(None, description="Page in source PDF")
    line_number: Optional[int] = Field(None, description="Line on page")


class Document(BaseModel):
    """
    Base document model for all parliamentary documents.
    
    This model provides common fields for all document types with
    immutable source tracking.
    """
    
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
    """
    Parliamentary statement from Hansard.
    
    Represents a single statement made by an MP or Senator during
    parliamentary proceedings.
    """
    
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
