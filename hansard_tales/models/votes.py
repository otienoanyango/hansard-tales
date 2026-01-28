"""
Vote-related data models.

This module defines models for parliamentary votes and proceedings.
"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List
from enum import Enum
from uuid import UUID, uuid4

from hansard_tales.models.base import Chamber, SourceReference


class VoteDirection(str, Enum):
    """Vote direction."""
    
    AYE = "aye"
    NO = "no"
    ABSTAIN = "abstain"
    ABSENT = "absent"


class MPVote(BaseModel):
    """Individual MP vote."""
    
    mp_id: UUID
    direction: VoteDirection


class Vote(BaseModel):
    """
    Parliamentary vote record.
    
    Represents a vote on a bill or motion, including individual
    MP votes and aggregate results.
    """
    
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
