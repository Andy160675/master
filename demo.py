#!/usr/bin/env python3
"""
Demonstration script for efficient merge and map operations.

This script showcases the usage and performance characteristics of the
efficient merge and map operations implemented in the module.
"""

import time
import random
from efficient_operations import (
    EfficientMerger, EfficientMapper, PerformanceOptimizer,
    merge_all_lists, merge_all_dicts, efficient_map
)


def demo_merge_operations():
    """Demonstrate various merge operations."""
    print("=" * 60)
    print("MERGE OPERATIONS DEMONSTRATION")
    print("=" * 60)
    
    # Demo 1: Merging sorted lists
    print("\n1. Merging Sorted Lists:")
    print("-" * 30)
    
    list1 = [1, 5, 9, 13]
    list2 = [2, 6, 10, 14]
    list3 = [3, 7, 11, 15]
    list4 = [4, 8, 12, 16]
    
    print(f"Input lists:")
    print(f"  List 1: {list1}")
    print(f"  List 2: {list2}")
    print(f"  List 3: {list3}")
    print(f"  List 4: {list4}")
    
    merged = EfficientMerger.merge_sorted_lists(list1, list2, list3, list4)
    print(f"Merged result: {merged}")
    
    # Demo 2: Merging dictionaries
    print("\n2. Merging Dictionaries:")
    print("-" * 30)
    
    dict1 = {'name': 'Alice', 'age': 25, 'city': 'NYC'}
    dict2 = {'age': 26, 'occupation': 'Engineer', 'city': 'SF'}
    dict3 = {'hobby': 'Reading', 'city': 'LA'}
    
    print(f"Input dictionaries:")
    print(f"  Dict 1: {dict1}")
    print(f"  Dict 2: {dict2}")
    print(f"  Dict 3: {dict3}")
    
    # Different merge strategies
    last_wins = EfficientMerger.merge_dicts(dict1, dict2, dict3, strategy='last_wins')
    first_wins = EfficientMerger.merge_dicts(dict1, dict2, dict3, strategy='first_wins')
    combine_lists = EfficientMerger.merge_dicts(dict1, dict2, dict3, strategy='combine_lists')
    
    print(f"\nLast wins strategy: {last_wins}")
    print(f"First wins strategy: {first_wins}")
    print(f"Combine lists strategy: {combine_lists}")
    
    # Demo 3: Merging regular lists
    print("\n3. Merging Regular Lists:")
    print("-" * 30)
    
    colors1 = ['red', 'blue']
    colors2 = ['green', 'blue', 'yellow']
    colors3 = ['red', 'purple']
    
    print(f"Input lists:")
    print(f"  Colors 1: {colors1}")
    print(f"  Colors 2: {colors2}")
    print(f"  Colors 3: {colors3}")
    
    merged_with_dupes = merge_all_lists(colors1, colors2, colors3)
    merged_no_dupes = merge_all_lists(colors1, colors2, colors3, remove_duplicates=True)
    
    print(f"Merged with duplicates: {merged_with_dupes}")
    print(f"Merged without duplicates: {merged_no_dupes}")


def demo_map_operations():
    """Demonstrate various mapping operations."""
    print("\n" + "=" * 60)
    print("MAP OPERATIONS DEMONSTRATION")
    print("=" * 60)
    
    # Demo 1: Regular mapping
    print("\n1. Regular Mapping:")
    print("-" * 25)
    
    numbers = list(range(1, 11))
    print(f"Input: {numbers}")
    
    def square_and_format(x):
        return f"{x}² = {x**2}"
    
    result = efficient_map(square_and_format, numbers)
    print("Mapped results:")
    for item in result:
        print(f"  {item}")
    
    # Demo 2: Indexed mapping
    print("\n2. Indexed Mapping:")
    print("-" * 25)
    
    words = ['apple', 'banana', 'cherry', 'date']
    print(f"Input: {words}")
    
    def format_with_index(index, word):
        return f"{index}: {word.upper()}"
    
    indexed_result = EfficientMapper.indexed_map(format_with_index, words)
    print("Indexed mapping results:")
    for item in indexed_result:
        print(f"  {item}")
    
    # Demo 3: Batch processing
    print("\n3. Batch Processing:")
    print("-" * 25)
    
    large_data = list(range(1, 21))
    print(f"Input (first 10): {large_data[:10]}...")
    
    def process_batch(batch):
        return [x * 3 for x in batch if x % 2 == 0]
    
    batch_result = EfficientMapper.batch_map(process_batch, large_data, batch_size=5)
    print(f"Batch processed (even numbers × 3): {batch_result}")


def demo_performance_analysis():
    """Demonstrate performance analysis capabilities."""
    print("\n" + "=" * 60)
    print("PERFORMANCE ANALYSIS DEMONSTRATION")
    print("=" * 60)
    
    # Demo 1: Function benchmarking
    print("\n1. Function Benchmarking:")
    print("-" * 30)
    
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)
    
    def fibonacci_optimized(n, memo={}):
        if n in memo:
            return memo[n]
        if n <= 1:
            return n
        memo[n] = fibonacci_optimized(n-1, memo) + fibonacci_optimized(n-2, memo)
        return memo[n]
    
    print("Benchmarking Fibonacci implementations:")
    
    # Benchmark regular fibonacci
    stats_regular = PerformanceOptimizer.benchmark_function(fibonacci, 25, iterations=10)
    print(f"\nRegular Fibonacci (n=25, 10 iterations):")
    print(f"  Average time: {stats_regular['avg_time']:.6f} seconds")
    print(f"  Min time: {stats_regular['min_time']:.6f} seconds")
    print(f"  Max time: {stats_regular['max_time']:.6f} seconds")
    
    # Benchmark optimized fibonacci
    stats_optimized = PerformanceOptimizer.benchmark_function(fibonacci_optimized, 25, iterations=10)
    print(f"\nOptimized Fibonacci (n=25, 10 iterations):")
    print(f"  Average time: {stats_optimized['avg_time']:.6f} seconds")
    print(f"  Min time: {stats_optimized['min_time']:.6f} seconds")
    print(f"  Max time: {stats_optimized['max_time']:.6f} seconds")
    
    speedup = stats_regular['avg_time'] / stats_optimized['avg_time']
    print(f"\nSpeedup: {speedup:.2f}x faster")
    
    # Demo 2: Memory profiling
    print("\n2. Memory Usage Profiling:")
    print("-" * 30)
    
    def create_large_structure(size):
        return {f"key_{i}": list(range(i, i+10)) for i in range(size)}
    
    print("Profiling memory usage for large data structure creation:")
    
    memory_stats = PerformanceOptimizer.profile_memory_usage(create_large_structure, 1000)
    print(f"  Baseline memory: {memory_stats['baseline_memory']:,} bytes")
    print(f"  Peak memory: {memory_stats['peak_memory']:,} bytes")
    print(f"  Memory increase: {memory_stats['memory_increase']:,} bytes")
    print(f"  Peak increase: {memory_stats['peak_increase']:,} bytes")
    print(f"  Created structure with {len(memory_stats['result'])} items")


def demo_efficiency_comparison():
    """Demonstrate efficiency of operations with large datasets."""
    print("\n" + "=" * 60)
    print("EFFICIENCY COMPARISON WITH LARGE DATASETS")
    print("=" * 60)
    
    # Generate large datasets
    print("\nGenerating large test datasets...")
    
    # Large sorted lists
    large_lists = []
    for i in range(5):
        large_list = sorted([random.randint(1, 10000) for _ in range(2000)])
        large_lists.append(large_list)
    
    print(f"Created 5 sorted lists with 2000 elements each")
    
    # Time the merge operation
    start_time = time.time()
    merged_large = EfficientMerger.merge_sorted_lists(*large_lists)
    merge_time = time.time() - start_time
    
    print(f"Merged {len(merged_large)} elements in {merge_time:.4f} seconds")
    print(f"Rate: {len(merged_large) / merge_time:.0f} elements/second")
    
    # Large dictionary merge
    print("\nTesting large dictionary merge...")
    
    large_dicts = []
    for i in range(10):
        large_dict = {f"key_{j}_{i}": random.randint(1, 1000) for j in range(1000)}
        large_dicts.append(large_dict)
    
    start_time = time.time()
    merged_dict = EfficientMerger.merge_dicts(*large_dicts)
    dict_merge_time = time.time() - start_time
    
    print(f"Merged 10 dictionaries with 1000 keys each")
    print(f"Result has {len(merged_dict)} unique keys")
    print(f"Merge completed in {dict_merge_time:.4f} seconds")
    
    # Large mapping operation
    print("\nTesting efficient mapping on large dataset...")
    
    large_data = list(range(10000))
    
    def complex_operation(x):
        return x ** 2 + 2 * x + 1
    
    # Test regular mapping
    start_time = time.time()
    regular_result = list(map(complex_operation, large_data))
    regular_time = time.time() - start_time
    
    # Test batch mapping
    start_time = time.time()
    batch_result = efficient_map(complex_operation, large_data, batch_size=500)
    batch_time = time.time() - start_time
    
    print(f"Regular mapping: {regular_time:.4f} seconds")
    print(f"Batch mapping: {batch_time:.4f} seconds")
    print(f"Results are identical: {regular_result == batch_result}")


def main():
    """Main demonstration function."""
    print("EFFICIENT MERGE AND MAP OPERATIONS")
    print("Demonstrating high-performance data processing capabilities")
    print()
    
    try:
        demo_merge_operations()
        demo_map_operations()
        demo_performance_analysis()
        demo_efficiency_comparison()
        
        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nThe efficient merge and map operations have been demonstrated with:")
        print("✓ Multiple merge strategies for different data types")
        print("✓ Optimized mapping operations with various approaches")
        print("✓ Performance monitoring and benchmarking capabilities")
        print("✓ Memory-efficient processing of large datasets")
        print("✓ Scalable algorithms suitable for production use")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()