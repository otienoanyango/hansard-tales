"""
Unit tests for StaticSiteGenerator.

Tests the static site generation functionality including page generation,
template rendering, and asset copying.
"""

import tempfile
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hansard_tales.database.models import (
    MPORM,
    Base,
    BillORM,
    ChamberEnum,
    DocumentORM,
    DocumentTypeEnum,
    StatementORM,
)
from hansard_tales.site.generator import StaticSiteGenerator


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    from datetime import datetime

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Add test data
    mp1 = MPORM(
        name="John Doe",
        chamber=ChamberEnum.NATIONAL_ASSEMBLY,
        constituency="Test Constituency",
        party="Test Party",
        parliament_term=2022,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mp2 = MPORM(
        name="Jane Smith",
        chamber=ChamberEnum.NATIONAL_ASSEMBLY,
        constituency="Another Constituency",
        party="Another Party",
        parliament_term=2022,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    session.add_all([mp1, mp2])
    session.commit()

    # Add documents (sessions)
    doc1 = DocumentORM(
        type=DocumentTypeEnum.HANSARD,
        chamber=ChamberEnum.NATIONAL_ASSEMBLY,
        title="Morning Session",
        date=date(2024, 1, 15),
        parliament_term=2022,
        source_url="http://example.com/session1.pdf",
        source_hash="hash1",
        download_date=datetime.now(),
        vector_doc_id="vec1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    doc2 = DocumentORM(
        type=DocumentTypeEnum.HANSARD,
        chamber=ChamberEnum.NATIONAL_ASSEMBLY,
        title="Afternoon Session",
        date=date(2024, 1, 16),
        parliament_term=2022,
        source_url="http://example.com/session2.pdf",
        source_hash="hash2",
        download_date=datetime.now(),
        vector_doc_id="vec2",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    session.add_all([doc1, doc2])
    session.commit()

    # Add bill
    bill1 = BillORM(
        bill_number="B001/2024",
        title="Test Bill 2024",
        chamber=ChamberEnum.NATIONAL_ASSEMBLY,
        status="First Reading",
        sponsor_id=mp1.id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    session.add(bill1)
    session.commit()

    # Add statements
    stmt1 = StatementORM(
        document_id=doc1.id,
        mp_id=mp1.id,
        text="This is a test statement",
        source_url="http://example.com/session1.pdf",
        source_hash="stmt_hash1",
        vector_doc_id="vec_stmt1",
        classification="substantive",
        sentiment="positive",
        quality_score=85.0,
        topics=["Healthcare"],
        created_at=datetime.now(),
    )
    stmt2 = StatementORM(
        document_id=doc1.id,
        mp_id=mp2.id,
        text="Another test statement",
        source_url="http://example.com/session1.pdf",
        source_hash="stmt_hash2",
        vector_doc_id="vec_stmt2",
        classification="substantive",
        sentiment="neutral",
        quality_score=90.0,
        topics=["Education"],
        created_at=datetime.now(),
    )
    session.add_all([stmt1, stmt2])
    session.commit()

    yield session

    session.close()


@pytest.fixture
def temp_dirs():
    """Create temporary directories for templates and output."""
    with tempfile.TemporaryDirectory() as template_dir:
        with tempfile.TemporaryDirectory() as output_dir:
            # Create template directory structure
            template_path = Path(template_dir)
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

            yield template_path, Path(output_dir)


class TestStaticSiteGenerator:
    """Test suite for StaticSiteGenerator."""

    def test_initialization(self, temp_db, temp_dirs):
        """Test generator initialization."""
        template_dir, output_dir = temp_dirs

        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        assert generator.db == temp_db
        assert generator.template_dir == template_dir
        assert generator.output_dir == output_dir
        assert generator.env is not None

    def test_slugify_filter(self, temp_db, temp_dirs):
        """Test slugify filter."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        assert generator._slugify("John Doe") == "john-doe"
        assert generator._slugify("Test (MP)") == "test-mp"
        assert generator._slugify("Multiple   Spaces") == "multiple-spaces"
        assert generator._slugify("Special!@#Characters") == "specialcharacters"

    def test_format_date_filter(self, temp_db, temp_dirs):
        """Test format_date filter."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        test_date = date(2024, 1, 15)
        assert generator._format_date(test_date) == "January 15, 2024"
        assert generator._format_date(None) == "Unknown"

    def test_format_number_filter(self, temp_db, temp_dirs):
        """Test format_number filter."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        assert generator._format_number(1234567) == "1,234,567"
        assert generator._format_number(100) == "100"
        assert generator._format_number(None) == "0"

    def test_truncate_words_filter(self, temp_db, temp_dirs):
        """Test truncate_words filter."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        text = "This is a long text with many words"
        assert generator._truncate_words(text, 3) == "This is a..."
        assert generator._truncate_words(text, 100) == text

    def test_homepage_generation(self, temp_db, temp_dirs):
        """Test homepage generation."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        generator._generate_homepage()

        # Check that index.html was created
        index_file = output_dir / "index.html"
        assert index_file.exists()

        # Check content
        content = index_file.read_text()
        assert "Homepage" in content


class TestMPPageGeneration:
    """Test MP page generation."""

    def test_mp_pages_generation(self, temp_db, temp_dirs):
        """Test MP pages generation."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        generator._generate_mp_pages()

        # Check that MPs directory was created
        mp_dir = output_dir / "mps"
        assert mp_dir.exists()

        # Check that index.html was created
        assert (mp_dir / "index.html").exists()

        # Check that individual MP pages were created
        assert (mp_dir / "john-doe.html").exists()
        assert (mp_dir / "jane-smith.html").exists()

    def test_mp_profile_data(self, temp_db, temp_dirs):
        """Test MP profile data retrieval."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        mp = temp_db.query(MPORM).first()
        profile_data = generator._get_mp_profile_data(mp)

        assert "total_statements" in profile_data
        assert "substantive_statements" in profile_data
        assert "avg_quality_score" in profile_data
        assert "top_topics" in profile_data
        assert "recent_statements" in profile_data


class TestSessionPageGeneration:
    """Test session page generation."""

    def test_session_pages_generation(self, temp_db, temp_dirs):
        """Test session pages generation."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        generator._generate_session_pages()

        # Check that sessions directory was created
        session_dir = output_dir / "sessions"
        assert session_dir.exists()

        # Check that index.html was created
        assert (session_dir / "index.html").exists()

        # Check that individual session pages were created
        # Use slugified title for filename
        assert any(f.name.startswith("2024-01-15-") for f in session_dir.iterdir() if f.is_file())
        assert any(f.name.startswith("2024-01-16-") for f in session_dir.iterdir() if f.is_file())

    def test_session_data(self, temp_db, temp_dirs):
        """Test session data retrieval."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        session = (
            temp_db.query(DocumentORM).filter(DocumentORM.type == DocumentTypeEnum.HANSARD).first()
        )
        session_data = generator._get_session_data(session)

        assert "statements" in session_data
        assert "total_statements" in session_data
        assert "substantive_statements" in session_data
        assert "mps_present" in session_data
        assert "main_topics" in session_data
        assert "votes" in session_data


class TestBillPageGeneration:
    """Test bill page generation."""

    def test_bill_pages_generation(self, temp_db, temp_dirs):
        """Test bill pages generation."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        generator._generate_bill_pages()

        # Check that bills directory was created
        bill_dir = output_dir / "bills"
        assert bill_dir.exists()

        # Check that index.html was created
        assert (bill_dir / "index.html").exists()

        # Check that individual bill pages were created
        assert (bill_dir / "test-bill-2024.html").exists()


class TestPartyPageGeneration:
    """Test party page generation."""

    def test_party_pages_generation(self, temp_db, temp_dirs):
        """Test party pages generation."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        generator._generate_party_pages()

        # Check that parties directory was created
        party_dir = output_dir / "parties"
        assert party_dir.exists()

        # Check that index.html was created
        assert (party_dir / "index.html").exists()

        # Check that individual party pages were created
        assert (party_dir / "test-party.html").exists()
        assert (party_dir / "another-party.html").exists()

    def test_get_party_data(self, temp_db, temp_dirs):
        """Test party data retrieval."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        party_data = generator._get_party_data("Test Party")

        assert "mps" in party_data
        assert "total_mps" in party_data
        assert "total_statements" in party_data
        assert "top_topics" in party_data


class TestSearchPageGeneration:
    """Test search page generation."""

    def test_search_page_generation(self, temp_db, temp_dirs):
        """Test search page generation."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        generator._generate_search_page()

        # Check that search directory was created
        search_dir = output_dir / "search"
        assert search_dir.exists()

        # Check that index.html was created
        assert (search_dir / "index.html").exists()

        # Check that data.json was created
        assert (search_dir / "data.json").exists()

    def test_build_search_index(self, temp_db, temp_dirs):
        """Test search index building."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        search_index = generator._build_search_index()

        assert "mps" in search_index
        assert "sessions" in search_index
        assert "bills" in search_index
        assert len(search_index["mps"]) == 2
        assert len(search_index["sessions"]) == 2
        assert len(search_index["bills"]) == 1


class TestStaticAssetCopying:
    """Test static asset copying."""

    def test_copy_static_assets(self, temp_db, temp_dirs):
        """Test static asset copying."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        # Create a test file in static directory
        (template_dir / "static" / "test.css").write_text("body { margin: 0; }")

        generator._copy_static_assets()

        # Check that static directory was copied
        static_dir = output_dir / "static"
        assert static_dir.exists()
        assert (static_dir / "test.css").exists()

    def test_copy_static_assets_missing_dir(self, temp_db, temp_dirs):
        """Test static asset copying with missing directory."""
        template_dir, output_dir = temp_dirs

        # Remove static directory
        import shutil

        shutil.rmtree(template_dir / "static")

        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        # Should not raise error
        generator._copy_static_assets()


class TestFullSiteGeneration:
    """Test full site generation."""

    def test_generate_site(self, temp_db, temp_dirs):
        """Test complete site generation."""
        template_dir, output_dir = temp_dirs
        generator = StaticSiteGenerator(
            db_session=temp_db, template_dir=template_dir, output_dir=output_dir
        )

        generator.generate_site()

        # Check that all directories were created
        assert (output_dir / "mps").exists()
        assert (output_dir / "sessions").exists()
        assert (output_dir / "bills").exists()
        assert (output_dir / "parties").exists()
        assert (output_dir / "search").exists()
        assert (output_dir / "static").exists()

        # Check that homepage was created
        assert (output_dir / "index.html").exists()
