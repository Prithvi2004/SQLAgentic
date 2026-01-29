# SQL Agent - User Guide

## 🚀 Quick Start

Simply type your questions in natural language, and the agent will:
1. Generate SQL automatically
2. Execute the query
3. Display results with insights
4. Save everything to a folder
5. Suggest follow-up questions

---

## 📖 Command Usage Guide

### 1. ASKING QUESTIONS (Natural Language)

Just type your question naturally:

```
❓ Ask a question: show me the latest 20 shipments

❓ Ask a question: what is the total weight by client?

❓ Ask a question: find shipments from last week

❓ Ask a question: count shipments by status
```

**The agent will:**
- Generate SQL automatically
- Execute the query
- Show results in a table
- Display data insights
- Save to `artifacts/query_YYYYMMDD_HHMMSS/`
- Suggest related questions

---

### 2. HISTORY COMMANDS

#### View Recent Queries
```
❓ Ask a question: history
```
Shows last 10 queries with IDs and timestamps.

```
❓ Ask a question: history 20
```
Shows last 20 queries.

**Output:**
```
📚 Recent Queries (last 10):
================================================================================
   ID   1 | 2026-01-29 11:05:30 | show me latest 20 shipments
⭐ ID   2 | 2026-01-29 11:06:15 | total weight by client
   ID   3 | 2026-01-29 11:07:22 | shipments from last week
================================================================================
```

#### Search History
```
❓ Ask a question: search shipment
```
Finds all queries containing "shipment".

```
❓ Ask a question: search weight
```
Finds all queries about weight.

#### Mark Favorites
```
❓ Ask a question: favorite 2
```
Toggles favorite status on query #2 (⭐ appears in history).

#### Replay a Query
```
❓ Ask a question: replay 2
```
Re-runs query #2 with fresh data.

---

### 3. EXPORT COMMANDS

After running a query, export the results:

#### Export to Excel
```
❓ Ask a question: export excel
```
Creates `export.xlsx` with:
- Formatted headers (blue background)
- Auto-adjusted column widths
- Professional styling

#### Export to JSON
```
❓ Ask a question: export json
```
Creates `export.json` with pretty-printed data.

#### Export to HTML
```
❓ Ask a question: export html
```
Creates `export.html` with:
- Interactive table
- Search functionality
- Responsive design
- Standalone file (no dependencies)

#### Export to PDF
```
❓ Ask a question: export pdf
```
Creates `export.pdf` with:
- Professional report layout
- Includes charts if available
- Formatted tables

**All exports are saved in the same folder as your query results.**

---

### 4. TEMPLATE COMMANDS

#### List Templates
```
❓ Ask a question: templates
```

**Shows 8 built-in templates:**
1. **Top N Records** - Get top N records sorted by column
2. **Date Range Analysis** - Filter by date range
3. **Group By Aggregation** - Aggregate data by group
4. **Join Multiple Tables** - Join two or more tables
5. **Trend Over Time** - Analyze trends over time
6. **Distinct Values** - Get unique values
7. **Count by Group** - Count records by category
8. **Recent Records** - Get most recent records

**Each template shows:**
- Description
- Example usage

---

### 5. ANALYSIS COMMANDS

#### Toggle Insights
```
❓ Ask a question: insights
```
Turns insights display ON or OFF.

**When ON (default), you see:**
- Summary statistics (min, max, avg, median)
- Data quality score
- Null value analysis
- Outlier detection
- Recommendations

**When OFF:**
- Only query results are shown
- Faster display for quick queries

#### View Performance Stats
```
❓ Ask a question: stats
```

**Shows:**
```
⚡ PERFORMANCE REPORT
================================================================================
📊 Query Statistics:
   Total Queries: 15
   Successful: 14
   Failed: 1

⏱️  Execution Times:
   Average: 156.45 ms
   Median: 145.23 ms
   Min: 98.12 ms
   Max: 534.56 ms

📈 Data Volume:
   Total Rows: 1,245
   Avg Rows/Query: 88

💡 Recommendations:
   ✅ Performance looks good!
================================================================================
```

---

### 6. SYSTEM COMMANDS

#### Refresh Schema
```
❓ Ask a question: refresh
```
Reloads the database schema (use after schema changes).

#### Show Help
```
❓ Ask a question: help
```
Displays all available commands.

#### Exit
```
❓ Ask a question: exit
```
or
```
❓ Ask a question: quit
```
Exits the application.

---

## 🎯 Complete Workflow Example

### Step 1: Ask a Question
```
❓ Ask a question: show me top 10 shipments by weight

🤖 Generated SQL: SELECT TOP 10 * FROM GV_SHIPMENT ORDER BY TTL_WEIGHT DESC
📊 Results (10 rows) - Execution time: 145.23ms
[Table displayed]

💾 Results saved to folder: query_20260129_110530/
   📄 result.md  - Formatted report
   📊 result.csv - Full data
   📈 chart.png  - Visualization
   🆔 Query ID: 5 (use 'replay 5' to re-run)

📊 DATA INSIGHTS REPORT
[Insights displayed]

💡 You might also want to ask:
   1. What is the average TTL_WEIGHT?
   2. Show me the distribution of TTL_WEIGHT
   3. Group results by TRP_MODE
```

### Step 2: Export to Excel
```
❓ Ask a question: export excel

✅ Exported to: artifacts/query_20260129_110530/export.xlsx
```

### Step 3: Mark as Favorite
```
❓ Ask a question: favorite 5

⭐ Added to favorites
```

### Step 4: View History
```
❓ Ask a question: history

📚 Recent Queries (last 10):
================================================================================
⭐ ID   5 | 2026-01-29 11:05:30 | show me top 10 shipments by weight
   ID   4 | 2026-01-29 11:04:15 | total shipments by client
   ID   3 | 2026-01-29 11:03:22 | shipments from last week
================================================================================
```

### Step 5: Check Performance
```
❓ Ask a question: stats

⚡ PERFORMANCE REPORT
[Performance metrics displayed]
```

---

## 💡 Tips & Best Practices

### 1. Natural Language Tips
- Be specific: "show me shipments from January 2026"
- Use common terms: "total", "count", "average", "latest"
- Mention columns: "sort by weight", "group by status"

### 2. Using History
- Use `favorite` for queries you run often
- Use `replay` instead of retyping questions
- Use `search` to find old queries quickly

### 3. Exports
- Export to **Excel** for business users
- Export to **JSON** for developers/APIs
- Export to **HTML** for sharing via email
- Export to **PDF** for formal reports

### 4. Performance
- Turn off `insights` for faster queries
- Check `stats` to identify slow queries
- Use `refresh` only when schema changes

### 5. Insights
- Review quality scores to find data issues
- Check outliers for anomalies
- Follow recommendations for better queries

---

## 🎨 Output Folder Structure

Each query creates a timestamped folder:

```
artifacts/
└── query_20260129_110530/
    ├── result.md       # Formatted report with HTML table
    ├── result.csv      # Full data in CSV
    ├── chart.png       # Visualization (if generated)
    ├── export.xlsx     # Excel export (if requested)
    ├── export.json     # JSON export (if requested)
    ├── export.html     # HTML export (if requested)
    └── export.pdf      # PDF export (if requested)
```

---

## 🆘 Troubleshooting

### "No results to export"
Run a query first, then use export commands.

### "Query ID not found"
Use `history` to see valid query IDs.

### Export fails
Check that dependencies are installed:
```bash
pip install openpyxl reportlab pyarrow
```

### Insights not showing
Type `insights` to toggle them back on.

---

## 🚀 You're Ready!

Start asking questions and explore all the powerful features of your enterprise SQL Agent!
