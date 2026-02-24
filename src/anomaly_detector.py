"""
Anomaly Detector - Proactive Data Quality Analysis
Automatically detects unusual patterns, outliers, and data quality issues.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class AnomalySeverity(Enum):
    """Anomaly severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Anomaly:
    """Single anomaly detection"""
    type: str
    severity: AnomalySeverity
    title: str
    description: str
    affected_column: Optional[str]
    affected_rows: int
    confidence: float  # 0.0 to 1.0
    details: Dict[str, Any]


class AnomalyDetector:
    """
    Detects anomalies and data quality issues in query results.
    Provides proactive insights without being asked.
    """
    
    def __init__(self):
        """Initialize anomaly detector."""
        self.min_rows_for_analysis = 3
    
    def analyze(self, df: pd.DataFrame) -> List[Anomaly]:
        """
        Analyze DataFrame for anomalies.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            List of detected anomalies
        """
        if df.empty or len(df) < self.min_rows_for_analysis:
            return []
        
        anomalies = []
        
        # Detect outliers in numeric columns
        anomalies.extend(self._detect_outliers(df))
        
        # Detect missing data patterns
        anomalies.extend(self._detect_missing_data(df))
        
        # Detect duplicates
        anomalies.extend(self._detect_duplicates(df))
        
        # Detect suspicious values
        anomalies.extend(self._detect_suspicious_values(df))
        
        # Sort by severity and confidence
        anomalies.sort(key=lambda x: (
            0 if x.severity == AnomalySeverity.CRITICAL else
            1 if x.severity == AnomalySeverity.WARNING else 2,
            -x.confidence
        ))
        
        return anomalies
    
    def _detect_outliers(self, df: pd.DataFrame) -> List[Anomaly]:
        """Detect statistical outliers using IQR method."""
        anomalies = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Skip if too many nulls
            if df[col].isna().sum() / len(df) > 0.5:
                continue
            
            # Calculate IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            if IQR == 0:
                continue
            
            # Define outlier bounds
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Find outliers
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            
            if len(outliers) > 0:
                outlier_pct = len(outliers) / len(df) * 100
                
                # Only report if significant
                if outlier_pct >= 5:
                    severity = (
                        AnomalySeverity.CRITICAL if outlier_pct > 20 else
                        AnomalySeverity.WARNING if outlier_pct > 10 else
                        AnomalySeverity.INFO
                    )
                    
                    anomalies.append(Anomaly(
                        type="outlier",
                        severity=severity,
                        title=f"Outliers detected in {col}",
                        description=f"Found {len(outliers)} outliers ({outlier_pct:.1f}% of data)",
                        affected_column=col,
                        affected_rows=len(outliers),
                        confidence=0.85,
                        details={
                            'lower_bound': float(lower_bound),
                            'upper_bound': float(upper_bound),
                            'outlier_count': len(outliers),
                            'outlier_percentage': outlier_pct
                        }
                    ))
        
        return anomalies
    
    def _detect_missing_data(self, df: pd.DataFrame) -> List[Anomaly]:
        """Detect missing data patterns."""
        anomalies = []
        
        for col in df.columns:
            null_count = df[col].isna().sum()
            null_pct = null_count / len(df) * 100
            
            if null_pct > 0:
                # Determine severity
                if null_pct == 100:
                    severity = AnomalySeverity.CRITICAL
                    title = f"Column {col} is completely empty"
                    description = "All values are NULL"
                elif null_pct >= 50:
                    severity = AnomalySeverity.WARNING
                    title = f"High missing data in {col}"
                    description = f"{null_pct:.1f}% of values are NULL"
                elif null_pct >= 20:
                    severity = AnomalySeverity.INFO
                    title = f"Missing data in {col}"
                    description = f"{null_pct:.1f}% of values are NULL"
                else:
                    continue  # Skip if less than 20%
                
                anomalies.append(Anomaly(
                    type="missing_data",
                    severity=severity,
                    title=title,
                    description=description,
                    affected_column=col,
                    affected_rows=null_count,
                    confidence=1.0,
                    details={
                        'null_count': null_count,
                        'null_percentage': null_pct
                    }
                ))
        
        return anomalies
    
    def _detect_duplicates(self, df: pd.DataFrame) -> List[Anomaly]:
        """Detect duplicate rows."""
        anomalies = []
        
        # Check for exact duplicates
        duplicate_rows = df.duplicated()
        dup_count = duplicate_rows.sum()
        
        if dup_count > 0:
            dup_pct = dup_count / len(df) * 100
            
            severity = (
                AnomalySeverity.CRITICAL if dup_pct > 30 else
                AnomalySeverity.WARNING if dup_pct > 10 else
                AnomalySeverity.INFO
            )
            
            anomalies.append(Anomaly(
                type="duplicate",
                severity=severity,
                title="Duplicate rows detected",
                description=f"Found {dup_count} duplicate rows ({dup_pct:.1f}% of data)",
                affected_column=None,
                affected_rows=dup_count,
                confidence=1.0,
                details={
                    'duplicate_count': dup_count,
                    'duplicate_percentage': dup_pct
                }
            ))
        
        return anomalies
    
    def _detect_suspicious_values(self, df: pd.DataFrame) -> List[Anomaly]:
        """Detect suspicious or unusual values."""
        anomalies = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Check for all zeros
            if (df[col] == 0).sum() / len(df) > 0.9:
                anomalies.append(Anomaly(
                    type="suspicious_value",
                    severity=AnomalySeverity.WARNING,
                    title=f"Column {col} mostly zeros",
                    description=f"{(df[col] == 0).sum() / len(df) * 100:.1f}% of values are zero",
                    affected_column=col,
                    affected_rows=(df[col] == 0).sum(),
                    confidence=0.75,
                    details={'zero_percentage': (df[col] == 0).sum() / len(df) * 100}
                ))
            
            # Check for negative values where unexpected
            if col.lower() in ['quantity', 'qty', 'count', 'amount', 'weight', 'volume']:
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    anomalies.append(Anomaly(
                        type="suspicious_value",
                        severity=AnomalySeverity.WARNING,
                        title=f"Negative values in {col}",
                        description=f"Found {negative_count} negative values (unexpected for this type)",
                        affected_column=col,
                        affected_rows=negative_count,
                        confidence=0.80,
                        details={'negative_count': negative_count}
                    ))
        
        return anomalies
    
    def format_anomaly_report(self, anomalies: List[Anomaly]) -> str:
        """Format anomalies for display."""
        if not anomalies:
            return "\n✅ No anomalies detected - data looks healthy!"
        
        lines = []
        lines.append("\n🔍 ANOMALY DETECTION REPORT:")
        lines.append("=" * 80)
        lines.append(f"Found {len(anomalies)} potential issues:\n")
        
        for i, anomaly in enumerate(anomalies, 1):
            # Icon based on severity
            if anomaly.severity == AnomalySeverity.CRITICAL:
                icon = "🚨"
            elif anomaly.severity == AnomalySeverity.WARNING:
                icon = "⚠️"
            else:
                icon = "ℹ️"
            
            lines.append(f"{i}. {icon} {anomaly.title}")
            lines.append(f"   {anomaly.description}")
            if anomaly.affected_column:
                lines.append(f"   Column: {anomaly.affected_column}")
            lines.append(f"   Confidence: {anomaly.confidence:.0%}")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
