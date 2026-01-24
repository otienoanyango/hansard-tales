"""
Storage configuration module.

This module provides configuration support for selecting and initializing
storage backends.
"""

from typing import Dict, Any, Optional

from hansard_tales.storage.base import StorageBackend
from hansard_tales.storage.filesystem import FilesystemStorage


# Default storage configuration
DEFAULT_STORAGE_BACKEND = "filesystem"

DEFAULT_STORAGE_CONFIG: Dict[str, Dict[str, Any]] = {
    "filesystem": {
        "base_dir": "data/pdfs/hansard"
    },
    # Future backends can be added here
    # "s3": {
    #     "bucket": "hansard-pdfs",
    #     "prefix": "hansard"
    # }
}


def get_storage_backend(
    backend_type: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> StorageBackend:
    """
    Get configured storage backend instance.
    
    This factory function creates and returns the appropriate storage
    backend based on configuration. It supports multiple backend types
    and allows custom configuration.
    
    Args:
        backend_type: Type of backend ('filesystem', 's3', etc.)
                     Defaults to DEFAULT_STORAGE_BACKEND
        config: Custom configuration dict for the backend
                Defaults to DEFAULT_STORAGE_CONFIG[backend_type]
                
    Returns:
        Configured StorageBackend instance
        
    Raises:
        ValueError: If backend_type is not supported
        
    Example:
        >>> # Use default filesystem storage
        >>> storage = get_storage_backend()
        
        >>> # Use filesystem with custom directory
        >>> storage = get_storage_backend(
        ...     backend_type="filesystem",
        ...     config={"base_dir": "custom/path"}
        ... )
    """
    # Use defaults if not specified
    if backend_type is None:
        backend_type = DEFAULT_STORAGE_BACKEND
    
    if config is None:
        config = DEFAULT_STORAGE_CONFIG.get(backend_type, {})
    
    # Create backend instance
    if backend_type == "filesystem":
        return FilesystemStorage(**config)
    # Future backends can be added here
    # elif backend_type == "s3":
    #     return S3Storage(**config)
    else:
        raise ValueError(
            f"Unsupported storage backend: {backend_type}. "
            f"Supported backends: {list(DEFAULT_STORAGE_CONFIG.keys())}"
        )


def get_default_storage() -> StorageBackend:
    """
    Get default storage backend instance.
    
    Convenience function that returns a storage backend with
    default configuration.
    
    Returns:
        Default StorageBackend instance (FilesystemStorage)
        
    Example:
        >>> storage = get_default_storage()
        >>> storage.exists("test.pdf")
        False
    """
    return get_storage_backend()
