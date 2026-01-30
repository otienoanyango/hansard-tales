"""
Property-based tests for StaticSiteGenerator.

Tests universal properties that should hold for all site generation scenarios.
"""

import tempfile
from datetime import date, datetime
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hansard_tales.database.models import (
    MPORM,
    Base,
    BillORM,
    ChamberEnum,
    DocumentORM,
    DocumentTypeEnum,
)
from hansard_tales.site.generator import StaticSiteGenerator


def create_test_db_with_data(num_mps=5, num_sessions=3, num_bills=2):
    """Create test database with specified amount of data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Add MPs
    mps = []
    for i in range(num_mps):
        mp = MPORM(
            name=f"MP {i}",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            constituency=f"Constituency {i}",
            party=f"Party {i % 3}",  # 3 parties
            parliament_term=2022,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(mp)
        mps.append(mp)
    session.commit()

    # Add sessions
    sessions = []
    for i in range(num_sessions):
        doc = DocumentORM(
            type=DocumentTypeEnum.HANSARD,
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            title=f"Session {i}",
            date=date(2024, 1, i + 1),
            parliament_term=2022,
            source_url=f"http://example.com/session{i}.pdf",
            source_hash=f"hash{i}",
            download_date=datetime.now(),
            vector_doc_id=f"vec{i}",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(doc)
        sessions.append(doc)
    session.commit()

    # Add bills
    for i in range(num_bills):
        bill = BillORM(
            bill_number=f"B{i:03d}/2024",
            title=f"Bill {i}",
            chamber=ChamberEnum.NATIONAL_ASSEMBLY,
            status="First Reading",
            sponsor_id=mps[0].id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(bill)
    session.commit()

    return session


def create_temp_templates():
    """Create temporary template directory with minimal templates."""
    temp_dir = tempfile.mkdtemp()
    template_path = Path(temp_dir)
    (template_path / "static").mkdir()

    # Create minimal templates
    (template_path / "base.html").write_text(
        "<!DOCTYPE html><html><body>{% block content %}{% endblock %}</body></html>"
    )
    (template_path / "homepage.html").write_text(
        "{% extends 'base.html' %}{% block content %}Homepage{% endblock %}"
    )
    (template_path / "mp_list.html").write_text(
        "{% extends 'base.html' %}{% block content %}MP List{% endblock %}"
    )
    (template_path / "mp_profile.html").write_text(
        "{% extends 'base.html' %}{% block content %}MP Profile{% endblock %}"
    )
    (template_path / "session_list.html").write_text(
        "{% extends 'base.html' %}{% block content %}Session List{% endblock %}"
    )
    (template_path / "session_detail.html").write_text(
        "{% extends 'base.html' %}{% block content %}Session Detail{% endblock %}"
    )
    (template_path / "bill_list.html").write_text(
        "{% extends 'base.html' %}{% block content %}Bill List{% endblock %}"
    )
    (template_path / "bill_detail.html").write_text(
        "{% extends 'base.html' %}{% block content %}Bill Detail{% endblock %}"
    )
    (template_path / "party_list.html").write_text(
        "{% extends 'base.html' %}{% block content %}Party List{% endblock %}"
    )
    (template_path / "party_detail.html").write_text(
        "{% extends 'base.html' %}{% block content %}Party Detail{% endblock %}"
    )
    (template_path / "search.html").write_text(
        "{% extends 'base.html' %}{% block content %}Search{% endblock %}"
    )

    return template_path


class TestPageGenerationCompleteness:
    """
    Property 11.1: Page generation completeness.

    **Validates**: Requirements 14.2
    **Property**: All entities must have generated pages
    """

    @given(
        num_mps=st.integers(min_value=1, max_value=10),
        num_sessions=st.integers(min_value=1, max_value=10),
        num_bills=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=10, deadline=None)
    def test_all_mps_have_pages(self, num_mps, num_sessions, num_bills):
        """
        Property: Every MP in database must have a generated profile page.

        **Validates: Requirements 14.2**
        """
        # Create test database
        session = create_test_db_with_data(num_mps, num_sessions, num_bills)

        # Create temporary directories
        template_dir = create_temp_templates()
        output_dir = Path(tempfile.mkdtemp())

        try:
            # Generate site
            generator = StaticSiteGenerator(
                db_session=session,
                template_dir=template_dir,
                output_dir=output_dir,
            )
            generator._generate_mp_pages()

            # Verify: Count MPs in database
            mp_count = session.query(MPORM).count()

            # Verify: Count generated MP pages (excluding index.html)
            mp_dir = output_dir / "mps"
            generated_pages = [
                f for f in mp_dir.iterdir() if f.is_file() and f.name != "index.html"
            ]

            # Property: Number of generated pages must equal number of MPs
            assert (
                len(generated_pages) == mp_count
            ), f"Expected {mp_count} MP pages, found {len(generated_pages)}"

        finally:
            session.close()
            import shutil

            shutil.rmtree(template_dir)
            shutil.rmtree(output_dir)

    @given(
        num_mps=st.integers(min_value=1, max_value=10),
        num_sessions=st.integers(min_value=1, max_value=10),
        num_bills=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=10, deadline=None)
    def test_all_sessions_have_pages(self, num_mps, num_sessions, num_bills):
        """
        Property: Every session in database must have a generated detail page.

        **Validates: Requirements 14.2**
        """
        # Create test database
        session = create_test_db_with_data(num_mps, num_sessions, num_bills)

        # Create temporary directories
        template_dir = create_temp_templates()
        output_dir = Path(tempfile.mkdtemp())

        try:
            # Generate site
            generator = StaticSiteGenerator(
                db_session=session,
                template_dir=template_dir,
                output_dir=output_dir,
            )
            generator._generate_session_pages()

            # Verify: Count sessions in database
            session_count = (
                session.query(DocumentORM)
                .filter(DocumentORM.type == DocumentTypeEnum.HANSARD)
                .count()
            )

            # Verify: Count generated session pages (excluding index.html)
            session_dir = output_dir / "sessions"
            generated_pages = [
                f for f in session_dir.iterdir() if f.is_file() and f.name != "index.html"
            ]

            # Property: Number of generated pages must equal number of sessions
            assert (
                len(generated_pages) == session_count
            ), f"Expected {session_count} session pages, found {len(generated_pages)}"

        finally:
            session.close()
            import shutil

            shutil.rmtree(template_dir)
            shutil.rmtree(output_dir)

    @given(
        num_mps=st.integers(min_value=1, max_value=10),
        num_sessions=st.integers(min_value=1, max_value=10),
        num_bills=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=10, deadline=None)
    def test_all_bills_have_pages(self, num_mps, num_sessions, num_bills):
        """
        Property: Every bill in database must have a generated detail page.

        **Validates: Requirements 14.2**
        """
        # Create test database
        session = create_test_db_with_data(num_mps, num_sessions, num_bills)

        # Create temporary directories
        template_dir = create_temp_templates()
        output_dir = Path(tempfile.mkdtemp())

        try:
            # Generate site
            generator = StaticSiteGenerator(
                db_session=session,
                template_dir=template_dir,
                output_dir=output_dir,
            )
            generator._generate_bill_pages()

            # Verify: Count bills in database
            bill_count = session.query(BillORM).count()

            # Verify: Count generated bill pages (excluding index.html)
            bill_dir = output_dir / "bills"
            generated_pages = [
                f for f in bill_dir.iterdir() if f.is_file() and f.name != "index.html"
            ]

            # Property: Number of generated pages must equal number of bills
            assert (
                len(generated_pages) == bill_count
            ), f"Expected {bill_count} bill pages, found {len(generated_pages)}"

        finally:
            session.close()
            import shutil

            shutil.rmtree(template_dir)
            shutil.rmtree(output_dir)


class TestLinkValidity:
    """
    Property 11.2: Link validity.

    **Validates**: Requirements 14.2
    **Property**: All internal links must be valid
    """

    @given(
        num_mps=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=5, deadline=None)
    def test_slugify_produces_valid_filenames(self, num_mps):
        """
        Property: Slugified names must produce valid filenames.

        **Validates: Requirements 14.2**
        """
        # Create test database
        session = create_test_db_with_data(num_mps, 1, 1)

        # Create temporary directories
        template_dir = create_temp_templates()
        output_dir = Path(tempfile.mkdtemp())

        try:
            # Generate site
            generator = StaticSiteGenerator(
                db_session=session,
                template_dir=template_dir,
                output_dir=output_dir,
            )

            # Test slugify on all MP names
            mps = session.query(MPORM).all()
            for mp in mps:
                slug = generator._slugify(mp.name)

                # Property: Slug must be valid filename
                assert slug, "Slug must not be empty"
                assert "/" not in slug, "Slug must not contain path separators"
                assert "\\" not in slug, "Slug must not contain backslashes"
                assert slug == slug.lower(), "Slug must be lowercase"
                assert not slug.startswith("-"), "Slug must not start with hyphen"
                assert not slug.endswith("-"), "Slug must not end with hyphen"

        finally:
            session.close()
            import shutil

            shutil.rmtree(template_dir)
            shutil.rmtree(output_dir)

    @given(
        num_mps=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=5, deadline=None)
    def test_search_index_urls_match_generated_pages(self, num_mps):
        """
        Property: URLs in search index must match generated page filenames.

        **Validates: Requirements 14.2**
        """
        # Create test database
        session = create_test_db_with_data(num_mps, 1, 1)

        # Create temporary directories
        template_dir = create_temp_templates()
        output_dir = Path(tempfile.mkdtemp())

        try:
            # Generate site
            generator = StaticSiteGenerator(
                db_session=session,
                template_dir=template_dir,
                output_dir=output_dir,
            )
            generator._generate_mp_pages()

            # Build search index
            search_index = generator._build_search_index()

            # Verify: All MP URLs in search index correspond to generated files
            for mp_entry in search_index["mps"]:
                url = mp_entry["url"]
                # Remove leading slash and convert to path
                file_path = output_dir / url.lstrip("/")

                # Property: File must exist
                assert file_path.exists(), f"File not found for URL: {url}"

        finally:
            session.close()
            import shutil

            shutil.rmtree(template_dir)
            shutil.rmtree(output_dir)
