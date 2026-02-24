"""
Structured Schema Builder for SQL Agent
Builds rich schema context with table metadata and sample values.
"""

import pyodbc
from typing import Dict, List, Any
import re


class SchemaBuilder:
    """Builds detailed structured schema context for LLM SQL generation."""
    
    def __init__(self, db_connection: str):
        """
        Initialize schema builder with database connection.
        
        Args:
            db_connection: Database connection string
        """
        self.db_connection = db_connection
        
    def get_structured_schema(self) -> str:
        """
        Build comprehensive structured schema with metadata and sample values.
        
        Returns:
            str: Formatted schema context optimized for LLM prompts
        """
        try:
            # Connect to database
            conn = pyodbc.connect(self.db_connection)
            cursor = conn.cursor()
            
            schema_context = []
            schema_context.append("# DATABASE SCHEMA DETAILS")
            schema_context.append("")
            
            # Get all user tables
            tables_query = """
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE' 
                ORDER BY TABLE_NAME
            """
            
            cursor.execute(tables_query)
            tables = [row[0] for row in cursor.fetchall()]
            
            for table_name in tables:
                schema_context.append(f"## TABLE: [{table_name}]")
                schema_context.append("")
                
                # Get column details
                columns_query = f"""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE,
                        CHARACTER_MAXIMUM_LENGTH
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                """
                
                cursor.execute(columns_query, (table_name,))
                columns = cursor.fetchall()
                
                column_details = []
                for col_name, data_type, is_nullable, max_length in columns:
                    nullable_str = "NULL" if is_nullable == "YES" else "NOT NULL"
                    max_len_str = f"({max_length})" if max_length else ""
                    column_details.append(
                        f"  - {col_name}: {data_type}{max_len_str} {nullable_str}"
                    )
                
                schema_context.extend(column_details)
                schema_context.append("")
                
                # Get sample values for each column
                schema_context.append("  Sample values:")
                
                for col_name, data_type, is_nullable, max_length in columns:
                    try:
                        # Skip binary/image data types
                        if any(bad_type in data_type.upper() for bad_type in ['BINARY', 'IMAGE', 'VARBINARY']):
                            continue
                        
                        sample_query = f"SELECT DISTINCT TOP 3 [{col_name}] FROM [{table_name}] WHERE [{col_name}] IS NOT NULL"
                        cursor.execute(sample_query)
                        samples = cursor.fetchall()
                        
                        if samples:
                            sample_values = [str(row[0])[:50] for row in samples]  # Truncate long values
                            schema_context.append(f"    - {col_name}: {', '.join(sample_values)}")
                        else:
                            schema_context.append(f"    - {col_name}: (no data)")
                            
                    except Exception as col_err:
                        # Skip columns that can't be sampled
                        schema_context.append(f"    - {col_name}: (unable to sample)")
                
                # Get primary keys
                pk_query = f"""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE TABLE_NAME = ? AND CONSTRAINT_NAME LIKE '%PRIMARY%'
                """
                cursor.execute(pk_query, (table_name,))
                pk_columns = [row[0] for row in cursor.fetchall()]
                
                if pk_columns:
                    schema_context.append(f"")
                    schema_context.append(f"  Primary key(s): {', '.join(pk_columns)}")
                
                # Get foreign keys
                fk_query = f"""
                    SELECT 
                        COLUMN_NAME,
                        REFERENCED_TABLE_NAME,
                        REFERENCED_COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_NAME = ? 
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """
                cursor.execute(fk_query, (table_name,))
                fk_info = cursor.fetchall()
                
                if fk_info:
                    schema_context.append(f"")
                    schema_context.append(f"  Foreign keys:")
                    for fk_col, ref_table, ref_col in fk_info:
                        schema_context.append(f"    - {fk_col} -> {ref_table}({ref_col})")
                
                schema_context.append("")
                schema_context.append("---")
                schema_context.append("")
            
            conn.close()
            return "\n".join(schema_context)
            
        except Exception as e:
            return f"Error building schema: {str(e)}"
    
    def get_schema_summary(self) -> str:
        """Get schema summary (backward compatibility)."""
        return self.get_structured_schema()