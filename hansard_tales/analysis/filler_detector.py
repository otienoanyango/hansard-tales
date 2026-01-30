"""
Statement Classification System (Filler Detection).

This module provides functionality for classifying statements as substantive
or filler content using rule-based patterns and length-based heuristics.
"""

import re
from enum import Enum

from hansard_tales.analysis.statement_segmenter import Statement


class StatementType(Enum):
    """
    Classification types for parliamentary statements.

    Attributes:
        SUBSTANTIVE: High-value statement with policy content
        PROCEDURAL: Procedural statements (motions, seconds, etc.)
        INTERRUPTION: Interruptions (applause, laughter, etc.)
        ADMINISTRATIVE: Administrative statements (adjournment, prayers, etc.)
        SHORT_ACK: Short acknowledgments (thank you, yes, no, etc.)
    """

    SUBSTANTIVE = "substantive"
    PROCEDURAL = "procedural"
    INTERRUPTION = "interruption"
    ADMINISTRATIVE = "administrative"
    SHORT_ACK = "short_acknowledgment"


class FillerDetector:
    """
    Detect filler/non-substantive statements.

    This class classifies statements into different types based on
    pattern matching and length-based heuristics. Filler statements
    include procedural, interruptions, administrative, and short
    acknowledgments.

    Filler Categories:
    1. Procedural: "I beg to move", "I second", "Question put and agreed to"
    2. Interruptions: "(Applause)", "(Laughter)", "(Interruptions)"
    3. Administrative: "The House rose at...", "Prayers"
    4. Short acknowledgments: "Thank you", "I agree", "Yes"
    """

    def __init__(self):
        """Initialize filler detector with pattern definitions."""
        self.filler_patterns = {
            StatementType.PROCEDURAL: [
                r"^I beg to move",
                r"^I second",
                r"^Question put and agreed to",
                r"^Motion made and Question proposed",
                r"^I beg to lay",
                r"^I beg to table",
                r"^I beg to present",
                r"^I beg to report",
                r"^I rise on a point of order",
                r"^Point of order",
                r"^Order! Order!",
                r"^Division required",
                r"^Question proposed",
                r"^Question put",
                r"^Agreed to",
                r"^Not agreed to",
            ],
            StatementType.INTERRUPTION: [
                r"^\(Applause\)",
                r"^\(Laughter\)",
                r"^\(Interruptions\)",
                r"^\(Loud consultations\)",
                r"^\(Consultations\)",
                r"^\(Interjections\)",
                r"^\(Members walked out\)",
                r"^\(An hon\. Member",
                r"^\(Several hon\. Members",
            ],
            StatementType.ADMINISTRATIVE: [
                r"^The House rose at",
                r"^Prayers",
                r"^ADJOURNMENT",
                r"^COMMUNICATION FROM THE CHAIR",
                r"^PAPERS LAID",
                r"^PETITIONS",
                r"^NOTICES OF MOTION",
                r"^STATEMENTS",
                r"^MESSAGES",
                r"^The House met at",
                r"^QUORUM",
                r"^Quorum bell",
            ],
            StatementType.SHORT_ACK: [
                r"^Thank you\.?$",
                r"^I agree\.?$",
                r"^Yes\.?$",
                r"^No\.?$",
                r"^Agreed\.?$",
                r"^Okay\.?$",
                r"^Alright\.?$",
                r"^Fine\.?$",
                r"^Very well\.?$",
                r"^I support\.?$",
                r"^I oppose\.?$",
                r"^Hear! Hear!\.?$",
            ],
        }

        # Compile patterns for efficiency
        self.compiled_patterns = {
            stmt_type: [re.compile(p, re.IGNORECASE) for p in patterns]
            for stmt_type, patterns in self.filler_patterns.items()
        }

    def classify(self, statement: Statement) -> tuple[StatementType, float]:
        """
        Classify statement as substantive or filler.

        Classification logic:
        1. Check length first (< 10 chars = SHORT_ACK)
        2. Check patterns for each filler type
        3. Default to SUBSTANTIVE if no patterns match

        Args:
            statement: Statement to classify

        Returns:
            Tuple of (StatementType, confidence_score)
            Confidence is 1.0 for length-based, 0.95 for pattern-based,
            0.90 for substantive (default)
        """
        text = statement.text.strip()

        # Check length first
        if len(text) < 10:
            return StatementType.SHORT_ACK, 1.0

        # Check patterns
        for stmt_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return stmt_type, 0.95

        # Default to substantive
        return StatementType.SUBSTANTIVE, 0.90

    def is_substantive(self, statement: Statement) -> bool:
        """
        Check if statement is substantive.

        Args:
            statement: Statement to check

        Returns:
            True if statement is substantive, False otherwise
        """
        stmt_type, confidence = self.classify(statement)
        return stmt_type == StatementType.SUBSTANTIVE
