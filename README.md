# SQL Agent - Enterprise Edition

## 🎯 Overview

An AI-powered SQL analytics platform that transforms natural language questions into SQL queries with enterprise-grade features.

## ✨ Features

### Core Capabilities
- **Natural Language to SQL**: Ask questions in plain English
- **Automatic Execution**: Queries run automatically with retry logic
- **Smart Visualization**: Auto-generates charts based on data
- **Read-Only Safety**: Prevents accidental data modification

### Advanced Features (NEW!)
- **📚 Query History**: SQLite-based tracking with search and favorites
- **🔍 Data Insights**: Automatic statistical analysis and quality checks
- **📤 Multi-Format Export**: Excel, JSON, HTML, PDF with professional formatting
- **📋 Query Templates**: 8 pre-built templates for common tasks
- **⚡ Performance Monitor**: Track execution times and optimization tips
- **💡 AI Suggestions**: Context-aware follow-up question recommendations
- **🔄 Data Comparator**: Compare datasets across time periods
- **🎯 Interactive Explorer**: Drill-down analysis without SQL

## 🚀 Quick Start

### Installation

```bash
# Clone or download the repository
cd SQLAgentic

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database connection
```

### Configuration

Create `.env` file:
```env
DB_CONNECTION_STRING=Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=BackupDB;Trusted_Connection=yes;
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-v3.1:671b-cloud
MAX_RETRY_ATTEMPTS=3
```

### Run

```bash
python main.py
```

## 📖 Usage

### Basic Queries

```
❓ Ask a question: show me the latest 20 shipments
❓ Ask a question: what is the total weight by client?
❓ Ask a question: count shipments by status
```

### Commands

| Command | Description |
|---------|-------------|
| `help` | Show all commands |
| `history [N]` | View query history |
| `search <keyword>` | Search history |
| `favorite <id>` | Bookmark query |
| `replay <id>` | Re-run query |
| `export <format>` | Export results (excel/json/html/pdf) |
| `templates` | List query templates |
| `stats` | Performance report |
| `insights` | Toggle insights on/off |
| `refresh` | Reload schema |
| `exit` | Quit application |

See [USER_GUIDE.md](USER_GUIDE.md) for detailed usage instructions.

## 📁 Project Structure

```
SQLAgentic/
├── main.py                    # Main application
├── src/
│   ├── db_manager.py         # Database connection
│   ├── sql_agent.py          # AI SQL generation
│   ├── visualizer.py         # Chart generation
│   ├── query_history.py      # History tracking
│   ├── data_insights.py      # Statistical analysis
│   ├── exporters.py          # Multi-format exports
│   ├── template_manager.py   # Query templates
│   ├── performance_monitor.py # Performance tracking
│   ├── query_suggester.py    # AI suggestions
│   ├── data_comparator.py    # Data comparison
│   └── interactive_explorer.py # Interactive mode
├── templates/
│   └── query_templates.json  # Template definitions
├── artifacts/
│   └── query_*/              # Query results folders
├── .agent/
│   ├── context/
│   │   └── schema.txt        # Cached schema
│   └── history/
│       └── queries.db        # Query history database
├── requirements.txt          # Python dependencies
├── .env                      # Configuration
├── USER_GUIDE.md            # Detailed usage guide
└── README.md                # This file
```

## 🎨 Output

Each query creates a timestamped folder with:
- `result.md` - Formatted report with HTML tables
- `result.csv` - Full data export
- `chart.png` - Visualization (if applicable)
- `export.*` - Additional exports (Excel, JSON, HTML, PDF)

## 🔧 Requirements

- Python 3.8+
- SQL Server with ODBC Driver 17
- Ollama with DeepSeek model
- Dependencies: pandas, pyodbc, sqlalchemy, matplotlib, tabulate, openpyxl, reportlab, pyarrow

## 📊 Features in Detail

### Query History
- Automatic logging to SQLite
- Search by keyword or date
- Favorite/bookmark queries
- Replay any previous query
- Export history to CSV/JSON

### Data Insights
- Summary statistics (min, max, avg, median, std)
- Data quality score (0-100)
- Null value analysis
- Outlier detection (IQR method)
- Distribution analysis
- Automated recommendations

### Export Formats
- **Excel**: Formatted headers, auto-width, summary stats
- **JSON**: Pretty-printed, multiple orientations
- **HTML**: Interactive tables with search
- **PDF**: Professional reports with charts

### Performance Monitoring
- Track execution times
- Success/failure rates
- Average, min, max, median metrics
- Optimization recommendations
- Slow query detection

### AI Suggestions
- Context-aware follow-up questions
- Based on query results and schema
- Suggests aggregations, filtering, grouping
- Time-based analysis for date columns

## 🛡️ Security

- **Read-Only Mode**: Prevents INSERT, UPDATE, DELETE, DROP
- **SQL Injection Protection**: Parameterized queries
- **Schema Validation**: Verifies table and column names
- **Error Handling**: Graceful failure with retry logic

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Additional export formats (Parquet, Avro)
- Scheduled queries
- Data quality dashboard
- Multi-database support
- Web interface

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Ollama for LLM inference
- DeepSeek for the AI model
- Pandas for data manipulation
- Matplotlib for visualizations

## 📧 Support

For issues or questions:
1. Check [USER_GUIDE.md](USER_GUIDE.md)
2. Review error messages
3. Verify configuration in `.env`
4. Ensure Ollama is running
5. Check database connectivity

---

**Built with ❤️ for enterprise data analytics**
