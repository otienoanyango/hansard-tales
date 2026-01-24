"""
Filesystem-based storage implementation.

This module provides a concrete implementation of StorageBackend
for local filesystem storage.
"""

import logging
import shutil
from pathlib import Path
from typing import List

from hansard_tales.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class FilesystemStorage(StorageBackend):
    """
    Filesystem-based storage implementation.
    
    This class implements the StorageBackend interface for local
    filesystem storage. All file operations are performed relative
    to a base directory.
    
    The implementation is thread-safe for parallel processing as
    filesystem operations are atomic at the OS level.
    
    Attributes:
        base_dir: Base directory for all storage operations
        
    Example:
        >>> storage = FilesystemStorage("data/pdfs/hansard")
        >>> storage.write("test.pdf", b"content")
        >>> storage.exists("test.pdf")
        True
    """
    
    def __init__(self, base_dir: str = "data/pdfs/hansard"):
        """
        Initialize filesystem storage.
        
        Creates base directory if it doesn't exist.
        
        Args:
            base_dir: Base directory for storage (default: data/pdfs/hansard)
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _resolve_path(self, path: str) -> Path:
        """
        Resolve relative path to absolute path within base directory.
        
        Args:
            path: Relative path
            
        Returns:
            Absolute Path object
        """
        return self.base_dir / path
    
    def exists(self, path: str) -> bool:
        """
        Check if file exists at the given path.
        
        Args:
            path: Path to file (relative to base_dir)
            
        Returns:
            True if file exists, False otherwise
            
        Example:
            >>> storage.exists("hansard_20240101_P.pdf")
            True
        """
        return self._resolve_path(path).exists()
    
    def get_size(self, path: str) -> int:
        """
        Get file size in bytes.
        
        Args:
            path: Path to file (relative to base_dir)
            
        Returns:
            File size in bytes
            
        Raises:
            FileNotFoundError: If file does not exist
            
        Example:
            >>> storage.get_size("hansard_20240101_P.pdf")
            1048576
        """
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return file_path.stat().st_size
    
    def write(self, path: str, content: bytes) -> None:
        """
        Write content to file.
        
        Creates parent directories if they don't exist.
        Overwrites existing file if present.
        
        Args:
            path: Path to file (relative to base_dir)
            content: Binary content to write
            
        Raises:
            IOError: If write operation fails
            
        Example:
            >>> storage.write("hansard_20240101_P.pdf", pdf_bytes)
        """
        file_path = self._resolve_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"File operation: WRITE path={path}, size={len(content)} bytes")
        file_path.write_bytes(content)
        logger.debug(f"Successfully wrote {len(content)} bytes to {path}")
    
    def read(self, path: str) -> bytes:
        """
        Read file content.
        
        Args:
            path: Path to file (relative to base_dir)
            
        Returns:
            Binary content of file
            
        Raises:
            FileNotFoundError: If file does not exist
            IOError: If read operation fails
            
        Example:
            >>> content = storage.read("hansard_20240101_P.pdf")
        """
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return file_path.read_bytes()
    
    def delete(self, path: str) -> None:
        """
        Delete file.
        
        Args:
            path: Path to file (relative to base_dir)
            
        Raises:
            FileNotFoundError: If file does not exist
            IOError: If delete operation fails
            
        Example:
            >>> storage.delete("hansard_20240101_P.pdf")
        """
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        logger.info(f"File operation: DELETE path={path}")
        file_path.unlink()
        logger.debug(f"Successfully deleted {path}")
    
    def move(self, src: str, dest: str) -> None:
        """
        Move/rename file.
        
        Creates parent directories for destination if they don't exist.
        Overwrites destination file if it exists.
        
        Args:
            src: Source path (relative to base_dir)
            dest: Destination path (relative to base_dir)
            
        Raises:
            FileNotFoundError: If source file does not exist
            IOError: If move operation fails
            
        Example:
            >>> storage.move("old_name.pdf", "hansard_20240101_P.pdf")
        """
        src_path = self._resolve_path(src)
        dest_path = self._resolve_path(dest)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {src}")
        
        # Create parent directories for destination
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"File operation: MOVE src={src}, dest={dest}")
        # Move file (overwrites if destination exists)
        shutil.move(str(src_path), str(dest_path))
        logger.debug(f"Successfully moved {src} to {dest}")
    
    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files with given prefix.
        
        Args:
            prefix: Prefix to filter files (default: "" for all files)
            
        Returns:
            List of file paths (relative to base_dir) matching prefix
            
        Example:
            >>> storage.list_files("hansard_20240101")
            ['hansard_20240101_P.pdf', 'hansard_20240101_A.pdf']
        """
        if not self.base_dir.exists():
            return []
        
        # Get all files in base directory
        all_files = []
        for file_path in self.base_dir.rglob("*"):
            if file_path.is_file():
                # Get relative path from base_dir
                relative_path = file_path.relative_to(self.base_dir)
                # Convert to string with forward slashes
                path_str = str(relative_path).replace("\\", "/")
                
                # Filter by prefix
                if path_str.startswith(prefix):
                    all_files.append(path_str)
        
        return sorted(all_files)
