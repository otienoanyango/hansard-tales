"""
Base data models for parliamentary documents.

This module defines the core Pydantic models used throughout the system,
including immutable source tracking for anti-hallucination.
"""

from datetime import UTC, date, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


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
    download_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    page_number: int | None = Field(None, description="Page in source PDF")
    line_number: int | None = Field(None, description="Line on page")


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
    session_id: str | None = None
    parliament_term: int = Field(..., ge=1, le=20)

    # Source tracking (immutable)
    source: SourceReference

    # Vector DB reference
    vector_doc_id: str = Field(..., description="ID in vector database")

    # Metadata (varies by document type)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


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
    timestamp: datetime | None = None

    # Source tracking (immutable)
    source: SourceReference

    # Vector DB reference
    vector_doc_id: str

    # Analysis results (populated by pipeline)
    classification: str | None = Field(None, description="filler or substantive")
    sentiment: str | None = Field(None, description="support, oppose, neutral")
    quality_score: float | None = Field(None, ge=0, le=100)
    topics: list[str] = Field(default_factory=list)
    related_bill_ids: list[UUID] = Field(default_factory=list)
    related_question_ids: list[UUID] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
