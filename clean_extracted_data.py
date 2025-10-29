#!/usr/bin/env python3
"""
Clean extracted CSV data to prepare for allocation.

Handles:
- Date format normalization
- Hut name standardization
- Invalid data filtering
- Party size conversion

Usage:
    python3 clean_extracted_data.py input.csv --output cleaned.csv
"""

import argparse
import csv
import re
from datetime import datetime

# Valid hut names
VALID_HUTS = ['Bradley', 'Benson', 'Peter Grubb', 'Ludlow']

def parse_traverse_request(row):
    """
    Parse a traverse request and split into two separate reservations.
    Returns list of 2 row dicts, or None if can't parse.

    Example input:
    Hut: "Bradley to Benson traverse"
    StartDate: "In to Bradley 3/20 In to Benson 3/22"
    EndDate: "Out of Bradley 3/22 Out of Benson 3/23"

    Returns:
    [
        {Bradley: 3/20-3/22},
        {Benson: 3/22-3/23}
    ]
    """
    hut_str = row['Hut'].lower()

    # Parse hut names from "Bradley to Benson traverse"
    match = re.search(r'(\w+)\s+to\s+(\w+)', hut_str)
    if not match:
        return None

    hut1_name = match.group(1).capitalize()
    hut2_name = match.group(2).capitalize()

    # Parse dates from "In to Bradley 3/20 In to Benson 3/22"
    start_str = row['StartDate']
    end_str = row['EndDate']

    # Extract dates using regex
    all_dates = re.findall(r'\d{1,2}/\d{1,2}', start_str + ' ' + end_str)

    # Remove duplicates while preserving order
    dates = []
    seen = set()
    for d in all_dates:
        if d not in seen:
            dates.append(d)
            seen.add(d)

    if len(dates) < 3:
        return None

    # dates[0] = into hut1, dates[1] = into hut2 (out of hut1), dates[2] = out of hut2
    year = "2026"  # Assume 2026
    date1 = f"{dates[0]}/{year}"  # Into first hut
    date2 = f"{dates[1]}/{year}"  # Into second hut (out of first)
    date3 = f"{dates[2]}/{year}"  # Out of second hut

    rows = []

    # First hut reservation
    rows.append({
        'UserName': row['UserName'],
        'PreferenceRank': row['PreferenceRank'],
        'Hut': hut1_name,
        'StartDate': date1,
        'EndDate': date2,
        'PartySize': row['PartySize']
    })

    # Second hut reservation
    rows.append({
        'UserName': row['UserName'],
        'PreferenceRank': row['PreferenceRank'],
        'Hut': hut2_name,
        'StartDate': date2,
        'EndDate': date3,
        'PartySize': row['PartySize']
    })

    return rows

def normalize_hut_name(hut_str):
    """
    Extract and normalize hut name.
    Returns (hut_name, is_valid, notes)
    """
    hut_str = hut_str.strip()

    # Check for traverse requests - will be handled separately
    if 'traverse' in hut_str.lower():
        return (hut_str, False, "Traverse request - will be split")

    # Check for "OR" multiple huts
    if ' OR ' in hut_str:
        # Extract first hut mentioned
        parts = hut_str.split(' OR ')
        for part in parts:
            for valid_hut in VALID_HUTS:
                if valid_hut.lower() in part.lower():
                    return (valid_hut, True, f"Multiple options: {hut_str}")
        return (hut_str, False, "Multiple huts specified")

    # Match against valid huts (case-insensitive, partial match)
    for valid_hut in VALID_HUTS:
        if valid_hut.lower() in hut_str.lower():
            return (valid_hut, True, None)

    # Check for common variations
    if 'grubb' in hut_str.lower():
        return ('Peter Grubb', True, "Matched 'Grubb'")

    return (hut_str, False, "Unknown hut name")

def normalize_date(date_str):
    """
    Parse various date formats and return YYYY-MM-DD.
    Returns (normalized_date, is_valid, error)
    """
    date_str = date_str.strip()

    # Strip parenthetical notes (e.g., "(could shift forward or back 1 day)")
    date_str = re.sub(r'\s*\([^)]*\)\s*', ' ', date_str).strip()

    # Already in correct format
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return (date_str, True, None)

    # Try various formats
    formats = [
        '%m/%d/%Y',
        '%m-%d-%Y',
        '%m/%d/%y',
        '%B %d, %Y',
        '%b %d, %Y',
        '%B %d %Y',
        '%b %d %Y',
        '%d %B %Y',
        '%d %b %Y',
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return (dt.strftime('%Y-%m-%d'), True, None)
        except:
            continue

    # Try more flexible parsing
    # "Jan 21 2026" or "March 1 2026"
    match = re.match(r'(\w+)\s+(\d+)\s+(\d{4})', date_str)
    if match:
        month_str, day, year = match.groups()
        # Try abbreviated month first
        try:
            dt = datetime.strptime(f"{month_str} {day} {year}", '%b %d %Y')
            return (dt.strftime('%Y-%m-%d'), True, None)
        except:
            pass
        # Try full month name
        try:
            dt = datetime.strptime(f"{month_str} {day} {year}", '%B %d %Y')
            return (dt.strftime('%Y-%m-%d'), True, None)
        except:
            pass

    return (date_str, False, "Unable to parse date")

def normalize_party_size(size_str):
    """
    Convert party size to integer or 'ENTIRE'.
    Returns (party_size, is_valid, error)
    """
    size_str = str(size_str).strip().upper()

    if size_str == 'ENTIRE':
        return ('ENTIRE', True, None)

    # Extract number
    match = re.search(r'\d+', size_str)
    if match:
        size = int(match.group())
        if size > 0:
            return (size, True, None)
        else:
            return (size_str, False, "Party size must be positive")

    return (size_str, False, "Cannot parse party size")

def clean_csv(input_file, output_file, include_invalid=False):
    """
    Clean and validate CSV data.

    Args:
        input_file: Input CSV path
        output_file: Output CSV path
        include_invalid: If True, include invalid rows with notes
    """
    with open(input_file, 'r') as fin:
        reader = csv.DictReader(fin)
        rows = list(reader)

    cleaned_rows = []
    invalid_rows = []
    issues = []

    for i, row in enumerate(rows, start=2):  # Start at 2 (line 1 is header)
        # Check if this is a traverse request that should be split
        if 'traverse' in row['Hut'].lower():
            traverse_rows = parse_traverse_request(row)
            if traverse_rows:
                # Process each part of the traverse separately
                for traverse_row in traverse_rows:
                    rows.append(traverse_row)
                print(f"  Split traverse request for {row['UserName']} into 2 reservations")
                continue  # Skip normal processing for this row

        cleaned = {}
        is_valid = True
        row_issues = []

        # Clean UserName
        cleaned['UserName'] = row['UserName'].strip()

        # Clean PreferenceRank
        try:
            cleaned['PreferenceRank'] = int(row['PreferenceRank'])
        except:
            row_issues.append(f"Invalid preference rank: {row['PreferenceRank']}")
            is_valid = False

        # Clean Hut
        hut, hut_valid, hut_note = normalize_hut_name(row['Hut'])
        cleaned['Hut'] = hut
        if not hut_valid:
            row_issues.append(hut_note or f"Invalid hut: {row['Hut']}")
            is_valid = False
        elif hut_note:
            row_issues.append(hut_note)

        # Clean StartDate
        start_date, start_valid, start_err = normalize_date(row['StartDate'])
        cleaned['StartDate'] = start_date
        if not start_valid:
            row_issues.append(f"Invalid start date: {row['StartDate']} - {start_err}")
            is_valid = False

        # Clean EndDate
        end_date, end_valid, end_err = normalize_date(row['EndDate'])
        cleaned['EndDate'] = end_date
        if not end_valid:
            row_issues.append(f"Invalid end date: {row['EndDate']} - {end_err}")
            is_valid = False

        # Clean PartySize
        party_size, size_valid, size_err = normalize_party_size(row['PartySize'])
        cleaned['PartySize'] = party_size
        if not size_valid:
            row_issues.append(f"Invalid party size: {row['PartySize']} - {size_err}")
            is_valid = False

        # Store results
        if is_valid:
            cleaned_rows.append(cleaned)
        else:
            invalid_rows.append({
                'line': i,
                'user': row['UserName'],
                'issues': '; '.join(row_issues),
                'original': row
            })
            if include_invalid:
                cleaned['_INVALID'] = '; '.join(row_issues)
                cleaned_rows.append(cleaned)

    # Write cleaned data
    if cleaned_rows:
        fieldnames = ['UserName', 'PreferenceRank', 'Hut', 'StartDate', 'EndDate', 'PartySize']
        if include_invalid:
            fieldnames.append('_INVALID')

        with open(output_file, 'w', newline='') as fout:
            writer = csv.DictWriter(fout, fieldnames=fieldnames)
            writer.writeheader()
            for row in cleaned_rows:
                writer.writerow(row)

    # Report results
    print(f"\n{'='*60}")
    print(f"DATA CLEANING COMPLETE")
    print(f"{'='*60}")
    print(f"Total rows processed: {len(rows)}")
    print(f"Valid rows: {len(cleaned_rows) - len(invalid_rows)}")
    print(f"Invalid rows: {len(invalid_rows)}")

    if invalid_rows:
        print(f"\n⚠ INVALID ROWS (need manual review):")
        for inv in invalid_rows:
            print(f"\nLine {inv['line']} - {inv['user']}")
            print(f"  Issues: {inv['issues']}")
            print(f"  Original: {inv['original']}")

    print(f"\nCleaned data saved to: {output_file}")

    return len(cleaned_rows), len(invalid_rows)

def main():
    parser = argparse.ArgumentParser(description='Clean extracted CSV data')
    parser.add_argument('input_csv', help='Input CSV file to clean')
    parser.add_argument('--output', default='cleaned_requests.csv', help='Output CSV file')
    parser.add_argument('--include-invalid', action='store_true', help='Include invalid rows with notes')

    args = parser.parse_args()

    clean_csv(args.input_csv, args.output, args.include_invalid)

if __name__ == '__main__':
    main()
