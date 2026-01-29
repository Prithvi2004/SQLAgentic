"""
Visualization Engine for SQL Agent
Automatically generates charts based on query results.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import warnings


class ChartGenerator:
    """Automatically generates visualizations from query results."""
    
    def __init__(self, artifacts_dir: str = "artifacts"):
        """
        Initialize the chart generator.
        
        Args:
            artifacts_dir: Directory to save generated charts
        """
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(exist_ok=True)
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8-darkgrid')
        print(f"✅ Chart generator initialized: {self.artifacts_dir}")
    
    def detect_chart_type(self, df: pd.DataFrame) -> Optional[Tuple[str, str, str]]:
        """
        Analyze DataFrame to determine appropriate chart type.
        
        Args:
            df: Query result DataFrame
            
        Returns:
            Optional[Tuple[str, str, str]]: (chart_type, x_column, y_column) or None
        """
        if df.empty or len(df.columns) < 2:
            return None
        
        # Look for date/datetime columns
        date_cols = []
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_cols.append(col)
            elif df[col].dtype == 'object':
                # Try to parse as date
                try:
                    # Suppress UserWarning about datetime format
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        pd.to_datetime(df[col].head(), errors='raise')
                    date_cols.append(col)
                except:
                    pass
        
        # Look for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Look for categorical columns
        categorical_cols = []
        for col in df.columns:
            if col not in date_cols and col not in numeric_cols:
                # Consider it categorical if it has reasonable number of unique values
                if df[col].nunique() <= 20:
                    categorical_cols.append(col)
        
        # Decision logic
        if date_cols and numeric_cols:
            # Time series: line chart
            return ('line', date_cols[0], numeric_cols[0])
        
        elif categorical_cols and numeric_cols:
            # Categorical data: bar chart
            return ('bar', categorical_cols[0], numeric_cols[0])
        
        elif len(numeric_cols) >= 2:
            # Two numeric columns: scatter plot
            return ('scatter', numeric_cols[0], numeric_cols[1])
        
        return None
    
    def generate_line_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                           output_path: Path) -> str:
        """
        Generate a line chart for time-series data.
        
        Args:
            df: DataFrame with data
            x_col: Column name for x-axis (date/time)
            y_col: Column name for y-axis (numeric)
            output_path: Path to save the chart
            
        Returns:
            str: Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Convert x column to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df[x_col]):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df[x_col] = pd.to_datetime(df[x_col])
        
        # Sort by date
        df_sorted = df.sort_values(x_col)
        
        # Plot
        ax.plot(df_sorted[x_col], df_sorted[y_col], 
                marker='o', linewidth=2, markersize=6, color='#2E86AB')
        
        # Formatting
        ax.set_xlabel(x_col, fontsize=12, fontweight='bold')
        ax.set_ylabel(y_col, fontsize=12, fontweight='bold')
        ax.set_title(f'{y_col} Over Time', fontsize=14, fontweight='bold', pad=20)
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45, ha='right')
        
        # Grid
        ax.grid(True, alpha=0.3)
        
        # Tight layout
        plt.tight_layout()
        
        # Save
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def generate_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                          output_path: Path) -> str:
        """
        Generate a bar chart for categorical data.
        
        Args:
            df: DataFrame with data
            x_col: Column name for x-axis (categorical)
            y_col: Column name for y-axis (numeric)
            output_path: Path to save the chart
            
        Returns:
            str: Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Sort by y value descending
        df_sorted = df.sort_values(y_col, ascending=False)
        
        # Limit to top 20 categories if too many
        if len(df_sorted) > 20:
            df_sorted = df_sorted.head(20)
            title_suffix = " (Top 20)"
        else:
            title_suffix = ""
        
        # Plot
        bars = ax.bar(range(len(df_sorted)), df_sorted[y_col], color='#A23B72')
        
        # Formatting
        ax.set_xlabel(x_col, fontsize=12, fontweight='bold')
        ax.set_ylabel(y_col, fontsize=12, fontweight='bold')
        ax.set_title(f'{y_col} by {x_col}{title_suffix}', fontsize=14, fontweight='bold', pad=20)
        
        # Set x-axis labels
        ax.set_xticks(range(len(df_sorted)))
        ax.set_xticklabels(df_sorted[x_col], rotation=45, ha='right')
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:,.0f}',
                   ha='center', va='bottom', fontsize=9)
        
        # Grid
        ax.grid(True, alpha=0.3, axis='y')
        
        # Tight layout
        plt.tight_layout()
        
        # Save
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def generate_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str, 
                             output_path: Path) -> str:
        """
        Generate a scatter plot for two numeric variables.
        
        Args:
            df: DataFrame with data
            x_col: Column name for x-axis
            y_col: Column name for y-axis
            output_path: Path to save the chart
            
        Returns:
            str: Path to saved chart
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plot
        ax.scatter(df[x_col], df[y_col], alpha=0.6, s=50, color='#F18F01')
        
        # Formatting
        ax.set_xlabel(x_col, fontsize=12, fontweight='bold')
        ax.set_ylabel(y_col, fontsize=12, fontweight='bold')
        ax.set_title(f'{y_col} vs {x_col}', fontsize=14, fontweight='bold', pad=20)
        
        # Grid
        ax.grid(True, alpha=0.3)
        
        # Tight layout
        plt.tight_layout()
        
        # Save
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def auto_visualize(self, df: pd.DataFrame, query: str = "") -> Optional[str]:
        """
        Automatically detect chart type and generate visualization.
        
        Args:
            df: Query result DataFrame
            query: Original user query (for context)
            
        Returns:
            Optional[str]: Path to saved chart, or None if no chart generated
        """
        # Detect chart type
        chart_info = self.detect_chart_type(df)
        
        if not chart_info:
            print("ℹ️  No suitable visualization detected")
            return None
        
        chart_type, x_col, y_col = chart_info
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.artifacts_dir / f"chart_{chart_type}_{timestamp}.png"
        
        # Generate appropriate chart
        try:
            if chart_type == 'line':
                print(f"📈 Generating line chart: {y_col} over {x_col}")
                chart_path = self.generate_line_chart(df, x_col, y_col, output_path)
            
            elif chart_type == 'bar':
                print(f"📊 Generating bar chart: {y_col} by {x_col}")
                chart_path = self.generate_bar_chart(df, x_col, y_col, output_path)
            
            elif chart_type == 'scatter':
                print(f"🔵 Generating scatter plot: {y_col} vs {x_col}")
                chart_path = self.generate_scatter_plot(df, x_col, y_col, output_path)
            
            else:
                return None
            
            print(f"✅ Chart saved: {chart_path}")
            return chart_path
            
        except Exception as e:
            print(f"❌ Failed to generate chart: {e}")
            return None
