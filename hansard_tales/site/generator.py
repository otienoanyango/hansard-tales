"""
Static site generator for Hansard Tales.

This module generates a static HTML website from processed parliamentary data
using Jinja2 templates.
"""

import re
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from hansard_tales.database.models import (
    MPORM,
    BillORM,
    DocumentORM,
    DocumentTypeEnum,
    StatementORM,
    VoteORM,
)
from hansard_tales.utils.logging import get_logger

logger = get_logger(__name__)


class StaticSiteGenerator:
    """
    Generate static HTML site from processed data.

    This class orchestrates the generation of a complete static website
    including MP profiles, session pages, bill pages, and search functionality.

    Attributes:
        db: Database session
        template_dir: Directory containing Jinja2 templates
        output_dir: Directory for generated HTML files
        env: Jinja2 environment

    Example:
        >>> generator = StaticSiteGenerator(
        ...     db_session=session,
        ...     template_dir=Path("templates"),
        ...     output_dir=Path("output")
        ... )
        >>> generator.generate_site()
    """

    def __init__(
        self,
        db_session: Session,
        template_dir: Path,
        output_dir: Path,
        static_dir: Path | None = None,
    ):
        """
        Initialize static site generator.

        Args:
            db_session: SQLAlchemy database session
            template_dir: Path to Jinja2 templates directory
            output_dir: Path to output directory for generated site
            static_dir: Optional path to static assets directory
        """
        self.db = db_session
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.static_dir = static_dir or self.template_dir / "static"

        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self.env.filters["slugify"] = self._slugify
        self.env.filters["format_date"] = self._format_date
        self.env.filters["format_number"] = self._format_number
        self.env.filters["truncate_words"] = self._truncate_words

        logger.info(
            f"Initialized StaticSiteGenerator with template_dir={template_dir}, "
            f"output_dir={output_dir}"
        )

    def generate_site(self) -> None:
        """
        Generate complete static site.

        This method orchestrates the generation of all pages including:
        - Homepage
        - MP pages (list and profiles)
        - Session pages (list and details)
        - Bill pages (list and details)
        - Party pages (list and details)
        - Search page
        - Static assets

        Raises:
            ValueError: If template directory doesn't exist
            IOError: If unable to write output files
        """
        logger.info("Starting static site generation")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate pages
        self._generate_homepage()
        self._generate_mp_pages()
        self._generate_session_pages()
        self._generate_bill_pages()
        self._generate_party_pages()
        self._generate_search_page()

        # Copy static assets
        self._copy_static_assets()

        logger.info(f"Static site generation complete. Output: {self.output_dir}")

    def _slugify(self, text: str) -> str:
        """
        Convert text to URL-safe slug.

        Args:
            text: Text to slugify

        Returns:
            URL-safe slug

        Example:
            >>> generator._slugify("John Doe (MP)")
            'john-doe-mp'
        """
        # Convert to lowercase
        text = text.lower()

        # Remove special characters
        text = re.sub(r"[^\w\s-]", "", text)

        # Replace spaces and underscores with hyphens
        text = re.sub(r"[\s_-]+", "-", text)

        # Remove leading/trailing hyphens
        text = text.strip("-")

        return text

    def _format_date(self, date_obj: date | None) -> str:
        """
        Format date for display.

        Args:
            date_obj: Date object to format

        Returns:
            Formatted date string

        Example:
            >>> generator._format_date(date(2024, 1, 15))
            'January 15, 2024'
        """
        if date_obj is None:
            return "Unknown"

        return date_obj.strftime("%B %d, %Y")

    def _format_number(self, number: int | None) -> str:
        """
        Format number with thousands separator.

        Args:
            number: Number to format

        Returns:
            Formatted number string

        Example:
            >>> generator._format_number(1234567)
            '1,234,567'
        """
        if number is None:
            return "0"

        return f"{number:,}"

    def _truncate_words(self, text: str, length: int = 50) -> str:
        """
        Truncate text to specified word count.

        Args:
            text: Text to truncate
            length: Maximum number of words

        Returns:
            Truncated text with ellipsis if needed

        Example:
            >>> generator._truncate_words("This is a long text", 3)
            'This is a...'
        """
        words = text.split()
        if len(words) <= length:
            return text

        return " ".join(words[:length]) + "..."

    def _generate_homepage(self) -> None:
        """
        Generate homepage with recent sessions and statistics.

        Creates the main index.html file with:
        - Recent parliamentary sessions
        - Overall statistics (MPs, sessions, statements, bills)
        - Quick links to major sections
        """
        logger.info("Generating homepage")

        # Fetch recent Hansard documents (sessions)
        recent_sessions = (
            self.db.query(DocumentORM)
            .filter(DocumentORM.type == DocumentTypeEnum.HANSARD)
            .order_by(DocumentORM.date.desc())
            .limit(10)
            .all()
        )

        # Calculate statistics
        stats = {
            "total_mps": self.db.query(MPORM).count(),
            "total_sessions": self.db.query(DocumentORM)
            .filter(DocumentORM.type == DocumentTypeEnum.HANSARD)
            .count(),
            "total_statements": self.db.query(StatementORM).count(),
            "total_bills": self.db.query(BillORM).count(),
        }

        # Render template
        template = self.env.get_template("homepage.html")
        html = template.render(recent_sessions=recent_sessions, stats=stats)

        # Write file
        output_file = self.output_dir / "index.html"
        output_file.write_text(html, encoding="utf-8")

        logger.info(f"Homepage generated: {output_file}")

    def _generate_mp_pages(self) -> None:
        """
        Generate MP list and individual profile pages.

        Creates:
        - mps/index.html: Directory of all MPs
        - mps/[mp-slug].html: Individual MP profile pages
        """
        logger.info("Generating MP pages")

        # Create MPs directory
        mp_dir = self.output_dir / "mps"
        mp_dir.mkdir(exist_ok=True)

        # Fetch all MPs
        mps = self.db.query(MPORM).order_by(MPORM.name).all()

        # Generate MP directory page
        template = self.env.get_template("mp_list.html")
        html = template.render(mps=mps)
        (mp_dir / "index.html").write_text(html, encoding="utf-8")

        logger.info(f"Generated MP list page with {len(mps)} MPs")

        # Generate individual MP profile pages
        profile_template = self.env.get_template("mp_profile.html")

        for mp in mps:
            # Fetch MP profile data
            profile_data = self._get_mp_profile_data(mp)

            # Render template
            html = profile_template.render(mp=mp, profile=profile_data)

            # Write file
            filename = f"{self._slugify(mp.name)}.html"
            (mp_dir / filename).write_text(html, encoding="utf-8")

        logger.info(f"Generated {len(mps)} MP profile pages")

    def _get_mp_profile_data(self, mp: MPORM) -> dict[str, Any]:
        """
        Fetch profile data for an MP.

        Args:
            mp: MP database object

        Returns:
            Dictionary containing profile statistics and data
        """
        from sqlalchemy import func

        # Statement counts
        total_statements = (
            self.db.query(func.count(StatementORM.id)).filter(StatementORM.mp_id == mp.id).scalar()
            or 0
        )

        substantive_statements = (
            self.db.query(func.count(StatementORM.id))
            .filter(StatementORM.mp_id == mp.id, StatementORM.classification == "substantive")
            .scalar()
            or 0
        )

        # Quality score average
        avg_quality = (
            self.db.query(func.avg(StatementORM.quality_score))
            .filter(StatementORM.mp_id == mp.id)
            .scalar()
            or 0.0
        )

        # Top topics - extract from JSON array
        statements_with_topics = (
            self.db.query(StatementORM.topics)
            .filter(StatementORM.mp_id == mp.id, StatementORM.topics.isnot(None))
            .all()
        )

        # Count topics
        topic_counts: dict[str, int] = {}
        for (topics,) in statements_with_topics:
            if topics:
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Get top 5 topics
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Recent statements
        recent_statements = (
            self.db.query(StatementORM)
            .filter(StatementORM.mp_id == mp.id)
            .order_by(StatementORM.created_at.desc())
            .limit(10)
            .all()
        )

        return {
            "total_statements": total_statements,
            "substantive_statements": substantive_statements,
            "avg_quality_score": float(avg_quality),
            "top_topics": top_topics,
            "recent_statements": recent_statements,
        }

    def _generate_session_pages(self) -> None:
        """
        Generate session list and detail pages.

        Creates:
        - sessions/index.html: List of all sessions
        - sessions/[date]-[type].html: Individual session detail pages
        """
        logger.info("Generating session pages")

        # Create sessions directory
        session_dir = self.output_dir / "sessions"
        session_dir.mkdir(exist_ok=True)

        # Fetch all Hansard documents (sessions)
        sessions = (
            self.db.query(DocumentORM)
            .filter(DocumentORM.type == DocumentTypeEnum.HANSARD)
            .order_by(DocumentORM.date.desc())
            .all()
        )

        # Generate session list page
        template = self.env.get_template("session_list.html")
        html = template.render(sessions=sessions)
        (session_dir / "index.html").write_text(html, encoding="utf-8")

        logger.info(f"Generated session list page with {len(sessions)} sessions")

        # Generate individual session detail pages
        detail_template = self.env.get_template("session_detail.html")

        for session in sessions:
            # Fetch session data
            session_data = self._get_session_data(session)

            # Render template
            html = detail_template.render(session=session, data=session_data)

            # Write file - use title as session type
            session_type = session.title.lower().replace(" ", "-")
            filename = f"{session.date}-{session_type}.html"
            (session_dir / filename).write_text(html, encoding="utf-8")

        logger.info(f"Generated {len(sessions)} session detail pages")

    def _get_session_data(self, session: DocumentORM) -> dict[str, Any]:
        """
        Fetch data for a session.

        Args:
            session: DocumentORM database object (Hansard document)

        Returns:
            Dictionary containing session statistics and data
        """

        # Fetch statements
        statements = (
            self.db.query(StatementORM)
            .filter(StatementORM.document_id == session.id)
            .order_by(StatementORM.created_at)
            .all()
        )

        # Count MPs present
        unique_mps = len({s.mp_id for s in statements if s.mp_id})

        # Get main topics - extract from JSON arrays
        topic_counts: dict[str, int] = {}
        for stmt in statements:
            if stmt.topics:
                for topic in stmt.topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Get top 5 topics
        main_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Get votes if any (would need to link votes to documents)
        votes: list[VoteORM] = []

        return {
            "statements": statements,
            "total_statements": len(statements),
            "substantive_statements": len(
                [s for s in statements if s.classification == "substantive"]
            ),
            "mps_present": unique_mps,
            "main_topics": main_topics,
            "votes": votes,
        }

    def _generate_bill_pages(self) -> None:
        """
        Generate bill list and detail pages.

        Creates:
        - bills/index.html: List of all bills
        - bills/[bill-slug].html: Individual bill detail pages
        """
        logger.info("Generating bill pages")

        # Create bills directory
        bill_dir = self.output_dir / "bills"
        bill_dir.mkdir(exist_ok=True)

        # Fetch all bills
        bills = self.db.query(BillORM).order_by(BillORM.created_at.desc()).all()

        # Generate bill list page
        template = self.env.get_template("bill_list.html")
        html = template.render(bills=bills)
        (bill_dir / "index.html").write_text(html, encoding="utf-8")

        logger.info(f"Generated bill list page with {len(bills)} bills")

        # Generate individual bill detail pages
        detail_template = self.env.get_template("bill_detail.html")

        for bill in bills:
            # Fetch bill data
            bill_data = self._get_bill_data(bill)

            # Render template
            html = detail_template.render(bill=bill, data=bill_data)

            # Write file
            filename = f"{self._slugify(bill.title)}.html"
            (bill_dir / filename).write_text(html, encoding="utf-8")

        logger.info(f"Generated {len(bills)} bill detail pages")

    def _get_bill_data(self, bill: BillORM) -> dict[str, Any]:
        """
        Fetch data for a bill.

        Args:
            bill: BillORM database object

        Returns:
            Dictionary containing bill-related data
        """
        # This would fetch related statements, votes, etc.
        # For now, return basic structure
        return {
            "related_statements": [],
            "related_votes": [],
            "discussion_count": 0,
        }

    def _generate_party_pages(self) -> None:
        """
        Generate party list and detail pages.

        Creates:
        - parties/index.html: List of all parties
        - parties/[party-slug].html: Individual party detail pages
        """
        logger.info("Generating party pages")

        # Create parties directory
        party_dir = self.output_dir / "parties"
        party_dir.mkdir(exist_ok=True)

        # Get unique parties from MPs
        parties = (
            self.db.query(MPORM.party)
            .filter(MPORM.party.isnot(None))
            .distinct()
            .order_by(MPORM.party)
            .all()
        )
        party_names = [p[0] for p in parties]

        # Generate party list page
        template = self.env.get_template("party_list.html")
        html = template.render(parties=party_names)
        (party_dir / "index.html").write_text(html, encoding="utf-8")

        logger.info(f"Generated party list page with {len(party_names)} parties")

        # Generate individual party detail pages
        detail_template = self.env.get_template("party_detail.html")

        for party_name in party_names:
            # Fetch party data
            party_data = self._get_party_data(party_name)

            # Render template
            html = detail_template.render(party=party_name, data=party_data)

            # Write file
            filename = f"{self._slugify(party_name)}.html"
            (party_dir / filename).write_text(html, encoding="utf-8")

        logger.info(f"Generated {len(party_names)} party detail pages")

    def _get_party_data(self, party_name: str) -> dict[str, Any]:
        """
        Fetch data for a party.

        Args:
            party_name: Name of the party

        Returns:
            Dictionary containing party statistics and data
        """
        from sqlalchemy import func

        # Get MPs in this party
        mps = self.db.query(MPORM).filter(MPORM.party == party_name).all()

        # Count statements by party members
        total_statements = (
            self.db.query(func.count(StatementORM.id))
            .join(MPORM, StatementORM.mp_id == MPORM.id)
            .filter(MPORM.party == party_name)
            .scalar()
            or 0
        )

        # Get top topics discussed by party - extract from JSON arrays
        statements_with_topics = (
            self.db.query(StatementORM.topics)
            .join(MPORM, StatementORM.mp_id == MPORM.id)
            .filter(MPORM.party == party_name, StatementORM.topics.isnot(None))
            .all()
        )

        # Count topics
        topic_counts: dict[str, int] = {}
        for (topics,) in statements_with_topics:
            if topics:
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Get top 5 topics
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "mps": mps,
            "total_mps": len(mps),
            "total_statements": total_statements,
            "top_topics": top_topics,
        }

    def _generate_search_page(self) -> None:
        """
        Generate search interface page.

        Creates:
        - search/index.html: Client-side search interface
        - search/data.json: Search index data for client-side search
        """
        logger.info("Generating search page")

        # Create search directory
        search_dir = self.output_dir / "search"
        search_dir.mkdir(exist_ok=True)

        # Generate search page
        template = self.env.get_template("search.html")
        html = template.render()
        (search_dir / "index.html").write_text(html, encoding="utf-8")

        # Generate search index data
        search_data = self._build_search_index()

        import json

        (search_dir / "data.json").write_text(json.dumps(search_data, indent=2), encoding="utf-8")

        logger.info("Generated search page and index")

    def _build_search_index(self) -> dict[str, list[dict[str, Any]]]:
        """
        Build search index data for client-side search.

        Returns:
            Dictionary containing searchable data for MPs, sessions, bills
        """
        # Build index for MPs
        mps = self.db.query(MPORM).all()
        mp_index = [
            {
                "type": "mp",
                "name": mp.name,
                "constituency": mp.constituency,
                "party": mp.party,
                "url": f"/mps/{self._slugify(mp.name)}.html",
            }
            for mp in mps
        ]

        # Build index for sessions (Hansard documents)
        sessions = (
            self.db.query(DocumentORM).filter(DocumentORM.type == DocumentTypeEnum.HANSARD).all()
        )
        session_index = [
            {
                "type": "session",
                "date": str(session.date),
                "session_type": session.title,
                "url": f"/sessions/{session.date}-{self._slugify(session.title)}.html",
            }
            for session in sessions
        ]

        # Build index for bills
        bills = self.db.query(BillORM).all()
        bill_index = [
            {
                "type": "bill",
                "title": bill.title,
                "date": str(bill.created_at.date()) if bill.created_at else None,
                "url": f"/bills/{self._slugify(bill.title)}.html",
            }
            for bill in bills
        ]

        return {
            "mps": mp_index,
            "sessions": session_index,
            "bills": bill_index,
        }

    def _copy_static_assets(self) -> None:
        """
        Copy static assets (CSS, JS, images) to output directory.

        Copies the entire static directory to output/static, preserving
        directory structure.
        """
        logger.info("Copying static assets")

        if not self.static_dir.exists():
            logger.warning(f"Static directory not found: {self.static_dir}")
            return

        # Destination directory
        dest_dir = self.output_dir / "static"

        # Remove existing static directory if it exists
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        # Copy static directory
        shutil.copytree(self.static_dir, dest_dir)

        logger.info(f"Copied static assets from {self.static_dir} to {dest_dir}")
