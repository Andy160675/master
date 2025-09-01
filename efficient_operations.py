"""
Efficient Merge and Map Operations Module

This module provides optimized implementations for merging various data structures
and efficient mapping operations with performance considerations.
"""

from typing import List, Dict, Any, Callable, TypeVar, Union, Iterable
from collections import defaultdict
import heapq
from functools import reduce

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


class EfficientMerger:
    """Provides efficient merge operations for different data types."""
    
    @staticmethod
    def merge_sorted_lists(*lists: List[T]) -> List[T]:
        """
        Efficiently merge multiple sorted lists using heap-based approach.
        Time complexity: O(n log k) where n is total elements, k is number of lists.
        
        Args:
            *lists: Variable number of sorted lists to merge
            
        Returns:
            A single sorted list containing all elements
        """
        if not lists:
            return []
        
        # Filter out empty lists
        non_empty_lists = [lst for lst in lists if lst]
        if not non_empty_lists:
            return []
        
        # Use heap for efficient merging
        heap = []
        result = []
        
        # Initialize heap with first element from each list
        for i, lst in enumerate(non_empty_lists):
            if lst:
                heapq.heappush(heap, (lst[0], i, 0))
        
        while heap:
            val, list_idx, elem_idx = heapq.heappop(heap)
            result.append(val)
            
            # Add next element from the same list if available
            if elem_idx + 1 < len(non_empty_lists[list_idx]):
                next_val = non_empty_lists[list_idx][elem_idx + 1]
                heapq.heappush(heap, (next_val, list_idx, elem_idx + 1))
        
        return result
    
    @staticmethod
    def merge_dicts(*dicts: Dict[K, V], strategy: str = 'last_wins') -> Dict[K, V]:
        """
        Efficiently merge multiple dictionaries with different merge strategies.
        
        Args:
            *dicts: Variable number of dictionaries to merge
            strategy: Merge strategy - 'last_wins', 'first_wins', 'combine_lists'
            
        Returns:
            Merged dictionary based on the specified strategy
        """
        if not dicts:
            return {}
        
        if strategy == 'last_wins':
            # Simple update - last value wins for duplicate keys
            result = {}
            for d in dicts:
                result.update(d)
            return result
        
        elif strategy == 'first_wins':
            # First occurrence wins for duplicate keys
            result = {}
            for d in dicts:
                for k, v in d.items():
                    if k not in result:
                        result[k] = v
            return result
        
        elif strategy == 'combine_lists':
            # Combine values into lists for duplicate keys
            result = defaultdict(list)
            for d in dicts:
                for k, v in d.items():
                    if isinstance(v, list):
                        result[k].extend(v)
                    else:
                        result[k].append(v)
            return dict(result)
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    @staticmethod
    def merge_lists(*lists: List[T], remove_duplicates: bool = False) -> List[T]:
        """
        Efficiently merge multiple lists.
        
        Args:
            *lists: Variable number of lists to merge
            remove_duplicates: Whether to remove duplicate values
            
        Returns:
            Merged list
        """
        if not lists:
            return []
        
        # Use itertools chain for memory efficiency
        from itertools import chain
        merged = list(chain(*lists))
        
        if remove_duplicates:
            # Use dict to preserve order while removing duplicates (Python 3.7+)
            return list(dict.fromkeys(merged))
        
        return merged


class EfficientMapper:
    """Provides efficient mapping operations with performance optimizations."""
    
    @staticmethod
    def parallel_map(func: Callable[[T], Any], iterable: Iterable[T], 
                    chunk_size: int = None) -> List[Any]:
        """
        Efficiently map a function over an iterable using multiprocessing for CPU-bound tasks.
        
        Args:
            func: Function to apply to each element
            iterable: Iterable to process
            chunk_size: Size of chunks for parallel processing
            
        Returns:
            List of mapped results
        """
        from multiprocessing import Pool, cpu_count
        import os
        
        data = list(iterable)
        if len(data) <= 1000:  # Use regular map for small datasets
            return list(map(func, data))
        
        if chunk_size is None:
            chunk_size = max(1, len(data) // (cpu_count() * 4))
        
        try:
            with Pool() as pool:
                return pool.map(func, data, chunksize=chunk_size)
        except Exception:
            # Fallback to regular map if multiprocessing fails
            return list(map(func, data))
    
    @staticmethod
    def batch_map(func: Callable[[List[T]], List[Any]], iterable: Iterable[T], 
                  batch_size: int = 1000) -> List[Any]:
        """
        Map function over batches of data for memory efficiency.
        
        Args:
            func: Function that processes a batch and returns a list
            iterable: Data to process
            batch_size: Size of each batch
            
        Returns:
            Flattened list of all results
        """
        from itertools import islice
        
        iterator = iter(iterable)
        results = []
        
        while True:
            batch = list(islice(iterator, batch_size))
            if not batch:
                break
            
            batch_results = func(batch)
            results.extend(batch_results)
        
        return results
    
    @staticmethod
    def memory_efficient_map(func: Callable[[T], Any], iterable: Iterable[T]):
        """
        Generator-based mapping for memory efficiency with large datasets.
        
        Args:
            func: Function to apply to each element
            iterable: Iterable to process
            
        Yields:
            Mapped results one at a time
        """
        for item in iterable:
            yield func(item)
    
    @staticmethod
    def indexed_map(func: Callable[[int, T], Any], iterable: Iterable[T]) -> List[Any]:
        """
        Map function with access to element index.
        
        Args:
            func: Function that takes (index, element) and returns result
            iterable: Iterable to process
            
        Returns:
            List of mapped results
        """
        return [func(i, item) for i, item in enumerate(iterable)]


class PerformanceOptimizer:
    """Utility class for performance monitoring and optimization."""
    
    @staticmethod
    def benchmark_function(func: Callable, *args, iterations: int = 1000, **kwargs):
        """
        Benchmark a function's performance.
        
        Args:
            func: Function to benchmark
            *args: Arguments for the function
            iterations: Number of iterations to run
            **kwargs: Keyword arguments for the function
            
        Returns:
            Dictionary with timing statistics
        """
        import time
        
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            end = time.perf_counter()
            times.append(end - start)
        
        return {
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': sum(times) / len(times),
            'total_time': sum(times),
            'iterations': iterations
        }
    
    @staticmethod
    def profile_memory_usage(func: Callable, *args, **kwargs):
        """
        Profile memory usage of a function.
        
        Args:
            func: Function to profile
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Memory usage statistics
        """
        import tracemalloc
        
        tracemalloc.start()
        
        # Get baseline memory
        baseline = tracemalloc.get_traced_memory()[0]
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Get peak memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return {
            'result': result,
            'baseline_memory': baseline,
            'current_memory': current,
            'peak_memory': peak,
            'memory_increase': current - baseline,
            'peak_increase': peak - baseline
        }


# Convenience functions for common operations
def merge_all_lists(*lists: List[T], remove_duplicates: bool = False) -> List[T]:
    """Convenience function to merge all lists efficiently."""
    return EfficientMerger.merge_lists(*lists, remove_duplicates=remove_duplicates)


def merge_all_dicts(*dicts: Dict[K, V], strategy: str = 'last_wins') -> Dict[K, V]:
    """Convenience function to merge all dictionaries efficiently."""
    return EfficientMerger.merge_dicts(*dicts, strategy=strategy)


def efficient_map(func: Callable[[T], Any], data: Iterable[T], 
                 use_parallel: bool = False, batch_size: int = None) -> List[Any]:
    """
    Convenience function for efficient mapping with automatic optimization.
    
    Args:
        func: Function to map over data
        data: Data to process
        use_parallel: Whether to use parallel processing
        batch_size: Batch size for processing (enables batch mode if set)
        
    Returns:
        List of mapped results
    """
    mapper = EfficientMapper()
    
    if batch_size:
        # Use batch processing
        def batch_func(batch):
            return [func(item) for item in batch]
        return mapper.batch_map(batch_func, data, batch_size)
    elif use_parallel:
        # Use parallel processing
        return mapper.parallel_map(func, data)
    else:
        # Use regular mapping
        return list(map(func, data))