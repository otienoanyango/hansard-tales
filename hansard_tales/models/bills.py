"""
Bill-related data models.

This module defines models for parliamentary bills, including
version tracking for amendments.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from enum import Enum
from uuid import UUID, uuid4

from hansard_tales.models.base import Chamber, SourceReference


class BillStatus(str, Enum):
    """Bill lifecycle status."""
    
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
    """
    Version of a bill (for amendment tracking).
    
    Each time a bill is amended, a new version is created to track
    the changes over time.
    """
    
    version_number: int = Field(..., ge=1)
    title: str
    text: str
    source: SourceReference
    vector_doc_id: str
    changes_summary: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Bill(BaseModel):
    """
    Parliamentary bill.
    
    Represents a proposed law with version tracking, sponsorship,
    and related documents.
    """
    
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
