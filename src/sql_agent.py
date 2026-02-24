"""
Advanced SQL Agent with Ollama Integration
Generates SQL queries from natural language with advanced agentic flow.
"""

import re
import ollama
from typing import Optional, Tuple, List, Dict
import pandas as pd


class SafetyViolationError(Exception):
    """Raised when a generated SQL query contains destructive operations."""
    pass


class SchemaValidationError(Exception):
    """Raised when SQL query references non-existent tables or columns."""
    pass


class QueryComplexityError(Exception):
    """Raised when decomposing complex queries."""
    pass


class SQLAgent:
    """Advanced SQL agent with natural language to SQL conversion."""
    
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
        self.structured_schema = None
        self.query_decomposition_strategy = None
        
        # Configure Ollama client
        self.client = ollama.Client(host=base_url)
        print(f"✅ Advanced SQL Agent initialized with model: {model_name}")
    
    def load_schema_context(self, schema_summary: str):
        """
        Load database schema context for SQL generation.
        
        Args:
            schema_summary: Formatted schema summary text
        """
        self.schema_context = schema_summary
        print("✅ Schema context loaded into agent")
    
    def load_structured_schema(self, structured_schema: Dict):
        """
        Load structured schema for validation and decomposition.
        
        Args:
            structured_schema: Dictionary with table metadata
        """
        self.structured_schema = structured_schema
        print("✅ Structured schema loaded for advanced validation")
    
    def decompose_query(self, user_query: str) -> Dict:
        """
        Determine if query needs decomposition and plan sub-queries.
        
        Args:
            user_query: Natural language question
            
        Returns:
            Dict with decomposition plan
        """
        try:
            prompt = f"""Analyze this natural language query and determine if it requires decomposition into simpler sub-queries.

USER QUERY: {user_query}

DATABASE SCHEMA CONTEXT:
{self.schema_context}

Consider:
- Does this involve multiple tables that need JOINs?
- Does it require sub-queries or CTEs?
- Does it need filtering before aggregation?
- Is it a multi-step analytical question?

Respond with JSON:
{{
  "requires_decomposition": true/false,
  "reason": "brief explanation",
  "sub_queries": ["step 1 description", "step 2 description", ...] or null if no decomposition,
  "complexity_level": "simple|moderate|complex"
}}
"""
            
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': 'You are a SQL analysis expert. Analyze query complexity and suggest decomposition if needed.'},
                    {'role': 'user', 'content': prompt}
                ],
                options={'temperature': 0.3}
            )
            
            result_text = response['message']['content']
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                import json
                plan = json.loads(json_match.group(0))
                return plan
            else:
                # Fallback: return simple plan
                return {
                    "requires_decomposition": False,
                    "reason": "Could not parse complexity analysis",
                    "sub_queries": None,
                    "complexity_level": "simple"
                }
                
        except Exception as e:
            print(f"❌ Query decomposition failed: {e}")
            return {
                "requires_decomposition": False,
                "reason": "Decomposition analysis failed",
                "sub_queries": None,
                "complexity_level": "simple"
            }
    
    def validate_against_schema(self, sql: str) -> bool:
        """
        Validate SQL query against actual schema before execution.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            bool: True if validation passes
            
        Raises:
            SchemaValidationError: If tables/columns don't exist
        """
        if not self.structured_schema:
            return True  # Skip if no structured schema loaded
        
        sql_upper = sql.upper()
        
        # Extract table names
        table_pattern = r'\bFROM\s+(\w+)'  # Simple table extraction
        table_matches = re.findall(table_pattern, sql_upper)
        
        # Extract column names (simplified)
        column_pattern = r'\bSELECT\s+([^\n]+?)\s+FROM'
        column_match = re.search(column_pattern, sql_upper, re.DOTALL)
        
        if column_match:
            columns_section = column_match.group(1)
            # Extract column names (basic approach)
            column_names = re.findall(r'\b(\w+)\b', columns_section)
            
            # Skip common SQL keywords
            sql_keywords = ['SELECT', 'DISTINCT', 'TOP', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'AS']
            column_names = [col for col in column_names if col.upper() not in sql_keywords]
        else:
            column_names = []
        
        # Validate tables exist
        for table in table_matches:
            if table not in self.structured_schema.get('tables', {}):
                raise SchemaValidationError(f"Table '{table}' does not exist in schema")
            
            # Validate columns exist in their tables
            for column in column_names:
                if column not in self.structured_schema['tables'][table].get('columns', []):
                    raise SchemaValidationError(f"Column '{column}' does not exist in table '{table}'")
        
        return True
    
    def score_confidence(self, sql: str, user_query: str) -> int:
        """
        Score confidence level of generated SQL (0-100).
        
        Args:
            sql: Generated SQL query
            user_query: Original user question
            
        Returns:
            int: Confidence score (0-100)
        """
        try:
            prompt = f"""Rate the confidence that this SQL query correctly answers the user's question.

USER QUESTION: {user_query}

GENERATED SQL:
{sql}

DATABASE SCHEMA:
{self.schema_context}

Rate confidence from 0-100 based on:
- Does SQL syntax look correct?
- Does it properly reference tables/columns?
- Does it address the question's intent?
- Are WHERE/JOIN/GROUP BY clauses appropriate?

Respond with ONLY the number: XX
"""
            
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': 'You are a SQL expert. Rate query confidence objectively.'},
                    {'role': 'user', 'content': prompt}
                ],
                options={'temperature': 0.1}
            )
            
            # Extract confidence score
            result_text = response['message']['content']
            score_match = re.search(r'\b(\d{1,3})\b', result_text)
            
            if score_match:
                confidence = int(score_match.group(1))
                return max(0, min(100, confidence))  # Clamp to 0-100
            else:
                return 50  # Default confidence if parsing fails
                
        except Exception as e:
            print(f"❌ Confidence scoring failed: {e}")
            return 50  # Fallback confidence
    
    def diagnose_error(self, user_query: str, sql: str, error_message: str) -> str:
        """
        Diagnose root cause of SQL execution error.
        
        Args:
            user_query: Original question
            sql: Failed SQL query
            error_message: Error from database
            
        Returns:
            str: Root cause diagnosis
        """
        try:
            prompt = f"""Diagnose why this SQL query failed and identify the root cause.

USER QUESTION: {user_query}

FAILED SQL:
{sql}

DATABASE SCHEMA:
{self.schema_context}

ERROR MESSAGE:
{error_message}

Analyze the error and identify exactly what needs to be fixed. Respond with ONE sentence diagnosis.

Diagnosis:"""
            
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': 'You are a SQL debugging expert. Identify root causes of SQL errors.'},
                    {'role': 'user', 'content': prompt}
                ],
                options={'temperature': 0.3}
            )
            
            diagnosis = response['message']['content'].strip()
            return diagnosis
            
        except Exception as e:
            return f"Diagnosis failed: {e}"
    
    def generate_safe_sql(self, user_query: str, previous_sql: Optional[str] = None, 
                         error_message: Optional[str] = None, diagnosis: Optional[str] = None) -> str:
        """
        Generate SQL query from natural language using Ollama.
        
        Args:
            user_query: Natural language question
            previous_sql: Previously generated SQL
            error_message: Error from previous attempt
            diagnosis: Root cause diagnosis if available
            
        Returns:
            str: Generated SQL query
        """
        # Build prompt
        if previous_sql and error_message:
            # Smart self-healing prompt with diagnosis
            prompt = self._build_healing_prompt(user_query, previous_sql, error_message, diagnosis)
        else:
            # Advanced initial generation prompt
            prompt = self._build_advanced_prompt(user_query)
        
        try:
            # Call Ollama
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': '''You are a SQL Server T-SQL expert with 15+ years experience.

KEY RULES:
- Generate ONLY valid T-SQL for SQL Server
- Use TOP instead of LIMIT for row limiting
- Always use table aliases for clarity
- Use square brackets for identifiers
- Include WHERE/JOIN/GROUP BY/ORDER BY as needed
- Always add TOP 1000 to prevent huge result sets
- Return ONLY the SQL code, no explanations

EXAMPLES OF GOOD QUERIES:
- "SELECT TOP 100 [ClientName], SUM([ShipmentWeight]) AS TotalWeight FROM [Shipments] s GROUP BY [ClientName] ORDER BY TotalWeight DESC"
- "SELECT TOP 50 [OrderID], [ShipDate], [Status] FROM [Orders] o WHERE [ShipDate] >= '2024-01-01' ORDER BY [ShipDate] DESC"
- "SELECT TOP 20 [Category], AVG([Price]) AS AvgPrice FROM [Products] p GROUP BY [Category] HAVING AVG([Price]) > 100"
'''
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.1,
                }
            )
            
            # Extract SQL from response
            sql = self._extract_sql(response['message']['content'])
            print(f"🤖 Generated SQL: {sql[:100]}...")
            return sql
            
        except Exception as e:
            print(f"❌ LLM generation failed: {e}")
            raise
    
    def _build_advanced_prompt(self, user_query: str) -> str:
        """Build advanced SQL generation prompt with enhanced context."""
        return f"""Given the database schema below, write a precise SQL Server T-SQL query.

DATABASE SCHEMA:
{self.schema_context}

USER QUESTION:
{user_query}

Generate a SQL query that:
- Uses proper T-SQL syntax (SQL Server)
- Uses square brackets for identifiers
- Includes table aliases
- Includes TOP 1000 to limit results
- Is syntactically correct

Return ONLY the SQL query (no explanations or markdown).

SQL Query:"""
    
    def _build_healing_prompt(self, user_query: str, previous_sql: str, 
                              error_message: str, diagnosis: str) -> str:
        """Build smart self-healing prompt with diagnosis context."""
        return f"""The previous SQL query failed. Here's the diagnosis: {diagnosis}

DATABASE SCHEMA:
{self.schema_context}

ORIGINAL USER QUESTION:
{user_query}

PREVIOUS SQL QUERY (FAILED):
{previous_sql}

ERROR MESSAGE:
{error_message}

Based on the diagnosis, generate a corrected SQL query that fixes this specific issue.

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
        for separator in ['\n\nThis query', '\n\nExplanation', '\n\nNote:']:
            if separator in sql:
                sql = sql.split(separator)[0].strip()
        
        return sql
    
    def validate_sql_safety(self, sql: str) -> bool:
        """
        Check if SQL query contains destructive operations.
        """
        sql_upper = sql.upper()
        
        for keyword in self.DESTRUCTIVE_KEYWORDS:
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                raise SafetyViolationError(
                    f"🚫 SAFETY VIOLATION: Query contains destructive keyword '{keyword}'. "
                    f"This agent is read-only and cannot execute write operations."
                )
        
        return True
    
    def execute_with_retry(self, user_query: str, max_retries: int = 3) -> Tuple[pd.DataFrame, str]:
        """
        Execute query with advanced self-healing retry logic.
        
        Returns:
            Tuple[pd.DataFrame, str]: Query results and final SQL used
        """
        
        print(f"\n🧠 Analyzing query complexity...")
        decomposition_plan = self.decompose_query(user_query)
        
        if decomposition_plan.get('requires_decomposition'):
            print(f"🔍 Query flagged as {decomposition_plan['complexity_level']} complexity")
            print(f"📋 Decomposition plan: {decomposition_plan['reason']}")
            
            if decomposition_plan.get('sub_queries'):
                print(f"📝 Sub-queries planned: {len(decomposition_plan['sub_queries'])}")
            
            self.query_decomposition_strategy = decomposition_plan
        else:
            print(f"✅ Query appears simple, proceeding directly")
        
        # Original retry logic with enhancements
        previous_sql = None
        error_message = None
        diagnosis = None
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"\n🔄 Attempt {attempt}/{max_retries}:")
                
                # Generate SQL
                sql = self.generate_safe_sql(user_query, previous_sql, error_message, diagnosis)
                
                # Score confidence
                confidence = self.score_confidence(sql, user_query)
                print(f"🎯 Confidence: {confidence}/100")
                
                # Low confidence - trigger immediate refinement
                if confidence < 60:
                    print("⚠️  Low confidence, attempting refinement...")
                    sql = self.generate_safe_sql(user_query, sql, "Confidence below threshold", 
                                                 "Low confidence score indicates potential issues")
                    confidence = self.score_confidence(sql, user_query)
                    print(f"🎯 Refined confidence: {confidence}/100")
                
                # Validate safety
                self.validate_sql_safety(sql)
                
                # Validate against schema
                try:
                    self.validate_against_schema(sql)
                    print("✅ Schema validation passed")
                except SchemaValidationError as ve:
                    print(f"⚠️  Schema validation warning: {ve}")
                    # Continue anyway but warn user
                
                # Execute query
                print(f"⚡ Executing query...")
                df = self.db_manager.execute_query(sql)
                
                print(f"✅ Success on attempt {attempt}!")
                return df, sql
                
            except SafetyViolationError as e:
                # Safety violations should not be retried
                print(str(e))
                raise
                
            except SchemaValidationError as e:
                # Schema validation errors get smart healing
                print(f"❌ Schema validation error: {str(e)}")
                error_message = str(e)
                diagnosis = f"Schema mismatch: {str(e)}"
                previous_sql = sql if 'sql' in locals() else None
                
            except Exception as e:
                error_message = str(e)
                previous_sql = sql if 'sql' in locals() else None
                
                # Diagnose the error
                if error_message and previous_sql:
                    diagnosis = self.diagnose_error(user_query, previous_sql, error_message)
                    print(f"🔍 Diagnosis: {diagnosis}")
                else:
                    diagnosis = "Unable to diagnose error"
                
                print(f"❌ Attempt {attempt} failed: {error_message}")
                
                if attempt == max_retries:
                    print(f"\n💥 All {max_retries} attempts failed.")
                    raise Exception(f"Failed after {max_retries} attempts. Last error: {error_message}")
                
                print(f"🔧 Attempting smart self-healing (retry {attempt + 1}/{max_retries})...")