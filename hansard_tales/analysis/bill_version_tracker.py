"""
Bill version tracking and change detection.

This module implements tracking of bill versions and detection of
changes between versions.
"""

import difflib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BillChange:
    """A detected change in a bill."""

    change_type: str  # "addition", "deletion", "modification"
    section_number: str
    old_text: Optional[str]
    new_text: Optional[str]
    description: str


class BillVersionTracker:
    """
    Tracker for bill versions and changes.

    This tracker handles:
    - Adding new bill versions
    - Generating diffs between versions
    - Detecting section-level changes
    - Summarizing changes

    Example:
        >>> tracker = BillVersionTracker()
        >>> tracker.add_version(1, bill_text_v1, "2024-01-15")
        >>> tracker.add_version(2, bill_text_v2, "2024-02-20")
        >>> changes = tracker.generate_diff(1, 2)
    """

    def __init__(self):
        """Initialize the tracker."""
        self.versions: dict[int, dict] = {}
        self.logger = self._get_logger()

    def _get_logger(self):
        """Get logger instance."""
        import logging

        return logging.getLogger(self.__class__.__name__)

    def add_version(
        self,
        version_number: int,
        text: str,
        date: str,
        title: str = "",
    ) -> None:
        """
        Add a new bill version.

        Args:
            version_number: Version number (typically 1, 2, 3, etc.)
            text: Full bill text
            date: Date of this version (ISO format recommended)
            title: Bill title for this version

        Raises:
            ValueError: If version already exists or version_number is invalid
        """
        if version_number < 1:
            raise ValueError("Version number must be >= 1")

        if version_number in self.versions:
            raise ValueError(f"Version {version_number} already exists")

        # Parse sections
        sections = self._parse_sections(text)

        self.versions[version_number] = {
            "text": text,
            "date": date,
            "title": title,
            "sections": sections,
            "timestamp": datetime.fromisoformat(date) if date else datetime.now(),
        }

        self.logger.info(f"Added version {version_number} with {len(sections)} sections")

    def generate_diff(self, version_from: int, version_to: int) -> list[BillChange]:
        """
        Generate diff between two versions.

        Args:
            version_from: Starting version number
            version_to: Ending version number

        Returns:
            List of BillChange objects representing differences

        Raises:
            ValueError: If versions don't exist
        """
        if version_from not in self.versions:
            raise ValueError(f"Version {version_from} not found")
        if version_to not in self.versions:
            raise ValueError(f"Version {version_to} not found")

        old_version = self.versions[version_from]
        new_version = self.versions[version_to]

        changes = []

        # Compare full text using difflib
        old_lines = old_version["text"].split("\n")
        new_lines = new_version["text"].split("\n")

        diff = difflib.unified_diff(old_lines, new_lines, lineterm="")
        diff_lines = list(diff)

        # Parse diff to identify section-level changes
        current_section = None
        for line in diff_lines:
            if line.startswith("---") or line.startswith("+++"):
                continue

            if line.startswith("@@"):
                # Extract section info if available
                match = re.search(r"@@ .* @@", line)
                if match:
                    current_section = match.group(0)
            elif line.startswith("-"):
                # Deleted line
                changes.append(
                    BillChange(
                        change_type="deletion",
                        section_number=current_section or "unknown",
                        old_text=line[1:].strip(),
                        new_text=None,
                        description=f"Deleted: {line[1:][:100]}...",
                    )
                )
            elif line.startswith("+"):
                # Added line
                changes.append(
                    BillChange(
                        change_type="addition",
                        section_number=current_section or "unknown",
                        old_text=None,
                        new_text=line[1:].strip(),
                        description=f"Added: {line[1:][:100]}...",
                    )
                )

        self.logger.info(
            f"Generated {len(changes)} changes from version {version_from} " f"to {version_to}"
        )
        return changes

    def get_changes_summary(self, version_from: int, version_to: int) -> str:
        """
        Get a text summary of changes between versions.

        Args:
            version_from: Starting version number
            version_to: Ending version number

        Returns:
            Human-readable summary of changes

        Raises:
            ValueError: If versions don't exist
        """
        changes = self.generate_diff(version_from, version_to)

        if not changes:
            return f"No changes between version {version_from} and {version_to}"

        # Categorize changes
        additions = [c for c in changes if c.change_type == "addition"]
        deletions = [c for c in changes if c.change_type == "deletion"]
        modifications = [c for c in changes if c.change_type == "modification"]

        summary = f"Changes from version {version_from} to {version_to}:\n"
        summary += f"- Additions: {len(additions)}\n"
        summary += f"- Deletions: {len(deletions)}\n"
        summary += f"- Modifications: {len(modifications)}\n"
        summary += f"- Total changes: {len(changes)}\n"

        # List major changes (first 5)
        if changes:
            summary += "\nFirst 5 changes:\n"
            for change in changes[:5]:
                summary += f"  - {change.change_type}: {change.description}\n"

        return summary

    def _parse_sections(self, text: str) -> dict:
        """
        Parse sections from bill text.

        Args:
            text: Full bill text

        Returns:
            Dictionary of sections {section_num: section_text}
        """
        import re

        sections = {}

        # Simple regex to find sections
        section_pattern = r"(?:Section\s+)?(\d+)[.—\-]?\s*(.+?)(?=Section\s+\d|^\s*\d+\.|$)"
        matches = re.finditer(section_pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)

        for match in matches:
            section_num = match.group(1).strip()
            section_text = match.group(2).strip()
            sections[section_num] = section_text

        return sections

    def list_versions(self) -> list[int]:
        """
        List all tracked versions.

        Returns:
            Sorted list of version numbers
        """
        return sorted(self.versions.keys())

    def get_version_info(self, version_number: int) -> Optional[dict]:
        """
        Get information about a specific version.

        Args:
            version_number: Version to retrieve

        Returns:
            Version info dict or None if not found
        """
        if version_number not in self.versions:
            return None

        version = self.versions[version_number]
        return {
            "version_number": version_number,
            "date": version["date"],
            "title": version["title"],
            "section_count": len(version["sections"]),
            "text_length": len(version["text"]),
        }
