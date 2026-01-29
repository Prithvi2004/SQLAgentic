"""
Query Template Manager for SQL Agent
Provides pre-built query templates for common analysis tasks.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import re


class TemplateManager:
    """Manages query templates for common tasks."""
    
    def __init__(self, templates_file: str = "templates/query_templates.json"):
        """Initialize template manager."""
        self.templates_file = Path(templates_file)
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load templates from JSON file."""
        if not self.templates_file.exists():
            # Create default templates
            default_templates = self._get_default_templates()
            self.templates_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.templates_file, 'w') as f:
                json.dump(default_templates, f, indent=2)
            return default_templates
        
        with open(self.templates_file, 'r') as f:
            return json.load(f)
    
    def _get_default_templates(self) -> Dict:
        """Get default query templates."""
        return {
            "top_n": {
                "name": "Top N Records",
                "description": "Get top N records sorted by a column",
                "template": "Show me the top {n} {table} records sorted by {column} {order}",
                "variables": ["n", "table", "column", "order"],
                "example": "Show me the top 10 shipment records sorted by date descending"
            },
            "date_range": {
                "name": "Date Range Analysis",
                "description": "Filter records by date range",
                "template": "Show me {table} records from {start_date} to {end_date}",
                "variables": ["table", "start_date", "end_date"],
                "example": "Show me shipment records from 2026-01-01 to 2026-01-31"
            },
            "aggregation": {
                "name": "Group By Aggregation",
                "description": "Aggregate data by group",
                "template": "Show me the {aggregation} of {column} grouped by {group_column} for {table}",
                "variables": ["aggregation", "column", "group_column", "table"],
                "example": "Show me the sum of weight grouped by client for shipments"
            },
            "join_tables": {
                "name": "Join Multiple Tables",
                "description": "Join two or more tables",
                "template": "Show me data from {table1} joined with {table2} on {join_column}",
                "variables": ["table1", "table2", "join_column"],
                "example": "Show me data from shipments joined with clients on client_id"
            },
            "trend_analysis": {
                "name": "Trend Over Time",
                "description": "Analyze trends over time periods",
                "template": "Show me the trend of {metric} over {time_period} for {table}",
                "variables": ["metric", "time_period", "table"],
                "example": "Show me the trend of shipment count over months for shipments"
            },
            "distinct_values": {
                "name": "Distinct Values",
                "description": "Get unique values from a column",
                "template": "Show me all distinct {column} values from {table}",
                "variables": ["column", "table"],
                "example": "Show me all distinct status values from shipments"
            },
            "count_by_group": {
                "name": "Count by Group",
                "description": "Count records by category",
                "template": "Count {table} records by {group_column}",
                "variables": ["table", "group_column"],
                "example": "Count shipment records by status"
            },
            "recent_records": {
                "name": "Recent Records",
                "description": "Get most recent records",
                "template": "Show me the most recent {n} {table} records",
                "variables": ["n", "table"],
                "example": "Show me the most recent 20 shipment records"
            }
        }
    
    def list_templates(self) -> List[Dict]:
        """List all available templates."""
        return [
            {
                "id": key,
                "name": value["name"],
                "description": value["description"],
                "example": value["example"]
            }
            for key, value in self.templates.items()
        ]
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get a specific template."""
        return self.templates.get(template_id)
    
    def apply_template(self, template_id: str, **variables) -> str:
        """Apply variables to a template."""
        template = self.templates.get(template_id)
        if not template:
            return None
        
        query = template["template"]
        for var, value in variables.items():
            query = query.replace(f"{{{var}}}", str(value))
        
        return query
    
    def save_custom_template(self, template_id: str, name: str, 
                            description: str, template: str, 
                            variables: List[str], example: str):
        """Save a custom template."""
        self.templates[template_id] = {
            "name": name,
            "description": description,
            "template": template,
            "variables": variables,
            "example": example
        }
        
        with open(self.templates_file, 'w') as f:
            json.dump(self.templates, f, indent=2)
