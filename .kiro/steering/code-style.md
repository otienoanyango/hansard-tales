---
inclusion: always
---

# Code Style Guide for Hansard Tales

## Overview

This project follows Python best practices with emphasis on readability, maintainability, and testability.

## Python Version

- **Target**: Python 3.12+
- Use modern Python features where appropriate
- Maintain compatibility with Python 3.10+ when possible

## Code Formatting

### Line Length
- Maximum: 100 characters (soft limit)
- Docstrings: 80 characters
- Break long lines logically

### Imports
```python
# Standard library
import os
import sys
from pathlib import Path
from datetime import datetime, date

# Third-party
import pytest
import sqlite3
from unittest.mock import Mock, patch

# Local
from hansard_tales.processors.pdf_processor import PDFProcessor
from hansard_tales.database.db_updater import DatabaseUpdater
```

**Order:**
1. Standard library
2. Third-party packages
3. Local modules

**Rules:**
- One import per line for `from` imports
- Group related imports
- Sort alphabetically within groups
- Avoid wildcard imports (`from module import *`)

### Naming Conventions

**Variables and Functions**: `snake_case`
```python
def process_pdf_file(pdf_path, output_dir):
    file_count = 0
    processed_items = []
```

**Classes**: `PascalCase`
```python
class PDFProcessor:
    class HistoricalDataProcessor:
```

**Constants**: `UPPER_SNAKE_CASE`
```python
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
DATEPARSER_AVAILABLE = True
```

**Private/Internal**: Prefix with `_`
```python
def _internal_helper():
    """Internal function."""
    
class MyClass:
    def _private_method(self):
        """Private method."""
```

**Module-level "private"**: Single underscore
```python
_internal_cache = {}

def _extract_date_from_filename(path):
    """Module-internal function."""
```

## Documentation

### Module Docstrings
```python
"""
Module description.

This module provides functionality for [purpose].
Key features:
- Feature 1
- Feature 2

Usage:
    from module import function
    result = function(args)
"""
```

### Function Docstrings
```python
def process_single_pdf(pdf_path: Path, db_path: Path, force: bool = False) -> ProcessedPDF:
    """
    Process a single PDF file (stateless, idempotent, portable).
    
    This function is designed to be:
    - Stateless: No shared state between calls
    - Idempotent: Can be called multiple times safely
    - Portable: Can run on any machine
    
    Args:
        pdf_path: Path to PDF file
        db_path: Path to database
        force: Force reprocess even if already processed
        
    Returns:
        ProcessedPDF with processing results
        
    Raises:
        ValueError: If pdf_path is invalid
        
    Example:
        >>> result = process_single_pdf(Path("test.pdf"), Path("db.db"))
        >>> print(result.status)
        'success'
    """
```

### Class Docstrings
```python
class HistoricalDataProcessor:
    """
    Process historical Hansard data with quality assurance.
    
    This class manages the complete pipeline for processing historical
    parliamentary data including downloading, processing, and validation.
    
    Attributes:
        year: Year to process (optional)
        start_date: Start date for filtering
        end_date: End date for filtering
        workers: Number of parallel workers
        
    Example:
        >>> processor = HistoricalDataProcessor(year=2024, workers=4)
        >>> success = processor.run()
    """
```

### Inline Comments
```python
# Good: Explain WHY, not WHAT
# Use content hashing to detect duplicates across sessions
statement_hash = compute_hash(statement.text)

# Bad: Obvious comment
# Increment counter
counter += 1

# Good: Clarify complex logic
# SQLite doesn't have a built-in UPSERT before 3.24,
# so we use INSERT OR REPLACE which may change row IDs
cursor.execute("INSERT OR REPLACE INTO ...")
```

## Type Hints

### Use Type Hints
```python
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from datetime import date

def extract_date(filename: str) -> Optional[date]:
    """Extract date from filename."""
    
def process_files(paths: List[Path]) -> Dict[str, int]:
    """Process multiple files."""
    
def get_stats() -> Tuple[int, int, float]:
    """Return count, total, average."""
```

### Complex Types
```python
from typing import Union, Callable, TypeVar
from dataclasses import dataclass

@dataclass
class ProcessedPDF:
    """Result of processing a single PDF."""
    pdf_path: str
    pdf_date: str
    status: str
    reason: Optional[str] = None
    statements: int = 0
    processing_time: float = 0.0
```

## Error Handling

### Specific Exceptions
```python
# Good: Specific exception
try:
    result = parse_date(date_str)
except ValueError as e:
    logger.error(f"Invalid date format: {e}")
    return None

# Bad: Catch-all
try:
    result = parse_date(date_str)
except Exception:  # Too broad
    return None
```

### Error Messages
```python
# Good: Descriptive error
raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")

# Bad: Vague error
raise ValueError("Invalid input")
```

### Logging vs Exceptions
```python
# Use exceptions for exceptional conditions
if not pdf_path.exists():
    raise FileNotFoundError(f"PDF not found: {pdf_path}")

# Use logging for expected issues
if not statements:
    logger.warning(f"No statements found in {pdf_path}")
    return ProcessedPDF(status='warning', reason='no_statements')
```

## Data Structures

### Use dataclasses
```python
from dataclasses import dataclass

@dataclass
class ProcessedPDF:
    """Result of processing a single PDF."""
    pdf_path: str
    pdf_date: str
    status: str
    statements: int = 0
    
# Usage
result = ProcessedPDF(
    pdf_path="test.pdf",
    pdf_date="2024-01-01",
    status="success",
    statements=10
)
```

### Use Enums for Constants
```python
from enum import Enum

class Status(Enum):
    """Processing status."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    SKIPPED = "skipped"

# Usage
result.status = Status.SUCCESS
```

### Prefer Pathlib
```python
from pathlib import Path

# Good: Use Path objects
pdf_path = Path("data/pdfs/test.pdf")
if pdf_path.exists():
    content = pdf_path.read_text()

# Bad: String manipulation
pdf_path = "data/pdfs/test.pdf"
if os.path.exists(pdf_path):
    with open(pdf_path) as f:
        content = f.read()
```

## Functions

### Keep Functions Focused
```python
# Good: Single responsibility
def extract_date_from_filename(path: Path) -> Optional[date]:
    """Extract date from filename."""
    # Only handles date extraction
    
def validate_date_range(start: date, end: date) -> bool:
    """Validate date range."""
    # Only handles validation

# Bad: Multiple responsibilities
def process_and_validate_date(path: Path, start: date, end: date):
    """Extract, validate, and format date."""
    # Does too many things
```

### Function Length
- Target: < 50 lines
- If longer, consider breaking into smaller functions
- Each function should do one thing well

### Default Arguments
```python
# Good: Immutable defaults
def process(path: Path, force: bool = False, workers: int = 4):
    """Process with defaults."""

# Bad: Mutable defaults
def process(path: Path, options: dict = {}):  # Don't do this!
    """Process with options."""

# Good: Use None for mutable defaults
def process(path: Path, options: Optional[dict] = None):
    """Process with options."""
    if options is None:
        options = {}
```

## Classes

### Class Structure
```python
class MyClass:
    """Class docstring."""
    
    # Class variables
    DEFAULT_TIMEOUT = 30
    
    def __init__(self, param: str):
        """Initialize instance."""
        # Public attributes
        self.param = param
        
        # Private attributes
        self._cache = {}
        
    # Public methods
    def public_method(self):
        """Public method."""
        
    # Private methods
    def _private_method(self):
        """Private helper method."""
        
    # Special methods
    def __str__(self):
        """String representation."""
        return f"MyClass({self.param})"
```

### Prefer Composition Over Inheritance
```python
# Good: Composition
class Processor:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.mp_identifier = MPIdentifier()
        
# Use inheritance only for true "is-a" relationships
class SpecializedProcessor(BaseProcessor):
    """Specialized version of base processor."""
```

## Database Operations

### Use Context Managers
```python
# Good: Automatic cleanup
def query_database(db_path: Path):
    """Query database."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM table")
        return cursor.fetchall()
    finally:
        conn.close()

# Better: With statement
def query_database(db_path: Path):
    """Query database."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM table")
        return cursor.fetchall()
```

### Parameterized Queries
```python
# Good: Parameterized
cursor.execute(
    "SELECT * FROM statements WHERE mp_id = ? AND date = ?",
    (mp_id, date)
)

# Bad: String formatting (SQL injection risk!)
cursor.execute(
    f"SELECT * FROM statements WHERE mp_id = {mp_id}"
)
```

## File Operations

### Use Context Managers
```python
# Good: Automatic cleanup
with open(file_path, 'r') as f:
    content = f.read()

# Good: Path objects
content = Path(file_path).read_text()
```

### Handle Encoding
```python
# Explicit encoding
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
```

## Parallel Processing

### Thread Safety
```python
# Each thread gets its own instances
def process_single_pdf(pdf_path: Path, db_path: Path) -> ProcessedPDF:
    """Process single PDF (thread-safe)."""
    # Create new instances per call
    pdf_processor = PDFProcessor()
    mp_identifier = MPIdentifier()
    
    # No shared state
    return process(pdf_path)
```

### Use ThreadPoolExecutor
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_multiple(pdf_files: List[Path], workers: int = 4):
    """Process multiple PDFs in parallel."""
    results = []
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_pdf = {
            executor.submit(process_single_pdf, pdf): pdf
            for pdf in pdf_files
        }
        
        for future in as_completed(future_to_pdf):
            pdf = future_to_pdf[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {pdf}: {e}")
    
    return results
```

## Performance

### Use Generators for Large Datasets
```python
# Good: Generator (memory efficient)
def read_large_file(path: Path):
    """Read file line by line."""
    with open(path) as f:
        for line in f:
            yield line.strip()

# Bad: Load everything (memory intensive)
def read_large_file(path: Path):
    """Read entire file."""
    with open(path) as f:
        return f.readlines()
```

### Batch Database Operations
```python
# Good: Batch insert
cursor.executemany(
    "INSERT INTO statements VALUES (?, ?, ?)",
    [(mp_id, session_id, text) for text in statements]
)

# Bad: Individual inserts
for text in statements:
    cursor.execute(
        "INSERT INTO statements VALUES (?, ?, ?)",
        (mp_id, session_id, text)
    )
```

## Common Patterns

### Retry Logic
```python
import time

def retry_operation(func, max_retries: int = 3, delay: float = 1.0):
    """Retry operation with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay * (2 ** attempt))
```

### Progress Tracking
```python
from tqdm import tqdm

def process_with_progress(items: List):
    """Process items with progress bar."""
    for item in tqdm(items, desc="Processing"):
        process(item)
```

### Configuration
```python
# Use dataclasses for configuration
@dataclass
class Config:
    """Application configuration."""
    db_path: Path = Path("data/hansard.db")
    pdf_dir: Path = Path("data/pdfs")
    workers: int = 4
    timeout: int = 30
```

## Anti-Patterns to Avoid

### Don't Use Mutable Default Arguments
```python
# Bad
def append_to(element, to=[]):
    to.append(element)
    return to

# Good
def append_to(element, to=None):
    if to is None:
        to = []
    to.append(element)
    return to
```

### Don't Catch and Ignore Exceptions
```python
# Bad
try:
    risky_operation()
except:
    pass

# Good
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    # Handle or re-raise
```

### Don't Use Global State
```python
# Bad: Global mutable state
cache = {}

def get_data(key):
    if key in cache:
        return cache[key]
    # ...

# Good: Pass state explicitly
def get_data(key, cache: dict):
    if key in cache:
        return cache[key]
    # ...
```

## Quick Reference

### Good Practices
✅ Use type hints
✅ Write docstrings
✅ Use Path objects
✅ Parameterize SQL queries
✅ Use context managers
✅ Handle exceptions specifically
✅ Keep functions focused
✅ Use dataclasses
✅ Write tests

### Bad Practices
❌ Mutable default arguments
❌ Catch-all exception handlers
❌ Global mutable state
❌ String concatenation for paths
❌ SQL injection vulnerabilities
❌ Functions > 50 lines
❌ Missing docstrings
❌ No type hints
❌ No tests
