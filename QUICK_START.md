# Quick Start Guide

## 1. Generate Sample Data

```bash
python3 generate_sample_data.py
```

This creates `sample_data/requests.csv` with 15 sample users.

## 2. Run the Allocator

```bash
python3 main.py sample_data/requests.csv
```

Results will be in the `output/` directory.

## 3. Review Results

```bash
# View best allocation
cat output/allocation_best.csv

# View alternative suggestions (if any users were unassigned)
cat output/alternative_suggestions.csv
```

## Creating Your Own Request File

Create a CSV file with these columns:

```csv
UserName,PreferenceRank,Hut,StartDate,EndDate,PartySize
John Smith,1,Bradley,2026-02-12,2026-02-14,4
John Smith,2,Benson,2026-02-15,2026-02-17,4
John Smith,3,Peter Grubb,2026-02-12,2026-02-14,4
John Smith,4,Ludlow,2026-02-20,2026-02-22,4
John Smith,5,Bradley,2026-03-01,2026-03-03,4
```

## Available Huts

- **Bradley**: 15 people capacity
- **Benson**: 12 people capacity
- **Peter Grubb**: 15 people capacity
- **Ludlow**: 15 people capacity

## Season

December 1, 2025 - May 31, 2026

## Tips

1. Each user can submit up to 5 preferences (ranked 1-5)
2. Each preference can be for different huts, dates, and even party sizes
3. The system tries to maximize overall satisfaction by assigning higher preferences when possible
4. Multiple groups can share a hut on the same night (up to capacity)

## Customization

Edit `hut_allocator/config.py` to change:
- Hut names and capacities
- Season dates
- Scoring weights for preferences
- Optimization parameters

## Advanced Usage

```bash
# More iterations for better results
python3 main.py requests.csv --iterations 30

# Custom output directory
python3 main.py requests.csv --output my_results/

# Longer timeout
python3 main.py requests.csv --timeout 600
```

## Troubleshooting

**Problem**: Many unassigned users
**Solution**: Too much demand for limited capacity. Try:
- Encouraging users to spread out their date preferences
- Reducing party sizes
- Increasing optimization iterations: `--iterations 50`

**Problem**: Invalid hut name errors
**Solution**: Hut names must exactly match (case-sensitive):
- Bradley
- Benson
- Peter Grubb
- Ludlow

**Problem**: Date out of range
**Solution**: All dates must be between Dec 1, 2025 and May 31, 2026
