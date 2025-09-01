#!/usr/bin/env python3
"""
Simple usage example demonstrating the most common use cases
for efficient merge and map operations.
"""

from efficient_operations import merge_all_lists, merge_all_dicts, efficient_map

def main():
    print("=== Efficient Merge and Map Operations - Quick Example ===\n")
    
    # Example 1: Merge multiple data sources
    print("1. Merging customer data from multiple sources:")
    customers_db1 = [{'id': 1, 'name': 'Alice'}, {'id': 3, 'name': 'Charlie'}]
    customers_db2 = [{'id': 2, 'name': 'Bob'}, {'id': 4, 'name': 'Diana'}]
    customers_db3 = [{'id': 5, 'name': 'Eve'}]
    
    # Merge all customer lists
    all_customers = merge_all_lists(customers_db1, customers_db2, customers_db3)
    print(f"   Total customers: {len(all_customers)}")
    for customer in all_customers:
        print(f"   - {customer}")
    
    # Example 2: Merge configuration dictionaries
    print("\n2. Merging configuration settings:")
    default_config = {'timeout': 30, 'retries': 3, 'debug': False}
    user_config = {'timeout': 60, 'log_level': 'INFO'}
    env_config = {'debug': True, 'api_key': 'secret123'}
    
    final_config = merge_all_dicts(default_config, user_config, env_config)
    print("   Final configuration:")
    for key, value in final_config.items():
        print(f"   - {key}: {value}")
    
    # Example 3: Efficient data processing
    print("\n3. Processing large dataset efficiently:")
    
    # Simulate processing sales data
    sales_data = [
        {'amount': 100, 'region': 'North'},
        {'amount': 250, 'region': 'South'},
        {'amount': 175, 'region': 'East'},
        {'amount': 300, 'region': 'West'},
        {'amount': 150, 'region': 'North'},
    ]
    
    # Calculate tax for each sale (20% tax rate)
    def calculate_tax(sale):
        return {
            'amount': sale['amount'],
            'region': sale['region'],
            'tax': sale['amount'] * 0.20,
            'total': sale['amount'] * 1.20
        }
    
    # Use efficient mapping
    processed_sales = efficient_map(calculate_tax, sales_data)
    
    print(f"   Processed {len(processed_sales)} sales records:")
    total_revenue = sum(sale['total'] for sale in processed_sales)
    total_tax = sum(sale['tax'] for sale in processed_sales)
    
    print(f"   - Total revenue: ${total_revenue:.2f}")
    print(f"   - Total tax collected: ${total_tax:.2f}")
    
    # Example 4: Merge and deduplicate tags
    print("\n4. Merging and deduplicating tags:")
    article1_tags = ['python', 'programming', 'tutorial']
    article2_tags = ['python', 'data-science', 'machine-learning']
    article3_tags = ['tutorial', 'beginner', 'python']
    
    all_tags = merge_all_lists(article1_tags, article2_tags, article3_tags, remove_duplicates=True)
    print(f"   Unique tags: {all_tags}")
    print(f"   Total unique tags: {len(all_tags)}")
    
    print("\n=== Example completed successfully! ===")

if __name__ == "__main__":
    main()