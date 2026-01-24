# Phase 2: Extended Documents - Design

## Introduction

This document provides detailed component designs for Phase 2 of the Hansard Tales system. It extends Phase 1's analysis pipeline to process Bills, Questions, and Petitions, enabling comprehensive legislative tracking and cross-document correlation.

**Design Principles**:
- **Build on Phase 1**: Reuse MP identifier, segmenter, LLM analyzer, and citation verifier
- **Anti-Hallucination First**: Every LLM output must include verifiable citations
- **Cost Consciousness**: Stay within $30/month budget through aggressive caching
- **Incremental Processing**: Support processing new documents without reprocessing old ones
- **Cross-Document Correlation**: Enable rich linking between bills, statements, votes, questions, and petitions

**Phase 2 Goals**:
- Process Bills with version tracking and lifecycle management
- Process Questions with answer pairing and ministry categorization
- Process Petitions with status tracking and sponsor linking
- Enable cross-document correlation (bills ↔ statements ↔ votes ↔ questions ↔ petitions)
- Enhance MP profiles with Q&A and bill sponsorship activity
- Generate bill tracking and legislative activity pages

## System Architecture

### Phase 2 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Bill Processing Pipeline                      │
│                                                                 │
│  PDF → Text Extraction → Metadata Extraction → Version Tracking │
│         → Structure Parsing → LLM Summarization                 │
│         → Citation Verification → Storage                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Question Processing Pipeline                    │
│                                                                 │
│  PDF → Text Extraction → Q&A Pairing → Metadata Extraction      │
│         → LLM Categorization → Storage                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Petition Processing Pipeline                    │
│                                                                 │
│  PDF → Text Extraction → Metadata Extraction → Status Tracking  │
│         → LLM Categorization → Storage                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Cross-Document Correlation Engine                   │
│                                                                 │
│  Bill-Statement Linking → Bill-Vote Linking                     │
│         → Question-Statement Linking → Topic Clustering         │
│         → MP Activity Aggregation                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                Enhanced Static Site Generation                   │
│                                                                 │
│  Bill Pages → Question Pages → Petition Pages                   │
│         → Enhanced MP Profiles → Legislative Dashboard          │
└─────────────────────────────────────────────────────────────────┘
```


## Design 1: Bill Scraper and Downloader

### Component Design

**Purpose**: Discover and download all bills from National Assembly website with version tracking

**Technology**: BeautifulSoup + requests (reuse from Phase 0) + version detection

**Builds On**: Phase 0 scraper infrastructure

### Bill URL Patterns

Bills are typically organized by:
- Parliamentary session (e.g., "13th Parliament")
- Year (e.g., "2024")
- Bill type (Public, Private, Money Bill)
- Version (First Reading, Second Reading, Committee, etc.)

### Implementation

```python
from typing import List, Optional, Dict
from dataclasses import dataclass
from pathlib import Path
from datetime import date
import re
import requests
from bs4 import BeautifulSoup
from hansard_tales.scrapers.base_scraper import BaseScraper  # From Phase 0

@dataclass
class BillMetadata:
    """Metadata for a bill"""
    bill_number: str
    title: str
    sponsor: str
    introduction_date: date
    version: str  # "First Reading", "Second Reading", etc.
    url: str
    filename: str
    ministry: Optional[str] = None
    bill_type: Optional[str] = None  # "Public", "Private", "Money Bill"

class BillScraper(BaseScraper):
    """Scrape and download bills from parliament website"""
    
    def __init__(self, config):
        super().__init__(config)
        self.bills_base_url = f"{self.base_url}/the-national-assembly/house-business/bills"
        self.version_patterns = [
            r'First\s+Reading',
            r'Second\s+Reading',
            r'Committee\s+Stage',
            r'Third\s+Reading',
            r'As\s+Passed',
        ]
    
    def discover_bills(self, session: Optional[str] = None) -> List[BillMetadata]:
        """Discover all available bills"""
        bills = []
        
        # Fetch bills index page
        response = self.session.get(self.bills_base_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find bill links (adjust selectors based on actual website structure)
        bill_links = soup.find_all('a', href=re.compile(r'/bills/.*\.pdf'))
        
        for link in bill_links:
            try:
                metadata = self._extract_bill_metadata(link)
                if metadata:
                    bills.append(metadata)
            except Exception as e:
                self.logger.error(f"Failed to extract metadata from {link}: {e}")
        
        return bills
    
    def _extract_bill_metadata(self, link) -> Optional[BillMetadata]:
        """Extract bill metadata from link"""
        url = link.get('href')
        if not url.startswith('http'):
            url = f"{self.base_url}{url}"
        
        # Extract bill number from text or URL
        text = link.get_text(strip=True)
        
        # Pattern: "Bill No. 15 of 2024"
        bill_num_match = re.search(r'Bill\s+No\.\s+(\d+)\s+of\s+(\d{4})', text)
        if not bill_num_match:
            return None
        
        bill_number = f"Bill No. {bill_num_match.group(1)} of {bill_num_match.group(2)}"
        
        # Extract title (usually after bill number)
        title = re.sub(r'Bill\s+No\.\s+\d+\s+of\s+\d{4}[:\-]?\s*', '', text).strip()
        
        # Detect version from URL or text
        version = self._detect_version(url, text)
        
        # Generate filename
        filename = self._generate_filename(bill_number, version)
        
        return BillMetadata(
            bill_number=bill_number,
            title=title,
            sponsor="",  # Extract from PDF content
            introduction_date=date.today(),  # Extract from PDF content
            version=version,
            url=url,
            filename=filename
        )
    
    def _detect_version(self, url: str, text: str) -> str:
        """Detect bill version from URL or text"""
        combined = f"{url} {text}".lower()
        
        for pattern in self.version_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                return re.search(pattern, combined, re.IGNORECASE).group(0)
        
        return "First Reading"  # Default
    
    def _generate_filename(self, bill_number: str, version: str) -> str:
        """Generate standardized filename"""
        # Convert "Bill No. 15 of 2024" to "bill_15_2024_first_reading.pdf"
        num_match = re.search(r'(\d+)\s+of\s+(\d{4})', bill_number)
        if num_match:
            num = num_match.group(1)
            year = num_match.group(2)
            version_slug = version.lower().replace(' ', '_')
            return f"bill_{num}_{year}_{version_slug}.pdf"
        
        return "unknown_bill.pdf"
    
    def download_bill(self, metadata: BillMetadata, output_dir: Path) -> Path:
        """Download a single bill PDF"""
        output_path = output_dir / metadata.filename
        
        # Check if already downloaded
        if output_path.exists():
            self.logger.info(f"Bill already downloaded: {output_path}")
            return output_path
        
        # Download with retry logic
        return self.download_pdf(metadata.url, output_path)
    
    def download_all_bills(self, output_dir: Path) -> List[Path]:
        """Discover and download all bills"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        bills = self.discover_bills()
        self.logger.info(f"Discovered {len(bills)} bills")
        
        downloaded = []
        for bill in bills:
            try:
                path = self.download_bill(bill, output_dir)
                downloaded.append(path)
            except Exception as e:
                self.logger.error(f"Failed to download {bill.bill_number}: {e}")
        
        return downloaded
```



## Design 2: Bill Text Extraction and Structure Parsing

### Component Design

**Purpose**: Extract structured text from bill PDFs preserving hierarchical structure

**Technology**: PyMuPDF + pdfplumber (reuse from Phase 1) + custom structure parser

**Builds On**: Phase 1 PDF processing infrastructure

### Bill Structure

Kenyan bills typically follow this structure:
- Title and Bill Number
- Sponsor information
- Explanatory Memorandum
- Parts (major divisions)
- Sections (numbered clauses)
- Subsections (lettered subdivisions)
- Schedules (appendices)

### Implementation

```python
from typing import List, Dict, Optional
from dataclasses import dataclass
import re
import fitz  # PyMuPDF
import pdfplumber

@dataclass
class BillSection:
    """A section in a bill"""
    section_number: str
    title: str
    text: str
    subsections: List['BillSection'] = None
    page_number: int = 0
    
    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []

@dataclass
class BillStructure:
    """Structured representation of a bill"""
    bill_number: str
    title: str
    sponsor: str
    introduction_date: Optional[str]
    ministry: Optional[str]
    bill_type: Optional[str]
    explanatory_memo: str
    parts: List[Dict[str, any]]  # Parts contain sections
    sections: List[BillSection]
    schedules: List[Dict[str, str]]
    full_text: str

class BillTextExtractor:
    """Extract and parse bill text"""
    
    def __init__(self):
        # Patterns for structure detection
        self.title_pattern = re.compile(r'THE\s+([A-Z\s]+)\s+BILL,?\s+(\d{4})', re.IGNORECASE)
        self.bill_num_pattern = re.compile(r'Bill\s+No\.\s+(\d+)\s+of\s+(\d{4})')
        self.section_pattern = re.compile(r'^(\d+)\.\s+(.+?)$', re.MULTILINE)
        self.subsection_pattern = re.compile(r'^\(([a-z])\)\s+(.+?)$', re.MULTILINE)
        self.part_pattern = re.compile(r'^PART\s+([IVX]+)\s*[-–—]\s*(.+?)$', re.MULTILINE)
    
    def extract_bill(self, pdf_path: Path) -> BillStructure:
        """Extract structured bill content"""
        # Extract raw text
        full_text = self._extract_text(pdf_path)
        
        # Extract metadata
        metadata = self._extract_metadata(full_text)
        
        # Extract explanatory memorandum
        memo = self._extract_explanatory_memo(full_text)
        
        # Parse structure
        parts = self._parse_parts(full_text)
        sections = self._parse_sections(full_text)
        schedules = self._parse_schedules(full_text)
        
        return BillStructure(
            bill_number=metadata.get('bill_number', ''),
            title=metadata.get('title', ''),
            sponsor=metadata.get('sponsor', ''),
            introduction_date=metadata.get('introduction_date'),
            ministry=metadata.get('ministry'),
            bill_type=metadata.get('bill_type'),
            explanatory_memo=memo,
            parts=parts,
            sections=sections,
            schedules=schedules,
            full_text=full_text
        )
    
    def _extract_text(self, pdf_path: Path) -> str:
        """Extract text from PDF"""
        text_parts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        return '\n\n'.join(text_parts)
    
    def _extract_metadata(self, text: str) -> Dict[str, str]:
        """Extract bill metadata from text"""
        metadata = {}
        
        # Extract title
        title_match = self.title_pattern.search(text)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # Extract bill number
        bill_num_match = self.bill_num_pattern.search(text)
        if bill_num_match:
            metadata['bill_number'] = f"Bill No. {bill_num_match.group(1)} of {bill_num_match.group(2)}"
        
        # Extract sponsor (usually after "Sponsored by")
        sponsor_match = re.search(r'Sponsored\s+by[:\s]+(.+?)(?:\n|$)', text, re.IGNORECASE)
        if sponsor_match:
            metadata['sponsor'] = sponsor_match.group(1).strip()
        
        # Extract ministry
        ministry_match = re.search(r'Ministry\s+of\s+(.+?)(?:\n|$)', text, re.IGNORECASE)
        if ministry_match:
            metadata['ministry'] = ministry_match.group(1).strip()
        
        # Detect bill type
        if re.search(r'Money\s+Bill', text, re.IGNORECASE):
            metadata['bill_type'] = 'Money Bill'
        elif re.search(r'Private\s+Bill', text, re.IGNORECASE):
            metadata['bill_type'] = 'Private Bill'
        else:
            metadata['bill_type'] = 'Public Bill'
        
        return metadata
    
    def _extract_explanatory_memo(self, text: str) -> str:
        """Extract explanatory memorandum"""
        # Look for "MEMORANDUM" section
        memo_match = re.search(
            r'MEMORANDUM\s+OF\s+OBJECTS\s+AND\s+REASONS\s*\n+(.*?)(?=\n\n[A-Z\s]+\n|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if memo_match:
            return memo_match.group(1).strip()
        
        return ""
    
    def _parse_parts(self, text: str) -> List[Dict[str, any]]:
        """Parse bill parts"""
        parts = []
        
        for match in self.part_pattern.finditer(text):
            part_num = match.group(1)
            part_title = match.group(2).strip()
            
            parts.append({
                'number': part_num,
                'title': part_title,
                'position': match.start()
            })
        
        return parts
    
    def _parse_sections(self, text: str) -> List[BillSection]:
        """Parse bill sections"""
        sections = []
        
        for match in self.section_pattern.finditer(text):
            section_num = match.group(1)
            section_text = match.group(2).strip()
            
            # Extract full section text (until next section)
            start = match.start()
            next_match = self.section_pattern.search(text, match.end())
            end = next_match.start() if next_match else len(text)
            
            full_section_text = text[start:end].strip()
            
            # Parse subsections
            subsections = self._parse_subsections(full_section_text)
            
            sections.append(BillSection(
                section_number=section_num,
                title=section_text,
                text=full_section_text,
                subsections=subsections
            ))
        
        return sections
    
    def _parse_subsections(self, section_text: str) -> List[BillSection]:
        """Parse subsections within a section"""
        subsections = []
        
        for match in self.subsection_pattern.finditer(section_text):
            letter = match.group(1)
            text = match.group(2).strip()
            
            subsections.append(BillSection(
                section_number=letter,
                title="",
                text=text
            ))
        
        return subsections
    
    def _parse_schedules(self, text: str) -> List[Dict[str, str]]:
        """Parse bill schedules"""
        schedules = []
        
        schedule_pattern = re.compile(r'SCHEDULE\s+([IVX]+|[A-Z])\s*\n+(.*?)(?=SCHEDULE|$)', re.DOTALL)
        
        for match in schedule_pattern.finditer(text):
            schedule_num = match.group(1)
            schedule_text = match.group(2).strip()
            
            schedules.append({
                'number': schedule_num,
                'text': schedule_text
            })
        
        return schedules
```



## Design 3: Bill Version Tracking and Diff Generation

### Component Design

**Purpose**: Track bill versions through legislative process and generate diffs

**Technology**: difflib for text comparison + custom version manager

**Builds On**: Phase 0 database schema (Bill and BillVersion models)

### Implementation

```python
from typing import List, Tuple
from difflib import unified_diff, SequenceMatcher
from dataclasses import dataclass

@dataclass
class BillChange:
    """A change between bill versions"""
    change_type: str  # "addition", "deletion", "modification"
    section: str
    old_text: Optional[str]
    new_text: Optional[str]
    line_number: int

class BillVersionTracker:
    """Track and compare bill versions"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def add_version(
        self,
        bill_id: str,
        version_text: str,
        version_stage: str,
        source_ref: SourceReference
    ) -> BillVersion:
        """Add a new version of a bill"""
        bill = self.db.query(BillORM).filter(BillORM.id == bill_id).first()
        
        # Get next version number
        version_num = len(bill.versions) + 1
        
        # Generate changes summary if previous version exists
        changes_summary = ""
        if bill.versions:
            prev_version = bill.versions[-1]
            changes = self.generate_diff(prev_version.text, version_text)
            changes_summary = self._summarize_changes(changes)
        
        # Create version
        version = BillVersion(
            version_number=version_num,
            title=f"{bill.title} - {version_stage}",
            text=version_text,
            source=source_ref,
            vector_doc_id=str(uuid4()),
            changes_summary=changes_summary
        )
        
        bill.versions.append(version)
        bill.current_version = version_num
        self.db.commit()
        
        return version
    
    def generate_diff(self, old_text: str, new_text: str) -> List[BillChange]:
        """Generate detailed diff between versions"""
        changes = []
        
        old_lines = old_text.split('\n')
        new_lines = new_text.split('\n')
        
        matcher = SequenceMatcher(None, old_lines, new_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                changes.append(BillChange(
                    change_type='modification',
                    section=self._identify_section(old_lines[i1]),
                    old_text='\n'.join(old_lines[i1:i2]),
                    new_text='\n'.join(new_lines[j1:j2]),
                    line_number=i1
                ))
            elif tag == 'delete':
                changes.append(BillChange(
                    change_type='deletion',
                    section=self._identify_section(old_lines[i1]),
                    old_text='\n'.join(old_lines[i1:i2]),
                    new_text=None,
                    line_number=i1
                ))
            elif tag == 'insert':
                changes.append(BillChange(
                    change_type='addition',
                    section=self._identify_section(new_lines[j1]),
                    old_text=None,
                    new_text='\n'.join(new_lines[j1:j2]),
                    line_number=j1
                ))
        
        return changes
    
    def _identify_section(self, line: str) -> str:
        """Identify which section a line belongs to"""
        section_match = re.match(r'^(\d+)\.\s+', line)
        if section_match:
            return f"Section {section_match.group(1)}"
        return "Unknown"
    
    def _summarize_changes(self, changes: List[BillChange]) -> str:
        """Generate human-readable summary of changes"""
        additions = sum(1 for c in changes if c.change_type == 'addition')
        deletions = sum(1 for c in changes if c.change_type == 'deletion')
        modifications = sum(1 for c in changes if c.change_type == 'modification')
        
        summary_parts = []
        if additions:
            summary_parts.append(f"{additions} addition(s)")
        if deletions:
            summary_parts.append(f"{deletions} deletion(s)")
        if modifications:
            summary_parts.append(f"{modifications} modification(s)")
        
        return ", ".join(summary_parts)
```

## Design 4: Bill Summarization with LLM

### Component Design

**Purpose**: Generate AI summaries of bills with key provisions and citations

**Technology**: Claude 3.5 Haiku (reuse from Phase 1) + structured prompts

**Builds On**: Phase 1 LLM analyzer and citation verifier

### Implementation

```python
from pydantic import BaseModel, Field
from typing import List

class BillSummary(BaseModel):
    """LLM-generated bill summary"""
    summary: str = Field(..., description="2-3 paragraph summary")
    key_provisions: List[str] = Field(..., max_items=5)
    affected_laws: List[str]
    objectives: str
    citations: List[str]  # Direct quotes from bill

class BillSummarizer:
    """Generate bill summaries using LLM"""
    
    def __init__(self, llm_analyzer: LLMAnalyzer, citation_verifier: CitationVerifier):
        self.llm = llm_analyzer
        self.verifier = citation_verifier
    
    def summarize_bill(self, bill_structure: BillStructure) -> BillSummary:
        """Generate summary of a bill"""
        # Build prompt
        prompt = self._build_prompt(bill_structure)
        
        # Call LLM
        response = self.llm.client.messages.create(
            model=self.llm.model,
            max_tokens=1024,
            system="""You are analyzing Kenyan parliamentary bills.

Generate a summary with:
1. 2-3 paragraph overview of the bill
2. 3-5 key provisions (specific clauses)
3. List of laws this bill amends or affects
4. Summary of bill objectives

CRITICAL: Include direct quotes as citations for all key points.""",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        summary = self._parse_response(response.content[0].text)
        
        # Verify citations
        verified_citations = []
        for citation in summary.citations:
            verified = self.verifier.verify_citation(
                citation,
                source_id=bill_structure.bill_number,
                threshold=0.90
            )
            if verified.verification_status == "verified":
                verified_citations.append(verified.quote)
        
        summary.citations = verified_citations
        
        return summary
    
    def _build_prompt(self, bill: BillStructure) -> str:
        """Build summarization prompt"""
        # Limit text to first 5000 chars to control costs
        text_sample = bill.full_text[:5000]
        
        return f"""Summarize this Kenyan parliamentary bill:

BILL: {bill.title}
NUMBER: {bill.bill_number}
SPONSOR: {bill.sponsor}

EXPLANATORY MEMORANDUM:
{bill.explanatory_memo[:1000]}

BILL TEXT (excerpt):
{text_sample}

Provide summary in JSON format:
{{
  "summary": "2-3 paragraph overview",
  "key_provisions": ["provision 1", "provision 2", ...],
  "affected_laws": ["law 1", "law 2", ...],
  "objectives": "summary of objectives",
  "citations": ["exact quote 1", "exact quote 2", ...]
}}"""
```



## Design 5: Question Scraper and Q&A Pairing

### Component Design

**Purpose**: Scrape questions and pair with answers

**Technology**: BeautifulSoup + custom Q&A matching algorithm

**Builds On**: Phase 0 scraper infrastructure

### Implementation Summary

```python
class QuestionScraper(BaseScraper):
    """Scrape parliamentary questions"""
    
    def discover_questions(self, date_range: Tuple[date, date]) -> List[QuestionMetadata]:
        """Discover questions in date range"""
        # Scrape questions index page
        # Extract question PDFs by date
        # Return metadata list
        pass
    
    def download_questions(self, output_dir: Path) -> List[Path]:
        """Download all question PDFs"""
        pass

class QuestionAnswerPairer:
    """Pair questions with answers"""
    
    def pair_qa(self, question_text: str, document_text: str) -> Optional[str]:
        """Find answer for question in document"""
        # Use pattern matching to find Q&A pairs
        # Questions typically numbered: "Question No. 123"
        # Answers follow immediately or in separate section
        # Return answer text if found
        pass
    
    def extract_questions(self, pdf_path: Path) -> List[Question]:
        """Extract all questions from PDF"""
        text = self._extract_text(pdf_path)
        
        # Pattern: "Question No. 123\nAsked by: Hon. Name\nQuestion: ..."
        question_pattern = re.compile(
            r'Question\s+No\.\s+(\d+).*?Asked\s+by[:\s]+(.+?)\n+(.+?)(?=Question\s+No\.|$)',
            re.DOTALL | re.IGNORECASE
        )
        
        questions = []
        for match in question_pattern.finditer(text):
            q_num = match.group(1)
            asker = match.group(2).strip()
            q_text = match.group(3).strip()
            
            # Try to find answer
            answer = self.pair_qa(q_text, text)
            
            questions.append(Question(
                question_number=q_num,
                asker_id=self._resolve_mp(asker),
                question_text=q_text,
                answer_text=answer,
                question_date=self._extract_date(text),
                chamber=Chamber.NATIONAL_ASSEMBLY,
                question_type=self._detect_type(text),
                source=self._create_source_ref(pdf_path),
                vector_doc_id=str(uuid4())
            ))
        
        return questions
```

## Design 6: Petition Scraper and Processor

### Component Design

**Purpose**: Scrape petitions and track status

**Technology**: BeautifulSoup + status tracking system

**Builds On**: Phase 0 scraper infrastructure

### Implementation Summary

```python
class PetitionScraper(BaseScraper):
    """Scrape public petitions"""
    
    def discover_petitions(self) -> List[PetitionMetadata]:
        """Discover all petitions"""
        pass
    
    def download_petitions(self, output_dir: Path) -> List[Path]:
        """Download petition PDFs"""
        pass

class PetitionProcessor:
    """Process petition documents"""
    
    def extract_petition(self, pdf_path: Path) -> Petition:
        """Extract petition from PDF"""
        text = self._extract_text(pdf_path)
        
        # Extract petition number
        pet_num = self._extract_petition_number(text)
        
        # Extract petitioner
        petitioner = self._extract_petitioner(text)
        
        # Extract sponsor MP
        sponsor = self._extract_sponsor(text)
        
        # Extract prayer (what is requested)
        prayer = self._extract_prayer(text)
        
        # Extract status
        status = self._extract_status(text)
        
        return Petition(
            petition_number=pet_num,
            title=self._extract_title(text),
            petitioner=petitioner,
            sponsor_id=self._resolve_mp(sponsor),
            submission_date=self._extract_date(text),
            chamber=Chamber.NATIONAL_ASSEMBLY,
            petition_text=text,
            prayer=prayer,
            status=status,
            source=self._create_source_ref(pdf_path),
            vector_doc_id=str(uuid4())
        )
    
    def _extract_prayer(self, text: str) -> str:
        """Extract prayer section"""
        # Pattern: "PRAYER" or "The petitioners pray that"
        prayer_pattern = re.compile(
            r'(?:PRAYER|The\s+petitioners?\s+pray\s+that)[:\s]+(.*?)(?=\n\n|$)',
            re.IGNORECASE | re.DOTALL
        )
        match = prayer_pattern.search(text)
        return match.group(1).strip() if match else ""
```

## Design 7: Cross-Document Correlation Engine

### Component Design

**Purpose**: Link bills, statements, votes, questions, and petitions

**Technology**: Vector similarity + rule-based matching + NER

**Builds On**: Phase 1 bill-statement linker + Phase 0 vector DB

### Implementation Summary

```python
class CorrelationEngine:
    """Correlate documents across types"""
    
    def __init__(self, db_session, vector_db, mp_identifier):
        self.db = db_session
        self.vector_db = vector_db
        self.mp_identifier = mp_identifier
    
    def correlate_bill_statements(self, bill_id: str) -> List[str]:
        """Find statements discussing a bill"""
        bill = self.db.query(BillORM).filter(BillORM.id == bill_id).first()
        
        # Method 1: Direct mentions (from Phase 1)
        mentions = self._find_bill_mentions(bill)
        
        # Method 2: Vector similarity
        similar = self._find_similar_statements(bill)
        
        # Combine and deduplicate
        statement_ids = list(set(mentions + similar))
        
        return statement_ids
    
    def correlate_bill_votes(self, bill_id: str) -> List[str]:
        """Find votes on a bill"""
        bill = self.db.query(BillORM).filter(BillORM.id == bill_id).first()
        
        # Votes typically reference bill number
        votes = self.db.query(VoteRecordORM).filter(
            VoteRecordORM.motion_text.contains(bill.bill_number)
        ).all()
        
        return [str(v.id) for v in votes]
    
    def correlate_question_statements(self, question_id: str) -> List[str]:
        """Find statements related to a question"""
        question = self.db.query(QuestionORM).filter(QuestionORM.id == question_id).first()
        
        # Oral questions appear in Hansard
        if question.question_type == QuestionType.ORAL:
            # Find statements on same date mentioning question number
            statements = self.db.query(StatementORM).filter(
                StatementORM.date == question.question_date,
                StatementORM.text.contains(question.question_number)
            ).all()
            
            return [str(s.id) for s in statements]
        
        return []
    
    def build_bill_lifecycle(self, bill_id: str) -> Dict:
        """Build complete bill lifecycle"""
        bill = self.db.query(BillORM).filter(BillORM.id == bill_id).first()
        
        return {
            'bill': bill,
            'versions': bill.versions,
            'statements': self.correlate_bill_statements(bill_id),
            'votes': self.correlate_bill_votes(bill_id),
            'questions': self._find_related_questions(bill_id),
            'timeline': self._generate_timeline(bill)
        }
    
    def aggregate_mp_activity(self, mp_id: str) -> Dict:
        """Aggregate all MP activity"""
        return {
            'bills_sponsored': self._get_sponsored_bills(mp_id),
            'questions_asked': self._get_questions_asked(mp_id),
            'petitions_sponsored': self._get_petitions_sponsored(mp_id),
            'statements': self._get_statements(mp_id),
            'votes': self._get_votes(mp_id)
        }
```



## Design 8: Enhanced MP Profile Generator

### Component Design

**Purpose**: Extend MP profiles with bill, question, and petition activity

**Technology**: SQL aggregation + Phase 1 profile generator

**Builds On**: Phase 1 MP profile generator

### Implementation Summary

```python
class EnhancedMPProfileGenerator(MPProfileGenerator):
    """Generate enhanced MP profiles with Phase 2 data"""
    
    def generate_profile(self, mp_id: str) -> EnhancedMPProfile:
        """Generate comprehensive MP profile"""
        # Get Phase 1 profile
        base_profile = super().generate_profile(mp_id)
        
        # Add Phase 2 data
        bills = self._get_bill_activity(mp_id)
        questions = self._get_question_activity(mp_id)
        petitions = self._get_petition_activity(mp_id)
        
        return EnhancedMPProfile(
            **base_profile.__dict__,
            bills_sponsored=bills['sponsored'],
            bills_co_sponsored=bills['co_sponsored'],
            bill_success_rate=bills['success_rate'],
            questions_asked=questions['total'],
            questions_answered=questions['answered'],
            questions_by_ministry=questions['by_ministry'],
            petitions_sponsored=petitions['total'],
            petition_topics=petitions['topics']
        )
```

## Design 9: Extended Static Site Generator

### Component Design

**Purpose**: Generate pages for bills, questions, petitions, and dashboard

**Technology**: Jinja2 (reuse from Phase 1) + new templates

**Builds On**: Phase 1 static site generator

### Implementation Summary

```python
class ExtendedSiteGenerator(StaticSiteGenerator):
    """Generate extended site with Phase 2 content"""
    
    def generate_site(self):
        """Generate complete site"""
        # Phase 1 pages
        super().generate_site()
        
        # Phase 2 pages
        self._generate_bill_pages()
        self._generate_question_pages()
        self._generate_petition_pages()
        self._generate_dashboard()
    
    def _generate_bill_pages(self):
        """Generate bill tracking pages"""
        bills = self.db.query(BillORM).all()
        
        # Bill directory
        self._render_template('bill_list.html', {'bills': bills}, 'bills/index.html')
        
        # Individual bill pages
        for bill in bills:
            lifecycle = self.correlation_engine.build_bill_lifecycle(str(bill.id))
            self._render_template(
                'bill_detail.html',
                {'bill': bill, 'lifecycle': lifecycle},
                f'bills/{self._slugify(bill.bill_number)}.html'
            )
    
    def _generate_dashboard(self):
        """Generate legislative activity dashboard"""
        dashboard_data = {
            'recent_bills': self._get_recent_bills(10),
            'recent_questions': self._get_recent_questions(10),
            'recent_petitions': self._get_recent_petitions(10),
            'active_debates': self._get_active_debates(),
            'upcoming_votes': self._get_upcoming_votes()
        }
        
        self._render_template('dashboard.html', dashboard_data, 'dashboard/index.html')
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Bill Processing Properties

**Property 1: Bill discovery completeness**
- *For any* set of bills on the parliament website, the scraper should discover all bills that match the discovery criteria
- **Validates: Requirements 1.1**

**Property 2: Version tracking consistency**
- *For any* bill with multiple versions, all versions should be linked to the same bill ID and ordered chronologically
- **Validates: Requirements 1.3**

**Property 3: Bill metadata extraction completeness**
- *For any* bill PDF, all required metadata fields (number, title, sponsor, date, ministry, type) should be extracted or marked as missing
- **Validates: Requirements 1.4**

**Property 4: Bill structure preservation**
- *For any* bill with hierarchical structure (parts, sections, subsections), the extracted structure should preserve the hierarchy
- **Validates: Requirements 1.2**

**Property 5: Bill summarization citation requirement**
- *For any* bill summary generated by LLM, the summary must include at least one verifiable citation from the source bill
- **Validates: Requirements 1.5**

**Property 6: Bill-statement correlation accuracy**
- *For any* bill mentioned in a statement, the correlation engine should link the statement to the correct bill (no false positives)
- **Validates: Requirements 1.6**

**Property 7: Bill-vote correlation completeness**
- *For any* vote record that references a bill number, the vote should be linked to that bill
- **Validates: Requirements 1.7**

**Property 8: Version diff generation**
- *For any* two versions of the same bill, the diff generator should identify all additions, deletions, and modifications
- **Validates: Requirements 1.3**

### Question Processing Properties

**Property 9: Question discovery completeness**
- *For any* date range, the scraper should discover all question PDFs available for that range
- **Validates: Requirements 2.1**

**Property 10: Q&A pairing accuracy**
- *For any* question with an answer in the same document, the pairer should correctly match question to answer
- **Validates: Requirements 2.2**

**Property 11: Question metadata extraction completeness**
- *For any* question PDF, all required metadata fields (number, asker, respondent, dates, type, ministry) should be extracted or marked as missing
- **Validates: Requirements 2.3**

**Property 12: Question type classification**
- *For any* question, it should be classified as either oral or written based on document indicators
- **Validates: Requirements 2.3**

**Property 13: Question categorization bounds**
- *For any* question categorized by LLM, it should have exactly 1 primary topic and 0-3 secondary topics
- **Validates: Requirements 2.4**

**Property 14: Oral question-statement linking**
- *For any* oral question, if it appears in Hansard on the same date, it should be linked to the corresponding statements
- **Validates: Requirements 2.5**

### Petition Processing Properties

**Property 15: Petition discovery completeness**
- *For any* set of petitions on the parliament website, the scraper should discover all available petitions
- **Validates: Requirements 3.1**

**Property 16: Petition text extraction completeness**
- *For any* petition PDF, all required sections (title, petitioner, text, prayer, sponsor) should be extracted or marked as missing
- **Validates: Requirements 3.2**

**Property 17: Petition metadata extraction completeness**
- *For any* petition PDF, all required metadata fields (number, date, sponsor, committee, status) should be extracted or marked as missing
- **Validates: Requirements 3.3**

**Property 18: Petition categorization bounds**
- *For any* petition categorized by LLM, it should have exactly 1 primary topic and 0-3 secondary topics
- **Validates: Requirements 3.4**

**Property 19: Petition status tracking**
- *For any* petition, status changes should be tracked chronologically with timestamps
- **Validates: Requirements 3.5**

### Cross-Document Correlation Properties

**Property 20: Bill lifecycle completeness**
- *For any* bill, the lifecycle should include all versions, related statements, related votes, and related questions
- **Validates: Requirements 4.1**

**Property 21: MP activity aggregation completeness**
- *For any* MP, the activity summary should include all bills sponsored, questions asked, petitions sponsored, statements made, and votes cast
- **Validates: Requirements 4.2**

**Property 22: Topic-based grouping consistency**
- *For any* topic, all documents (bills, questions, petitions) tagged with that topic should be grouped together
- **Validates: Requirements 4.3**

**Property 23: Timeline chronological ordering**
- *For any* bill lifecycle timeline, all events should be ordered chronologically by date
- **Validates: Requirements 4.1**

### Enhanced MP Profile Properties

**Property 24: Bill sponsorship tracking completeness**
- *For any* MP profile, all bills where the MP is listed as sponsor or co-sponsor should be included
- **Validates: Requirements 5.1**

**Property 25: Question activity tracking completeness**
- *For any* MP profile, all questions asked by the MP should be included with answer status
- **Validates: Requirements 5.2**

**Property 26: Petition sponsorship tracking completeness**
- *For any* MP profile, all petitions sponsored by the MP should be included with status
- **Validates: Requirements 5.3**

**Property 27: Success rate calculation accuracy**
- *For any* MP, the bill success rate should equal (passed bills / total bills sponsored) * 100
- **Validates: Requirements 5.1**

### Site Generation Properties

**Property 28: Bill page generation completeness**
- *For any* bill in the database, an individual bill page should be generated
- **Validates: Requirements 6.1**

**Property 29: Question page generation completeness**
- *For any* question in the database, an individual question page should be generated
- **Validates: Requirements 6.2**

**Property 30: Petition page generation completeness**
- *For any* petition in the database, an individual petition page should be generated
- **Validates: Requirements 6.3**

**Property 31: Dashboard data freshness**
- *For any* dashboard generation, it should include the most recent bills, questions, and petitions based on date
- **Validates: Requirements 6.4**

**Property 32: Search functionality coverage**
- *For any* document (bill, question, petition) in the database, it should be findable through the search interface
- **Validates: Requirements 6.1, 6.2**

### Data Quality Properties

**Property 33: No duplicate downloads**
- *For any* document (bill, question, petition), downloading it multiple times should not create duplicate database records
- **Validates: Requirements 1.1, 2.1, 3.1**

**Property 34: Data completeness verification**
- *For any* processing run, the system should verify that all documents from the source are present in the database
- **Validates: Requirements 8.1**

**Property 35: Missing data flagging**
- *For any* document with incomplete metadata, the system should flag it for manual review
- **Validates: Requirements 8.1**

**Property 36: Cost tracking accuracy**
- *For any* LLM API call, the cost should be tracked and aggregated correctly
- **Validates: Requirements 7.2**



## Technology Stack

### Core Technologies (from Phase 0/1)

**Database**: PostgreSQL/SQLite
- SQLAlchemy ORM for data models
- Alembic for migrations
- Support for both SQLite (dev) and PostgreSQL (prod)

**Vector Database**: Qdrant/ChromaDB
- Sentence-transformers for embeddings
- Semantic search for document correlation
- Reuse Phase 0 vector DB infrastructure

**LLM**: Claude 3.5 Haiku
- Bill summarization
- Question/petition categorization
- Cost: ~$1 per 1000 documents
- Reuse Phase 1 LLM analyzer

**PDF Processing**: PyMuPDF + pdfplumber
- Text extraction
- Table extraction (for structured data)
- Reuse Phase 1 PDF processor

**Web Scraping**: BeautifulSoup + requests
- Bill/question/petition discovery
- Metadata extraction
- Reuse Phase 0 scraper infrastructure

**Site Generation**: Jinja2
- Static HTML generation
- Template-based rendering
- Reuse Phase 1 site generator

### New Technologies for Phase 2

**Diff Generation**: difflib (Python standard library)
- Bill version comparison
- Change tracking
- No additional dependencies

**Text Similarity**: fuzzywuzzy
- Q&A pairing
- Entity matching
- Already used in Phase 1

## Cost Analysis

### LLM Usage Estimates

**Bill Summarization**:
- Average bill: ~10,000 tokens input, ~500 tokens output
- Cost per bill: ~$0.01
- 100 bills: ~$1.00

**Question Categorization**:
- Average question: ~500 tokens input, ~100 tokens output
- Cost per question: ~$0.001
- 1000 questions: ~$1.00

**Petition Categorization**:
- Average petition: ~1000 tokens input, ~100 tokens output
- Cost per petition: ~$0.002
- 500 petitions: ~$1.00

**Total Monthly Estimate**:
- Phase 1 (Hansard analysis): ~$15/month
- Phase 2 (Bills, Questions, Petitions): ~$15/month
- **Total: ~$30/month** (within budget)

### Cost Optimization Strategies

1. **Aggressive Caching**: Cache all LLM outputs (40% cost reduction)
2. **Batch Processing**: Process similar documents together
3. **Incremental Updates**: Only process new/changed documents
4. **Smart Sampling**: Summarize only substantive bills
5. **Context Pruning**: Limit input text to essential sections

## Error Handling

### Bill Processing Errors

**Missing Metadata**: Flag for manual review, continue processing
**Version Detection Failure**: Default to "First Reading", log warning
**Structure Parsing Failure**: Store raw text, flag for review
**LLM Timeout**: Retry with exponential backoff, cache failures

### Question Processing Errors

**Q&A Pairing Failure**: Mark as unanswered, flag for review
**MP Resolution Failure**: Store raw name, flag for manual linking
**Date Extraction Failure**: Use PDF filename date, log warning

### Petition Processing Errors

**Prayer Extraction Failure**: Use full text, flag for review
**Status Detection Failure**: Default to "submitted", log warning
**Sponsor Resolution Failure**: Store raw name, flag for manual linking

### Correlation Errors

**False Positives**: Use confidence thresholds, manual review queue
**Missing Links**: Log potential matches below threshold
**Circular References**: Detect and break cycles

## Testing Strategy

### Unit Tests

**Bill Processor**:
- Test metadata extraction with sample PDFs
- Test structure parsing with various bill formats
- Test version detection with known versions
- Test diff generation with modified bills

**Question Processor**:
- Test Q&A pairing with sample documents
- Test metadata extraction
- Test type classification (oral vs written)

**Petition Processor**:
- Test text extraction
- Test prayer extraction
- Test status detection

**Correlation Engine**:
- Test bill-statement linking with known pairs
- Test bill-vote linking
- Test question-statement linking

### Property-Based Tests

**Property Tests** (minimum 100 iterations each):
- Bill discovery completeness
- Version tracking consistency
- Metadata extraction completeness
- Q&A pairing accuracy
- Correlation accuracy
- MP activity aggregation
- Page generation completeness

### Integration Tests

**End-to-End Pipelines**:
- Bill processing: scrape → extract → summarize → store → generate pages
- Question processing: scrape → extract → pair → categorize → store → generate pages
- Petition processing: scrape → extract → categorize → store → generate pages
- Correlation: process all documents → correlate → verify links

### Manual Validation

**Accuracy Checks** (sample-based):
- 50 bills: verify metadata accuracy
- 100 questions: verify Q&A pairing
- 30 petitions: verify text extraction
- 50 correlations: verify link accuracy

## Performance Targets

### Processing Times

**Bill Processing**: <5 minutes per bill
- Text extraction: <30 seconds
- Structure parsing: <1 minute
- LLM summarization: <2 minutes
- Storage: <30 seconds

**Question Processing**: <2 minutes per question list
- Text extraction: <30 seconds
- Q&A pairing: <30 seconds
- Categorization: <30 seconds
- Storage: <30 seconds

**Petition Processing**: <3 minutes per petition
- Text extraction: <1 minute
- Categorization: <1 minute
- Storage: <30 seconds

**Correlation Processing**: <10 minutes for full dataset
- Bill-statement linking: <5 minutes
- Bill-vote linking: <2 minutes
- Question-statement linking: <2 minutes
- MP aggregation: <1 minute

**Site Generation**: <15 minutes for complete site
- Bill pages: <5 minutes
- Question pages: <3 minutes
- Petition pages: <2 minutes
- MP profiles: <3 minutes
- Dashboard: <2 minutes

### Optimization Strategies

1. **Parallel Processing**: Use ThreadPoolExecutor for independent documents
2. **Database Indexing**: Index frequently queried fields (bill_number, question_number, dates)
3. **Vector DB Optimization**: Batch embedding generation
4. **Caching**: Cache LLM outputs, embeddings, and correlation results
5. **Incremental Updates**: Only process new/changed documents

## Implementation Timeline

### Week 7: Bill Processing
- Bill scraper and downloader
- Bill text extraction and structure parsing
- Bill version tracking
- Unit tests

### Week 8: Bill Analysis and Correlation
- Bill summarization with LLM
- Bill-statement correlation
- Bill-vote correlation
- Integration tests

### Week 9: Questions and Petitions
- Question scraper and Q&A pairing
- Petition scraper and processor
- LLM categorization for both
- Unit tests

### Week 10: Integration and Site Generation
- Cross-document correlation engine
- Enhanced MP profiles
- Extended site generator
- End-to-end tests
- Documentation

## File Structure

```
hansard_tales/
├── scrapers/
│   ├── bill_scraper.py           # Design 1
│   ├── question_scraper.py       # Design 5
│   └── petition_scraper.py       # Design 6
├── processors/
│   ├── bill_processor.py         # Design 2
│   ├── bill_version_tracker.py   # Design 3
│   ├── bill_summarizer.py        # Design 4
│   ├── question_processor.py     # Design 5
│   └── petition_processor.py     # Design 6
├── correlation/
│   └── correlation_engine.py     # Design 7
├── profiles/
│   └── enhanced_mp_profile.py    # Design 8
├── site/
│   └── extended_generator.py     # Design 9
└── tests/
    ├── test_bill_scraper.py
    ├── test_bill_processor.py
    ├── test_bill_version_tracker.py
    ├── test_bill_summarizer.py
    ├── test_question_processor.py
    ├── test_petition_processor.py
    ├── test_correlation_engine.py
    ├── test_enhanced_mp_profile.py
    └── test_extended_generator.py
```

## Configuration

```yaml
# config/phase2.yaml
phase2:
  bills:
    scraper:
      base_url: "https://parliament.go.ke/the-national-assembly/house-business/bills"
      download_dir: "data/bills"
    processor:
      max_text_length: 50000  # Limit for LLM input
      summarization_enabled: true
    version_tracking:
      enabled: true
      diff_generation: true
  
  questions:
    scraper:
      base_url: "https://parliament.go.ke/the-national-assembly/house-business/questions"
      download_dir: "data/questions"
    processor:
      qa_pairing_threshold: 0.85
      categorization_enabled: true
  
  petitions:
    scraper:
      base_url: "https://parliament.go.ke/the-national-assembly/house-business/petitions"
      download_dir: "data/petitions"
    processor:
      categorization_enabled: true
      status_tracking: true
  
  correlation:
    bill_statement_threshold: 0.80
    question_statement_threshold: 0.85
    vector_similarity_enabled: true
    max_correlations_per_document: 50
  
  site_generation:
    bill_pages_enabled: true
    question_pages_enabled: true
    petition_pages_enabled: true
    dashboard_enabled: true
    search_enabled: true
```

## Risk Mitigation

**Risk 1**: Bill structure varies significantly
- **Mitigation**: Flexible parser, fallback to raw text, manual review queue

**Risk 2**: Q&A pairing accuracy < 95%
- **Mitigation**: Multiple pairing strategies, confidence thresholds, manual review

**Risk 3**: LLM costs exceed $30/month
- **Mitigation**: Aggressive caching, batch processing, budget alerts

**Risk 4**: Correlation false positives
- **Mitigation**: Confidence thresholds, manual review queue, user feedback

**Risk 5**: Processing time exceeds targets
- **Mitigation**: Parallel processing, caching, incremental updates

## Summary

This design document provides detailed specifications for implementing Phase 2 of the Hansard Tales system. Each component is designed with:

- Clear purpose and technology choices
- Concrete implementation code
- Correctness properties for testing
- Integration points with Phase 1 components

The design prioritizes:
1. **Reuse**: Build on Phase 0/1 infrastructure
2. **Cost Control**: Stay within $30/month budget
3. **Accuracy**: High thresholds for all processing tasks
4. **Testability**: Property-based tests for all components
5. **Maintainability**: Clear separation of concerns

**Key Innovations**:
- Bill version tracking with diff generation
- Q&A pairing algorithm
- Cross-document correlation engine
- Enhanced MP profiles with legislative activity
- Comprehensive legislative dashboard

**Next Step**: Create `tasks.md` with actionable implementation tasks.

