"""
SQL Agent with Ollama Integration
Generates SQL queries from natural language using local LLM with self-healing capabilities.
"""

import re
import ollama
from typing import Optional, Tuple
import pandas as pd


class SafetyViolationError(Exception):
    """Raised when a generated SQL query contains destructive operations."""
    pass


class SQLAgent:
    """Autonomous SQL agent with natural language to SQL conversion."""
    
    # Destructive SQL keywords to block
    DESTRUCTIVE_KEYWORDS = [
        'DROP', 'DELETE', 'UPDATE', 'TRUNCATE', 'ALTER', 'INSERT',
        'CREATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
    ]
    
    def __init__(self, db_manager, base_url: str = "http://localhost:11434", 
                 model_name: str = "deepseek-v3.1:671b-cloud"):
        """
        Initialize the SQL Agent.
        
        Args:
            db_manager: DatabaseManager instance
            base_url: Ollama server URL
            model_name: Ollama model name
        """
        self.db_manager = db_manager
        self.base_url = base_url
        self.model_name = model_name
        self.schema_context = None
        
        # Configure Ollama client
        self.client = ollama.Client(host=base_url)
        print(f"✅ SQL Agent initialized with model: {model_name}")
    
    def load_schema_context(self, schema_summary: str):
        """
        Load database schema context for SQL generation.
        
        Args:
            schema_summary: Formatted schema summary text
        """
        self.schema_context = schema_summary
        print("✅ Schema context loaded into agent")
    
    def generate_safe_sql(self, user_query: str, previous_sql: Optional[str] = None, 
                         error_message: Optional[str] = None) -> str:
        """
        Generate SQL query from natural language using Ollama.
        
        Args:
            user_query: Natural language question
            previous_sql: Previously generated SQL (for retry attempts)
            error_message: Error from previous attempt (for self-healing)
            
        Returns:
            str: Generated SQL query
        """
        # Build prompt
        if previous_sql and error_message:
            # Self-healing prompt
            prompt = self._build_healing_prompt(user_query, previous_sql, error_message)
        else:
            # Initial generation prompt
            prompt = self._build_initial_prompt(user_query)
        
        try:
            # Call Ollama
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a SQL Server expert. Generate only valid T-SQL queries. Return ONLY the SQL code without explanations or markdown formatting.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.1,  # Low temperature for consistent SQL generation
                }
            )
            
            # Extract SQL from response
            sql = self._extract_sql(response['message']['content'])
            print(f"🤖 Generated SQL: {sql[:100]}...")
            return sql
            
        except Exception as e:
            print(f"❌ LLM generation failed: {e}")
            raise
    
    def _build_initial_prompt(self, user_query: str) -> str:
        """Build initial SQL generation prompt."""
        return f"""Given the database schema below, write a SQL Server query to answer the user's question.

DATABASE SCHEMA:
{self.schema_context}

USER QUESTION:
{user_query}

RULES:
- Return ONLY the SQL query, no explanations
- Use proper SQL Server T-SQL syntax
- Use TOP instead of LIMIT for row limiting
- Always use table aliases for clarity
- Use square brackets for table/column names with spaces
- Return only SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)
- Include appropriate WHERE, JOIN, GROUP BY, ORDER BY clauses as needed

SQL Query:"""
    
    def _build_healing_prompt(self, user_query: str, previous_sql: str, 
                              error_message: str) -> str:
        """Build self-healing prompt with error context."""
        return f"""The previous SQL query failed. Please fix it based on the error message.

DATABASE SCHEMA:
{self.schema_context}

ORIGINAL USER QUESTION:
{user_query}

PREVIOUS SQL QUERY (FAILED):
{previous_sql}

ERROR MESSAGE:
{error_message}

Please generate a corrected SQL query that fixes this error. Return ONLY the corrected SQL query.

Corrected SQL Query:"""
    
    def _extract_sql(self, response_text: str) -> str:
        """
        Extract SQL query from LLM response.
        Handles markdown code blocks and plain text.
        """
        # Remove markdown code blocks if present
        sql = response_text.strip()
        
        # Check for ```sql or ``` code blocks
        code_block_pattern = r'```(?:sql)?\s*(.*?)\s*```'
        matches = re.findall(code_block_pattern, sql, re.DOTALL | re.IGNORECASE)
        
        if matches:
            sql = matches[0].strip()
        
        # Remove any leading/trailing whitespace
        sql = sql.strip()
        
        # Remove any explanatory text after the query
        # (stop at common explanation starters)
        for separator in ['\n\nThis query', '\n\nExplanation', '\n\nNote:']:
            if separator in sql:
                sql = sql.split(separator)[0].strip()
        
        return sql
    
    def validate_sql_safety(self, sql: str) -> bool:
        """
        Check if SQL query contains destructive operations.
        
        Args:
            sql: SQL query string
            
        Returns:
            bool: True if safe, False if contains destructive keywords
            
        Raises:
            SafetyViolationError: If destructive keywords found
        """
        sql_upper = sql.upper()
        
        for keyword in self.DESTRUCTIVE_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                raise SafetyViolationError(
                    f"🚫 SAFETY VIOLATION: Query contains destructive keyword '{keyword}'. "
                    f"This agent is read-only and cannot execute write operations."
                )
        
        return True
    
    def execute_with_retry(self, user_query: str, max_retries: int = 3) -> Tuple[pd.DataFrame, str]:
        """
        Execute query with self-healing retry logic.
        
        Args:
            user_query: Natural language question
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple[pd.DataFrame, str]: Query results and final SQL used
            
        Raises:
            Exception: If all retry attempts fail
        """
        previous_sql = None
        error_message = None
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"\n🔄 Attempt {attempt}/{max_retries}: Generating SQL...")
                
                # Generate SQL
                sql = self.generate_safe_sql(user_query, previous_sql, error_message)
                
                # Validate safety
                self.validate_sql_safety(sql)
                
                # Execute query
                print(f"⚡ Executing query...")
                df = self.db_manager.execute_query(sql)
                
                print(f"✅ Success on attempt {attempt}!")
                return df, sql
                
            except SafetyViolationError as e:
                # Safety violations should not be retried
                print(str(e))
                raise
                
            except Exception as e:
                error_message = str(e)
                previous_sql = sql if 'sql' in locals() else None
                
                print(f"❌ Attempt {attempt} failed: {error_message}")
                
                if attempt == max_retries:
                    print(f"\n💥 All {max_retries} attempts failed.")
                    raise Exception(f"Failed after {max_retries} attempts. Last error: {error_message}")
                
                print(f"🔧 Attempting self-healing (retry {attempt + 1}/{max_retries})...")
