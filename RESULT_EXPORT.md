# Query Results Organization

## New Folder Structure

Each query now gets its own dedicated folder with all related files organized together!

### Folder Naming

```
artifacts/
  └── query_20260129_104530/
      ├── result.md       # Formatted report with HTML table
      ├── result.csv      # Full data in CSV format
      └── chart.png       # Visualization (if generated)
```

**Folder Name Format:** `query_YYYYMMDD_HHMMSS`
- Example: `query_20260129_104530` = Query run on Jan 29, 2026 at 10:45:30

## What's in Each Folder?

### 📄 result.md
- User's original question
- SQL query that was executed
- Beautiful HTML table with:
  - Dark blue header
  - Alternating row colors
  - Clean borders
  - Proper formatting
- Collapsible plain markdown table

### 📊 result.csv
- Complete data without truncation
- All rows and columns
- Excel-compatible (UTF-8 with BOM)
- Perfect for further analysis

### 📈 chart.png
- Auto-generated visualization
- Only created if data is suitable for charting
- Line, bar, or scatter plot based on data type

## Benefits

✅ **Organized** - All files for one query in one place
✅ **Easy to Find** - Timestamped folder names
✅ **Clean** - No clutter in artifacts root
✅ **Complete** - Everything you need in one folder
✅ **Shareable** - Copy entire folder to share results

## Example Output

When you run a query, you'll see:

```
💾 Results saved to folder: query_20260129_104530/
   📄 result.md  - Formatted report
   📊 result.csv - Full data
   📈 chart.png  - Visualization
```

## Usage

No action needed! The new structure is automatic.

**To access your results:**
1. Navigate to `artifacts/`
2. Find the folder with your query timestamp
3. Open `result.md` for formatted view
4. Open `result.csv` in Excel for analysis
5. View `chart.png` for visualization
