"""
Data Insights Engine for SQL Agent
Automatically analyzes query results and provides statistical insights.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import Counter


class DataInsights:
    """Generates automated insights from query results."""
    
    def __init__(self):
        """Initialize the insights engine."""
        pass
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Perform comprehensive analysis on DataFrame.
        
        Args:
            df: Query result DataFrame
            
        Returns:
            Dictionary containing all insights
        """
        if df.empty:
            return {"error": "No data to analyze"}
        
        insights = {
            "summary": self._get_summary_stats(df),
            "data_quality": self._check_data_quality(df),
            "distributions": self._analyze_distributions(df),
            "correlations": self._find_correlations(df),
            "outliers": self._detect_outliers(df),
            "recommendations": []
        }
        
        # Generate recommendations based on findings
        insights["recommendations"] = self._generate_recommendations(insights, df)
        
        return insights
    
    def _get_summary_stats(self, df: pd.DataFrame) -> Dict:
        """Get summary statistics for numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            return {"message": "No numeric columns found"}
        
        stats = {}
        for col in numeric_cols:
            stats[col] = {
                "count": int(df[col].count()),
                "min": float(df[col].min()) if pd.notna(df[col].min()) else None,
                "max": float(df[col].max()) if pd.notna(df[col].max()) else None,
                "mean": float(df[col].mean()) if pd.notna(df[col].mean()) else None,
                "median": float(df[col].median()) if pd.notna(df[col].median()) else None,
                "std": float(df[col].std()) if pd.notna(df[col].std()) else None,
                "sum": float(df[col].sum()) if pd.notna(df[col].sum()) else None
            }
        
        return stats
    
    def _check_data_quality(self, df: pd.DataFrame) -> Dict:
        """Check data quality metrics."""
        total_rows = len(df)
        quality = {}
        
        for col in df.columns:
            null_count = df[col].isnull().sum()
            null_pct = (null_count / total_rows) * 100
            
            unique_count = df[col].nunique()
            unique_pct = (unique_count / total_rows) * 100
            
            # Check for duplicates in this column
            duplicate_count = total_rows - unique_count
            
            quality[col] = {
                "null_count": int(null_count),
                "null_percentage": round(null_pct, 2),
                "unique_values": int(unique_count),
                "unique_percentage": round(unique_pct, 2),
                "duplicate_count": int(duplicate_count),
                "data_type": str(df[col].dtype)
            }
        
        # Overall quality score (0-100)
        avg_null_pct = sum(q["null_percentage"] for q in quality.values()) / len(quality)
        quality_score = max(0, 100 - avg_null_pct)
        
        return {
            "columns": quality,
            "overall_quality_score": round(quality_score, 2),
            "total_rows": total_rows,
            "total_columns": len(df.columns)
        }
    
    def _analyze_distributions(self, df: pd.DataFrame) -> Dict:
        """Analyze data distributions."""
        distributions = {}
        
        # Numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # Calculate quartiles
            q1 = df[col].quantile(0.25)
            q2 = df[col].quantile(0.50)
            q3 = df[col].quantile(0.75)
            
            distributions[col] = {
                "type": "numeric",
                "quartiles": {
                    "Q1": float(q1) if pd.notna(q1) else None,
                    "Q2_median": float(q2) if pd.notna(q2) else None,
                    "Q3": float(q3) if pd.notna(q3) else None
                },
                "skewness": float(df[col].skew()) if pd.notna(df[col].skew()) else None
            }
        
        # Categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if df[col].nunique() <= 20:  # Only for reasonable number of categories
                value_counts = df[col].value_counts().head(10)
                distributions[col] = {
                    "type": "categorical",
                    "top_values": value_counts.to_dict(),
                    "category_count": int(df[col].nunique())
                }
        
        return distributions
    
    def _find_correlations(self, df: pd.DataFrame) -> List[Dict]:
        """Find correlations between numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return []
        
        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr()
        
        # Find strong correlations (> 0.7 or < -0.7)
        correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]
                
                if abs(corr_value) > 0.7 and pd.notna(corr_value):
                    correlations.append({
                        "column1": col1,
                        "column2": col2,
                        "correlation": round(float(corr_value), 3),
                        "strength": "strong" if abs(corr_value) > 0.9 else "moderate"
                    })
        
        return correlations
    
    def _detect_outliers(self, df: pd.DataFrame) -> Dict:
        """Detect outliers using IQR method."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outliers = {}
        
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_count = outlier_mask.sum()
            
            if outlier_count > 0:
                outliers[col] = {
                    "count": int(outlier_count),
                    "percentage": round((outlier_count / len(df)) * 100, 2),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "outlier_values": df[col][outlier_mask].head(5).tolist()
                }
        
        return outliers
    
    def _generate_recommendations(self, insights: Dict, df: pd.DataFrame) -> List[str]:
        """Generate actionable recommendations based on insights."""
        recommendations = []
        
        # Check data quality
        quality = insights.get("data_quality", {})
        if quality.get("overall_quality_score", 100) < 80:
            recommendations.append("⚠️ Data quality is below 80%. Consider investigating missing values.")
        
        # Check for high null percentages
        for col, info in quality.get("columns", {}).items():
            if info["null_percentage"] > 20:
                recommendations.append(f"⚠️ Column '{col}' has {info['null_percentage']}% missing values")
        
        # Check for outliers
        outliers = insights.get("outliers", {})
        if outliers:
            recommendations.append(f"🔍 Found outliers in {len(outliers)} column(s). Review for data anomalies.")
        
        # Check for correlations
        correlations = insights.get("correlations", [])
        if correlations:
            strong_corr = [c for c in correlations if c["strength"] == "strong"]
            if strong_corr:
                recommendations.append(f"📊 Found {len(strong_corr)} strong correlation(s). Consider multicollinearity.")
        
        # Check for low cardinality
        for col, info in quality.get("columns", {}).items():
            if info["unique_percentage"] < 1 and len(df) > 100:
                recommendations.append(f"💡 Column '{col}' has very low cardinality ({info['unique_values']} unique values)")
        
        if not recommendations:
            recommendations.append("✅ No major data quality issues detected")
        
        return recommendations
    
    def format_insights_report(self, insights: Dict) -> str:
        """
        Format insights as a readable report.
        
        Args:
            insights: Insights dictionary from analyze()
            
        Returns:
            Formatted string report
        """
        lines = []
        lines.append("\n" + "="*80)
        lines.append("📊 DATA INSIGHTS REPORT")
        lines.append("="*80)
        
        # Summary Statistics
        if "summary" in insights and insights["summary"]:
            lines.append("\n📈 SUMMARY STATISTICS")
            lines.append("-" * 80)
            for col, stats in insights["summary"].items():
                if isinstance(stats, dict):
                    lines.append(f"\n{col}:")
                    for stat_name, value in stats.items():
                        if value is not None:
                            lines.append(f"  {stat_name:12s}: {value:,.2f}" if isinstance(value, float) else f"  {stat_name:12s}: {value:,}")
        
        # Data Quality
        if "data_quality" in insights:
            quality = insights["data_quality"]
            lines.append(f"\n\n🎯 DATA QUALITY SCORE: {quality.get('overall_quality_score', 0)}/100")
            lines.append("-" * 80)
            lines.append(f"Total Rows: {quality.get('total_rows', 0):,}")
            lines.append(f"Total Columns: {quality.get('total_columns', 0)}")
            
            # Show columns with issues
            problem_cols = []
            for col, info in quality.get("columns", {}).items():
                if info["null_percentage"] > 10:
                    problem_cols.append(f"  • {col}: {info['null_percentage']}% missing")
            
            if problem_cols:
                lines.append("\nColumns with Missing Data:")
                lines.extend(problem_cols)
        
        # Outliers
        if "outliers" in insights and insights["outliers"]:
            lines.append("\n\n🔍 OUTLIERS DETECTED")
            lines.append("-" * 80)
            for col, info in insights["outliers"].items():
                lines.append(f"{col}: {info['count']} outliers ({info['percentage']}%)")
        
        # Correlations
        if "correlations" in insights and insights["correlations"]:
            lines.append("\n\n🔗 CORRELATIONS")
            lines.append("-" * 80)
            for corr in insights["correlations"][:5]:  # Show top 5
                lines.append(f"{corr['column1']} ↔ {corr['column2']}: {corr['correlation']:.3f} ({corr['strength']})")
        
        # Recommendations
        if "recommendations" in insights:
            lines.append("\n\n💡 RECOMMENDATIONS")
            lines.append("-" * 80)
            for rec in insights["recommendations"]:
                lines.append(f"  {rec}")
        
        lines.append("\n" + "="*80)
        
        return "\n".join(lines)
