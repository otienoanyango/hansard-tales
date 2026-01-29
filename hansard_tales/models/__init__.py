"""
Data models for Hansard Tales.

This module provides Pydantic models for all parliamentary documents
with immutable source tracking for anti-hallucination.
"""

from hansard_tales.models.base import (
    Chamber,
    Document,
    DocumentType,
    SourceReference,
    Statement,
)
from hansard_tales.models.bills import (
    Bill,
    BillStatus,
    BillVersion,
)
from hansard_tales.models.petitions import (
    Petition,
)
from hansard_tales.models.questions import (
    Question,
    QuestionType,
)
from hansard_tales.models.votes import (
    MPVote,
    Vote,
    VoteDirection,
)

__all__ = [
    # Base models
    "Chamber",
    "DocumentType",
    "SourceReference",
    "Document",
    "Statement",
    # Bill models
    "BillStatus",
    "BillVersion",
    "Bill",
    # Vote models
    "VoteDirection",
    "MPVote",
    "Vote",
    # Question models
    "QuestionType",
    "Question",
    # Petition models
    "Petition",
]
