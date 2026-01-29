"""
Question-related data models.

This module defines models for parliamentary questions.
"""

from datetime import UTC, date, datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from hansard_tales.models.base import Chamber, SourceReference


class QuestionType(str, Enum):
    """Question type."""

    ORAL = "oral"
    WRITTEN = "written"


class Question(BaseModel):
    """
    Parliamentary question.

    Represents a question asked by an MP/Senator to a minister
    or government official.
    """

    id: UUID = Field(default_factory=uuid4)
    question_number: str
    asker_id: UUID = Field(..., description="MP/Senator who asked")
    respondent_id: UUID | None = Field(None, description="Minister/official")
    question_text: str = Field(..., min_length=1)
    answer_text: str | None = None
    question_date: date
    answer_date: date | None = None
    chamber: Chamber

    # Categorization
    question_type: QuestionType
    ministry: str | None = None
    topics: list[str] = Field(default_factory=list)

    # Source tracking
    source: SourceReference
    vector_doc_id: str

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
