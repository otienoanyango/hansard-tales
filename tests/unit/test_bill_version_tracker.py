"""
Unit tests for BillVersionTracker.
"""

import pytest

from hansard_tales.analysis.bill_version_tracker import (
    BillChange,
    BillVersionTracker,
)


@pytest.fixture
def tracker():
    """Create a bill version tracker instance."""
    return BillVersionTracker()


class TestBillVersionTrackerAddVersion:
    """Tests for adding bill versions."""

    def test_add_version_first(self, tracker):
        """Test adding first version."""
        text = "PART I\nSection 1. Title"
        tracker.add_version(1, text, "2024-01-15", "Test Bill")

        versions = tracker.list_versions()
        assert 1 in versions

    def test_add_version_multiple(self, tracker):
        """Test adding multiple versions."""
        text1 = "Version 1 text"
        text2 = "Version 2 text"
        text3 = "Version 3 text"

        tracker.add_version(1, text1, "2024-01-15")
        tracker.add_version(2, text2, "2024-02-20")
        tracker.add_version(3, text3, "2024-03-10")

        versions = tracker.list_versions()
        assert versions == [1, 2, 3]

    def test_add_version_duplicate_fails(self, tracker):
        """Test that adding duplicate version raises error."""
        text = "Test text"
        tracker.add_version(1, text, "2024-01-15")

        with pytest.raises(ValueError):
            tracker.add_version(1, text, "2024-02-20")

    def test_add_version_invalid_number(self, tracker):
        """Test that invalid version numbers raise error."""
        text = "Test text"

        with pytest.raises(ValueError):
            tracker.add_version(0, text, "2024-01-15")

        with pytest.raises(ValueError):
            tracker.add_version(-1, text, "2024-01-15")

    def test_add_version_with_metadata(self, tracker):
        """Test adding version with metadata."""
        text = "Version text"
        title = "Agriculture Bill"
        date = "2024-01-15"

        tracker.add_version(1, text, date, title)

        info = tracker.get_version_info(1)
        assert info["title"] == title
        assert info["version_number"] == 1


class TestBillVersionTrackerDiff:
    """Tests for diff generation."""

    def test_generate_diff_simple(self, tracker):
        """Test generating diff between simple versions."""
        text1 = "Section 1. Title\nSection 2. Commencement"
        text2 = "Section 1. Title\nSection 2. Commencement\nSection 3. Definitions"

        tracker.add_version(1, text1, "2024-01-15")
        tracker.add_version(2, text2, "2024-02-20")

        changes = tracker.generate_diff(1, 2)

        assert len(changes) > 0
        assert any(c.change_type == "addition" for c in changes)

    def test_generate_diff_deletion(self, tracker):
        """Test diff with deletions."""
        text1 = "Section 1\nSection 2\nSection 3"
        text2 = "Section 1\nSection 3"

        tracker.add_version(1, text1, "2024-01-15")
        tracker.add_version(2, text2, "2024-02-20")

        changes = tracker.generate_diff(1, 2)

        assert any(c.change_type == "deletion" for c in changes)

    def test_generate_diff_modification(self, tracker):
        """Test diff with modifications."""
        text1 = "Section 1. Old title\nOther text"
        text2 = "Section 1. New title\nOther text"

        tracker.add_version(1, text1, "2024-01-15")
        tracker.add_version(2, text2, "2024-02-20")

        changes = tracker.generate_diff(1, 2)

        assert len(changes) > 0

    def test_generate_diff_nonexistent_version(self, tracker):
        """Test diff with nonexistent version."""
        tracker.add_version(1, "text1", "2024-01-15")

        with pytest.raises(ValueError):
            tracker.generate_diff(1, 999)

        with pytest.raises(ValueError):
            tracker.generate_diff(999, 1)

    def test_generate_diff_same_version(self, tracker):
        """Test diff between same version."""
        text = "Section 1. Title"
        tracker.add_version(1, text, "2024-01-15")

        changes = tracker.generate_diff(1, 1)

        # Diff between same version should have minimal or no changes
        assert isinstance(changes, list)

    def test_generate_diff_multiple_changes(self, tracker):
        """Test diff with multiple types of changes."""
        text1 = """
        PART I
        1. Title
        2. Scope
        3. Definitions
        """

        text2 = """
        PART I
        1. Title
        2. Scope and Application
        3. Definitions
        4. Authority
        5. Commencement
        """

        tracker.add_version(1, text1, "2024-01-15")
        tracker.add_version(2, text2, "2024-02-20")

        changes = tracker.generate_diff(1, 2)

        assert len(changes) > 0
        assert any(c.change_type == "addition" for c in changes)


class TestBillVersionTrackerSummary:
    """Tests for change summaries."""

    def test_get_changes_summary_simple(self, tracker):
        """Test generating changes summary."""
        text1 = "Section 1"
        text2 = "Section 1\nSection 2"

        tracker.add_version(1, text1, "2024-01-15")
        tracker.add_version(2, text2, "2024-02-20")

        summary = tracker.get_changes_summary(1, 2)

        assert isinstance(summary, str)
        assert "version" in summary.lower()
        assert "changes" in summary.lower()

    def test_get_changes_summary_no_changes(self, tracker):
        """Test summary when no changes exist."""
        text = "Section 1\nSection 2"

        tracker.add_version(1, text, "2024-01-15")
        tracker.add_version(2, text, "2024-02-20")

        summary = tracker.get_changes_summary(1, 2)

        assert "no changes" in summary.lower()

    def test_get_changes_summary_includes_counts(self, tracker):
        """Test that summary includes change counts."""
        text1 = "Original text\nSection 1"
        text2 = "Modified text\nSection 1\nSection 2"

        tracker.add_version(1, text1, "2024-01-15")
        tracker.add_version(2, text2, "2024-02-20")

        summary = tracker.get_changes_summary(1, 2)

        # Summary should contain change type counts
        assert "Additions:" in summary or "additions" in summary.lower()


class TestBillVersionTrackerInfo:
    """Tests for version information retrieval."""

    def test_get_version_info_exists(self, tracker):
        """Test getting info for existing version."""
        text = "Test content"
        tracker.add_version(1, text, "2024-01-15", "Test Bill")

        info = tracker.get_version_info(1)

        assert info is not None
        assert info["version_number"] == 1
        assert info["title"] == "Test Bill"
        assert info["text_length"] == len(text)

    def test_get_version_info_nonexistent(self, tracker):
        """Test getting info for nonexistent version."""
        info = tracker.get_version_info(999)

        assert info is None

    def test_list_versions_ordered(self, tracker):
        """Test listing versions in order."""
        tracker.add_version(3, "text3", "2024-03-15")
        tracker.add_version(1, "text1", "2024-01-15")
        tracker.add_version(2, "text2", "2024-02-15")

        versions = tracker.list_versions()

        assert versions == [1, 2, 3]

    def test_get_version_info_section_count(self, tracker):
        """Test that version info includes section count."""
        text = """
        Section 1. First
        Section 2. Second
        Section 3. Third
        """
        tracker.add_version(1, text, "2024-01-15")

        info = tracker.get_version_info(1)

        assert "section_count" in info


class TestBillVersionTrackerParsing:
    """Tests for section parsing."""

    def test_parse_sections_simple(self, tracker):
        """Test parsing sections."""
        text = """
        Section 1. Title
        Section 2. Scope
        Section 3. Definitions
        """
        tracker.add_version(1, text, "2024-01-15")

        info = tracker.get_version_info(1)
        assert info["section_count"] >= 1

    def test_parse_sections_with_content(self, tracker):
        """Test parsing sections with detailed content."""
        text = """
        Section 1. Short title
        This Act may be cited as the Test Act, 2024.

        Section 2. Application
        This Act applies to all areas.

        Section 3. Definitions
        In this Act—
        "person" means any individual...
        """
        tracker.add_version(1, text, "2024-01-15")

        info = tracker.get_version_info(1)
        assert info["section_count"] >= 1


class TestBillVersionTrackerEdgeCases:
    """Tests for edge cases."""

    def test_empty_version_text(self, tracker):
        """Test adding version with empty text."""
        tracker.add_version(1, "", "2024-01-15")

        info = tracker.get_version_info(1)
        assert info["text_length"] == 0

    def test_large_version_text(self, tracker):
        """Test adding version with large text."""
        large_text = "Section " + "\n".join([f"{i}. Content" for i in range(1, 101)])
        tracker.add_version(1, large_text, "2024-01-15")

        info = tracker.get_version_info(1)
        assert info["text_length"] > 1000

    def test_version_with_special_chars(self, tracker):
        """Test version with special characters."""
        text = 'Section 1. Title with "quotes" and –dashes\nAnd other chars: © ® ™'
        tracker.add_version(1, text, "2024-01-15")

        diff = tracker.generate_diff(1, 1)
        assert isinstance(diff, list)

    def test_diff_with_unicode(self, tracker):
        """Test diff with unicode characters."""
        text1 = "Section 1. Original text"
        text2 = "Section 1. Modified text with français and español"

        tracker.add_version(1, text1, "2024-01-15")
        tracker.add_version(2, text2, "2024-02-20")

        changes = tracker.generate_diff(1, 2)
        assert isinstance(changes, list)


class TestBillVersionTrackerConsistency:
    """Tests for consistency and correctness."""

    def test_multiple_diffs_consistency(self, tracker):
        """Test that multiple diff calls give consistent results."""
        text1 = "Original"
        text2 = "Modified"

        tracker.add_version(1, text1, "2024-01-15")
        tracker.add_version(2, text2, "2024-02-20")

        diff1 = tracker.generate_diff(1, 2)
        diff2 = tracker.generate_diff(1, 2)

        assert len(diff1) == len(diff2)

    def test_diff_type_consistency(self, tracker):
        """Test that diff returns BillChange objects."""
        text1 = "Text 1"
        text2 = "Text 2"

        tracker.add_version(1, text1, "2024-01-15")
        tracker.add_version(2, text2, "2024-02-20")

        changes = tracker.generate_diff(1, 2)

        for change in changes:
            assert isinstance(change, BillChange)
            assert change.change_type in ["addition", "deletion", "modification"]
