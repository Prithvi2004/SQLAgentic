"""
Query History Manager for SQL Agent
Tracks all queries with SQLite backend for search, replay, and favorites.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd


class QueryHistory:
    """Manages query history with SQLite database."""
    
    def __init__(self, db_path: str = ".agent/history/queries.db"):
        """
        Initialize query history manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create queries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_query TEXT NOT NULL,
                generated_sql TEXT NOT NULL,
                rows_returned INTEGER,
                execution_time_ms REAL,
                is_favorite INTEGER DEFAULT 0,
                tags TEXT,
                notes TEXT,
                result_folder TEXT
            )
        """)
        
        # Create index for faster searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON queries(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_favorite 
            ON queries(is_favorite)
        """)
        
        conn.commit()
        conn.close()
    
    def add_query(self, user_query: str, generated_sql: str, 
                  rows_returned: int, execution_time_ms: float,
                  result_folder: str = None) -> int:
        """
        Add a query to history.
        
        Args:
            user_query: Original natural language query
            generated_sql: Generated SQL query
            rows_returned: Number of rows in result
            execution_time_ms: Query execution time in milliseconds
            result_folder: Path to results folder
            
        Returns:
            int: Query ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO queries 
            (timestamp, user_query, generated_sql, rows_returned, 
             execution_time_ms, result_folder)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, user_query, generated_sql, rows_returned, 
              execution_time_ms, result_folder))
        
        query_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return query_id
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """
        Get recent queries.
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of query dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM queries 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def search(self, keyword: str = None, 
               start_date: str = None, 
               end_date: str = None,
               favorites_only: bool = False) -> List[Dict]:
        """
        Search query history.
        
        Args:
            keyword: Search term (searches in user_query and generated_sql)
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            favorites_only: Only return favorited queries
            
        Returns:
            List of matching query dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM queries WHERE 1=1"
        params = []
        
        if keyword:
            query += " AND (user_query LIKE ? OR generated_sql LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        if favorites_only:
            query += " AND is_favorite = 1"
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_by_id(self, query_id: int) -> Optional[Dict]:
        """
        Get a specific query by ID.
        
        Args:
            query_id: Query ID
            
        Returns:
            Query dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM queries WHERE id = ?", (query_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def toggle_favorite(self, query_id: int) -> bool:
        """
        Toggle favorite status of a query.
        
        Args:
            query_id: Query ID
            
        Returns:
            bool: New favorite status
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current status
        cursor.execute("SELECT is_favorite FROM queries WHERE id = ?", (query_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return False
        
        new_status = 0 if row[0] else 1
        
        cursor.execute("""
            UPDATE queries 
            SET is_favorite = ? 
            WHERE id = ?
        """, (new_status, query_id))
        
        conn.commit()
        conn.close()
        
        return bool(new_status)
    
    def add_note(self, query_id: int, note: str):
        """
        Add a note to a query.
        
        Args:
            query_id: Query ID
            note: Note text
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE queries 
            SET notes = ? 
            WHERE id = ?
        """, (note, query_id))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self) -> Dict:
        """
        Get history statistics.
        
        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total queries
        cursor.execute("SELECT COUNT(*) FROM queries")
        stats['total_queries'] = cursor.fetchone()[0]
        
        # Favorites count
        cursor.execute("SELECT COUNT(*) FROM queries WHERE is_favorite = 1")
        stats['favorites'] = cursor.fetchone()[0]
        
        # Average execution time
        cursor.execute("SELECT AVG(execution_time_ms) FROM queries")
        avg_time = cursor.fetchone()[0]
        stats['avg_execution_time_ms'] = round(avg_time, 2) if avg_time else 0
        
        # Total rows returned
        cursor.execute("SELECT SUM(rows_returned) FROM queries")
        total_rows = cursor.fetchone()[0]
        stats['total_rows_returned'] = total_rows if total_rows else 0
        
        # Most recent query
        cursor.execute("SELECT timestamp FROM queries ORDER BY timestamp DESC LIMIT 1")
        recent = cursor.fetchone()
        stats['last_query'] = recent[0] if recent else None
        
        conn.close()
        
        return stats
    
    def export_history(self, output_path: str, format: str = 'csv'):
        """
        Export query history to file.
        
        Args:
            output_path: Output file path
            format: Export format ('csv' or 'json')
        """
        conn = sqlite3.connect(self.db_path)
        
        if format == 'csv':
            df = pd.read_sql_query("SELECT * FROM queries ORDER BY timestamp DESC", conn)
            df.to_csv(output_path, index=False)
        elif format == 'json':
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM queries ORDER BY timestamp DESC")
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
        
        conn.close()
    
    def clear_history(self, keep_favorites: bool = True):
        """
        Clear query history.
        
        Args:
            keep_favorites: If True, keep favorited queries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if keep_favorites:
            cursor.execute("DELETE FROM queries WHERE is_favorite = 0")
        else:
            cursor.execute("DELETE FROM queries")
        
        conn.commit()
        conn.close()
