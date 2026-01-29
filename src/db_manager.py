"""
Database Manager for BackupDB SQL Agent
Handles SQL Server connection, schema extraction, and query execution.
"""

import pyodbc
import pandas as pd
from sqlalchemy import create_engine, text
from typing import Optional
import urllib
import warnings

# Suppress SQLAlchemy warnings about SQL Server version
warnings.filterwarnings('ignore', message='.*Unrecognized server version info.*')


class DatabaseManager:
    """Manages database connections and operations for the SQL Agent."""
    
    def __init__(self, connection_string: str):
        """
        Initialize the database manager.
        
        Args:
            connection_string: ODBC connection string for SQL Server
        """
        self.connection_string = connection_string
        self.engine = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Create SQLAlchemy engine with connection pooling."""
        try:
            # Convert ODBC connection string to SQLAlchemy format
            params = urllib.parse.quote_plus(self.connection_string)
            sqlalchemy_url = f"mssql+pyodbc:///?odbc_connect={params}"
            
            # Create engine with connection pooling
            self.engine = create_engine(
                sqlalchemy_url,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=5,
                max_overflow=10
            )
            print("✅ Database engine initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize database engine: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            print("✅ Database connection test successful")
            return True
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False
    
    def get_schema_summary(self) -> str:
        """
        Extract database schema information from INFORMATION_SCHEMA.
        
        Returns:
            str: Formatted schema summary with tables and columns
        """
        try:
            query = """
            SELECT 
                t.TABLE_SCHEMA,
                t.TABLE_NAME,
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.IS_NULLABLE,
                c.CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.TABLES t
            INNER JOIN INFORMATION_SCHEMA.COLUMNS c 
                ON t.TABLE_NAME = c.TABLE_NAME 
                AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
            WHERE t.TABLE_TYPE = 'BASE TABLE'
            ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION
            """
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn)
            
            # Format schema summary
            schema_summary = []
            schema_summary.append("=" * 80)
            schema_summary.append("DATABASE SCHEMA SUMMARY - BackupDB")
            schema_summary.append("=" * 80)
            schema_summary.append("")
            
            # Group by table
            for (schema, table), group in df.groupby(['TABLE_SCHEMA', 'TABLE_NAME']):
                schema_summary.append(f"📊 Table: [{schema}].[{table}]")
                schema_summary.append("   Columns:")
                
                for _, row in group.iterrows():
                    col_name = row['COLUMN_NAME']
                    data_type = row['DATA_TYPE']
                    nullable = "NULL" if row['IS_NULLABLE'] == 'YES' else "NOT NULL"
                    
                    # Add length for string types
                    if row['CHARACTER_MAXIMUM_LENGTH'] and pd.notna(row['CHARACTER_MAXIMUM_LENGTH']):
                        data_type = f"{data_type}({int(row['CHARACTER_MAXIMUM_LENGTH'])})"
                    
                    schema_summary.append(f"      - {col_name}: {data_type} {nullable}")
                
                schema_summary.append("")
            
            # Add statistics
            total_tables = df[['TABLE_SCHEMA', 'TABLE_NAME']].drop_duplicates().shape[0]
            total_columns = len(df)
            schema_summary.append("=" * 80)
            schema_summary.append(f"📈 Total Tables: {total_tables} | Total Columns: {total_columns}")
            schema_summary.append("=" * 80)
            
            result = "\n".join(schema_summary)
            print(f"✅ Schema extracted: {total_tables} tables, {total_columns} columns")
            return result
            
        except Exception as e:
            print(f"❌ Failed to extract schema: {e}")
            raise
    
    def execute_query(self, sql: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a DataFrame.
        
        Args:
            sql: SQL query string (SELECT only)
            
        Returns:
            pd.DataFrame: Query results
            
        Raises:
            Exception: If query execution fails
        """
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)
            
            print(f"✅ Query executed successfully: {len(df)} rows returned")
            return df
            
        except Exception as e:
            # Extract specific SQL Server error message
            error_msg = str(e)
            print(f"❌ Query execution failed: {error_msg}")
            raise Exception(f"SQL Error: {error_msg}")
    
    def close(self):
        """Clean up database connections."""
        if self.engine:
            self.engine.dispose()
            print("✅ Database connections closed")
