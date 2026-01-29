"""
Query Suggester for SQL Agent
Provides AI-powered follow-up question suggestions.
"""

from typing import List, Dict
import pandas as pd


class QuerySuggester:
    """Generates smart query suggestions based on context."""
    
    def __init__(self):
        """Initialize query suggester."""
        pass
    
    def suggest_followups(self, user_query: str, df: pd.DataFrame, 
                         sql: str) -> List[str]:
        """
        Suggest follow-up questions based on current query and results.
        
        Args:
            user_query: Original user question
            df: Query results
            sql: Generated SQL
            
        Returns:
            List of suggested questions
        """
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
    
    def suggest_templates(self) -> List[Dict[str, str]]:
        """Suggest query templates."""
        return [
            {
                "category": "Analysis",
                "suggestions": [
                    "Show me top N records by column",
                    "Compare metrics across groups",
                    "Analyze trends over time"
                ]
            },
            {
                "category": "Filtering",
                "suggestions": [
                    "Filter by date range",
                    "Find records matching criteria",
                    "Show only distinct values"
                ]
            },
            {
                "category": "Aggregation",
                "suggestions": [
                    "Calculate sum/average/count",
                    "Group by category",
                    "Find min/max values"
                ]
            }
        ]
