"""
MP Identification System.

This module provides functionality for identifying MPs in Hansard text
and matching them to database records using regex patterns, spaCy NER,
and fuzzy matching.
"""

import re
from dataclasses import dataclass

import spacy
from fuzzywuzzy import fuzz
from sqlalchemy.orm import Session

from hansard_tales.database.models import MPORM


@dataclass
class MPMatch:
    """
    Result of MP identification.

    Attributes:
        mp_id: UUID of the matched MP
        name: Full name of the MP
        confidence: Confidence score (0.0-1.0)
        constituency: MP's constituency (optional)
        party: MP's party (optional)
    """

    mp_id: str
    name: str
    confidence: float
    constituency: str | None = None
    party: str | None = None


class MPIdentifier:
    """
    Identify MPs in Hansard text.

    This class uses multiple strategies to identify MPs:
    1. Regex patterns for common name formats
    2. spaCy NER for person name extraction
    3. Fuzzy matching for name variations
    4. Database caching for performance

    Hansard uses several formats for MP names:
    - Hon. John Doe (Nairobi West, UDA)
    - Dr. Jane Smith (Kisumu Central, ODM)
    - The Speaker (Hon. Moses Wetangula)
    - Mr. John Doe
    - John Doe (in subsequent mentions)
    """

    def __init__(self, db_session: Session, nlp_model: str = "en_core_web_sm"):
        """
        Initialize MP identifier.

        Args:
            db_session: SQLAlchemy database session
            nlp_model: spaCy model name (default: en_core_web_sm)
        """
        self.db = db_session
        self.nlp = spacy.load(nlp_model)
        self.mp_cache = self._load_mp_cache()

        # Compile regex patterns for MP name formats
        # Patterns handle both title case (John Doe) and uppercase (JOHN DOE) names
        self.patterns = [
            # Hon. Name (Constituency, Party)
            re.compile(
                r"(?:Hon\.|Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+"
                r"([A-Z]+(?:\s+[A-Z]+)+)\s*"
                r"\(([^,]+),\s*([^)]+)\)"
            ),
            # Hon. Name
            re.compile(r"(?:Hon\.|Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+" r"([A-Z]+(?:\s+[A-Z]+)+)"),
            # Name (Constituency)
            re.compile(r"([A-Z]+(?:\s+[A-Z]+)+)\s*" r"\(([^)]+)\)"),
        ]

    def _load_mp_cache(self) -> dict:
        """
        Load all MPs into memory for fast lookup.

        Creates a cache with multiple indexes:
        - Full name (lowercase)
        - Last name (lowercase)

        Returns:
            Dictionary mapping names to MP records
        """
        # Get all MPs (chamber filtering not strictly necessary, but keep for safety)
        mps = self.db.query(MPORM).all()

        cache = {}
        for mp in mps:
            # Index by full name
            cache[mp.name.lower()] = mp

            # Index by last name
            last_name = mp.name.split()[-1].lower()
            if last_name not in cache:
                cache[last_name] = []
            if isinstance(cache[last_name], list):
                cache[last_name].append(mp)
            else:
                cache[last_name] = [cache[last_name], mp]

        return cache

    def identify(self, text: str, context: dict | None = None) -> MPMatch | None:
        """
        Identify MP from text mention.

        Uses multiple strategies in order:
        1. Regex pattern matching (highest confidence)
        2. spaCy NER extraction (medium confidence)

        Args:
            text: Text containing MP mention
            context: Optional context for disambiguation

        Returns:
            MPMatch if MP identified, None otherwise
        """
        # Try regex patterns first
        for pattern in self.patterns:
            match = pattern.search(text)
            if match:
                name = match.group(1)
                constituency = match.group(2) if len(match.groups()) > 1 else None
                party = match.group(3) if len(match.groups()) > 2 else None

                mp = self._match_to_database(name, constituency, party)
                if mp:
                    return MPMatch(
                        mp_id=str(mp.id),
                        name=mp.name,
                        confidence=0.95,
                        constituency=mp.constituency,
                        party=mp.party,
                    )

        # Try NER extraction
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                mp = self._match_to_database(ent.text)
                if mp:
                    return MPMatch(
                        mp_id=str(mp.id),
                        name=mp.name,
                        confidence=0.80,
                        constituency=mp.constituency,
                        party=mp.party,
                    )

        return None

    def _match_to_database(
        self, name: str, constituency: str | None = None, party: str | None = None
    ) -> MPORM | None:
        """
        Match extracted name to database record.

        Uses multiple strategies:
        1. Exact name match
        2. Fuzzy name matching with constituency/party boosting

        Args:
            name: Extracted MP name
            constituency: Optional constituency for disambiguation
            party: Optional party for disambiguation

        Returns:
            Matched MP record or None
        """
        name_lower = name.lower()

        # Exact match
        if name_lower in self.mp_cache:
            mp = self.mp_cache[name_lower]
            if not isinstance(mp, list):
                return mp

        # Fuzzy match on full name
        best_match = None
        best_score = 0

        for cached_name, mp in self.mp_cache.items():
            if isinstance(mp, list):
                continue

            score = fuzz.ratio(name_lower, cached_name)

            # Boost score if constituency matches
            if constituency and mp.constituency:
                if constituency.lower() in mp.constituency.lower():
                    score += 20

            # Boost score if party matches
            if party and mp.party:
                if party.lower() in mp.party.lower():
                    score += 10

            if score > best_score and score >= 85:
                best_score = score
                best_match = mp

        return best_match

    def identify_batch(self, texts: list[str]) -> list[MPMatch | None]:
        """
        Identify MPs in batch of texts.

        Args:
            texts: List of text strings containing MP mentions

        Returns:
            List of MPMatch objects (None for unmatched texts)
        """
        return [self.identify(text) for text in texts]
