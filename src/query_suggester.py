"""
Advanced Query Suggester for SQL Agent
Provides LLM-powered follow-up question suggestions.
"""

from typing import List
import pandas as pd
import ollama
import re


class QuerySuggester:
    """Generates smart query suggestions based on context."""
    
    def __init__(self, base_url: str = "http://localhost:11434", 
                 model_name: str = "deepseek-v3.1:671b-cloud"):
        """Initialize query suggester with LLM."""
        self.base_url = base_url
        self.model_name = model_name
        self.client = ollama.Client(host=base_url)
    
    def suggest_followups(self, user_query: str, df: pd.DataFrame, 
                         sql: str) -> List[str]:
        """
        Suggest smart follow-up questions using LLM.
        
        Args:
            user_query: Original user question
            df: Query results
            sql: Generated SQL
            
        Returns:
            List of suggested questions
        """
        # Try LLM-driven suggestions first
        llm_suggestions = self._get_llm_suggestions(user_query, df)
        if llm_suggestions:
            return llm_suggestions
        
        # Fall back to rule-based suggestions
        return self._get_rule_based_suggestions(user_query, df, sql)
    
    def _get_llm_suggestions(self, user_query: str, df: pd.DataFrame) -> List[str]:
        """Get LLM-powered smart suggestions."""
        try:
            # Build result summary
            column_names = list(df.columns)
            row_count = len(df)
            
            if row_count > 0:
                sample_row = df.iloc[0].to_dict()
                sample_repr = {k: str(v)[:50] for k, v in sample_row.items()}  # Truncate values
            else:
                sample_repr = {}
            
            prompt = f"""Given a user's SQL query and its results, suggest 3 smart follow-up questions.

ORIGINAL QUESTION: {user_query}

QUERY RESULTS SUMMARY:
- Columns: {column_names}
- Number of rows: {row_count}
- Sample row: {sample_repr}

Suggest 3 insightful follow-up questions that a data analyst would ask next.
Focus on:
- Deeper analysis (trends, patterns, correlations)
- Comparison to other data
- Specific filtering or aggregation
- Time-based analysis
- Quality checks or anomalies

Format as a numbered list:
1. First suggestion
2. Second suggestion
3. Third suggestion
"""
            
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': 'You are a data analysis expert. Suggest insightful follow-up questions based on SQL query results.'},
                    {'role': 'user', 'content': prompt}
                ],
                options={'temperature': 0.4}
            )
            
            suggestions_text = response['message']['content']
            
            # Extract numbered list
            suggestions = []
            for line in suggestions_text.split('\n'):
                # Match numbered items
                match = re.match(r'^\s*\d+\.\s*(.+)', line)
                if match:
                    suggestion = match.group(1).strip()
                    if suggestion:
                        suggestions.append(suggestion)
            
            # Return top 3 suggestions
            return suggestions[:3] if suggestions else []
            
        except Exception as e:
            print(f"⚠️  LLM suggestions failed, using rule-based fallback: {e}")
            return []  # Empty triggers fallback
    
    def _get_rule_based_suggestions(self, user_query: str, df: pd.DataFrame, 
                                   sql: str) -> List[str]:
        """Fallback to rule-based suggestions."""
        suggestions = []
        
        if df.empty:
            return ["Try a different query or check your filters"]
        
        # Analyze the data structure
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        # Suggest aggregations if numeric columns exist
        if numeric_cols:
            for col in numeric_cols[:2]:  # Top 2 numeric columns
                suggestions.append(f"What is the average {col}?")
                suggestions.append(f"Show me the distribution of {col}")
        
        # Suggest time-based analysis if date columns exist
        if date_cols:
            for col in date_cols[:1]:
                suggestions.append(f"Show me trends over time using {col}")
                suggestions.append(f"What are the monthly totals?")
        
        # Suggest grouping if categorical columns exist
        if categorical_cols:
            for col in categorical_cols[:2]:
                if df[col].nunique() < 20:  # Reasonable number of categories
                    suggestions.append(f"Group results by {col}")
                    if numeric_cols:
                        suggestions.append(f"Compare {numeric_cols[0]} across different {col}")
        
        # Suggest filtering
        if len(df) > 10:
            suggestions.append("Show me only the top 10 results")
            suggestions.append("Filter these results by a specific condition")
        
        # Suggest expansion
        if len(df) < 100:
            suggestions.append("Show me more records")
        
        # Suggest related analysis
        if "shipment" in user_query.lower():
            suggestions.append("Show me shipment details with client information")
            suggestions.append("What is the status breakdown of these shipments?")
        
        # Limit to top 5 suggestions
        return suggestions[:5]
    
    def suggest_from_schema(self, schema_summary: str) -> List[str]:
        """Suggest queries based on database schema."""
        suggestions = [
            "Show me the latest 20 shipment records",
            "What are the different shipment statuses?",
            "Show me shipments grouped by client",
            "What is the total weight of all shipments?",
            "Show me shipments from the last 30 days",
            "Which clients have the most shipments?",
            "Show me shipment trends over time",
            "What is the average shipment volume?"
        ]
        
        return suggestions
    
    def suggest_templates(self) -> List[str]:
        """Suggest query templates."""
        return [
            "Show me top N records by column",
            "Compare metrics across groups",
            "Analyze trends over time"
        ]