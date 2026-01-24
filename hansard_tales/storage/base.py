"""
Abstract base class for storage backends.

This module defines the interface that all storage backends must implement.
"""

from abc import ABC, abstractmethod
from typing import List


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.
    
    This class defines the interface for file storage operations that
    all concrete storage implementations must provide. It enables the
    system to support multiple storage backends (filesystem, S3, etc.)
    through a unified interface.
    
    All methods should be thread-safe for parallel processing.
    """
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """
        Check if file exists at the given path.
        
        Args:
            path: Path to file (relative to storage root)
            
        Returns:
            True if file exists, False otherwise
            
        Example:
            >>> storage.exists("hansard_20240101_P.pdf")
            True
        """
        pass
    
    @abstractmethod
    def get_size(self, path: str) -> int:
        """
        Get file size in bytes.
        
        Args:
            path: Path to file (relative to storage root)
            
        Returns:
            File size in bytes
            
        Raises:
            FileNotFoundError: If file does not exist
            
        Example:
            >>> storage.get_size("hansard_20240101_P.pdf")
            1048576
        """
        pass
    
    @abstractmethod
    def write(self, path: str, content: bytes) -> None:
        """
        Write content to file.
        
        Creates parent directories if they don't exist.
        Overwrites existing file if present.
        
        Args:
            path: Path to file (relative to storage root)
            content: Binary content to write
            
        Raises:
            IOError: If write operation fails
            
        Example:
            >>> storage.write("hansard_20240101_P.pdf", pdf_bytes)
        """
        pass
    
    @abstractmethod
    def read(self, path: str) -> bytes:
        """
        Read file content.
        
        Args:
            path: Path to file (relative to storage root)
            
        Returns:
            Binary content of file
            
        Raises:
            FileNotFoundError: If file does not exist
            IOError: If read operation fails
            
        Example:
            >>> content = storage.read("hansard_20240101_P.pdf")
        """
        pass
    
    @abstractmethod
    def delete(self, path: str) -> None:
        """
        Delete file.
        
        Args:
            path: Path to file (relative to storage root)
            
        Raises:
            FileNotFoundError: If file does not exist
            IOError: If delete operation fails
            
        Example:
            >>> storage.delete("hansard_20240101_P.pdf")
        """
        pass
    
    @abstractmethod
    def move(self, src: str, dest: str) -> None:
        """
        Move/rename file.
        
        Creates parent directories for destination if they don't exist.
        Overwrites destination file if it exists.
        
        Args:
            src: Source path (relative to storage root)
            dest: Destination path (relative to storage root)
            
        Raises:
            FileNotFoundError: If source file does not exist
            IOError: If move operation fails
            
        Example:
            >>> storage.move("old_name.pdf", "hansard_20240101_P.pdf")
        """
        pass
    
    @abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files with given prefix.
        
        Args:
            prefix: Prefix to filter files (default: "" for all files)
            
        Returns:
            List of file paths (relative to storage root) matching prefix
            
        Example:
            >>> storage.list_files("hansard_20240101")
            ['hansard_20240101_P.pdf', 'hansard_20240101_A.pdf']
        """
        pass
