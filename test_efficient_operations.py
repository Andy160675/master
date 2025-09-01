"""
Test suite for efficient merge and map operations.
"""

import unittest
import time
from typing import List, Dict
from efficient_operations import (
    EfficientMerger, EfficientMapper, PerformanceOptimizer,
    merge_all_lists, merge_all_dicts, efficient_map
)


class TestEfficientMerger(unittest.TestCase):
    """Test cases for EfficientMerger class."""
    
    def test_merge_sorted_lists_basic(self):
        """Test basic functionality of merge_sorted_lists."""
        list1 = [1, 3, 5]
        list2 = [2, 4, 6]
        list3 = [0, 7, 8]
        
        result = EfficientMerger.merge_sorted_lists(list1, list2, list3)
        expected = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        
        self.assertEqual(result, expected)
    
    def test_merge_sorted_lists_empty(self):
        """Test merge_sorted_lists with empty lists."""
        result = EfficientMerger.merge_sorted_lists()
        self.assertEqual(result, [])
        
        result = EfficientMerger.merge_sorted_lists([], [], [])
        self.assertEqual(result, [])
        
        result = EfficientMerger.merge_sorted_lists([1, 2], [], [3, 4])
        self.assertEqual(result, [1, 2, 3, 4])
    
    def test_merge_sorted_lists_single_element(self):
        """Test merge_sorted_lists with single elements."""
        result = EfficientMerger.merge_sorted_lists([1], [2], [0])
        self.assertEqual(result, [0, 1, 2])
    
    def test_merge_dicts_last_wins(self):
        """Test merge_dicts with last_wins strategy."""
        dict1 = {'a': 1, 'b': 2}
        dict2 = {'b': 3, 'c': 4}
        dict3 = {'c': 5, 'd': 6}
        
        result = EfficientMerger.merge_dicts(dict1, dict2, dict3, strategy='last_wins')
        expected = {'a': 1, 'b': 3, 'c': 5, 'd': 6}
        
        self.assertEqual(result, expected)
    
    def test_merge_dicts_first_wins(self):
        """Test merge_dicts with first_wins strategy."""
        dict1 = {'a': 1, 'b': 2}
        dict2 = {'b': 3, 'c': 4}
        dict3 = {'c': 5, 'd': 6}
        
        result = EfficientMerger.merge_dicts(dict1, dict2, dict3, strategy='first_wins')
        expected = {'a': 1, 'b': 2, 'c': 4, 'd': 6}
        
        self.assertEqual(result, expected)
    
    def test_merge_dicts_combine_lists(self):
        """Test merge_dicts with combine_lists strategy."""
        dict1 = {'a': 1, 'b': 2}
        dict2 = {'b': 3, 'c': 4}
        dict3 = {'c': 5, 'd': 6}
        
        result = EfficientMerger.merge_dicts(dict1, dict2, dict3, strategy='combine_lists')
        expected = {'a': [1], 'b': [2, 3], 'c': [4, 5], 'd': [6]}
        
        self.assertEqual(result, expected)
    
    def test_merge_dicts_empty(self):
        """Test merge_dicts with empty input."""
        result = EfficientMerger.merge_dicts()
        self.assertEqual(result, {})
    
    def test_merge_dicts_invalid_strategy(self):
        """Test merge_dicts with invalid strategy."""
        with self.assertRaises(ValueError):
            EfficientMerger.merge_dicts({'a': 1}, strategy='invalid')
    
    def test_merge_lists_basic(self):
        """Test basic merge_lists functionality."""
        list1 = [1, 2, 3]
        list2 = [4, 5, 6]
        list3 = [7, 8, 9]
        
        result = EfficientMerger.merge_lists(list1, list2, list3)
        expected = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        
        self.assertEqual(result, expected)
    
    def test_merge_lists_with_duplicates(self):
        """Test merge_lists with duplicate removal."""
        list1 = [1, 2, 3, 2]
        list2 = [3, 4, 5]
        list3 = [5, 6, 1]
        
        result = EfficientMerger.merge_lists(list1, list2, list3, remove_duplicates=True)
        expected = [1, 2, 3, 4, 5, 6]  # Order preserved, duplicates removed
        
        self.assertEqual(result, expected)
    
    def test_merge_lists_empty(self):
        """Test merge_lists with empty input."""
        result = EfficientMerger.merge_lists()
        self.assertEqual(result, [])


class TestEfficientMapper(unittest.TestCase):
    """Test cases for EfficientMapper class."""
    
    def test_parallel_map_basic(self):
        """Test basic parallel_map functionality."""
        def square(x):
            return x ** 2
        
        data = list(range(10))
        result = EfficientMapper.parallel_map(square, data)
        expected = [x ** 2 for x in data]
        
        self.assertEqual(result, expected)
    
    def test_parallel_map_small_dataset(self):
        """Test parallel_map with small dataset (should use regular map)."""
        def double(x):
            return x * 2
        
        data = [1, 2, 3]
        result = EfficientMapper.parallel_map(double, data)
        expected = [2, 4, 6]
        
        self.assertEqual(result, expected)
    
    def test_batch_map(self):
        """Test batch_map functionality."""
        def process_batch(batch):
            return [x * 2 for x in batch]
        
        data = list(range(10))
        result = EfficientMapper.batch_map(process_batch, data, batch_size=3)
        expected = [x * 2 for x in data]
        
        self.assertEqual(result, expected)
    
    def test_memory_efficient_map(self):
        """Test memory_efficient_map functionality."""
        def increment(x):
            return x + 1
        
        data = [1, 2, 3, 4, 5]
        result = list(EfficientMapper.memory_efficient_map(increment, data))
        expected = [2, 3, 4, 5, 6]
        
        self.assertEqual(result, expected)
    
    def test_indexed_map(self):
        """Test indexed_map functionality."""
        def add_index(index, value):
            return value + index
        
        data = [10, 20, 30]
        result = EfficientMapper.indexed_map(add_index, data)
        expected = [10, 21, 32]  # 10+0, 20+1, 30+2
        
        self.assertEqual(result, expected)


class TestPerformanceOptimizer(unittest.TestCase):
    """Test cases for PerformanceOptimizer class."""
    
    def test_benchmark_function(self):
        """Test benchmark_function functionality."""
        def simple_function(x):
            return x * 2
        
        stats = PerformanceOptimizer.benchmark_function(
            simple_function, 5, iterations=100
        )
        
        self.assertIn('min_time', stats)
        self.assertIn('max_time', stats)
        self.assertIn('avg_time', stats)
        self.assertIn('total_time', stats)
        self.assertEqual(stats['iterations'], 100)
        self.assertGreaterEqual(stats['max_time'], stats['min_time'])
    
    def test_profile_memory_usage(self):
        """Test profile_memory_usage functionality."""
        def create_list(size):
            return list(range(size))
        
        stats = PerformanceOptimizer.profile_memory_usage(create_list, 1000)
        
        self.assertIn('result', stats)
        self.assertIn('baseline_memory', stats)
        self.assertIn('current_memory', stats)
        self.assertIn('peak_memory', stats)
        self.assertIn('memory_increase', stats)
        self.assertIn('peak_increase', stats)
        
        # Should have created a list of 1000 elements
        self.assertEqual(len(stats['result']), 1000)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""
    
    def test_merge_all_lists(self):
        """Test merge_all_lists convenience function."""
        result = merge_all_lists([1, 2], [3, 4], [5, 6])
        expected = [1, 2, 3, 4, 5, 6]
        self.assertEqual(result, expected)
        
        result = merge_all_lists([1, 2, 1], [2, 3], remove_duplicates=True)
        expected = [1, 2, 3]
        self.assertEqual(result, expected)
    
    def test_merge_all_dicts(self):
        """Test merge_all_dicts convenience function."""
        result = merge_all_dicts({'a': 1}, {'b': 2}, {'c': 3})
        expected = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(result, expected)
        
        result = merge_all_dicts({'a': 1}, {'a': 2}, strategy='first_wins')
        expected = {'a': 1}
        self.assertEqual(result, expected)
    
    def test_efficient_map_regular(self):
        """Test efficient_map with regular mapping."""
        def square(x):
            return x ** 2
        
        result = efficient_map(square, [1, 2, 3, 4])
        expected = [1, 4, 9, 16]
        self.assertEqual(result, expected)
    
    def test_efficient_map_batch(self):
        """Test efficient_map with batch processing."""
        def square(x):
            return x ** 2
        
        result = efficient_map(square, range(10), batch_size=3)
        expected = [x ** 2 for x in range(10)]
        self.assertEqual(result, expected)


class TestPerformanceCharacteristics(unittest.TestCase):
    """Test performance characteristics of the implementations."""
    
    def test_merge_sorted_lists_performance(self):
        """Test that merge_sorted_lists is efficient for large inputs."""
        # Create multiple sorted lists
        lists = []
        for i in range(10):
            lists.append(list(range(i * 1000, (i + 1) * 1000)))
        
        start_time = time.time()
        result = EfficientMerger.merge_sorted_lists(*lists)
        end_time = time.time()
        
        # Should complete quickly and produce correct result
        self.assertLess(end_time - start_time, 1.0)  # Should take less than 1 second
        self.assertEqual(len(result), 10000)
        self.assertEqual(result, sorted(result))  # Should be properly sorted
    
    def test_dict_merge_performance(self):
        """Test that dictionary merging is efficient."""
        # Create multiple large dictionaries
        dicts = []
        for i in range(10):
            d = {f"key_{j}_{i}": j for j in range(1000)}
            dicts.append(d)
        
        start_time = time.time()
        result = EfficientMerger.merge_dicts(*dicts)
        end_time = time.time()
        
        # Should complete quickly
        self.assertLess(end_time - start_time, 1.0)
        self.assertGreater(len(result), 5000)  # Should have many keys


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)