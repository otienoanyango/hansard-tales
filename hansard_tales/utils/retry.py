"""
Retry logic utilities for Hansard Tales.

This module provides retry decorators and utilities using tenacity
for handling transient failures with exponential backoff.
"""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)
from typing import Callable, TypeVar, Any
import requests

from hansard_tales.utils.errors import StorageError


T = TypeVar('T')


def retry_on_network_error(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0
) -> Callable:
    """
    Decorator for retrying operations that may fail due to network errors.
    
    Uses exponential backoff with configurable parameters. Retries on
    requests.RequestException and its subclasses.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        
    Returns:
        Decorator function
        
    Example:
        >>> @retry_on_network_error(max_attempts=3)
        ... def download_file(url):
        ...     response = requests.get(url)
        ...     response.raise_for_status()
        ...     return response.content
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(requests.RequestException)
    )


def retry_on_storage_error(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0
) -> Callable:
    """
    Decorator for retrying operations that may fail due to storage errors.
    
    Uses exponential backoff with configurable parameters. Retries on
    StorageError and ConnectionError.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        
    Returns:
        Decorator function
        
    Example:
        >>> @retry_on_storage_error(max_attempts=3)
        ... def save_to_database(data):
        ...     session.add(data)
        ...     session.commit()
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((StorageError, ConnectionError))
    )


@retry_on_network_error(max_attempts=3)
def download_with_retry(url: str, timeout: int = 30) -> bytes:
    """
    Download content from URL with automatic retry.
    
    Retries up to 3 times with exponential backoff on network errors.
    
    Args:
        url: URL to download from
        timeout: Request timeout in seconds
        
    Returns:
        Downloaded content as bytes
        
    Raises:
        requests.RequestException: If all retry attempts fail
        
    Example:
        >>> content = download_with_retry("https://example.com/file.pdf")
    """
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content


def store_with_retry(
    data: Any,
    storage_func: Callable[[Any], None],
    max_attempts: int = 3
) -> None:
    """
    Store data with automatic retry.
    
    Wraps a storage function with retry logic for handling transient
    storage failures.
    
    Args:
        data: Data to store
        storage_func: Function that performs storage operation
        max_attempts: Maximum number of retry attempts
        
    Raises:
        StorageError: If all retry attempts fail
        
    Example:
        >>> def save_to_db(data):
        ...     session.add(data)
        ...     session.commit()
        >>> store_with_retry(my_data, save_to_db)
    """
    @retry_on_storage_error(max_attempts=max_attempts)
    def _store():
        try:
            storage_func(data)
        except Exception as e:
            raise StorageError(f"Failed to store data: {e}") from e
    
    _store()
