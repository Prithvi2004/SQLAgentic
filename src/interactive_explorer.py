"""
Simple Interactive Data Explorer
Provides drill-down capabilities without writing SQL.
"""

import pandas as pd
from typing import List, Dict, Optional, Tuple


class InteractiveExplorer:
    """Interactive data exploration without SQL."""
    
    def __init__(self):
        """Initialize explorer."""
        self.current_data = None
        self.filter_history = []
    
    def load_data(self, df: pd.DataFrame):
        """Load data for exploration."""
        self.current_data = df.copy()
        self.filter_history = []
    
    def get_column_info(self) -> Dict:
        """Get information about available columns."""
        if self.current_data is None:
            return {}
        
        info = {}
        for col in self.current_data.columns:
            dtype = str(self.current_data[col].dtype)
            unique_count = self.current_data[col].nunique()
            null_count = self.current_data[col].isnull().sum()
            
            info[col] = {
                "type": dtype,
                "unique_values": unique_count,
                "null_count": null_count,
                "sample_values": self.current_data[col].dropna().head(5).tolist()
            }
        
        return info
    
    def filter_by_value(self, column: str, value) -> pd.DataFrame:
        """Filter data by column value."""
        if self.current_data is None:
            return None
        
        filtered = self.current_data[self.current_data[column] == value]
        self.filter_history.append(f"{column} = {value}")
        return filtered
    
    def filter_by_range(self, column: str, min_val, max_val) -> pd.DataFrame:
        """Filter numeric column by range."""
        if self.current_data is None:
            return None
        
        filtered = self.current_data[
            (self.current_data[column] >= min_val) & 
            (self.current_data[column] <= max_val)
        ]
        self.filter_history.append(f"{column} between {min_val} and {max_val}")
        return filtered
    
    def group_and_aggregate(self, group_by: str, agg_column: str, 
                           agg_func: str = 'sum') -> pd.DataFrame:
        """Group data and aggregate."""
        if self.current_data is None:
            return None
        
        result = self.current_data.groupby(group_by)[agg_column].agg(agg_func).reset_index()
        result.columns = [group_by, f"{agg_func}_{agg_column}"]
        return result
    
    def get_top_n(self, column: str, n: int = 10, ascending: bool = False) -> pd.DataFrame:
        """Get top N records by column."""
        if self.current_data is None:
            return None
        
        return self.current_data.nlargest(n, column) if not ascending else \
               self.current_data.nsmallest(n, column)
    
    def get_unique_values(self, column: str) -> List:
        """Get unique values from column."""
        if self.current_data is None:
            return []
        
        return self.current_data[column].unique().tolist()
    
    def pivot_table(self, index: str, columns: str, values: str, 
                   aggfunc: str = 'sum') -> pd.DataFrame:
        """Create pivot table."""
        if self.current_data is None:
            return None
        
        return pd.pivot_table(
            self.current_data,
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc,
            fill_value=0
        )
    
    def reset_filters(self):
        """Reset all filters."""
        self.filter_history = []
    
    def get_filter_summary(self) -> str:
        """Get summary of applied filters."""
        if not self.filter_history:
            return "No filters applied"
        
        return "Filters: " + " AND ".join(self.filter_history)
