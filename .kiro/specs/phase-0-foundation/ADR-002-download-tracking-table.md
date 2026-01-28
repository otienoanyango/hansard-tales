# ADR-002: Download Tracking Table for Duplicate Prevention

**Status**: Accepted  
**Date**: 2026-01-28  
**Decision Makers**: Development Team  
**Related Requirements**: Requirement 1 (Database Schema), Requirement 4 (Web Scrapers)  
**Related ADRs**: ADR-001 (Hansard Scraper Implementation)

## Context

The web scrapers download PDFs from parliament.go.ke and need to avoid redownloading files that have already been fetched. The current implementation has a placeholder `_is_duplicate()` method that always returns False, meaning files would be redownloaded on every scrape run.

### Problem Statement

Without duplicate tracking:
- Wasted bandwidth downloading same files repeatedly
- Wasted storage space with duplicate files
- Slower scraping operations
- Potential rate limiting issues from excessive requests
- No audit trail of what has been downloaded

### Requirements

From Requirement 4, AC 9: "EACH scraper SHALL skip already-downloaded documents (based on hash)"

## Decision

We will implement a `downloaded_files` table in the database to track all downloaded PDFs by their SHA256 hash.

### Table Schema

```python
class DownloadedFileORM(Base):
    """Downloaded files tracking table for duplicate prevention"""
    __tablename__ = "downloaded_files"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Source tracking
    source_url = Column(Text, nullable=False)
    source_hash = Column(String(64), nullable=False, unique=True)
    
    # File information
    standardized_filename = Column(String(255), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    document_type = Column(String(50), nullable=False)
    
    # Download tracking
    download_date = Column(DateTime, nullable=False)
    file_path = Column(Text, nullable=False)
    
    # Metadata
    chamber = Column(String(50))
    parliament_term = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_downloaded_files_hash', 'source_hash'),
        Index('idx_downloaded_files_type', 'document_type'),
        Index('idx_downloaded_files_date', 'download_date'),
    )
```

### Integration with BaseScraper

**_is_duplicate() Implementation:**
```python
def _is_duplicate(self, doc_hash: str) -> bool:
    """Check if document already exists by querying downloaded_files table."""
    existing = session.query(DownloadedFileORM).filter(
        DownloadedFileORM.source_hash == doc_hash
    ).first()
    return existing is not None
```

**_record_download() Implementation:**
```python
def _record_download(self, doc: ScrapedDocument, file_path: Path, chamber: Chamber) -> None:
    """Record downloaded file in database."""
    record = DownloadedFileORM(
        source_url=doc.url,
        source_hash=doc.hash,
        standardized_filename=doc.filename,
        original_filename=doc.metadata.get('original_filename', doc.filename),
        file_size=len(doc.content),
        document_type=doc.metadata['document_type'],
        download_date=datetime.utcnow(),
        file_path=str(file_path),
        chamber=chamber.value,
        parliament_term=2022
    )
    session.add(record)
    session.commit()
```

**Updated scrape() workflow:**
```python
def scrape(...):
    urls = self.get_document_urls(chamber, start_date, end_date)
    documents = []
    
    for url in urls:
        try:
            doc = self.download_document(url)
            
            # Check database for duplicate
            if skip_existing and self._is_duplicate(doc.hash):
                continue
            
            # Save to filesystem
            file_path = self.save_document(doc, output_dir)
            
            # Record in database
            self._record_download(doc, file_path, chamber)
            
            documents.append(doc)
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            continue
    
    return documents
```

## Rationale

### Why a Separate Table?

**Option 1: Use documents table** (Rejected)
- Documents table is for processed documents with full metadata
- Downloaded files may not be processed yet
- Mixing concerns (download tracking vs document storage)

**Option 2: Use filesystem only** (Rejected)
- No centralized tracking
- Requires filesystem scanning to check duplicates
- No metadata about downloads
- Difficult to query (when was file downloaded? by whom?)

**Option 3: Separate downloaded_files table** (Selected)
- ✅ Single responsibility: track downloads
- ✅ Fast duplicate checking via indexed hash
- ✅ Audit trail of all downloads
- ✅ Metadata for troubleshooting
- ✅ Can track files before processing
- ✅ Supports cleanup operations

### Why SHA256 Hash?

- Cryptographically secure (collision-resistant)
- Standard for file integrity verification
- Already computed during download
- Unique identifier regardless of filename changes
- Enables deduplication across different URLs

### Why Track Both Filenames?

- `standardized_filename`: For consistent file organization
- `original_filename`: For debugging and reference
- Enables mapping between parliament.go.ke naming and our naming

## Consequences

### Positive

- **Efficiency**: Avoids redownloading existing files
- **Bandwidth**: Reduces network usage
- **Speed**: Faster scraping (skip existing files)
- **Audit Trail**: Complete history of downloads
- **Debugging**: Can track when/where files were downloaded
- **Cleanup**: Can identify orphaned files

### Negative

- **Database Size**: Additional table grows over time
- **Complexity**: Requires database connection in scrapers
- **Migration**: Needs new Alembic migration
- **Testing**: More complex test setup (database fixtures)

### Mitigation

- Index on source_hash for fast lookups
- Periodic cleanup of old records (future enhancement)
- Use connection pooling for performance
- Comprehensive test coverage for duplicate detection

## Implementation Plan

### Phase 1: Database Schema (Task 2.4)
1. Create DownloadedFileORM model
2. Generate Alembic migration
3. Apply migration to development database
4. Write ORM tests

### Phase 2: Scraper Integration (Task 4.6)
1. Implement _is_duplicate() with database query
2. Implement _record_download() with database insert
3. Update scrape() method to call _record_download()
4. Add database session management to scrapers
5. Write integration tests

### Phase 3: Testing (Task 4.7)
1. Test duplicate detection with database
2. Test record insertion
3. Test scrape workflow with tracking
4. Test error handling (database unavailable)

## Alternatives Considered

### Alternative 1: Redis Cache
- Use Redis to track downloaded hashes
- **Rejected**: Requires additional infrastructure, not persistent

### Alternative 2: JSON File
- Store hashes in JSON file
- **Rejected**: Not scalable, no query capabilities, race conditions

### Alternative 3: Bloom Filter
- Use probabilistic data structure
- **Rejected**: False positives possible, no metadata storage

### Alternative 4: No Tracking
- Always redownload files
- **Rejected**: Wasteful, slow, violates requirements

## References

- Requirement 1: Database Schema Foundation (requirements.md)
- Requirement 4: Basic Web Scrapers, AC 9 (requirements.md)
- Design 3: Database Schema (design.md)
- Design 5: Web Scrapers (design.md)
- Task 2.4: Download Tracking Table (tasks.md)

## Review Notes

This ADR documents the decision to implement download tracking using a dedicated database table. The implementation will be completed in Task 2.4 (Database) and integrated with scrapers in a future task.
