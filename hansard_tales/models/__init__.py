"""
Data models for Hansard Tales.

This module provides Pydantic models for all parliamentary documents
with immutable source tracking for anti-hallucination.
"""

from hansard_tales.models.base import (
    Chamber,
    DocumentType,
    SourceReference,
    Document,
    Statement,
)
from hansard_tales.models.bills import (
    BillStatus,
    BillVersion,
    Bill,
)
from hansard_tales.models.votes import (
    VoteDirection,
    MPVote,
    Vote,
)
from hansard_tales.models.questions import (
    QuestionType,
    Question,
)
from hansard_tales.models.petitions import (
    Petition,
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
