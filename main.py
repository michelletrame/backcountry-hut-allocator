#!/usr/bin/env python3
"""
Backcountry Hut Reservation Allocator

This script optimally allocates reservation requests to backcountry huts
based on user preferences, date availability, and hut capacity constraints.

Usage:
    python main.py <input_csv> [--output <output_dir>]

Example:
    python main.py sample_data/requests.csv --output results/
"""

import sys
import os
import argparse
from datetime import datetime

from hut_allocator.config import HUTS, SEASON_START, SEASON_END, NUM_ITERATIONS, TIMEOUT_SECONDS
from hut_allocator.csv_handler import load_requests_from_csv, save_allocation_to_csv, save_alternatives_to_csv
from hut_allocator.optimizer import Optimizer

def main():
    parser = argparse.ArgumentParser(description='Allocate backcountry hut reservations')
    parser.add_argument('input_csv', help='Input CSV file with reservation requests')
    parser.add_argument('--output', default='output', help='Output directory for results')
    parser.add_argument('--iterations', type=int, default=NUM_ITERATIONS, help='Number of optimization iterations')
    parser.add_argument('--timeout', type=int, default=TIMEOUT_SECONDS, help='Timeout in seconds')

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input_csv):
        print(f"Error: Input file '{args.input_csv}' not found.")
        sys.exit(1)

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    print("="*60)
    print("BACKCOUNTRY HUT RESERVATION ALLOCATOR")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  Huts: {', '.join(f'{name} ({cap})' for name, cap in HUTS.items())}")
    print(f"  Season: {SEASON_START.strftime('%Y-%m-%d')} to {SEASON_END.strftime('%Y-%m-%d')}")
    print(f"  Iterations: {args.iterations}")
    print(f"  Timeout: {args.timeout}s")

    # Load requests
    print(f"\nLoading requests from: {args.input_csv}")
    requests = load_requests_from_csv(args.input_csv)
    print(f"Loaded {len(requests)} requests from {len(set(r.user_name for r in requests))} users")

    # Validate requests
    print("\nValidating requests...")
    valid_requests = []
    for req in requests:
        if req.hut_name not in HUTS:
            print(f"  Warning: Skipping invalid hut '{req.hut_name}' for {req.user_name}")
            continue
        if req.start_date < SEASON_START or req.end_date > SEASON_END:
            print(f"  Warning: Dates outside season for {req.user_name} - {req}")
            continue
        if req.party_size > HUTS[req.hut_name]:
            print(f"  Warning: Party size ({req.party_size}) exceeds hut capacity for {req.user_name}")
            continue
        valid_requests.append(req)

    print(f"Valid requests: {len(valid_requests)}")

    if not valid_requests:
        print("\nNo valid requests to process.")
        sys.exit(1)

    # Run optimization
    optimizer = Optimizer(HUTS, valid_requests, SEASON_START, SEASON_END)
    best_allocation, top_allocations = optimizer.optimize(
        num_iterations=args.iterations,
        timeout=args.timeout
    )

    # Display results
    print(best_allocation.get_summary())

    # Save best allocation
    output_file = os.path.join(args.output, 'allocation_best.csv')
    save_allocation_to_csv(best_allocation, output_file)
    print(f"\nSaved best allocation to: {output_file}")

    # Save top 3 allocations
    for i, alloc in enumerate(top_allocations[:3], 1):
        output_file = os.path.join(args.output, f'allocation_top{i}.csv')
        save_allocation_to_csv(alloc, output_file)
        print(f"Saved top {i} allocation (score: {alloc.score}) to: {output_file}")

    # Generate suggestions for unassigned users
    if best_allocation.unassigned_requests:
        print(f"\nGenerating alternatives for {len(set(r.user_name for r in best_allocation.unassigned_requests))} unassigned users...")
        suggestions = optimizer.suggest_alternatives(best_allocation)
        suggestions_file = os.path.join(args.output, 'alternative_suggestions.csv')
        save_alternatives_to_csv(suggestions, suggestions_file)
        print(f"Saved alternative suggestions to: {suggestions_file}")

    # Statistics
    print("\n" + "="*60)
    print("FINAL STATISTICS")
    print("="*60)
    users = set(req.user_name for req in valid_requests)
    assigned_users = len(set(req.user_name for req in best_allocation.assigned_requests))
    print(f"Users assigned: {assigned_users}/{len(users)} ({100*assigned_users/len(users):.1f}%)")

    pref_counts = {}
    for req in best_allocation.assigned_requests:
        pref_counts[req.preference_rank] = pref_counts.get(req.preference_rank, 0) + 1

    print("\nAssignments by preference:")
    for pref in sorted(pref_counts.keys()):
        print(f"  Preference {pref}: {pref_counts[pref]} users")

    print("\n" + "="*60)
    print("DONE!")
    print("="*60)

if __name__ == '__main__':
    main()
