# Storage Abstraction Guide

## Overview

The Hansard Tales storage abstraction layer provides a unified interface for storing and retrieving PDF files across different storage backends. This design allows the system to work with local filesystem storage today while supporting cloud storage (S3, Azure, etc.) in the future without code changes.

## Architecture

### Storage Backend Interface

All storage backends implement the `StorageBackend` abstract base class:

```python
from hansard_tales.storage.base import StorageBackend

class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        
    @abstractmethod
    def get_size(self, path: str) -> int:
        """Get file size in bytes."""
        
    @abstractmethod
    def write(self, path: str, content: bytes) -> None:
        """Write content to file."""
        
    @abstractmethod
    def read(self, path: str) -> bytes:
        """Read file content."""
        
    @abstractmethod
    def delete(self, path: str) -> None:
        """Delete file."""
        
    @abstractmethod
    def move(self, src: str, dest: str) -> None:
        """Move/rename file."""
        
    @abstractmethod
    def list_files(self, prefix: str) -> List[str]:
        """List files with given prefix."""
```

### Current Implementation: Filesystem Storage

The default implementation uses local filesystem storage:

```python
from hansard_tales.storage.filesystem import FilesystemStorage

# Create storage with default directory
storage = FilesystemStorage()  # Uses data/pdfs/hansard

# Create storage with custom directory
storage = FilesystemStorage("custom/path")
```

## Usage

### Basic Operations

```python
from hansard_tales.storage.filesystem import FilesystemStorage

# Initialize storage
storage = FilesystemStorage("data/pdfs/hansard")

# Check if file exists
if storage.exists("hansard_20240101_P.pdf"):
    print("File exists")

# Get file size
size = storage.get_size("hansard_20240101_P.pdf")
print(f"File size: {size} bytes")

# Write file
content = b"PDF content here"
storage.write("hansard_20240101_P.pdf", content)

# Read file
content = storage.read("hansard_20240101_P.pdf")

# List files with prefix
files = storage.list_files("hansard_202401")
for file in files:
    print(file)

# Move/rename file
storage.move("old_name.pdf", "new_name.pdf")

# Delete file
storage.delete("hansard_20240101_P.pdf")
```

### Integration with Scraper

The scraper uses storage abstraction for all file operations:

```python
from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.storage.filesystem import FilesystemStorage

# Create storage backend
storage = FilesystemStorage("data/pdfs/hansard")

# Create scraper with storage
scraper = HansardScraper(
    storage=storage,
    db_path="data/hansard.db"
)

# Scraper uses storage for all operations
hansards = scraper.scrape_all(max_pages=5)
scraper.download_all(hansards)
```

### Configuration

Use the configuration module for centralized storage setup:

```python
from hansard_tales.storage.config import get_storage_backend

# Get default storage (filesystem)
storage = get_storage_backend()

# Get storage with custom configuration
storage = get_storage_backend(
    backend_type="filesystem",
    config={"base_dir": "custom/path"}
)

# Get default storage (convenience function)
from hansard_tales.storage.config import get_default_storage
storage = get_default_storage()
```

## Filesystem Storage Details

### Directory Structure

The filesystem storage organizes files in a single directory:

```
data/pdfs/hansard/
├── hansard_20240101_P.pdf
├── hansard_20240101_A.pdf
├── hansard_20240102_P.pdf
├── hansard_20240102_A.pdf
└── ...
```

### Path Handling

- All paths are relative to the base directory
- Absolute paths are not supported
- Subdirectories are created automatically

### File Operations

**Write Operation**:
```python
# Writes to data/pdfs/hansard/hansard_20240101_P.pdf
storage.write("hansard_20240101_P.pdf", content)
```

**Read Operation**:
```python
# Reads from data/pdfs/hansard/hansard_20240101_P.pdf
content = storage.read("hansard_20240101_P.pdf")
```

**List Operation**:
```python
# Lists all files starting with "hansard_202401"
files = storage.list_files("hansard_202401")
# Returns: ["hansard_20240101_P.pdf", "hansard_20240102_P.pdf", ...]
```

### Error Handling

```python
from pathlib import Path

try:
    content = storage.read("nonexistent.pdf")
except FileNotFoundError:
    print("File not found")

try:
    storage.write("readonly.pdf", content)
except PermissionError:
    print("Permission denied")
```

## Future Storage Backends

### S3 Storage (Planned)

Future implementation for AWS S3:

```python
from hansard_tales.storage.s3 import S3Storage

# Create S3 storage
storage = S3Storage(
    bucket="hansard-pdfs",
    prefix="hansard",
    region="us-east-1"
)

# Use same interface as filesystem storage
storage.write("hansard_20240101_P.pdf", content)
```

### Azure Blob Storage (Planned)

Future implementation for Azure:

```python
from hansard_tales.storage.azure import AzureBlobStorage

# Create Azure storage
storage = AzureBlobStorage(
    container="hansard-pdfs",
    prefix="hansard",
    connection_string="..."
)

# Use same interface
storage.write("hansard_20240101_P.pdf", content)
```

## Implementing Custom Storage Backend

To implement a custom storage backend:

1. **Inherit from StorageBackend**:

```python
from hansard_tales.storage.base import StorageBackend
from typing import List

class CustomStorage(StorageBackend):
    """Custom storage implementation."""
    
    def __init__(self, **config):
        """Initialize with custom configuration."""
        self.config = config
        # Initialize your storage client
    
    def exists(self, path: str) -> bool:
        """Check if file exists in storage."""
        # Implement check logic
        pass
    
    def get_size(self, path: str) -> int:
        """Get file size in bytes."""
        # Implement size retrieval
        pass
    
    def write(self, path: str, content: bytes) -> None:
        """Write content to storage."""
        # Implement write logic
        pass
    
    def read(self, path: str) -> bytes:
        """Read file content from storage."""
        # Implement read logic
        pass
    
    def delete(self, path: str) -> None:
        """Delete file from storage."""
        # Implement delete logic
        pass
    
    def move(self, src: str, dest: str) -> None:
        """Move/rename file in storage."""
        # Implement move logic
        pass
    
    def list_files(self, prefix: str) -> List[str]:
        """List files with given prefix."""
        # Implement list logic
        pass
```

2. **Register in Configuration**:

```python
# In hansard_tales/storage/config.py
from hansard_tales.storage.custom import CustomStorage

DEFAULT_STORAGE_CONFIG["custom"] = {
    "param1": "value1",
    "param2": "value2"
}

def get_storage_backend(backend_type=None, config=None):
    # ... existing code ...
    
    elif backend_type == "custom":
        return CustomStorage(**config)
```

3. **Use Custom Storage**:

```python
from hansard_tales.storage.config import get_storage_backend

storage = get_storage_backend(
    backend_type="custom",
    config={"param1": "value1"}
)
```

## Best Practices

### 1. Always Use Storage Abstraction

**Good**:
```python
# Use storage abstraction
storage = FilesystemStorage("data/pdfs/hansard")
if storage.exists("file.pdf"):
    content = storage.read("file.pdf")
```

**Bad**:
```python
# Direct file operations (don't do this!)
from pathlib import Path
if Path("data/pdfs/hansard/file.pdf").exists():
    content = Path("data/pdfs/hansard/file.pdf").read_bytes()
```

### 2. Handle Errors Gracefully

```python
try:
    content = storage.read("file.pdf")
except FileNotFoundError:
    logger.warning(f"File not found: file.pdf")
    # Handle missing file
except Exception as e:
    logger.error(f"Storage error: {e}")
    # Handle other errors
```

### 3. Use Relative Paths

```python
# Good: Relative path
storage.write("hansard_20240101_P.pdf", content)

# Bad: Absolute path (may not work with all backends)
storage.write("/data/pdfs/hansard/hansard_20240101_P.pdf", content)
```

### 4. Batch Operations

```python
# Good: Batch list operation
files = storage.list_files("hansard_202401")
for file in files:
    process(file)

# Bad: Individual exists checks
for i in range(1, 32):
    filename = f"hansard_202401{i:02d}_P.pdf"
    if storage.exists(filename):
        process(filename)
```

### 5. Clean Up Resources

```python
# Write temporary file
storage.write("temp.pdf", content)

try:
    # Process file
    process_pdf("temp.pdf")
finally:
    # Clean up
    storage.delete("temp.pdf")
```

## Performance Considerations

### Filesystem Storage

**Advantages**:
- Fast local access
- No network latency
- Simple implementation
- No API rate limits

**Limitations**:
- Limited to single machine
- No built-in redundancy
- Manual backup required
- Disk space constraints

### Cloud Storage (Future)

**Advantages**:
- Scalable storage
- Built-in redundancy
- Geographic distribution
- Automatic backups

**Limitations**:
- Network latency
- API rate limits
- Cost per operation
- Requires internet connection

## Migration Between Backends

To migrate from filesystem to cloud storage:

1. **Create new storage backend**:
```python
from hansard_tales.storage.s3 import S3Storage

old_storage = FilesystemStorage("data/pdfs/hansard")
new_storage = S3Storage("hansard-pdfs", "hansard")
```

2. **Copy files**:
```python
files = old_storage.list_files("")
for file in files:
    content = old_storage.read(file)
    new_storage.write(file, content)
```

3. **Update database paths** (if needed):
```python
import sqlite3

conn = sqlite3.connect("data/hansard.db")
cursor = conn.cursor()

# Update file paths if format changes
cursor.execute("""
    UPDATE downloaded_pdfs
    SET file_path = 's3://hansard-pdfs/hansard/' || file_path
    WHERE file_path NOT LIKE 's3://%'
""")

conn.commit()
conn.close()
```

4. **Update configuration**:
```python
# In your application
storage = get_storage_backend(
    backend_type="s3",
    config={"bucket": "hansard-pdfs", "prefix": "hansard"}
)
```

## Testing

### Unit Tests

Test storage operations:

```python
import pytest
from hansard_tales.storage.filesystem import FilesystemStorage

def test_write_and_read(tmp_path):
    """Test write and read operations."""
    storage = FilesystemStorage(str(tmp_path))
    
    # Write file
    content = b"test content"
    storage.write("test.pdf", content)
    
    # Read file
    read_content = storage.read("test.pdf")
    assert read_content == content

def test_exists(tmp_path):
    """Test exists check."""
    storage = FilesystemStorage(str(tmp_path))
    
    # File doesn't exist
    assert not storage.exists("test.pdf")
    
    # Write file
    storage.write("test.pdf", b"content")
    
    # File exists
    assert storage.exists("test.pdf")
```

### Integration Tests

Test with scraper:

```python
def test_scraper_with_storage(tmp_path, temp_db):
    """Test scraper with storage abstraction."""
    storage = FilesystemStorage(str(tmp_path))
    
    scraper = HansardScraper(
        storage=storage,
        db_path=temp_db
    )
    
    # Scrape and download
    hansards = scraper.scrape_all(max_pages=1)
    stats = scraper.download_all(hansards)
    
    # Verify files in storage
    files = storage.list_files("")
    assert len(files) > 0
```

## Troubleshooting

### Issue: Permission Denied

**Cause**: Insufficient permissions on storage directory

**Solution**:
```bash
# Check permissions
ls -la data/pdfs/

# Fix permissions
chmod 755 data/pdfs/hansard/
```

### Issue: Disk Space Full

**Cause**: Storage directory out of space

**Solution**:
```bash
# Check disk space
df -h data/

# Clean old files
python scripts/db_manager.py clean --db-path data/hansard.db

# Move to larger disk
mv data/pdfs/hansard /mnt/large-disk/hansard
ln -s /mnt/large-disk/hansard data/pdfs/hansard
```

### Issue: Slow File Operations

**Cause**: Network filesystem, slow disk, or many small files

**Solution**:
1. Use local SSD storage
2. Batch operations when possible
3. Consider cloud storage for better performance

## Related Documentation

- [Workflow Orchestration](WORKFLOW_ORCHESTRATION.md) - Using storage in workflows
- [Architecture](ARCHITECTURE.md) - System architecture overview
- [Development Guide](DEVELOPMENT.md) - Development workflow

## Support

For issues or questions:
- Check error messages in logs
- Review this documentation
- Open an issue on GitHub
- Contact maintainer

---

**Last Updated**: January 2025
