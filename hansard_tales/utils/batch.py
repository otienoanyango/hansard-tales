"""
Batch processing utilities for Hansard Tales.

This module provides utilities for processing items in batches with
error isolation and graceful degradation.
"""

from typing import List, Callable, TypeVar, Generic, Tuple, Any

from hansard_tales.utils.errors import capture_error_context, log_error
from hansard_tales.utils.logging import Logger


T = TypeVar('T')
R = TypeVar('R')


class BatchProcessor(Generic[T, R]):
    """
    Process items in batch with error isolation.
    
    Processes a list of items using a provided function, isolating errors
    so that a single item failure doesn't stop the entire batch.
    
    Type Parameters:
        T: Type of input items
        R: Type of result items
        
    Attributes:
        logger: Logger instance for error logging
        
    Example:
        >>> from hansard_tales.utils.logging import get_logger
        >>> logger = get_logger("app")
        >>> processor = BatchProcessor(logger)
        >>> 
        >>> def process_pdf(path):
        ...     return extract_text(path)
        >>> 
        >>> results, errors = processor.process_batch(
        ...     items=pdf_files,
        ...     process_func=process_pdf,
        ...     continue_on_error=True
        ... )
    """
    
    def __init__(self, logger: Logger):
        """
        Initialize batch processor.
        
        Args:
            logger: Logger instance for error logging
        """
        self.logger = logger
    
    def process_batch(
        self,
        items: List[T],
        process_func: Callable[[T], R],
        continue_on_error: bool = True,
        component: str = "batch_processor",
        operation: str = "process_item"
    ) -> Tuple[List[R], List[Tuple[T, Exception]]]:
        """
        Process batch of items, isolating errors.
        
        Processes each item in the batch using the provided function.
        If continue_on_error is True, errors are logged and collected
        but processing continues. If False, the first error stops processing.
        
        Args:
            items: List of items to process
            process_func: Function to process each item
            continue_on_error: Whether to continue on error (default: True)
            component: Component name for error logging
            operation: Operation name for error logging
            
        Returns:
            Tuple of (successful_results, failed_items_with_errors)
            
        Example:
            >>> results, errors = processor.process_batch(
            ...     items=[1, 2, 3, 4, 5],
            ...     process_func=lambda x: x * 2,
            ...     continue_on_error=True
            ... )
            >>> print(f"Processed {len(results)} items, {len(errors)} failed")
        """
        results: List[R] = []
        errors: List[Tuple[T, Exception]] = []
        
        for item in items:
            try:
                result = process_func(item)
                results.append(result)
            except Exception as e:
                errors.append((item, e))
                
                # Capture and log error context
                error_context = capture_error_context(
                    error=e,
                    component=component,
                    operation=operation,
                    input_data={"item": str(item)}
                )
                log_error(self.logger, error_context)
                
                if not continue_on_error:
                    raise
        
        # Log batch processing summary
        self.logger.info(
            "batch_processing_complete",
            total_items=len(items),
            successful=len(results),
            failed=len(errors),
            component=component,
            operation=operation
        )
        
        return results, errors
    
    def process_batch_with_progress(
        self,
        items: List[T],
        process_func: Callable[[T], R],
        continue_on_error: bool = True,
        component: str = "batch_processor",
        operation: str = "process_item",
        log_interval: int = 10
    ) -> Tuple[List[R], List[Tuple[T, Exception]]]:
        """
        Process batch of items with progress logging.
        
        Similar to process_batch but logs progress at regular intervals.
        
        Args:
            items: List of items to process
            process_func: Function to process each item
            continue_on_error: Whether to continue on error (default: True)
            component: Component name for error logging
            operation: Operation name for error logging
            log_interval: Log progress every N items
            
        Returns:
            Tuple of (successful_results, failed_items_with_errors)
        """
        results: List[R] = []
        errors: List[Tuple[T, Exception]] = []
        total = len(items)
        
        for idx, item in enumerate(items, 1):
            try:
                result = process_func(item)
                results.append(result)
            except Exception as e:
                errors.append((item, e))
                
                error_context = capture_error_context(
                    error=e,
                    component=component,
                    operation=operation,
                    input_data={"item": str(item), "index": idx}
                )
                log_error(self.logger, error_context)
                
                if not continue_on_error:
                    raise
            
            # Log progress at intervals
            if idx % log_interval == 0 or idx == total:
                self.logger.info(
                    "batch_processing_progress",
                    processed=idx,
                    total=total,
                    successful=len(results),
                    failed=len(errors),
                    progress_percent=round((idx / total) * 100, 2),
                    component=component,
                    operation=operation
                )
        
        return results, errors


def process_in_batches(
    items: List[T],
    process_func: Callable[[T], R],
    logger: Logger,
    batch_size: int = 100,
    continue_on_error: bool = True
) -> Tuple[List[R], List[Tuple[T, Exception]]]:
    """
    Process items in smaller batches.
    
    Splits a large list of items into smaller batches and processes
    each batch separately. Useful for memory management and progress tracking.
    
    Args:
        items: List of items to process
        process_func: Function to process each item
        logger: Logger instance
        batch_size: Size of each batch
        continue_on_error: Whether to continue on error
        
    Returns:
        Tuple of (all_successful_results, all_failed_items_with_errors)
        
    Example:
        >>> results, errors = process_in_batches(
        ...     items=large_list,
        ...     process_func=process_item,
        ...     logger=logger,
        ...     batch_size=50
        ... )
    """
    processor = BatchProcessor(logger)
    all_results: List[R] = []
    all_errors: List[Tuple[T, Exception]] = []
    
    # Split into batches
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(items) + batch_size - 1) // batch_size
        
        logger.info(
            "processing_batch",
            batch_number=batch_num,
            total_batches=total_batches,
            batch_size=len(batch)
        )
        
        results, errors = processor.process_batch(
            items=batch,
            process_func=process_func,
            continue_on_error=continue_on_error
        )
        
        all_results.extend(results)
        all_errors.extend(errors)
    
    return all_results, all_errors
