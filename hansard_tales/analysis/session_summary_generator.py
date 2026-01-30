"""
Session summary generation for parliamentary sessions.

This module provides functionality to generate comprehensive summaries
of parliamentary sessions using LLM-powered analysis.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class SessionSummary:
    """
    Summary of a parliamentary session.

    This dataclass captures all key information about a session including
    overview, key events, participation metrics, and main topics.
    """

    session_id: str
    date: date
    session_type: str  # "morning", "afternoon", "evening"

    # Overview
    title: str
    summary: str  # 2-3 paragraphs

    # Key events
    key_debates: list[str] = field(default_factory=list)
    bills_discussed: list[str] = field(default_factory=list)
    votes_held: list[str] = field(default_factory=list)

    # Participation
    total_mps_present: int = 0
    total_statements: int = 0

    # Topics
    main_topics: list[str] = field(default_factory=list)


class SessionSummaryGenerator:
    """
    Generate comprehensive summaries of parliamentary sessions.

    This class aggregates session data and uses LLM to generate
    human-readable summaries with structured information about
    debates, bills, votes, and participation.

    Example:
        >>> from hansard_tales.analysis.llm_analyzer import LLMAnalyzer
        >>> llm = LLMAnalyzer(api_key="sk-...")
        >>> generator = SessionSummaryGenerator(db_session, llm)
        >>> summary = generator.generate_summary("session-123")
        >>> print(summary.title)
        'Healthcare Budget Debate - December 2024'
    """

    def __init__(self, db_session: Any, llm_analyzer: Any):
        """
        Initialize session summary generator.

        Args:
            db_session: SQLAlchemy database session
            llm_analyzer: LLMAnalyzer instance for generating summaries
        """
        self.db = db_session
        self.llm = llm_analyzer

    def generate_summary(self, session_id: str) -> SessionSummary:
        """
        Generate comprehensive summary for a session.

        Args:
            session_id: ID of the session to summarize

        Returns:
            SessionSummary with all session information

        Raises:
            ValueError: If session not found

        Example:
            >>> summary = generator.generate_summary("session-123")
            >>> print(f"Session: {summary.title}")
            >>> print(f"MPs present: {summary.total_mps_present}")
        """
        # Fetch session data (sessions are stored as documents)
        from hansard_tales.database.models import DocumentORM

        session = self.db.query(DocumentORM).filter(DocumentORM.session_id == session_id).first()

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Aggregate statements
        statements = self._aggregate_statements(session_id)

        # Generate LLM summary
        summary_text = self._generate_llm_summary(session, statements)

        # Parse structured data
        return self._parse_summary(session, statements, summary_text)

    def _aggregate_statements(self, session_id: str) -> list[Any]:
        """
        Aggregate substantive statements for a session.

        Args:
            session_id: Session ID

        Returns:
            List of substantive statement records
        """
        from hansard_tales.database.models import StatementORM

        statements = (
            self.db.query(StatementORM)
            .filter(
                StatementORM.session_id == session_id,
                StatementORM.classification == "substantive",
            )
            .all()
        )

        return statements

    def _generate_llm_summary(self, session: Any, statements: list[Any]) -> str:
        """
        Generate summary using LLM.

        Args:
            session: Session ORM object (DocumentORM)
            statements: List of statement ORM objects

        Returns:
            JSON string with summary data
        """
        # Build context from statements
        context_parts = []
        for s in statements[:20]:  # Limit to top 20 statements
            mp_name = s.mp.name if hasattr(s, "mp") and s.mp else "Unknown MP"
            # Get topics from JSON metadata
            topics = s.topics if hasattr(s, "topics") and s.topics else {}
            primary_topic = (
                topics.get("primary", "Unknown") if isinstance(topics, dict) else "Unknown"
            )
            # Get key points from JSON metadata
            related_data = s.related_bill_ids if hasattr(s, "related_bill_ids") else {}
            key_points = (
                related_data.get("key_points", []) if isinstance(related_data, dict) else []
            )

            context_parts.append(
                f"MP: {mp_name}\nTopic: {primary_topic}\nKey points: {', '.join(key_points[:3])}"
            )

        context = "\n\n".join(context_parts)

        # Get session type from metadata
        session_type = (
            session.doc_metadata.get("session_type", "unknown")
            if hasattr(session, "doc_metadata")
            else "unknown"
        )

        # Build prompt
        prompt = f"""Summarize this parliamentary session:

Date: {session.date}
Type: {session_type}

Key statements:
{context}

Provide:
1. A title for the session (5-10 words)
2. A 2-3 paragraph summary of main discussions
3. List of key debates (3-5 items)
4. Main topics discussed (3-5 topics)

Format as JSON:
{{
  "title": "...",
  "summary": "...",
  "key_debates": ["...", "..."],
  "main_topics": ["...", "..."]
}}"""

        # Call LLM
        response = self.llm.client.messages.create(
            model=self.llm.model,
            max_tokens=1024,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def _parse_summary(
        self, session: Any, statements: list[Any], summary_text: str
    ) -> SessionSummary:
        """
        Parse LLM output into structured summary.

        Args:
            session: Session ORM object (DocumentORM)
            statements: List of statement ORM objects
            summary_text: JSON string from LLM

        Returns:
            SessionSummary object

        Raises:
            ValueError: If summary_text cannot be parsed
        """
        # Extract JSON from response (may be wrapped in markdown)
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", summary_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r"\{.*\}", summary_text, re.DOTALL)
            if not json_match:
                raise ValueError(f"No JSON found in summary: {summary_text[:200]}")
            json_str = json_match.group(0)

        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in summary: {e}") from e

        # Get bills discussed
        bills = self._get_bills_discussed(statements)

        # Get votes held
        votes = self._get_votes_held(
            session.session_id if hasattr(session, "session_id") else str(session.id)
        )

        # Calculate participation
        total_mps_present = len({s.mp_id for s in statements if hasattr(s, "mp_id")})

        # Get session type from metadata
        session_type = (
            session.doc_metadata.get("session_type", "unknown")
            if hasattr(session, "doc_metadata")
            else "unknown"
        )

        return SessionSummary(
            session_id=session.session_id if hasattr(session, "session_id") else str(session.id),
            date=session.date,
            session_type=session_type,
            title=data.get("title", "Parliamentary Session"),
            summary=data.get("summary", ""),
            key_debates=data.get("key_debates", []),
            bills_discussed=bills,
            votes_held=votes,
            total_mps_present=total_mps_present,
            total_statements=len(statements),
            main_topics=data.get("main_topics", []),
        )

    def _get_bills_discussed(self, statements: list[Any]) -> list[str]:
        """
        Get list of bills discussed in statements.

        Args:
            statements: List of statement ORM objects

        Returns:
            List of bill titles
        """
        from hansard_tales.database.models import BillORM

        # Get statement IDs
        statement_ids = [s.id for s in statements]

        if not statement_ids:
            return []

        # Get bills from related_bill_ids in statements
        bill_ids = set()
        for s in statements:
            if hasattr(s, "related_bill_ids") and s.related_bill_ids:
                # related_bill_ids is stored as JSON
                if isinstance(s.related_bill_ids, str):
                    try:
                        ids = json.loads(s.related_bill_ids)
                        if isinstance(ids, list):
                            bill_ids.update(ids)
                    except json.JSONDecodeError:
                        pass
                elif isinstance(s.related_bill_ids, list):
                    bill_ids.update(s.related_bill_ids)

        if not bill_ids:
            return []

        # Query bills
        bills = self.db.query(BillORM).filter(BillORM.id.in_(bill_ids)).all()

        return [b.title for b in bills]

    def _get_votes_held(self, session_id: str) -> list[str]:
        """
        Get list of votes held in session.

        Args:
            session_id: Session ID

        Returns:
            List of vote motion texts
        """
        from hansard_tales.database.models import VoteORM

        votes = self.db.query(VoteORM).filter(VoteORM.session_id == session_id).all()

        return [v.motion_text for v in votes if hasattr(v, "motion_text")]

    def generate_batch(self, session_ids: list[str]) -> list[SessionSummary]:
        """
        Generate summaries for multiple sessions.

        Args:
            session_ids: List of session IDs

        Returns:
            List of SessionSummary objects (same order as input)

        Example:
            >>> session_ids = ["session-1", "session-2", "session-3"]
            >>> summaries = generator.generate_batch(session_ids)
            >>> print(f"Generated {len(summaries)} summaries")
        """
        results = []

        for session_id in session_ids:
            try:
                summary = self.generate_summary(session_id)
                results.append(summary)
            except Exception as e:
                # Log error but continue processing
                print(f"Error generating summary for {session_id}: {e}")
                # Create error summary
                results.append(
                    SessionSummary(
                        session_id=session_id,
                        date=date.today(),
                        session_type="unknown",
                        title=f"Error: {str(e)[:50]}",
                        summary="Summary generation failed",
                        key_debates=[],
                        bills_discussed=[],
                        votes_held=[],
                        total_mps_present=0,
                        total_statements=0,
                        main_topics=[],
                    )
                )

        return results
