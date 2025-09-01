# Efficient Merge and Map Operations

This project provides highly optimized implementations for merging various data structures and efficient mapping operations with performance considerations. It addresses the requirement for "merge all and map efficiency" by providing scalable, memory-efficient algorithms suitable for production use.

## Features

### 🚀 Efficient Merge Operations
- **Sorted List Merging**: O(n log k) heap-based algorithm for merging multiple sorted lists
- **Dictionary Merging**: Multiple strategies (last wins, first wins, combine lists) for merging dictionaries
- **List Merging**: Fast concatenation with optional duplicate removal

### 🎯 Optimized Map Operations  
- **Parallel Mapping**: Multiprocessing support for CPU-bound operations
- **Batch Processing**: Memory-efficient processing of large datasets
- **Indexed Mapping**: Access to element indices during mapping
- **Memory-Efficient Streaming**: Generator-based mapping for large datasets

### 📊 Performance Analysis
- **Function Benchmarking**: Detailed timing statistics for performance optimization
- **Memory Profiling**: Track memory usage patterns and identify bottlenecks
- **Scalability Testing**: Validate performance with large datasets

## Quick Start

### Installation

No external dependencies required - uses only Python standard library.

```python
# Import the main functionality
from efficient_operations import (
    EfficientMerger, EfficientMapper, PerformanceOptimizer,
    merge_all_lists, merge_all_dicts, efficient_map
)
```

### Basic Usage

#### Merging Operations

```python
# Merge sorted lists efficiently
list1 = [1, 5, 9]
list2 = [2, 6, 10]  
list3 = [3, 7, 11]
merged = EfficientMerger.merge_sorted_lists(list1, list2, list3)
# Result: [1, 2, 3, 5, 6, 7, 9, 10, 11]

# Merge dictionaries with different strategies
dict1 = {'a': 1, 'b': 2}
dict2 = {'b': 3, 'c': 4}

# Last value wins for duplicate keys
merged = EfficientMerger.merge_dicts(dict1, dict2, strategy='last_wins')
# Result: {'a': 1, 'b': 3, 'c': 4}

# Combine duplicate keys into lists
merged = EfficientMerger.merge_dicts(dict1, dict2, strategy='combine_lists')
# Result: {'a': [1], 'b': [2, 3], 'c': [4]}

# Merge regular lists with duplicate removal
colors1 = ['red', 'blue']
colors2 = ['blue', 'green']
merged = merge_all_lists(colors1, colors2, remove_duplicates=True)
# Result: ['red', 'blue', 'green']
```

#### Mapping Operations

```python
# Efficient mapping with automatic optimization
data = list(range(1000))
result = efficient_map(lambda x: x**2, data, use_parallel=True)

# Batch processing for memory efficiency
def process_batch(batch):
    return [x * 2 for x in batch]

result = EfficientMapper.batch_map(process_batch, data, batch_size=100)

# Indexed mapping with access to element position
def format_with_index(index, value):
    return f"{index}: {value}"

result = EfficientMapper.indexed_map(format_with_index, ['a', 'b', 'c'])
# Result: ['0: a', '1: b', '2: c']
```

#### Performance Analysis

```python
# Benchmark function performance
def fibonacci(n):
    return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)

stats = PerformanceOptimizer.benchmark_function(fibonacci, 20, iterations=100)
print(f"Average time: {stats['avg_time']:.6f} seconds")

# Profile memory usage
def create_large_list(size):
    return list(range(size))

memory_stats = PerformanceOptimizer.profile_memory_usage(create_large_list, 10000)
print(f"Memory increase: {memory_stats['memory_increase']} bytes")
```

## Performance Characteristics

### Time Complexity
- **Sorted List Merging**: O(n log k) where n = total elements, k = number of lists
- **Dictionary Merging**: O(n) where n = total key-value pairs
- **List Merging**: O(n) where n = total elements
- **Parallel Mapping**: O(n/p) where p = number of CPU cores

### Space Complexity
- **Memory-efficient streaming**: O(1) additional space for generator-based operations
- **Batch processing**: O(batch_size) memory usage
- **Duplicate removal**: O(n) for tracking unique elements

### Scalability
The implementation handles large datasets efficiently:
- ✅ Merges 10,000+ elements in milliseconds
- ✅ Processes dictionaries with 10,000+ keys efficiently  
- ✅ Supports parallel processing for CPU-bound operations
- ✅ Memory-efficient for datasets that don't fit in memory

## API Reference

### EfficientMerger Class

#### `merge_sorted_lists(*lists) -> List`
Merges multiple sorted lists using a heap-based algorithm.

**Parameters:**
- `*lists`: Variable number of sorted lists to merge

**Returns:** Single sorted list containing all elements

#### `merge_dicts(*dicts, strategy='last_wins') -> Dict`
Merges multiple dictionaries with configurable strategies.

**Parameters:**
- `*dicts`: Variable number of dictionaries to merge
- `strategy`: Merge strategy ('last_wins', 'first_wins', 'combine_lists')

**Returns:** Merged dictionary

#### `merge_lists(*lists, remove_duplicates=False) -> List`
Merges multiple lists with optional duplicate removal.

**Parameters:**
- `*lists`: Variable number of lists to merge
- `remove_duplicates`: Whether to remove duplicate values

**Returns:** Merged list

### EfficientMapper Class

#### `parallel_map(func, iterable, chunk_size=None) -> List`
Maps function over iterable using multiprocessing for large datasets.

**Parameters:**
- `func`: Function to apply to each element
- `iterable`: Data to process
- `chunk_size`: Size of chunks for parallel processing

**Returns:** List of mapped results

#### `batch_map(func, iterable, batch_size=1000) -> List`
Maps function over batches of data for memory efficiency.

**Parameters:**
- `func`: Function that processes a batch and returns a list
- `iterable`: Data to process
- `batch_size`: Size of each batch

**Returns:** Flattened list of all results

#### `memory_efficient_map(func, iterable)`
Generator-based mapping for memory efficiency with large datasets.

**Parameters:**
- `func`: Function to apply to each element
- `iterable`: Data to process

**Yields:** Mapped results one at a time

#### `indexed_map(func, iterable) -> List`
Maps function with access to element index.

**Parameters:**
- `func`: Function that takes (index, element) and returns result
- `iterable`: Data to process

**Returns:** List of mapped results

### PerformanceOptimizer Class

#### `benchmark_function(func, *args, iterations=1000, **kwargs) -> Dict`
Benchmarks function performance with detailed timing statistics.

#### `profile_memory_usage(func, *args, **kwargs) -> Dict`
Profiles memory usage of a function execution.

## Testing

Run the comprehensive test suite:

```bash
python test_efficient_operations.py
```

The test suite includes:
- ✅ 24 test cases covering all functionality
- ✅ Performance validation for large datasets
- ✅ Edge case handling (empty inputs, single elements)
- ✅ Memory efficiency verification

## Demonstration

Run the demonstration script to see all features in action:

```bash
python demo.py
```

The demonstration showcases:
- Merge operations with various data types
- Mapping operations with different optimization strategies
- Performance analysis and benchmarking
- Efficiency comparison with large datasets

## License

This project is licensed under the Apache License 2.0. See LICENSE file for details.

## Contributing

Contributions are welcome! The implementation focuses on:
- Minimal, surgical changes to achieve maximum efficiency
- Comprehensive test coverage
- Clear documentation and examples
- Performance optimization without sacrificing readability

---

*Built with efficiency in mind - merge all your data and map with optimal performance!*
