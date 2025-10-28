#!/usr/bin/env python3
"""Generate sample reservation request data for testing."""

import os
from hut_allocator.csv_handler import generate_sample_csv

def main():
    # Create sample_data directory
    os.makedirs('sample_data', exist_ok=True)

    # Generate sample data with 15 users (75 total requests)
    output_file = 'sample_data/requests.csv'
    generate_sample_csv(output_file, num_users=15)

    print(f"\nSample data generated: {output_file}")
    print("\nTo run the allocator:")
    print(f"  python main.py {output_file}")

if __name__ == '__main__':
    main()
