# Backcountry Hut Reservation Allocator

An optimization system for allocating backcountry hut reservations based on user preferences, date availability, and capacity constraints.

## Overview

This tool solves the problem of fairly distributing limited backcountry hut reservations among multiple users who have submitted ranked preferences. It uses iterative optimization algorithms to maximize overall satisfaction while respecting capacity constraints.

## Features

- **Document Processing**: Automatically extract reservation data from PDF and Word documents
- **Ranked Preferences**: Users submit up to 5 reservation requests, ranked by preference (1 = most preferred)
- **Multi-Night Stays**: Supports variable-length reservations (1-N nights)
- **Shared Capacity**: Multiple groups can share a hut on the same night (up to capacity)
- **Optimization Algorithm**: Uses multi-start local search to find optimal allocations
- **Alternative Suggestions**: Automatically suggests alternatives for unassigned users
- **Hybrid Parsing**: Python parsers for speed + AI fallback for complex cases
- **CSV Input/Output**: Easy-to-use CSV format for requests and results

## System Configuration

### Huts (can be modified in `hut_allocator/config.py`)
- **Bradley**: 15 people
- **Benson**: 12 people
- **Peter Grubb**: 15 people
- **Ludlow**: 15 people

### Season
December 1, 2025 - May 31, 2026

### Scoring
- Preference 1: 100 points
- Preference 2: 50 points
- Preference 3: 25 points
- Preference 4: 10 points
- Preference 5: 5 points

The optimizer tries to maximize total points across all users.

## Installation

```bash
# Clone or download this repository
cd backcountry-hut-allocator

# Install required libraries for document processing
pip3 install pdfplumber python-docx anthropic
```

**Note**: If you only need CSV input (no document processing), no external dependencies are required.

## Quick Start

### Option 1: Process Documents Directly (NEW!)

Convert PDF/Word reservation forms to allocations in one command:

```bash
python3 process_reservations.py ~/path/to/forms --output results/
```

See [DOCUMENT_WORKFLOW.md](DOCUMENT_WORKFLOW.md) for detailed documentation.

### Option 2: Use CSV Input (Original Method)

## Input Format

Create a CSV file with the following columns:

```csv
UserName,PreferenceRank,Hut,StartDate,EndDate,PartySize
John Smith,1,Bradley,2026-02-12,2026-02-14,4
John Smith,2,Benson,2026-02-15,2026-02-17,4
John Smith,3,Peter Grubb,2026-02-12,2026-02-14,4
Jane Doe,1,Ludlow,2026-02-12,2026-02-15,6
Jane Doe,2,Bradley,2026-02-20,2026-02-22,6
```

### Column Descriptions
- **UserName**: Name of the person/group requesting
- **PreferenceRank**: 1-5, where 1 is most preferred
- **Hut**: Must match one of the configured hut names
- **StartDate**: Check-in date (YYYY-MM-DD)
- **EndDate**: Check-out date (YYYY-MM-DD) - exclusive
- **PartySize**: Number of people in the group

### Important Notes
- Each user can submit up to 5 requests (one for each preference rank 1-5)
- Dates must fall within the season
- Party size cannot exceed hut capacity
- EndDate is exclusive (e.g., 2026-02-12 to 2026-02-14 is 2 nights)

## Usage

### Basic Usage

```bash
python main.py sample_data/requests.csv
```

### With Custom Output Directory

```bash
python main.py sample_data/requests.csv --output results/
```

### With Custom Parameters

```bash
python main.py sample_data/requests.csv --iterations 30 --timeout 600
```

### Command-Line Options

- `input_csv`: Path to input CSV file (required)
- `--output DIR`: Output directory for results (default: `output/`)
- `--iterations N`: Number of optimization iterations (default: 20)
- `--timeout N`: Timeout in seconds (default: 300)

## Output Files

The tool generates several output files:

### 1. `allocation_best.csv`
The best allocation found, showing which users got which reservations:

```csv
UserName,PreferenceRank,Hut,StartDate,EndDate,PartySize,Status
John Smith,1,Bradley,2026-02-12,2026-02-14,4,ASSIGNED (Preference 1)
Jane Doe,2,Bradley,2026-02-20,2026-02-22,6,ASSIGNED (Preference 2)
Bob Jones,1,Benson,2026-02-12,2026-02-15,3,UNASSIGNED
```

### 2. `allocation_top1.csv`, `allocation_top2.csv`, `allocation_top3.csv`
The top 3 alternative allocations (in case you want to review other options)

### 3. `alternative_suggestions.csv`
Alternative hut/date suggestions for users who didn't get any of their choices:

```csv
UserName,AlternativeHut,Dates,PartySize,Note
Bob Jones,Ludlow,2026-02-12 to 2026-02-15,3,Different hut, same dates
```

## How It Works

### Algorithm Overview

1. **Initialization**: Generate multiple starting solutions using greedy (preference-first) and random assignments
2. **Local Search**: For each solution, iteratively try swapping assignments to improve the total score
3. **Multi-Start**: Run multiple iterations to avoid getting stuck in local optima
4. **Selection**: Return the best solution found

### Optimization Strategy

The optimizer uses two main strategies:
1. **Swap unassigned with assigned**: Try to fit unassigned high-preference requests by swapping with assigned lower-preference requests
2. **Preference improvement**: Try to improve users' preference ranks by beneficial swaps

### Constraints

- Hut capacity cannot be exceeded on any night
- Each user gets at most one assignment (their highest-preference available choice)
- Reservations must fall within the defined season

## Generating Sample Data

To generate sample data for testing:

```python
from hut_allocator.csv_handler import generate_sample_csv

generate_sample_csv('sample_data/requests.csv', num_users=20)
```

Or run the provided script:

```bash
python generate_sample_data.py
```

## Customization

### Modifying Huts or Season

Edit `hut_allocator/config.py`:

```python
HUTS = {
    "Bradley": 15,
    "Benson": 12,
    "Peter Grubb": 15,
    "Ludlow": 15
}

SEASON_START = datetime(2025, 12, 1)
SEASON_END = datetime(2026, 5, 31)
```

### Adjusting Scoring

Modify `PREFERENCE_SCORES` in `hut_allocator/config.py`:

```python
PREFERENCE_SCORES = {
    1: 100,  # First choice
    2: 50,   # Second choice
    3: 25,   # Third choice
    4: 10,   # Fourth choice
    5: 5     # Fifth choice
}
```

### Tuning Optimization

Adjust parameters in `hut_allocator/config.py`:

```python
NUM_ITERATIONS = 20           # More iterations = better results, slower
TIMEOUT_SECONDS = 300         # Total time budget
NUM_SWAP_ATTEMPTS = 50        # Swaps to try per iteration
```

## Tips for Best Results

1. **More iterations**: Increase `--iterations` for better results (20-50 works well)
2. **Longer timeout**: Give more time for complex allocations
3. **Realistic requests**: Users should submit feasible alternatives across different dates
4. **Spread demand**: Encourage users to choose different date ranges in their preferences

## Example Workflow

```bash
# 1. Generate sample data (or prepare your own CSV)
python generate_sample_data.py

# 2. Run allocation
python main.py sample_data/requests.csv --output results/ --iterations 30

# 3. Review results
cat results/allocation_best.csv

# 4. Check alternatives for unassigned users
cat results/alternative_suggestions.csv
```

## Troubleshooting

**Issue**: "No valid requests to process"
- Check that hut names match configuration exactly (case-sensitive)
- Verify dates are within season range
- Ensure party sizes don't exceed hut capacities

**Issue**: Many users unassigned
- Reduce party sizes or increase iterations
- Check if there's too much demand for specific dates/huts
- Review alternative suggestions for available options

**Issue**: Low scores
- The optimization is working but demand exceeds capacity
- Consider expanding season, adding huts, or reducing party sizes

## License

Open source - feel free to modify and use for your hut allocation needs!
