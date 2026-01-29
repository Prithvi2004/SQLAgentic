"""
SQL Agent - Main CLI Interface
Natural language to SQL query system with autonomous execution and visualization.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from tabulate import tabulate

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from db_manager import DatabaseManager
from sql_agent import SQLAgent, SafetyViolationError
from visualizer import ChartGenerator
from query_history import QueryHistory
from data_insights import DataInsights
from exporters import DataExporter
from template_manager import TemplateManager
from performance_monitor import PerformanceMonitor
from query_suggester import QuerySuggester
from data_comparator import DataComparator
from interactive_explorer import InteractiveExplorer


class BackupDBAgent:
    """Main application class for the BackupDB SQL Agent."""
    
    def __init__(self):
        """Initialize the agent and all components."""
        self.db_manager = None
        self.sql_agent = None
        self.visualizer = None
        self.schema_cache_path = Path(".agent/context/schema.txt")
        self.current_query_folder = None
        
        # Advanced features
        self.history = None
        self.insights = None
        self.exporter = None
        self.templates = None
        self.performance = None
        self.suggester = None
        self.comparator = None
        self.explorer = None
        self.last_result = None
        self.show_insights = True
        
    def initialize(self):
        """Set up all components and load configuration."""
        print("\n" + "="*80)
        print("🤖 SQL Agent - Initializing...")
        print("="*80 + "\n")
        
        # Load environment variables
        load_dotenv()
        
        # Get configuration
        db_connection = os.getenv(
            'DB_CONNECTION_STRING',
            'Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=BackupDB;Trusted_Connection=yes;'
        )
        ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        ollama_model = os.getenv('OLLAMA_MODEL', 'deepseek-v3.1:671b-cloud')
        max_retries = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
        
        print(f"📋 Configuration:")
        print(f"   Database: BackupDB (SQL Server)")
        print(f"   LLM Model: {ollama_model}")
        print(f"   Ollama URL: {ollama_base_url}")
        print(f"   Max Retries: {max_retries}\n")
        
        # Initialize database manager
        print("🔌 Connecting to database...")
        try:
            self.db_manager = DatabaseManager(db_connection)
            if not self.db_manager.test_connection():
                raise Exception("Database connection test failed")
        except Exception as e:
            print(f"\n❌ Failed to connect to database: {e}")
            print("\nPlease check:")
            print("  1. SQL Server is running")
            print("  2. BackupDB database exists")
            print("  3. ODBC Driver 17 for SQL Server is installed")
            print("  4. Connection string in .env is correct")
            sys.exit(1)
        
        # Load or generate schema
        print("\n📊 Loading database schema...")
        schema_summary = self._load_or_generate_schema()
        
        # Initialize SQL agent
        print("\n🧠 Initializing AI agent...")
        try:
            self.sql_agent = SQLAgent(
                db_manager=self.db_manager,
                base_url=ollama_base_url,
                model_name=ollama_model
            )
            self.sql_agent.load_schema_context(schema_summary)
        except Exception as e:
            print(f"\n❌ Failed to initialize AI agent: {e}")
            print("\nPlease check:")
            print("  1. Ollama is running (ollama serve)")
            print(f"  2. Model '{ollama_model}' is pulled (ollama pull {ollama_model})")
            print(f"  3. Ollama is accessible at {ollama_base_url}")
            sys.exit(1)
        
        # Initialize visualizer
        print("\n📈 Initializing visualization engine...")
        self.visualizer = ChartGenerator()
        
        # Initialize advanced features
        print("\n🚀 Initializing advanced features...")
        self.history = QueryHistory()
        self.insights = DataInsights()
        self.exporter = DataExporter()
        self.templates = TemplateManager()
        self.performance = PerformanceMonitor()
        self.suggester = QuerySuggester()
        self.comparator = DataComparator()
        self.explorer = InteractiveExplorer()
        print("✅ All advanced features loaded!")
        
        print("\n" + "="*80)
        print("✅ BackupDB SQL Agent Ready!")
        print("="*80 + "\n")
    
    def _load_or_generate_schema(self) -> str:
        """Load schema from cache or generate fresh."""
        # Create cache directory if needed
        self.schema_cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if cache exists
        if self.schema_cache_path.exists():
            print(f"   Loading from cache: {self.schema_cache_path}")
            with open(self.schema_cache_path, 'r', encoding='utf-8') as f:
                schema_summary = f.read()
            print("   ✅ Schema loaded from cache")
        else:
            print("   Extracting schema from database...")
            schema_summary = self.db_manager.get_schema_summary()
            
            # Save to cache
            with open(self.schema_cache_path, 'w', encoding='utf-8') as f:
                f.write(schema_summary)
            print(f"   ✅ Schema cached to: {self.schema_cache_path}")
        
        return schema_summary
    
    def refresh_schema(self):
        """Force refresh of schema cache."""
        print("\n🔄 Refreshing schema cache...")
        if self.schema_cache_path.exists():
            self.schema_cache_path.unlink()
        schema_summary = self._load_or_generate_schema()
        if self.sql_agent:
            self.sql_agent.load_schema_context(schema_summary)
        print("✅ Schema refreshed!\n")
    
    
    def _save_result_to_file(self, user_query: str, sql: str, df) -> str:
        """
        Save query results to files in a dedicated folder.
        
        Args:
            user_query: Original user question
            sql: SQL query executed
            df: Results DataFrame
            
        Returns:
            str: Path to saved markdown file
        """
        from datetime import datetime
        
        # Generate timestamp for folder name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create query-specific folder
        query_folder = Path(f"artifacts/query_{timestamp}")
        query_folder.mkdir(parents=True, exist_ok=True)
        
        # Define file paths
        md_filepath = query_folder / "result.md"
        csv_filepath = query_folder / "result.csv"
        
        # Save CSV for easy viewing in Excel
        df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
        
        # Build markdown content
        content = []
        content.append("# SQL Query Result")
        content.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"**Query Folder:** `{query_folder.name}`")
        content.append(f"\n---\n")
        
        content.append("## User Question")
        content.append(f"\n```\n{user_query}\n```\n")
        
        content.append("## SQL Query")
        content.append(f"\n```sql\n{sql}\n```\n")
        
        content.append(f"## Results\n")
        content.append(f"**Total Rows:** {len(df)}")
        content.append(f"**Total Columns:** {len(df.columns)}\n")
        
        # Add file reference
        content.append(f"> 💡 **Files in this folder:**")
        content.append(f"> - `result.md` - This file with formatted table")
        content.append(f"> - `result.csv` - Full data in CSV format")
        content.append(f"> - `chart.png` - Visualization (if generated)\n")
        
        # Prepare display DataFrame
        df_display = df.fillna('')
        
        # Add table section
        content.append(f"### Data Table\n")
        
        # Generate clean markdown table using tabulate
        try:
            from tabulate import tabulate
            table_md = tabulate(
                df_display,
                headers='keys',
                tablefmt='github',  # Clean GitHub-flavored markdown
                showindex=False,
                maxcolwidths=50  # Limit column width
            )
            content.append(table_md)
        except Exception as e:
            # Fallback to pandas markdown
            content.append(df_display.to_markdown(index=False, max_colwidth=50))
        
        content.append("\n")  # Add spacing
        
        # Write markdown file
        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        # Store folder path for chart generation
        self.current_query_folder = query_folder
        
        return str(md_filepath)
    
    def run_query(self, user_query: str):
        """Execute a user query with full feature integration."""
        try:
            # Start performance monitoring
            self.performance.start_query()
            
            # Execute with retry logic
            df, sql = self.sql_agent.execute_with_retry(user_query)
            
            # Record performance
            execution_time = self.performance.end_query(sql, len(df), success=True)
            
            # Display SQL used
            print(f"\n📝 SQL Query Used:")
            print("-" * 80)
            print(sql)
            print("-" * 80)
            
            # Display results
            print(f"\n📊 Results ({len(df)} rows) - Execution time: {execution_time:.2f}ms")
            print("-" * 80)
            
            if df.empty:
                print("No results found.")
            else:
                # Prepare DataFrame for display
                df_display = df.fillna('')
                
                # Limit preview to first 20 rows for large datasets
                preview_limit = 20
                if len(df_display) > preview_limit:
                    df_preview = df_display.head(preview_limit)
                    print(f"Showing first {preview_limit} of {len(df)} rows:")
                else:
                    df_preview = df_display
                
                # Format table with tabulate
                try:
                    table = tabulate(
                        df_preview,
                        headers='keys',
                        tablefmt='grid',
                        showindex=False,
                        maxcolwidths=30
                    )
                    print(table)
                except Exception as e:
                    print(f"⚠️  Table formatting error, showing raw data:")
                    print(df_preview.to_string(max_rows=preview_limit, max_colwidth=30))
            
            print("-" * 80)
            
            # Save results and log to history
            if not df.empty:
                result_file = self._save_result_to_file(user_query, sql, df)
                query_folder = self.current_query_folder
                
                # Log to history
                query_id = self.history.add_query(
                    user_query, sql, len(df), execution_time, str(query_folder)
                )
                
                # Store for later use
                self.last_result = {
                    "query_id": query_id,
                    "df": df,
                    "sql": sql,
                    "user_query": user_query
                }
                
                print(f"\n💾 Results saved to folder: {query_folder.name}/")
                print(f"   📄 result.md  - Formatted report")
                print(f"   📊 result.csv - Full data")
                print(f"   🆔 Query ID: {query_id} (use 'replay {query_id}' to re-run)")
                
                # Generate and display insights
                if self.show_insights:
                    try:
                        insights = self.insights.analyze(df)
                        print(self.insights.format_insights_report(insights))
                    except Exception as e:
                        print(f"⚠️  Could not generate insights: {e}")
                
                # Try to generate visualization
                try:
                    chart_path = self.visualizer.auto_visualize(df, user_query)
                    if chart_path:
                        import shutil
                        new_chart_path = self.current_query_folder / "chart.png"
                        shutil.move(chart_path, new_chart_path)
                        print(f"   📈 chart.png  - Visualization")
                    else:
                        # Explain why no chart was generated
                        if len(df.columns) < 2:
                            print(f"ℹ️  No visualization: Query has only 1 column (need at least 2 for charts)")
                        else:
                            print(f"ℹ️  No suitable visualization detected for this data")
                except Exception as e:
                    print(f"⚠️  Could not generate visualization: {e}")
                
                # Show AI suggestions
                try:
                    suggestions = self.suggester.suggest_followups(user_query, df, sql)
                    if suggestions:
                        print(f"\n💡 You might also want to ask:")
                        for i, suggestion in enumerate(suggestions[:3], 1):
                            print(f"   {i}. {suggestion}")
                except Exception as e:
                    pass  # Silently skip if suggestions fail
            
        except SafetyViolationError as e:
            print(f"\n{e}\n")
            self.performance.end_query("", 0, success=False)
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            self.performance.end_query("", 0, success=False)
    
    def handle_command(self, command: str) -> bool:
        """Handle special commands. Returns True if command was handled, False if it's a regular query."""
        cmd_lower = command.lower().strip()
        parts = command.split()
        
        # Exit commands
        if cmd_lower in ['exit', 'quit', 'q']:
            return 'exit'
        
        # Help
        if cmd_lower in ['help', '?']:
            self.show_help()
            return True
        
        # Refresh schema
        if cmd_lower == 'refresh':
            self.refresh_schema()
            return True
        
        # History commands
        if cmd_lower.startswith('history'):
            if len(parts) == 1:
                self.show_history(10)
            elif parts[1].isdigit():
                self.show_history(int(parts[1]))
            return True
        
        # Search history
        if cmd_lower.startswith('search '):
            keyword = ' '.join(parts[1:])
            self.search_history(keyword)
            return True
        
        # Favorite
        if cmd_lower.startswith('favorite ') and len(parts) == 2:
            query_id = int(parts[1])
            self.toggle_favorite(query_id)
            return True
        
        # Replay
        if cmd_lower.startswith('replay ') and len(parts) == 2:
            query_id = int(parts[1])
            self.replay_query(query_id)
            return True
        
        # Export
        if cmd_lower.startswith('export '):
            format_type = parts[1] if len(parts) > 1 else 'excel'
            self.export_last_result(format_type)
            return True
        
        # Templates
        if cmd_lower == 'templates':
            self.show_templates()
            return True
        
        # Performance stats
        if cmd_lower in ['stats', 'performance']:
            print(self.performance.format_report())
            return True
        
        # Toggle insights
        if cmd_lower == 'insights':
            self.show_insights = not self.show_insights
            print(f"✅ Insights display: {'ON' if self.show_insights else 'OFF'}")
            return True
        
        return False
    
    def show_help(self):
        """Display help information."""
        help_text = """
================================================================================
🤖 SQL Agent - Command Reference
================================================================================

QUERY COMMANDS:
  <natural language>     Ask any question in plain English
  
HISTORY COMMANDS:
  history [N]           Show last N queries (default: 10)
  search <keyword>      Search query history
  favorite <id>         Toggle favorite status
  replay <id>           Re-run a previous query
  
EXPORT COMMANDS:
  export excel          Export last result to Excel
  export json           Export to JSON
  export html           Export to interactive HTML
  export pdf            Export to PDF report
  
TEMPLATE COMMANDS:
  templates             List available query templates
  
ANALYSIS COMMANDS:
  insights              Toggle insights display on/off
  stats                 Show performance statistics
  
SYSTEM COMMANDS:
  refresh               Reload database schema
  help                  Show this help message
  exit/quit             Exit the application

================================================================================
"""
        print(help_text)
    
    def show_history(self, limit: int = 10):
        """Show query history."""
        queries = self.history.get_recent(limit)
        if not queries:
            print("No query history yet.")
            return
        
        print(f"\n📚 Recent Queries (last {limit}):")
        print("="*80)
        for q in queries:
            fav = "⭐" if q['is_favorite'] else "  "
            timestamp = q['timestamp'][:19]
            print(f"{fav} ID {q['id']:3d} | {timestamp} | {q['user_query'][:50]}")
        print("="*80)
    
    def search_history(self, keyword: str):
        """Search query history."""
        results = self.history.search(keyword=keyword)
        if not results:
            print(f"No queries found matching '{keyword}'")
            return
        
        print(f"\n🔍 Search Results for '{keyword}':")
        print("="*80)
        for q in results:
            print(f"ID {q['id']:3d} | {q['timestamp'][:19]} | {q['user_query']}")
        print("="*80)
    
    def toggle_favorite(self, query_id: int):
        """Toggle favorite status."""
        is_fav = self.history.toggle_favorite(query_id)
        print(f"{'⭐ Added to' if is_fav else '❌ Removed from'} favorites")
    
    def replay_query(self, query_id: int):
        """Replay a previous query."""
        query = self.history.get_by_id(query_id)
        if not query:
            print(f"Query ID {query_id} not found")
            return
        
        print(f"\n🔄 Replaying query: {query['user_query']}")
        self.run_query(query['user_query'])
    
    def export_last_result(self, format_type: str):
        """Export last result in specified format."""
        if not self.last_result:
            print("No results to export. Run a query first.")
            return
        
        df = self.last_result['df']
        folder = self.current_query_folder
        
        try:
            if format_type == 'excel':
                path = folder / "export.xlsx"
                self.exporter.export_excel(df, str(path))
            elif format_type == 'json':
                path = folder / "export.json"
                self.exporter.export_json(df, str(path))
            elif format_type == 'html':
                path = folder / "export.html"
                self.exporter.export_html(df, str(path))
            elif format_type == 'pdf':
                path = folder / "export.pdf"
                chart = folder / "chart.png" if (folder / "chart.png").exists() else None
                self.exporter.export_pdf(df, str(path), chart_path=str(chart) if chart else None)
            
            print(f"✅ Exported to: {path}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def show_templates(self):
        """Show available templates."""
        templates = self.templates.list_templates()
        print("\n📋 Available Query Templates:")
        print("="*80)
        for t in templates:
            print(f"\n{t['name']}:")
            print(f"   {t['description']}")
            print(f"   Example: {t['example']}")
        print("="*80)
    
    def interactive_loop(self):
        """Main interactive query loop."""
        print("💬 Enter your questions in natural language")
        print("   Commands: 'help' for all commands, 'exit' to quit\n")
        
        while True:
            try:
                # Get user input
                user_input = input("❓ Ask a question: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                result = self.handle_command(user_input)
                if result == 'exit':
                    print("\n👋 Goodbye!")
                    break
                elif result:
                    continue
                
                # Run as query
                self.run_query(user_input)
                print()  # Blank line for readability
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}\n")
    
    def cleanup(self):
        """Clean up resources."""
        if self.db_manager:
            self.db_manager.close()


def main():
    """Main entry point."""
    agent = BackupDBAgent()
    
    try:
        agent.initialize()
        agent.interactive_loop()
    finally:
        agent.cleanup()


if __name__ == "__main__":
    main()
