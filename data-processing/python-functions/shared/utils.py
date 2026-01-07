"""
Shared utilities for Hansard Tales Python functions
"""

import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MP:
    """Member of Parliament data structure"""
    id: str
    name: str
    constituency: str
    party: str
    current_term_start: Optional[datetime] = None


@dataclass
class StatementAnalysis:
    """AI analysis result for a parliamentary statement"""
    statement_id: str
    mp_id: str
    topic: str
    stance: str  # for/against/neutral/unclear
    quality: str  # substantive/heckling/procedural/empty
    confidence: float
    reasoning: str


def validate_mp(mp: MP) -> bool:
    """Validate MP data structure"""
    if not mp.name or not mp.name.strip():
        raise ValueError("MP name cannot be empty")
    if not mp.constituency or not mp.constituency.strip():
        raise ValueError("MP constituency cannot be empty") 
    if not mp.party or not mp.party.strip():
        raise ValueError("MP party cannot be empty")
    return True


def normalize_mp_name(name: str) -> str:
    """Normalize MP names for consistent matching"""
    if not name:
        return ""
    
    # Remove common prefixes
    name = name.strip()
    name = re.sub(r'^Hon\.\s*', '', name)
    name = re.sub(r'\(Dr\)\s*', '', name)
    name = re.sub(r'\(Eng\)\s*', '', name)
    
    # Normalize spacing
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()


def extract_date_from_text(text: str) -> Optional[datetime]:
    """Extract date from Hansard text using common patterns"""
    if not text:
        return None
        
    # Common date patterns
    patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY  
        r'(\d{1,2})\w{0,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',  # DD Month YYYY
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                # Handle ISO format
                if '-' in match.group(0):
                    return datetime.strptime(match.group(0), '%Y-%m-%d')
                # Handle other formats would go here
                return datetime.strptime(match.group(0), '%Y-%m-%d')  # Simplified
            except ValueError:
                continue
    
    return None


def calculate_performance_score(attendance_rate: float, bills_sponsored: float, quality_score: float) -> float:
    """Calculate MP performance score using weighted average"""
    # Weighted average: 40% attendance, 30% bills, 30% quality
    score = (attendance_rate * 0.4 + bills_sponsored * 0.3 + quality_score * 0.3)
    
    # Cap between 0 and 100
    return min(max(score, 0.0), 100.0)


def filter_procedural_statements(statements: List[str]) -> List[str]:
    """Filter out procedural statements that don't need AI analysis"""
    procedural_patterns = [
        r'the house (?:rose|stands adjourned)',
        r'question (?:put and agreed|proposed)',
        r'hon\.\s+members.*(?:upstanding|take.*seats)',
        r'(?:prayers|quorum|communication from the chair)',
        r'next order'
    ]
    
    filtered = []
    for statement in statements:
        is_procedural = False
        for pattern in procedural_patterns:
            if re.search(pattern, statement.lower()):
                is_procedural = True
                break
        
        if not is_procedural:
            filtered.append(statement)
    
    return filtered


def estimate_ai_cost(statements: List[str], cost_per_statement: float = 0.001) -> float:
    """Estimate cost for AI analysis of statements"""
    return len(statements) * cost_per_statement


def build_analysis_prompt(statements: List[str], context: str = "") -> str:
    """Build prompt for AI analysis"""
    if not statements:
        return ""
        
    prompt = f"Analyze these parliamentary statements"
    if context:
        prompt += f" from {context}"
    prompt += ":\n\n"
    
    for i, statement in enumerate(statements[:25], 1):  # Limit to 25 for cost control
        prompt += f"{i}. {statement}\n"
    
    prompt += "\nFor each statement, provide JSON with: stance, quality, confidence"
    return prompt
