"""
MP profile generation from aggregated parliamentary data.

This module generates comprehensive MP profiles including:
- Activity metrics (statements, votes, attendance)
- Topic analysis (top topics discussed)
- Bill involvement (sponsored, discussed)
- Sentiment analysis
- LLM-generated summary

All profiles are generated from database aggregations with optional
LLM summarization for narrative descriptions.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MPProfile:
    """
    Comprehensive MP profile from aggregated data.

    This dataclass contains all information about an MP's parliamentary
    activity including statements, votes, topics, bills, and a generated
    summary.

    Example:
        >>> profile = MPProfile(
        ...     mp_id="123",
        ...     name="Hon. John Doe",
        ...     constituency="Nairobi West",
        ...     party="UDA",
        ...     total_statements=150,
        ...     substantive_statements=120,
        ...     avg_quality_score=75.5
        ... )
        >>> print(f"{profile.name}: {profile.total_statements} statements")
    """

    # Basic MP information
    mp_id: str
    name: str
    constituency: str
    party: str

    # Activity metrics
    total_statements: int = 0
    substantive_statements: int = 0
    avg_quality_score: float = 0.0

    # Participation metrics
    sessions_attended: int = 0
    votes_cast: int = 0
    votes_aye: int = 0
    votes_no: int = 0
    votes_abstain: int = 0

    # Topic analysis (topic, count)
    top_topics: list[tuple[str, int]] = field(default_factory=list)

    # Bill involvement
    bills_sponsored: list[str] = field(default_factory=list)
    bills_discussed: list[str] = field(default_factory=list)

    # Sentiment analysis
    avg_sentiment: str = "neutral"
    sentiment_distribution: dict[str, int] = field(default_factory=dict)

    # Generated content
    summary: str = ""
    key_positions: list[str] = field(default_factory=list)

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate profile data after initialization."""
        # Ensure quality score is in valid range
        if self.avg_quality_score < 0:
            self.avg_quality_score = 0.0
        elif self.avg_quality_score > 100:
            self.avg_quality_score = 100.0

        # Ensure vote counts are non-negative
        if self.votes_cast < 0:
            self.votes_cast = 0
        if self.votes_aye < 0:
            self.votes_aye = 0
        if self.votes_no < 0:
            self.votes_no = 0
        if self.votes_abstain < 0:
            self.votes_abstain = 0

        # Ensure statement counts are non-negative
        if self.total_statements < 0:
            self.total_statements = 0
        if self.substantive_statements < 0:
            self.substantive_statements = 0

        # Ensure substantive statements don't exceed total
        if self.substantive_statements > self.total_statements:
            self.substantive_statements = self.total_statements

    @property
    def participation_rate(self) -> float:
        """
        Calculate participation rate as percentage of substantive statements.

        Returns:
            Percentage of substantive statements (0-100)
        """
        if self.total_statements == 0:
            return 0.0
        return (self.substantive_statements / self.total_statements) * 100

    @property
    def voting_alignment(self) -> dict[str, float]:
        """
        Calculate voting alignment percentages.

        Returns:
            Dictionary with aye, no, abstain percentages
        """
        if self.votes_cast == 0:
            return {"aye": 0.0, "no": 0.0, "abstain": 0.0}

        return {
            "aye": (self.votes_aye / self.votes_cast) * 100,
            "no": (self.votes_no / self.votes_cast) * 100,
            "abstain": (self.votes_abstain / self.votes_cast) * 100,
        }

    def to_dict(self) -> dict[str, Any]:
        """
        Convert profile to dictionary for serialization.

        Returns:
            Dictionary representation of profile
        """
        return {
            "mp_id": self.mp_id,
            "name": self.name,
            "constituency": self.constituency,
            "party": self.party,
            "total_statements": self.total_statements,
            "substantive_statements": self.substantive_statements,
            "avg_quality_score": self.avg_quality_score,
            "sessions_attended": self.sessions_attended,
            "votes_cast": self.votes_cast,
            "votes_aye": self.votes_aye,
            "votes_no": self.votes_no,
            "votes_abstain": self.votes_abstain,
            "top_topics": self.top_topics,
            "bills_sponsored": self.bills_sponsored,
            "bills_discussed": self.bills_discussed,
            "avg_sentiment": self.avg_sentiment,
            "sentiment_distribution": self.sentiment_distribution,
            "summary": self.summary,
            "key_positions": self.key_positions,
            "participation_rate": self.participation_rate,
            "voting_alignment": self.voting_alignment,
            "metadata": self.metadata,
        }


class MPProfileGenerator:
    """
    Generate comprehensive MP profiles from database aggregations.

    This class aggregates MP activity data from the database including:
    - Statement counts and quality scores
    - Voting records
    - Topic analysis
    - Bill involvement
    - Sentiment analysis

    Optionally generates LLM summaries for narrative descriptions.

    Example:
        >>> from hansard_tales.database.db_updater import DatabaseUpdater
        >>> db = DatabaseUpdater("data/hansard.db")
        >>> generator = MPProfileGenerator(db.session)
        >>> profile = generator.generate_profile("mp-id-123")
        >>> print(f"{profile.name}: {profile.total_statements} statements")
    """

    def __init__(self, db_session, llm_analyzer=None):
        """
        Initialize MP profile generator.

        Args:
            db_session: SQLAlchemy database session
            llm_analyzer: Optional LLMAnalyzer for summary generation
        """
        self.db = db_session
        self.llm = llm_analyzer

    def _aggregate_statistics(self, mp_id: str) -> dict[str, Any]:
        """
        Aggregate MP statistics from database.

        This method queries the database to compute:
        - Statement counts (total, substantive)
        - Average quality score
        - Vote counts (total, aye, no, abstain)
        - Top topics discussed
        - Bills sponsored and discussed
        - Sentiment distribution

        Args:
            mp_id: UUID of the MP

        Returns:
            Dictionary with aggregated statistics

        Example:
            >>> stats = generator._aggregate_statistics("mp-id-123")
            >>> print(stats['total_statements'])
            150
        """
        from sqlalchemy import func

        from hansard_tales.database.models import (
            BillORM,
            MPVoteORM,
            StatementORM,
        )

        # Statement counts
        total_statements = (
            self.db.query(func.count(StatementORM.id)).filter(StatementORM.mp_id == mp_id).scalar()
            or 0
        )

        substantive_statements = (
            self.db.query(func.count(StatementORM.id))
            .filter(StatementORM.mp_id == mp_id, StatementORM.classification == "substantive")
            .scalar()
            or 0
        )

        # Quality score average
        avg_quality = (
            self.db.query(func.avg(StatementORM.quality_score))
            .filter(StatementORM.mp_id == mp_id, StatementORM.quality_score.isnot(None))
            .scalar()
            or 0.0
        )

        # Vote counts
        votes = self.db.query(MPVoteORM).filter(MPVoteORM.mp_id == mp_id).all()

        votes_aye = sum(1 for v in votes if v.direction == "aye")
        votes_no = sum(1 for v in votes if v.direction == "no")
        votes_abstain = sum(1 for v in votes if v.direction == "abstain")

        # Top topics (from statements)
        top_topics_query = (
            self.db.query(StatementORM.topics, func.count(StatementORM.id))
            .filter(StatementORM.mp_id == mp_id, StatementORM.topics.isnot(None))
            .group_by(StatementORM.topics)
            .order_by(func.count(StatementORM.id).desc())
            .limit(10)
            .all()
        )

        # Flatten topics (topics is JSON array)
        topic_counts: dict[str, int] = {}
        for topics_json, count in top_topics_query:
            if topics_json:
                for topic in topics_json:
                    topic_counts[topic] = topic_counts.get(topic, 0) + count

        # Sort by count and take top 5
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Bills sponsored
        bills_sponsored = self.db.query(BillORM.title).filter(BillORM.sponsor_id == mp_id).all()
        bills_sponsored_list = [bill[0] for bill in bills_sponsored]

        # Bills discussed (from related_statement_ids)
        bills_discussed_query = (
            self.db.query(BillORM.title)
            .join(StatementORM, StatementORM.related_bill_ids.contains([BillORM.id]))
            .filter(StatementORM.mp_id == mp_id)
            .distinct()
            .all()
        )
        bills_discussed_list = [bill[0] for bill in bills_discussed_query]

        # Sentiment distribution
        sentiment_counts = (
            self.db.query(StatementORM.sentiment, func.count(StatementORM.id))
            .filter(StatementORM.mp_id == mp_id, StatementORM.sentiment.isnot(None))
            .group_by(StatementORM.sentiment)
            .all()
        )
        sentiment_distribution = dict(sentiment_counts)

        # Calculate average sentiment (most common)
        avg_sentiment = "neutral"
        if sentiment_distribution:
            avg_sentiment = max(sentiment_distribution.items(), key=lambda x: x[1])[0]

        # Sessions attended (unique document_ids)
        sessions_attended = (
            self.db.query(func.count(func.distinct(StatementORM.document_id)))
            .filter(StatementORM.mp_id == mp_id)
            .scalar()
            or 0
        )

        return {
            "total_statements": total_statements,
            "substantive_statements": substantive_statements,
            "avg_quality_score": float(avg_quality),
            "sessions_attended": sessions_attended,
            "votes_cast": len(votes),
            "votes_aye": votes_aye,
            "votes_no": votes_no,
            "votes_abstain": votes_abstain,
            "top_topics": top_topics,
            "bills_sponsored": bills_sponsored_list,
            "bills_discussed": bills_discussed_list,
            "avg_sentiment": avg_sentiment,
            "sentiment_distribution": sentiment_distribution,
        }

    def _aggregate_topics(self, mp_id: str, limit: int = 10) -> list[tuple[str, int]]:
        """
        Aggregate topics discussed by MP.

        This method analyzes all statements by the MP and aggregates
        topics from the topics JSON field, counting occurrences.

        Args:
            mp_id: UUID of the MP
            limit: Maximum number of topics to return (default: 10)

        Returns:
            List of (topic, count) tuples sorted by count descending

        Example:
            >>> topics = generator._aggregate_topics("mp-id-123", limit=5)
            >>> print(topics)
            [('Healthcare', 45), ('Education', 32), ('Finance', 28), ...]
        """

        from hansard_tales.database.models import StatementORM

        # Query all statements with topics
        statements_with_topics = (
            self.db.query(StatementORM.topics)
            .filter(StatementORM.mp_id == mp_id, StatementORM.topics.isnot(None))
            .all()
        )

        # Count topic occurrences
        topic_counts: dict[str, int] = {}
        for (topics_json,) in statements_with_topics:
            if topics_json and isinstance(topics_json, list):
                for topic in topics_json:
                    if topic:  # Skip empty strings
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Sort by count and return top N
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_topics[:limit]

    def _get_topic_statements(self, mp_id: str, topic: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get sample statements for a specific topic.

        Args:
            mp_id: UUID of the MP
            topic: Topic to filter by
            limit: Maximum number of statements to return

        Returns:
            List of statement dictionaries with id, text, quality_score

        Example:
            >>> statements = generator._get_topic_statements("mp-id-123", "Healthcare")
            >>> print(len(statements))
            5
        """
        from hansard_tales.database.models import StatementORM

        # Query statements containing the topic
        statements = (
            self.db.query(StatementORM)
            .filter(
                StatementORM.mp_id == mp_id,
                StatementORM.topics.contains([topic]),
                StatementORM.classification == "substantive",
            )
            .order_by(StatementORM.quality_score.desc().nullslast())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(stmt.id),
                "text": stmt.text[:200] + "..." if len(stmt.text) > 200 else stmt.text,
                "quality_score": stmt.quality_score or 0.0,
                "created_at": stmt.created_at.isoformat() if stmt.created_at else None,
            }
            for stmt in statements
        ]

    def _aggregate_bills(self, mp_id: str) -> dict[str, list[str]]:
        """
        Aggregate bills sponsored and discussed by MP.

        This method finds:
        - Bills sponsored by the MP (as primary sponsor)
        - Bills discussed by the MP (mentioned in statements)

        Args:
            mp_id: UUID of the MP

        Returns:
            Dictionary with 'sponsored' and 'discussed' lists of bill titles

        Example:
            >>> bills = generator._aggregate_bills("mp-id-123")
            >>> print(f"Sponsored: {len(bills['sponsored'])}")
            >>> print(f"Discussed: {len(bills['discussed'])}")
        """
        from hansard_tales.database.models import BillORM, StatementORM

        # Bills sponsored (as primary sponsor)
        bills_sponsored = self.db.query(BillORM.title).filter(BillORM.sponsor_id == mp_id).all()
        sponsored_list = [bill[0] for bill in bills_sponsored]

        # Bills discussed (from statements with related_bill_ids)
        # Note: This is a simplified query - in production, you'd need to
        # properly handle JSON array contains queries based on your database
        statements_with_bills = (
            self.db.query(StatementORM.related_bill_ids)
            .filter(StatementORM.mp_id == mp_id, StatementORM.related_bill_ids.isnot(None))
            .all()
        )

        # Collect unique bill IDs
        discussed_bill_ids = set()
        for (bill_ids,) in statements_with_bills:
            if bill_ids and isinstance(bill_ids, list):
                discussed_bill_ids.update(bill_ids)

        # Get bill titles for discussed bills
        discussed_list = []
        if discussed_bill_ids:
            discussed_bills = (
                self.db.query(BillORM.title)
                .filter(BillORM.id.in_(discussed_bill_ids))
                .distinct()
                .all()
            )
            discussed_list = [bill[0] for bill in discussed_bills]

        return {"sponsored": sponsored_list, "discussed": discussed_list}

    def _get_bill_involvement_details(self, mp_id: str, bill_id: str) -> dict[str, Any]:
        """
        Get detailed involvement of MP with a specific bill.

        Args:
            mp_id: UUID of the MP
            bill_id: UUID of the bill

        Returns:
            Dictionary with involvement details (statements, votes, sponsorship)

        Example:
            >>> details = generator._get_bill_involvement_details("mp-id", "bill-id")
            >>> print(details['statement_count'])
            12
        """
        from hansard_tales.database.models import (
            BillORM,
            MPVoteORM,
            StatementORM,
            VoteORM,
        )

        # Check if MP is sponsor
        bill = self.db.query(BillORM).filter(BillORM.id == bill_id).first()
        is_sponsor = bill and str(bill.sponsor_id) == mp_id

        # Count statements mentioning this bill
        statement_count = (
            self.db.query(StatementORM)
            .filter(StatementORM.mp_id == mp_id, StatementORM.related_bill_ids.contains([bill_id]))
            .count()
        )

        # Get MP's votes on this bill
        votes = (
            self.db.query(MPVoteORM)
            .join(VoteORM)
            .filter(VoteORM.bill_id == bill_id, MPVoteORM.mp_id == mp_id)
            .all()
        )

        vote_directions = [vote.direction for vote in votes]

        return {
            "is_sponsor": is_sponsor,
            "statement_count": statement_count,
            "votes": vote_directions,
            "bill_title": bill.title if bill else "Unknown",
        }

    def _generate_summary(self, mp, stats: dict[str, Any]) -> str:
        """
        Generate LLM summary of MP profile.

        This method uses the LLM analyzer to generate a 2-3 sentence
        narrative summary of the MP's parliamentary activity based on
        aggregated statistics.

        Args:
            mp: MP ORM object with basic info
            stats: Dictionary of aggregated statistics

        Returns:
            Generated summary text (2-3 sentences)

        Example:
            >>> summary = generator._generate_summary(mp_obj, stats)
            >>> print(summary)
            'Hon. John Doe is an active member focusing primarily on healthcare...'
        """
        if not self.llm:
            # Return basic summary without LLM
            return self._generate_basic_summary(mp, stats)

        # Build prompt for LLM
        top_topics_str = ", ".join(t[0] for t in stats.get("top_topics", [])[:3])

        prompt = f"""Generate a brief profile summary for this MP:

Name: {mp.name}
Constituency: {mp.constituency}
Party: {mp.party}

Statistics:
- Total statements: {stats.get('total_statements', 0)}
- Substantive statements: {stats.get('substantive_statements', 0)}
- Average quality score: {stats.get('avg_quality_score', 0):.1f}/100
- Votes cast: {stats.get('votes_cast', 0)}
- Top topics: {top_topics_str or 'None'}
- Bills sponsored: {len(stats.get('bills_sponsored', []))}

Write a 2-3 sentence summary highlighting their key focus areas and participation level.
Be factual and objective. Do not make assumptions beyond the provided data."""

        try:
            response = self.llm.client.messages.create(
                model=self.llm.model,
                max_tokens=256,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )

            if response.content and len(response.content) > 0:
                return response.content[0].text.strip()

        except Exception as e:
            # Fall back to basic summary on error
            print(f"LLM summary generation failed: {e}")

        return self._generate_basic_summary(mp, stats)

    def _generate_basic_summary(self, mp, stats: dict[str, Any]) -> str:
        """
        Generate basic summary without LLM.

        This is a fallback method that creates a simple template-based
        summary when LLM is not available or fails.

        Args:
            mp: MP ORM object
            stats: Dictionary of aggregated statistics

        Returns:
            Template-based summary text
        """
        total_statements = stats.get("total_statements", 0)
        substantive = stats.get("substantive_statements", 0)
        top_topics = stats.get("top_topics", [])
        votes_cast = stats.get("votes_cast", 0)

        # Build summary parts
        parts = [f"{mp.name} represents {mp.constituency} for {mp.party}."]

        if total_statements > 0:
            parts.append(
                f"They have made {total_statements} statements "
                f"({substantive} substantive) in parliament."
            )

        if top_topics:
            top_topic = top_topics[0][0]
            parts.append(f"Their primary focus area is {top_topic}.")

        if votes_cast > 0:
            parts.append(f"They have participated in {votes_cast} votes.")

        return " ".join(parts)

    def _extract_key_positions(self, mp_id: str, limit: int = 5) -> list[str]:
        """
        Extract key positions from MP's statements.

        This method identifies the MP's key positions by analyzing
        high-quality statements with strong sentiment.

        Args:
            mp_id: UUID of the MP
            limit: Maximum number of positions to extract

        Returns:
            List of key position statements

        Example:
            >>> positions = generator._extract_key_positions("mp-id-123")
            >>> print(positions[0])
            'Supports increased healthcare funding for rural areas'
        """
        from hansard_tales.database.models import StatementORM

        # Query high-quality statements with clear sentiment
        statements = (
            self.db.query(StatementORM)
            .filter(
                StatementORM.mp_id == mp_id,
                StatementORM.classification == "substantive",
                StatementORM.quality_score.isnot(None),
                StatementORM.sentiment.in_(["positive", "negative"]),
            )
            .order_by(StatementORM.quality_score.desc())
            .limit(limit * 2)  # Get more to filter
            .all()
        )

        # Extract key points from statements
        key_positions = []
        for stmt in statements:
            if len(key_positions) >= limit:
                break

            # Use first sentence or first 100 chars as position
            text = stmt.text.strip()
            first_sentence = text.split(".")[0] if "." in text else text
            if len(first_sentence) > 100:
                first_sentence = first_sentence[:100] + "..."

            # Add sentiment context
            sentiment_prefix = "Supports" if stmt.sentiment == "positive" else "Opposes"
            position = f"{sentiment_prefix}: {first_sentence}"

            key_positions.append(position)

        return key_positions

    def generate_profile(self, mp_id: str) -> MPProfile:
        """
        Generate comprehensive MP profile.

        This is the main method that orchestrates profile generation by:
        1. Fetching MP data from database
        2. Aggregating statistics
        3. Generating summary (with LLM if available)
        4. Extracting key positions
        5. Creating MPProfile object

        Args:
            mp_id: UUID of the MP

        Returns:
            Complete MPProfile object

        Raises:
            ValueError: If MP not found in database

        Example:
            >>> profile = generator.generate_profile("mp-id-123")
            >>> print(f"{profile.name}: {profile.total_statements} statements")
            >>> print(f"Quality: {profile.avg_quality_score:.1f}/100")
        """
        from hansard_tales.database.models import MPORM

        # Fetch MP data
        mp = self.db.query(MPORM).filter(MPORM.id == mp_id).first()
        if not mp:
            raise ValueError(f"MP not found: {mp_id}")

        # Aggregate statistics
        stats = self._aggregate_statistics(mp_id)

        # Generate summary
        summary = self._generate_summary(mp, stats)

        # Extract key positions
        key_positions = self._extract_key_positions(mp_id)

        # Create profile
        return MPProfile(
            mp_id=str(mp.id),
            name=mp.name,
            constituency=mp.constituency or "",
            party=mp.party or "",
            total_statements=stats["total_statements"],
            substantive_statements=stats["substantive_statements"],
            avg_quality_score=stats["avg_quality_score"],
            sessions_attended=stats["sessions_attended"],
            votes_cast=stats["votes_cast"],
            votes_aye=stats["votes_aye"],
            votes_no=stats["votes_no"],
            votes_abstain=stats["votes_abstain"],
            top_topics=stats["top_topics"],
            bills_sponsored=stats["bills_sponsored"],
            bills_discussed=stats["bills_discussed"],
            avg_sentiment=stats["avg_sentiment"],
            sentiment_distribution=stats["sentiment_distribution"],
            summary=summary,
            key_positions=key_positions,
        )

    def generate_profiles_batch(
        self, mp_ids: list[str] | None = None, chamber: str | None = None, limit: int | None = None
    ) -> list[MPProfile]:
        """
        Generate profiles for multiple MPs in batch.

        This method efficiently generates profiles for multiple MPs,
        optionally filtered by chamber or limited to a specific count.

        Args:
            mp_ids: Optional list of specific MP IDs to generate profiles for
            chamber: Optional chamber filter ("national_assembly" or "senate")
            limit: Optional maximum number of profiles to generate

        Returns:
            List of MPProfile objects

        Example:
            >>> # Generate profiles for all MPs
            >>> profiles = generator.generate_profiles_batch()
            >>> print(f"Generated {len(profiles)} profiles")
            >>>
            >>> # Generate profiles for specific MPs
            >>> profiles = generator.generate_profiles_batch(mp_ids=["id1", "id2"])
            >>>
            >>> # Generate profiles for National Assembly only
            >>> profiles = generator.generate_profiles_batch(chamber="national_assembly")
        """
        from hansard_tales.database.models import MPORM

        # Build query
        query = self.db.query(MPORM)

        if mp_ids:
            query = query.filter(MPORM.id.in_(mp_ids))

        if chamber:
            query = query.filter(MPORM.chamber == chamber)

        if limit:
            query = query.limit(limit)

        # Fetch MPs
        mps = query.all()

        # Generate profiles
        profiles = []
        for mp in mps:
            try:
                profile = self.generate_profile(str(mp.id))
                profiles.append(profile)
            except Exception as e:
                print(f"Error generating profile for {mp.name}: {e}")
                continue

        return profiles

    def generate_profiles_by_party(self, party: str) -> list[MPProfile]:
        """
        Generate profiles for all MPs in a specific party.

        Args:
            party: Party name to filter by

        Returns:
            List of MPProfile objects for party members

        Example:
            >>> profiles = generator.generate_profiles_by_party("UDA")
            >>> print(f"Generated {len(profiles)} UDA profiles")
        """
        from hansard_tales.database.models import MPORM

        mps = self.db.query(MPORM).filter(MPORM.party == party).all()

        profiles = []
        for mp in mps:
            try:
                profile = self.generate_profile(str(mp.id))
                profiles.append(profile)
            except Exception as e:
                print(f"Error generating profile for {mp.name}: {e}")
                continue

        return profiles

    def generate_profiles_by_constituency(self, constituency: str) -> list[MPProfile]:
        """
        Generate profiles for all MPs representing a constituency.

        Args:
            constituency: Constituency name to filter by

        Returns:
            List of MPProfile objects for constituency representatives

        Example:
            >>> profiles = generator.generate_profiles_by_constituency("Nairobi West")
            >>> print(f"Generated {len(profiles)} profiles")
        """
        from hansard_tales.database.models import MPORM

        mps = self.db.query(MPORM).filter(MPORM.constituency == constituency).all()

        profiles = []
        for mp in mps:
            try:
                profile = self.generate_profile(str(mp.id))
                profiles.append(profile)
            except Exception as e:
                print(f"Error generating profile for {mp.name}: {e}")
                continue

        return profiles
