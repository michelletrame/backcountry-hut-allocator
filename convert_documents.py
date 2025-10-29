#!/usr/bin/env python3
"""
Document to CSV Converter

Converts PDF and DOCX reservation request forms to CSV format.
Uses hybrid approach: Python parsers first, AI fallback for complex cases.

Usage:
    python3 convert_documents.py <input_folder> --output <output.csv>
    python3 convert_documents.py ~/Desktop/"hut docs" --output requests.csv

Options:
    --output: Output CSV file path (default: converted_requests.csv)
    --use-ai: Force AI parsing for all documents
    --no-ai: Never use AI parsing, Python only
    --api-key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
"""

import os
import sys
import argparse
import csv
from pathlib import Path

from hut_allocator.pdf_parser import PDFParser
from hut_allocator.docx_parser import DOCXParser
from hut_allocator.ai_parser import AIParser

def should_use_ai_fallback(parsed_data):
    """
    Determine if we should fall back to AI parsing.
    Returns True if data is incomplete or suspicious.
    """
    # Check if leader name is missing
    if not parsed_data.get('leader_name'):
        return True

    # Check if no preferences were found
    if not parsed_data.get('preferences'):
        return True

    # Check if preferences are incomplete
    for pref in parsed_data.get('preferences', []):
        required = ['preference_rank', 'hut_name', 'date_in', 'date_out', 'party_size']
        if not all(key in pref for key in required):
            return True

    return False

def parse_document(file_path, use_ai=False, force_python=False, api_key=None):
    """
    Parse a single document using hybrid approach.

    Args:
        file_path: Path to PDF or DOCX file
        use_ai: If True, use AI parser directly
        force_python: If True, never use AI fallback
        api_key: Anthropic API key for AI parsing

    Returns:
        List of CSV row dictionaries
    """
    file_ext = file_path.lower().split('.')[-1]
    filename = os.path.basename(file_path)

    print(f"\n{'='*60}")
    print(f"Processing: {filename}")
    print(f"{'='*60}")

    rows = []

    # Use AI parser directly if requested
    if use_ai:
        print("Method: AI Parser (forced)")
        try:
            parser = AIParser(file_path, api_key=api_key)
            rows = parser.to_csv_rows()
            print(f"✓ Successfully extracted {len(rows)} requests")
            return rows
        except Exception as e:
            print(f"✗ AI parsing failed: {e}")
            return []

    # Try Python parser first
    try:
        if file_ext == 'pdf':
            print("Method: Python PDF Parser")
            parser = PDFParser(file_path)
        elif file_ext in ['docx', 'doc']:
            print("Method: Python DOCX Parser")
            parser = DOCXParser(file_path)
        else:
            print(f"✗ Unsupported file type: {file_ext}")
            return []

        data = parser.parse()
        rows = parser.to_csv_rows()

        print(f"Leader: {data.get('leader_name', 'Not found')}")
        print(f"Email: {data.get('email', 'Not found')}")
        print(f"Preferences extracted: {len(data.get('preferences', []))}")

        # Check if we should use AI fallback
        if should_use_ai_fallback(data) and not force_python:
            print("\n⚠ Data incomplete or unclear. Trying AI fallback...")
            try:
                ai_parser = AIParser(file_path, api_key=api_key)
                ai_rows = ai_parser.to_csv_rows()
                if len(ai_rows) > len(rows):
                    print(f"✓ AI extracted more complete data ({len(ai_rows)} requests)")
                    return ai_rows
                else:
                    print(f"→ Using Python parser results ({len(rows)} requests)")
            except Exception as e:
                print(f"✗ AI fallback failed: {e}")
                print(f"→ Using Python parser results ({len(rows)} requests)")

        else:
            print(f"✓ Successfully extracted {len(rows)} requests")

    except Exception as e:
        print(f"✗ Python parsing failed: {e}")

        # Try AI fallback if not disabled
        if not force_python:
            print("\nTrying AI fallback...")
            try:
                parser = AIParser(file_path, api_key=api_key)
                rows = parser.to_csv_rows()
                print(f"✓ AI extracted {len(rows)} requests")
            except Exception as e2:
                print(f"✗ AI fallback also failed: {e2}")

    return rows

def convert_folder(input_folder, output_csv, use_ai=False, force_python=False, api_key=None):
    """
    Convert all PDF and DOCX files in a folder to CSV.

    Args:
        input_folder: Path to folder containing documents
        output_csv: Output CSV file path
        use_ai: Force AI parsing for all documents
        force_python: Never use AI fallback
        api_key: Anthropic API key
    """
    input_path = Path(input_folder)

    if not input_path.exists():
        print(f"Error: Folder '{input_folder}' not found.")
        sys.exit(1)

    # Find all PDF and DOCX files
    files = []
    for ext in ['*.pdf', '*.docx', '*.doc']:
        files.extend(input_path.glob(ext))

    if not files:
        print(f"No PDF or DOCX files found in '{input_folder}'")
        sys.exit(1)

    print(f"\nFound {len(files)} document(s) to process:")
    for f in files:
        print(f"  - {f.name}")

    # Process each file
    all_rows = []
    successful = 0
    failed = 0

    for file_path in files:
        try:
            rows = parse_document(str(file_path), use_ai, force_python, api_key)
            if rows:
                all_rows.extend(rows)
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Error processing {file_path.name}: {e}")
            failed += 1

    # Write to CSV
    if all_rows:
        with open(output_csv, 'w', newline='') as f:
            fieldnames = ['UserName', 'PreferenceRank', 'Hut', 'StartDate', 'EndDate', 'PartySize', 'Sanctioned']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"\n{'='*60}")
        print(f"CONVERSION COMPLETE")
        print(f"{'='*60}")
        print(f"Files processed: {len(files)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"Total requests extracted: {len(all_rows)}")
        print(f"\nOutput saved to: {output_csv}")
    else:
        print(f"\n✗ No data extracted from any documents.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Convert reservation request forms to CSV')
    parser.add_argument('input_folder', help='Folder containing PDF/DOCX files')
    parser.add_argument('--output', default='converted_requests.csv', help='Output CSV file')
    parser.add_argument('--use-ai', action='store_true', help='Force AI parsing for all documents')
    parser.add_argument('--no-ai', action='store_true', help='Never use AI parsing, Python only')
    parser.add_argument('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY)')

    args = parser.parse_args()

    if args.use_ai and args.no_ai:
        print("Error: Cannot use both --use-ai and --no-ai")
        sys.exit(1)

    convert_folder(
        args.input_folder,
        args.output,
        use_ai=args.use_ai,
        force_python=args.no_ai,
        api_key=args.api_key
    )

if __name__ == '__main__':
    main()
