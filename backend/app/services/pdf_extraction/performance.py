"""
Performance optimization utilities for PDF extraction pipeline.

This module provides utilities for:
- Parallel page processing with asyncio
- Batch LLM calls
- Local filesystem caching
- Memory management
- Database write optimization
"""

import asyncio
import hashlib
import json
import logging
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, TypeVar, Coroutine
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)

T = TypeVar('T')


class ParallelProcessor:
    """
    Handles parallel processing of pages and operations.
    
    Uses asyncio for concurrent operations while maintaining thread safety.
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize parallel processor.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        logger.info(f"ParallelProcessor initialized with {max_workers} workers")
    
    async def process_pages_parallel(
        self,
        pages: List[str],
        process_func: Callable[[str, int], Coroutine[Any, Any, T]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[T]:
        """
        Process pages in parallel using asyncio.
        
        Args:
            pages: List of page contents to process
            process_func: Async function to process each page (page_content, page_index) -> result
            progress_callback: Optional callback for progress updates (completed, total)
            
        Returns:
            List of results in same order as input pages
        """
        async def process_with_semaphore(page: str, index: int) -> T:
            async with self.semaphore:
                result = await process_func(page, index)
                if progress_callback:
                    progress_callback(index + 1, len(pages))
                return result
        
        # Create tasks for all pages
        tasks = [
            process_with_semaphore(page, i)
            for i, page in enumerate(pages)
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing page {i}: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def process_batch_parallel(
        self,
        items: List[Any],
        process_func: Callable[[Any], Coroutine[Any, Any, T]],
        batch_size: int = 10
    ) -> List[T]:
        """
        Process items in parallel batches.
        
        Args:
            items: List of items to process
            process_func: Async function to process each item
            batch_size: Number of items to process per batch
            
        Returns:
            List of results
        """
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            async def process_with_semaphore(item: Any) -> T:
                async with self.semaphore:
                    return await process_func(item)
            
            batch_tasks = [process_with_semaphore(item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error in batch processing: {result}")
                    results.append(None)
                else:
                    results.append(result)
        
        return results


class BatchLLMProcessor:
    """
    Handles batching of LLM calls to reduce API overhead.
    
    Groups similar operations into batches and processes them together.
    """
    
    def __init__(self, batch_size: int = 10, batch_delay: float = 0.5):
        """
        Initialize batch LLM processor.
        
        Args:
            batch_size: Maximum number of items per batch
            batch_delay: Delay in seconds before processing batch
        """
        self.batch_size = batch_size
        self.batch_delay = batch_delay
        self._pending_batches: Dict[str, List[Dict[str, Any]]] = {}
        logger.info(f"BatchLLMProcessor initialized (batch_size={batch_size})")
    
    async def add_to_batch(
        self,
        batch_key: str,
        item: Dict[str, Any],
        process_func: Callable[[List[Dict[str, Any]]], Coroutine[Any, Any, List[Any]]]
    ) -> Any:
        """
        Add item to batch and process when batch is full.
        
        Args:
            batch_key: Key to group similar operations
            item: Item to add to batch
            process_func: Function to process the batch
            
        Returns:
            Result for this item
        """
        if batch_key not in self._pending_batches:
            self._pending_batches[batch_key] = []
        
        self._pending_batches[batch_key].append(item)
        
        # Process batch if full
        if len(self._pending_batches[batch_key]) >= self.batch_size:
            return await self._process_batch(batch_key, process_func)
        
        # Wait for more items or timeout
        await asyncio.sleep(self.batch_delay)
        
        # Process whatever we have
        if self._pending_batches.get(batch_key):
            return await self._process_batch(batch_key, process_func)
    
    async def _process_batch(
        self,
        batch_key: str,
        process_func: Callable[[List[Dict[str, Any]]], Coroutine[Any, Any, List[Any]]]
    ) -> List[Any]:
        """
        Process a batch of items.
        
        Args:
            batch_key: Batch identifier
            process_func: Function to process the batch
            
        Returns:
            List of results
        """
        batch = self._pending_batches.pop(batch_key, [])
        if not batch:
            return []
        
        logger.debug(f"Processing batch '{batch_key}' with {len(batch)} items")
        
        try:
            results = await process_func(batch)
            return results
        except Exception as e:
            logger.error(f"Error processing batch '{batch_key}': {e}")
            return [None] * len(batch)
    
    async def flush_all(
        self,
        process_funcs: Dict[str, Callable[[List[Dict[str, Any]]], Coroutine[Any, Any, List[Any]]]]
    ) -> Dict[str, List[Any]]:
        """
        Flush all pending batches.
        
        Args:
            process_funcs: Dictionary mapping batch_key to process function
            
        Returns:
            Dictionary mapping batch_key to results
        """
        results = {}
        
        for batch_key in list(self._pending_batches.keys()):
            if batch_key in process_funcs:
                batch_results = await self._process_batch(batch_key, process_funcs[batch_key])
                results[batch_key] = batch_results
        
        return results


class CacheManager:
    """
    Manages local filesystem caching for structure analysis patterns.
    
    Caches structure patterns for similar books to speed up processing.
    """
    
    def __init__(self, cache_dir: str = "backend/data/cache"):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"CacheManager initialized (cache_dir={cache_dir})")
    
    def _get_cache_key(self, metadata: Dict[str, Any]) -> str:
        """
        Generate cache key from book metadata.
        
        Args:
            metadata: Book metadata dictionary
            
        Returns:
            Cache key string
        """
        # Create key from subject, grade_level, and publisher
        key_parts = [
            metadata.get("subject", ""),
            metadata.get("grade_level", ""),
            metadata.get("publisher", ""),
        ]
        key_string = "_".join(str(p).lower().replace(" ", "_") for p in key_parts if p)
        
        # Hash for consistent filename
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
        return f"{key_string}_{key_hash}"
    
    def get_cached_structure(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached structure pattern for similar books.
        
        Args:
            metadata: Book metadata
            
        Returns:
            Cached structure data or None if not found
        """
        cache_key = self._get_cache_key(metadata)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            logger.debug(f"Cache miss for key: {cache_key}")
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Cache hit for key: {cache_key}")
            return data
        except Exception as e:
            logger.error(f"Error reading cache file {cache_file}: {e}")
            return None
    
    def save_structure_to_cache(
        self,
        metadata: Dict[str, Any],
        structure_data: Dict[str, Any]
    ) -> None:
        """
        Save structure pattern to cache.
        
        Args:
            metadata: Book metadata
            structure_data: Structure data to cache
        """
        cache_key = self._get_cache_key(metadata)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(structure_data, f, indent=2)
            
            logger.info(f"Saved structure to cache: {cache_key}")
        except Exception as e:
            logger.error(f"Error writing cache file {cache_file}: {e}")
    
    def invalidate_cache(self, metadata: Dict[str, Any]) -> None:
        """
        Invalidate cache for specific metadata.
        
        Args:
            metadata: Book metadata
        """
        cache_key = self._get_cache_key(metadata)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            cache_file.unlink()
            logger.info(f"Invalidated cache: {cache_key}")
    
    def clear_all_cache(self) -> None:
        """Clear all cached data."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        logger.info("Cleared all cache")


class MemoryManager:
    """
    Manages memory usage during PDF processing.
    
    Implements streaming processing, lazy loading, and explicit garbage collection.
    """
    
    def __init__(self, max_memory_mb: int = 2048):
        """
        Initialize memory manager.
        
        Args:
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_memory_mb = max_memory_mb
        self.gc_threshold = max_memory_mb * 0.8  # Trigger GC at 80%
        logger.info(f"MemoryManager initialized (max={max_memory_mb}MB)")
    
    def get_memory_usage_mb(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            Memory usage in MB
        """
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return memory_info.rss / (1024 * 1024)
    
    def check_memory_and_gc(self) -> None:
        """
        Check memory usage and trigger garbage collection if needed.
        """
        current_memory = self.get_memory_usage_mb()
        
        if current_memory > self.gc_threshold:
            logger.warning(
                f"Memory usage ({current_memory:.2f}MB) exceeds threshold "
                f"({self.gc_threshold:.2f}MB), triggering GC"
            )
            gc.collect()
            
            new_memory = self.get_memory_usage_mb()
            freed = current_memory - new_memory
            logger.info(f"GC freed {freed:.2f}MB (now at {new_memory:.2f}MB)")
    
    def process_in_chunks(
        self,
        items: List[Any],
        process_func: Callable[[List[Any]], Any],
        chunk_size: int = 100
    ) -> List[Any]:
        """
        Process items in chunks with memory management.
        
        Args:
            items: List of items to process
            process_func: Function to process each chunk
            chunk_size: Number of items per chunk
            
        Returns:
            List of results
        """
        results = []
        
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            
            # Process chunk
            chunk_results = process_func(chunk)
            results.extend(chunk_results)
            
            # Check memory and GC if needed
            self.check_memory_and_gc()
        
        return results
    
    def cleanup_after_chapter(self) -> None:
        """
        Explicit cleanup after processing a chapter.
        
        Triggers garbage collection to free memory.
        """
        logger.debug("Cleaning up after chapter")
        gc.collect()
        
        current_memory = self.get_memory_usage_mb()
        logger.debug(f"Memory after cleanup: {current_memory:.2f}MB")


class DatabaseOptimizer:
    """
    Optimizes database write operations.
    
    Implements bulk inserts, connection pooling, and async writes.
    """
    
    def __init__(self, batch_size: int = 50):
        """
        Initialize database optimizer.
        
        Args:
            batch_size: Number of records per bulk insert
        """
        self.batch_size = batch_size
        self._write_queue: List[Dict[str, Any]] = []
        logger.info(f"DatabaseOptimizer initialized (batch_size={batch_size})")
    
    def add_to_write_queue(self, record: Dict[str, Any]) -> None:
        """
        Add record to write queue.
        
        Args:
            record: Database record to write
        """
        self._write_queue.append(record)
    
    async def flush_write_queue(
        self,
        write_func: Callable[[List[Dict[str, Any]]], Coroutine[Any, Any, int]]
    ) -> int:
        """
        Flush write queue using bulk insert.
        
        Args:
            write_func: Async function to write batch of records
            
        Returns:
            Number of records written
        """
        if not self._write_queue:
            return 0
        
        total_written = 0
        
        # Process in batches
        for i in range(0, len(self._write_queue), self.batch_size):
            batch = self._write_queue[i:i + self.batch_size]
            
            try:
                written = await write_func(batch)
                total_written += written
            except Exception as e:
                logger.error(f"Error writing batch: {e}")
        
        # Clear queue
        self._write_queue.clear()
        
        logger.info(f"Flushed write queue: {total_written} records written")
        return total_written
    
    def get_queue_size(self) -> int:
        """
        Get current write queue size.
        
        Returns:
            Number of records in queue
        """
        return len(self._write_queue)


def async_wrapper(func: Callable) -> Callable:
    """
    Decorator to convert sync function to async.
    
    Args:
        func: Synchronous function to wrap
        
    Returns:
        Async version of the function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))
    
    return wrapper
