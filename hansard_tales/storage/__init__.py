"""
Storage abstraction layer for Hansard Tales.

This module provides a unified interface for file storage operations,
supporting multiple backends (filesystem, S3, etc.).
"""

from hansard_tales.storage.base import StorageBackend
from hansard_tales.storage.filesystem import FilesystemStorage
from hansard_tales.storage.config import (
    get_storage_backend,
    get_default_storage,
    DEFAULT_STORAGE_BACKEND,
    DEFAULT_STORAGE_CONFIG
)

__all__ = [
    'StorageBackend',
    'FilesystemStorage',
    'get_storage_backend',
    'get_default_storage',
    'DEFAULT_STORAGE_BACKEND',
    'DEFAULT_STORAGE_CONFIG'
]
