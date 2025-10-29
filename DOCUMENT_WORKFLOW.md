# Document Processing Workflow

The hut allocator now supports **automatic extraction** from PDF and Word documents! This eliminates manual CSV creation.

## Quick Start

### One-Command Workflow

Process documents and run allocation in one step:

```bash
python3 process_reservations.py ~/path/to/forms --output results/
```

### Step-by-Step Workflow

If you prefer more control:

```bash
# 1. Convert documents to CSV
python3 convert_documents.py ~/path/to/forms --output requests.csv

# 2. Clean the data
python3 clean_extracted_data.py requests.csv --output cleaned.csv

# 3. Run allocation
python3 main.py cleaned.csv --output results/
```

## Supported Formats

- **.docx** (Word documents) ✅
- **.pdf** (PDF forms) ✅
- **.pages** (Pages documents) ❌ (convert to PDF first)

## Form Template

The system expects forms with this structure:

### Leader Contact Information
- Leader Name
- Email
- Phone

### Hut Preferences (1-5)
Each preference should have:
- Hut Name (Bradley, Benson, Peter Grubb, or Ludlow)
- Date In (check-in date)
- Date Out (check-out date)
- Number of Guests (number or "ENTIRE")

## Parsing Methods

### Python Parser (Default, Fast, Free)
- Extracts structured data from well-formatted documents
- Works best with Word documents (.docx)
- May struggle with:
  - Scanned/handwritten forms
  - Complex PDF form fields
  - Unusual formatting

### AI Parser (Hybrid Fallback, Flexible, Requires API Key)
- Uses Claude AI to understand complex/handwritten forms
- Automatically used when Python parser fails
- Requires ANTHROPIC_API_KEY environment variable

## Usage Examples

### Basic Usage (Python Parser Only)

```bash
python3 process_reservations.py ~/Desktop/jan-hut --output results/ --no-ai
```

### Hybrid Mode (Python + AI Fallback)

Set your API key first:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Then run:
```bash
python3 process_reservations.py ~/Desktop/jan-hut --output results/
```

### Force AI for All Documents

```bash
python3 process_reservations.py ~/Desktop/jan-hut --use-ai --api-key YOUR_KEY
```

## Understanding the Output

The workflow creates these files:

```
results/
├── converted_requests.csv      # Raw extracted data from documents
├── cleaned_requests.csv        # Cleaned and validated data
└── allocation/
    ├── allocation_best.csv            # Best allocation found
    ├── allocation_top1.csv            # Alternative allocation #1
    ├── allocation_top2.csv            # Alternative allocation #2
    ├── allocation_top3.csv            # Alternative allocation #3
    └── alternative_suggestions.csv    # Suggestions for unassigned users
```

### converted_requests.csv
Direct extraction from forms - may contain formatting issues.

### cleaned_requests.csv
Validated data ready for allocation. Invalid rows are flagged.

### allocation_best.csv
Final assignments showing which users got which reservations.

### alternative_suggestions.csv
Alternative dates/huts for users who didn't get any of their choices.

## Data Cleaning

The cleaner handles:

✅ **Date normalization**: "Jan 12 2026" → "2026-01-12"
✅ **Hut name standardization**: "Grubb" → "Peter Grubb"
✅ **Party size conversion**: "ENTIRE" → hut capacity
✅ **Validation**: Flags incomplete or invalid data

### Invalid Data Examples

Will be flagged for manual review:
- ❌ Traverse requests: "Bradley to Benson traverse"
- ❌ Multiple hut options: "Benson OR Grubb OR Bradley"
- ❌ Unparseable dates: "flexible dates in March"
- ❌ Missing required fields

## Troubleshooting

### Problem: "No data extracted"

**For PDFs:**
- PDFs might be scanned images → Use `--use-ai`
- PDF might have form fields that aren't filled → Check the PDF

**For DOCX:**
- File might be corrupted → Try opening in Word
- Format might not match expected template

### Problem: "Many invalid rows"

Run the cleaner separately to see details:
```bash
python3 clean_extracted_data.py converted.csv --output cleaned.csv
```

Review the console output for specific issues.

### Problem: "AI parsing failed"

Check:
1. API key is set correctly
2. You have API credits
3. File isn't corrupted

## Advanced Options

### process_reservations.py Options

```bash
--output DIR          Output folder (default: final_results)
--use-ai              Force AI parsing for all documents
--no-ai               Never use AI (Python only)
--api-key KEY         Anthropic API key
--iterations N        Allocation iterations (default: 20)
--keep-temp           Keep intermediate files
```

### convert_documents.py Options

```bash
--output FILE         Output CSV file
--use-ai              Force AI for all
--no-ai               Python only
--api-key KEY         API key
```

### clean_extracted_data.py Options

```bash
--output FILE         Output CSV file
--include-invalid     Include invalid rows with notes
```

## Tips for Best Results

1. **Use Word documents when possible** - They parse more reliably than PDFs
2. **Encourage typed forms** - Handwritten forms need AI parsing
3. **Standardize hut names** - Use exact names: Bradley, Benson, Peter Grubb, Ludlow
4. **Use consistent date formats** - "MM/DD/YYYY" or "Month DD, YYYY"
5. **Review invalid rows** - Some requests may need manual CSV entry

## Getting an API Key

To use AI parsing:

1. Go to https://console.anthropic.com/
2. Sign up for an account
3. Navigate to API Keys
4. Create a new key
5. Set it as environment variable:
   ```bash
   export ANTHROPIC_API_KEY="your-key-here"
   ```

Or pass it directly:
```bash
python3 process_reservations.py ~/forms --api-key YOUR_KEY
```

## Example Workflow

```bash
# Set API key (optional, for AI fallback)
export ANTHROPIC_API_KEY="your-key-here"

# Process all reservation forms in one command
python3 process_reservations.py ~/Desktop/jan-hut --output jan_allocation --iterations 30

# Review results
cat jan_allocation/allocation/allocation_best.csv

# Check who didn't get assigned
cat jan_allocation/allocation/alternative_suggestions.csv

# If needed, manually handle invalid rows
# (they'll be listed in the console output)
```

## Migration from CSV-Only Workflow

Old workflow:
```bash
# Manually create CSV, then:
python3 main.py requests.csv
```

New workflow:
```bash
# Automatically extract from documents:
python3 process_reservations.py ~/forms
```

Both workflows still work! The CSV workflow remains fully supported.
