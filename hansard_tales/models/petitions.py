"""
Petition-related data models.

This module defines models for public petitions to parliament.
"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List
from uuid import UUID, uuid4

from hansard_tales.models.base import Chamber, SourceReference


class Petition(BaseModel):
    """
    Public petition to parliament.
    
    Represents a petition submitted by citizens to parliament,
    sponsored by an MP/Senator.
    """
    
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
    committee: str | None = None
    response: str | None = None
    
    # Categorization
    topics: List[str] = Field(default_factory=list)
    
    # Source tracking
    source: SourceReference
    vector_doc_id: str
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
