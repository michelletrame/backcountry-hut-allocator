#!/usr/bin/env python3
"""
Complete Reservation Processing Workflow

This script handles the entire workflow from documents to final allocation:
1. Convert PDF/DOCX forms to CSV
2. Clean and validate the data
3. Run allocation optimization
4. Generate results and alternatives

Usage:
    python3 process_reservations.py <docs_folder> [options]

Example:
    python3 process_reservations.py ~/Desktop/jan-hut --output results/
    python3 process_reservations.py ~/Desktop/jan-hut --use-ai --api-key YOUR_KEY
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode != 0:
        print(f"\n✗ Error: {description} failed")
        return False

    return True

def main():
    parser = argparse.ArgumentParser(description='Complete reservation processing workflow')
    parser.add_argument('docs_folder', help='Folder containing PDF/DOCX reservation forms')
    parser.add_argument('--output', default='final_results', help='Output folder for results')
    parser.add_argument('--use-ai', action='store_true', help='Force AI parsing for all documents')
    parser.add_argument('--no-ai', action='store_true', help='Never use AI parsing')
    parser.add_argument('--api-key', help='Anthropic API key for AI parsing')
    parser.add_argument('--iterations', type=int, default=20, help='Allocation iterations')
    parser.add_argument('--keep-temp', action='store_true', help='Keep temporary files')

    args = parser.parse_args()

    # Verify docs folder exists
    if not os.path.exists(args.docs_folder):
        print(f"Error: Documents folder '{args.docs_folder}' not found")
        sys.exit(1)

    # Create output folder
    os.makedirs(args.output, exist_ok=True)

    # Step 1: Convert documents to CSV
    print("\n" + "="*60)
    print("STEP 1: CONVERTING DOCUMENTS TO CSV")
    print("="*60)

    converted_csv = os.path.join(args.output, 'converted_requests.csv')
    convert_cmd = ['python3', 'convert_documents.py', args.docs_folder, '--output', converted_csv]

    if args.use_ai:
        convert_cmd.append('--use-ai')
    if args.no_ai:
        convert_cmd.append('--no-ai')
    if args.api_key:
        convert_cmd.extend(['--api-key', args.api_key])

    if not run_command(convert_cmd, "Document conversion"):
        sys.exit(1)

    # Step 2: Clean data
    print("\n" + "="*60)
    print("STEP 2: CLEANING AND VALIDATING DATA")
    print("="*60)

    cleaned_csv = os.path.join(args.output, 'cleaned_requests.csv')
    clean_cmd = ['python3', 'clean_extracted_data.py', converted_csv, '--output', cleaned_csv]

    if not run_command(clean_cmd, "Data cleaning"):
        sys.exit(1)

    # Step 3: Run allocation
    print("\n" + "="*60)
    print("STEP 3: RUNNING ALLOCATION OPTIMIZATION")
    print("="*60)

    allocation_folder = os.path.join(args.output, 'allocation')
    allocate_cmd = [
        'python3', 'main.py', cleaned_csv,
        '--output', allocation_folder,
        '--iterations', str(args.iterations)
    ]

    if not run_command(allocate_cmd, "Allocation optimization"):
        sys.exit(1)

    # Summary
    print("\n" + "="*60)
    print("🎉 WORKFLOW COMPLETE!")
    print("="*60)
    print(f"\nResults saved to: {args.output}/")
    print(f"\nFiles created:")
    print(f"  1. {converted_csv} - Raw extracted data")
    print(f"  2. {cleaned_csv} - Cleaned and validated data")
    print(f"  3. {allocation_folder}/allocation_best.csv - Best allocation")
    print(f"  4. {allocation_folder}/alternative_suggestions.csv - Alternatives for unassigned")

    print(f"\nNext steps:")
    print(f"  1. Review: cat {allocation_folder}/allocation_best.csv")
    print(f"  2. Check alternatives: cat {allocation_folder}/alternative_suggestions.csv")
    print(f"  3. Manual handling may be needed for invalid requests in {converted_csv}")

    # Cleanup temp files if requested
    if not args.keep_temp:
        print(f"\n(Tip: Use --keep-temp to preserve intermediate files)")

if __name__ == '__main__':
    main()
