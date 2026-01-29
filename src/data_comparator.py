"""
Data Comparator for SQL Agent
Compare query results across different time periods or conditions.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


class DataComparator:
    """Compare datasets and highlight differences."""
    
    def __init__(self):
        """Initialize data comparator."""
        self.comparison_cache = {}
    
    def compare_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame,
                          label1: str = "Current", label2: str = "Previous") -> Dict:
        """
        Compare two DataFrames and find differences.
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            label1: Label for first dataset
            label2: Label for second dataset
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            "labels": {
                "dataset1": label1,
                "dataset2": label2
            },
            "row_counts": {
                label1: len(df1),
                label2: len(df2),
                "difference": len(df1) - len(df2)
            },
            "column_comparison": self._compare_columns(df1, df2),
            "summary_comparison": {},
            "recommendations": []
        }
        
        # Compare numeric columns
        numeric_cols = set(df1.select_dtypes(include=['number']).columns) & \
                      set(df2.select_dtypes(include=['number']).columns)
        
        if numeric_cols:
            comparison["summary_comparison"] = self._compare_summaries(
                df1, df2, list(numeric_cols), label1, label2
            )
        
        # Generate recommendations
        comparison["recommendations"] = self._generate_comparison_recommendations(comparison)
        
        return comparison
    
    def _compare_columns(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Dict:
        """Compare column structures."""
        cols1 = set(df1.columns)
        cols2 = set(df2.columns)
        
        return {
            "common_columns": list(cols1 & cols2),
            "only_in_first": list(cols1 - cols2),
            "only_in_second": list(cols2 - cols1),
            "total_common": len(cols1 & cols2)
        }
    
    def _compare_summaries(self, df1: pd.DataFrame, df2: pd.DataFrame,
                          columns: List[str], label1: str, label2: str) -> Dict:
        """Compare summary statistics."""
        summaries = {}
        
        for col in columns:
            if col in df1.columns and col in df2.columns:
                sum1 = df1[col].sum()
                sum2 = df2[col].sum()
                avg1 = df1[col].mean()
                avg2 = df2[col].mean()
                
                summaries[col] = {
                    "sum": {
                        label1: float(sum1) if pd.notna(sum1) else 0,
                        label2: float(sum2) if pd.notna(sum2) else 0,
                        "change": float(sum1 - sum2) if pd.notna(sum1) and pd.notna(sum2) else 0,
                        "change_pct": ((sum1 - sum2) / sum2 * 100) if sum2 != 0 and pd.notna(sum2) else 0
                    },
                    "average": {
                        label1: float(avg1) if pd.notna(avg1) else 0,
                        label2: float(avg2) if pd.notna(avg2) else 0,
                        "change": float(avg1 - avg2) if pd.notna(avg1) and pd.notna(avg2) else 0,
                        "change_pct": ((avg1 - avg2) / avg2 * 100) if avg2 != 0 and pd.notna(avg2) else 0
                    }
                }
        
        return summaries
    
    def _generate_comparison_recommendations(self, comparison: Dict) -> List[str]:
        """Generate recommendations based on comparison."""
        recommendations = []
        
        # Check row count changes
        row_diff = comparison["row_counts"]["difference"]
        if abs(row_diff) > 0:
            change_type = "increased" if row_diff > 0 else "decreased"
            recommendations.append(f"📊 Row count {change_type} by {abs(row_diff)}")
        
        # Check for missing columns
        if comparison["column_comparison"]["only_in_first"]:
            recommendations.append(f"⚠️ Columns removed: {', '.join(comparison['column_comparison']['only_in_first'][:3])}")
        
        if comparison["column_comparison"]["only_in_second"]:
            recommendations.append(f"✨ New columns added: {', '.join(comparison['column_comparison']['only_in_second'][:3])}")
        
        # Check for significant changes in summaries
        for col, stats in comparison.get("summary_comparison", {}).items():
            sum_change_pct = abs(stats["sum"]["change_pct"])
            if sum_change_pct > 20:
                direction = "increased" if stats["sum"]["change_pct"] > 0 else "decreased"
                recommendations.append(f"📈 {col} total {direction} by {sum_change_pct:.1f}%")
        
        if not recommendations:
            recommendations.append("✅ No significant changes detected")
        
        return recommendations
    
    def format_comparison_report(self, comparison: Dict) -> str:
        """Format comparison as readable report."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("🔄 DATA COMPARISON REPORT")
        lines.append("="*80)
        
        label1 = comparison["labels"]["dataset1"]
        label2 = comparison["labels"]["dataset2"]
        
        # Row counts
        lines.append(f"\n📊 Row Counts:")
        lines.append(f"   {label1}: {comparison['row_counts'][label1]:,}")
        lines.append(f"   {label2}: {comparison['row_counts'][label2]:,}")
        lines.append(f"   Difference: {comparison['row_counts']['difference']:+,}")
        
        # Column comparison
        col_comp = comparison["column_comparison"]
        lines.append(f"\n📋 Columns:")
        lines.append(f"   Common: {col_comp['total_common']}")
        if col_comp["only_in_first"]:
            lines.append(f"   Only in {label1}: {', '.join(col_comp['only_in_first'][:5])}")
        if col_comp["only_in_second"]:
            lines.append(f"   Only in {label2}: {', '.join(col_comp['only_in_second'][:5])}")
        
        # Summary comparison
        if comparison.get("summary_comparison"):
            lines.append(f"\n📈 Metric Changes:")
            for col, stats in list(comparison["summary_comparison"].items())[:5]:
                sum_change = stats["sum"]["change_pct"]
                lines.append(f"   {col}:")
                lines.append(f"      Total: {sum_change:+.1f}%")
                lines.append(f"      Average: {stats['average']['change_pct']:+.1f}%")
        
        # Recommendations
        lines.append(f"\n💡 Key Findings:")
        for rec in comparison["recommendations"]:
            lines.append(f"   {rec}")
        
        lines.append("\n" + "="*80)
        
        return "\n".join(lines)
