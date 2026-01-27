"""
Tests for storage abstraction layer.

This module contains both unit tests and property-based tests for
the storage abstraction layer, validating the StorageBackend interface
and FilesystemStorage implementation.
"""

import tempfile
import shutil
from pathlib import Path
import pytest
from hypothesis import given, strategies as st

from hansard_tales.storage import (
    StorageBackend,
    FilesystemStorage,
    get_storage_backend,
    get_default_storage,
    DEFAULT_STORAGE_BACKEND
)


class TestFilesystemStorage:
    """Unit tests for FilesystemStorage implementation."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage for testing."""
        temp_dir = tempfile.mkdtemp()
        storage = FilesystemStorage(temp_dir)
        yield storage
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_initialization_creates_directory(self):
        """Test that initialization creates base directory."""
        temp_dir = tempfile.mkdtemp()
        storage_dir = Path(temp_dir) / "test_storage"
        
        # Directory should not exist yet
        assert not storage_dir.exists()
        
        # Create storage
        storage = FilesystemStorage(str(storage_dir))
        
        # Directory should now exist
        assert storage_dir.exists()
        assert storage_dir.is_dir()
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_write_creates_file(self, temp_storage):
        """Test that write creates file with correct content."""
        content = b"test content"
        temp_storage.write("test.pdf", content)
        
        assert temp_storage.exists("test.pdf")
        assert temp_storage.read("test.pdf") == content
    
    def test_write_creates_parent_directories(self, temp_storage):
        """Test that write creates parent directories if needed."""
        content = b"test content"
        temp_storage.write("subdir/nested/test.pdf", content)
        
        assert temp_storage.exists("subdir/nested/test.pdf")
        assert temp_storage.read("subdir/nested/test.pdf") == content
    
    def test_write_overwrites_existing_file(self, temp_storage):
        """Test that write overwrites existing file."""
        temp_storage.write("test.pdf", b"original")
        temp_storage.write("test.pdf", b"updated")
        
        assert temp_storage.read("test.pdf") == b"updated"
    
    def test_exists_returns_false_for_nonexistent_file(self, temp_storage):
        """Test that exists returns False for nonexistent file."""
        assert not temp_storage.exists("nonexistent.pdf")
    
    def test_exists_returns_true_for_existing_file(self, temp_storage):
        """Test that exists returns True for existing file."""
        temp_storage.write("test.pdf", b"content")
        assert temp_storage.exists("test.pdf")
    
    def test_get_size_returns_correct_size(self, temp_storage):
        """Test that get_size returns correct file size."""
        content = b"test content with some length"
        temp_storage.write("test.pdf", content)
        
        assert temp_storage.get_size("test.pdf") == len(content)
    
    def test_get_size_raises_for_nonexistent_file(self, temp_storage):
        """Test that get_size raises FileNotFoundError for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            temp_storage.get_size("nonexistent.pdf")
    
    def test_read_returns_correct_content(self, temp_storage):
        """Test that read returns correct file content."""
        content = b"test content"
        temp_storage.write("test.pdf", content)
        
        assert temp_storage.read("test.pdf") == content
    
    def test_read_raises_for_nonexistent_file(self, temp_storage):
        """Test that read raises FileNotFoundError for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            temp_storage.read("nonexistent.pdf")
    
    def test_delete_removes_file(self, temp_storage):
        """Test that delete removes file."""
        temp_storage.write("test.pdf", b"content")
        assert temp_storage.exists("test.pdf")
        
        temp_storage.delete("test.pdf")
        assert not temp_storage.exists("test.pdf")
    
    def test_delete_raises_for_nonexistent_file(self, temp_storage):
        """Test that delete raises FileNotFoundError for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            temp_storage.delete("nonexistent.pdf")
    
    def test_move_renames_file(self, temp_storage):
        """Test that move renames file."""
        content = b"test content"
        temp_storage.write("old.pdf", content)
        
        temp_storage.move("old.pdf", "new.pdf")
        
        assert not temp_storage.exists("old.pdf")
        assert temp_storage.exists("new.pdf")
        assert temp_storage.read("new.pdf") == content
    
    def test_move_creates_parent_directories(self, temp_storage):
        """Test that move creates parent directories for destination."""
        content = b"test content"
        temp_storage.write("test.pdf", content)
        
        temp_storage.move("test.pdf", "subdir/nested/test.pdf")
        
        assert not temp_storage.exists("test.pdf")
        assert temp_storage.exists("subdir/nested/test.pdf")
        assert temp_storage.read("subdir/nested/test.pdf") == content
    
    def test_move_overwrites_destination(self, temp_storage):
        """Test that move overwrites destination file if it exists."""
        temp_storage.write("src.pdf", b"source content")
        temp_storage.write("dest.pdf", b"destination content")
        
        temp_storage.move("src.pdf", "dest.pdf")
        
        assert not temp_storage.exists("src.pdf")
        assert temp_storage.exists("dest.pdf")
        assert temp_storage.read("dest.pdf") == b"source content"
    
    def test_move_raises_for_nonexistent_source(self, temp_storage):
        """Test that move raises FileNotFoundError for nonexistent source."""
        with pytest.raises(FileNotFoundError):
            temp_storage.move("nonexistent.pdf", "dest.pdf")
    
    def test_list_files_returns_empty_for_empty_storage(self, temp_storage):
        """Test that list_files returns empty list for empty storage."""
        assert temp_storage.list_files() == []
    
    def test_list_files_returns_all_files(self, temp_storage):
        """Test that list_files returns all files."""
        temp_storage.write("file1.pdf", b"content1")
        temp_storage.write("file2.pdf", b"content2")
        temp_storage.write("subdir/file3.pdf", b"content3")
        
        files = temp_storage.list_files()
        assert len(files) == 3
        assert "file1.pdf" in files
        assert "file2.pdf" in files
        assert "subdir/file3.pdf" in files
    
    def test_list_files_filters_by_prefix(self, temp_storage):
        """Test that list_files filters by prefix."""
        temp_storage.write("hansard_20240101_P.pdf", b"content1")
        temp_storage.write("hansard_20240101_A.pdf", b"content2")
        temp_storage.write("hansard_20240102_P.pdf", b"content3")
        temp_storage.write("other.pdf", b"content4")
        
        files = temp_storage.list_files("hansard_20240101")
        assert len(files) == 2
        assert "hansard_20240101_P.pdf" in files
        assert "hansard_20240101_A.pdf" in files
        assert "hansard_20240102_P.pdf" not in files
        assert "other.pdf" not in files
    
    def test_list_files_returns_sorted_results(self, temp_storage):
        """Test that list_files returns sorted results."""
        temp_storage.write("c.pdf", b"content")
        temp_storage.write("a.pdf", b"content")
        temp_storage.write("b.pdf", b"content")
        
        files = temp_storage.list_files()
        assert files == ["a.pdf", "b.pdf", "c.pdf"]


class TestStorageInterface:
    """Property-based tests for storage interface."""
    
    @given(
        content=st.binary(min_size=0, max_size=10000)
    )
    def test_property_storage_preserves_content(self, content):
        """
        Feature: end-to-end-workflow-validation, Property 1.1:
        Storage operations preserve file content.
        
        For any binary content, writing and then reading should return
        the exact same content.
        
        Validates: Requirements 1.1, 1.2
        """
        # Create temporary storage for this test
        temp_dir = tempfile.mkdtemp()
        try:
            temp_storage = FilesystemStorage(temp_dir)
            filename = "test.pdf"
            
            # Write content
            temp_storage.write(filename, content)
            
            # Read content
            read_content = temp_storage.read(filename)
            
            # Content should be preserved exactly
            assert read_content == content
            
            # File should exist
            assert temp_storage.exists(filename)
            
            # Size should match
            assert temp_storage.get_size(filename) == len(content)
        finally:
            shutil.rmtree(temp_dir)
    
    @given(
        filename=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='._-'
            ),
            min_size=1,
            max_size=50
        ).filter(lambda x: x and not x.startswith('.') and not x.endswith('.')),
        content=st.binary(min_size=1, max_size=1000)
    )
    def test_property_write_read_cycle(self, filename, content):
        """
        Property: Write-read cycle preserves content for any filename.
        
        For any valid filename and content, the write-read cycle should
        preserve the content exactly.
        """
        # Create temporary storage for this test
        temp_dir = tempfile.mkdtemp()
        try:
            temp_storage = FilesystemStorage(temp_dir)
            
            # Add .pdf extension to ensure valid filename
            filename = f"{filename}.pdf"
            
            # Write and read
            temp_storage.write(filename, content)
            read_content = temp_storage.read(filename)
            
            # Content should match
            assert read_content == content
        finally:
            shutil.rmtree(temp_dir)
    
    @given(
        old_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            min_size=1,
            max_size=20
        ),
        new_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            min_size=1,
            max_size=20
        ),
        content=st.binary(min_size=1, max_size=1000)
    )
    def test_property_move_preserves_content(
        self,
        old_name,
        new_name,
        content
    ):
        """
        Property: Move operation preserves file content.
        
        For any source and destination filenames, moving a file should
        preserve its content exactly.
        
        Note: This test is skipped on case-insensitive filesystems (macOS)
        because moving 'Ż.pdf' to 'ż.pdf' doesn't delete the old file when
        the filesystem treats them as the same file.
        """
        # Create temporary storage for this test
        temp_dir = tempfile.mkdtemp()
        try:
            temp_storage = FilesystemStorage(temp_dir)
            
            # Add .pdf extension
            old_name = f"{old_name}.pdf"
            new_name = f"{new_name}.pdf"
            
            # Skip if names are the same
            if old_name == new_name:
                return
            
            # Skip if names differ only in case on case-insensitive filesystems
            # (macOS HFS+/APFS treats 'Ż.pdf' and 'ż.pdf' as the same file)
            if old_name.lower() == new_name.lower():
                return
            
            # Write original file
            temp_storage.write(old_name, content)
            
            # Move file
            temp_storage.move(old_name, new_name)
            
            # Old file should not exist
            assert not temp_storage.exists(old_name)
            
            # New file should exist with same content
            assert temp_storage.exists(new_name)
            assert temp_storage.read(new_name) == content
        finally:
            shutil.rmtree(temp_dir)


class TestStorageConfiguration:
    """Unit tests for storage configuration."""
    
    def test_get_default_storage_returns_filesystem(self):
        """Test that get_default_storage returns FilesystemStorage."""
        storage = get_default_storage()
        assert isinstance(storage, FilesystemStorage)
    
    def test_get_storage_backend_with_default_type(self):
        """Test get_storage_backend with default backend type."""
        storage = get_storage_backend()
        assert isinstance(storage, FilesystemStorage)
    
    def test_get_storage_backend_with_explicit_filesystem(self):
        """Test get_storage_backend with explicit filesystem type."""
        storage = get_storage_backend(backend_type="filesystem")
        assert isinstance(storage, FilesystemStorage)
    
    def test_get_storage_backend_with_custom_config(self):
        """Test get_storage_backend with custom configuration."""
        temp_dir = tempfile.mkdtemp()
        try:
            storage = get_storage_backend(
                backend_type="filesystem",
                config={"base_dir": temp_dir}
            )
            assert isinstance(storage, FilesystemStorage)
            assert storage.base_dir == Path(temp_dir)
        finally:
            shutil.rmtree(temp_dir)
    
    def test_get_storage_backend_raises_for_unsupported_type(self):
        """Test that get_storage_backend raises for unsupported backend."""
        with pytest.raises(ValueError, match="Unsupported storage backend"):
            get_storage_backend(backend_type="unsupported")
    
    def test_default_storage_backend_is_filesystem(self):
        """Test that default storage backend is filesystem."""
        assert DEFAULT_STORAGE_BACKEND == "filesystem"
