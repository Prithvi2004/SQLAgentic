"""
Performance Monitor for SQL Agent
Tracks query performance metrics and provides optimization suggestions.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque
import statistics


class PerformanceMonitor:
    """Monitors and analyzes query performance."""
    
    def __init__(self, max_history: int = 100):
        """Initialize performance monitor."""
        self.max_history = max_history
        self.query_metrics = deque(maxlen=max_history)
        self.current_query_start = None
    
    def start_query(self):
        """Start timing a query."""
        self.current_query_start = time.time()
    
    def end_query(self, query: str, rows_returned: int, success: bool = True) -> float:
        """
        End timing and record metrics.
        
        Returns:
            float: Execution time in milliseconds
        """
        if self.current_query_start is None:
            return 0.0
        
        execution_time = (time.time() - self.current_query_start) * 1000  # ms
        
        metric = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:200],  # Store first 200 chars
            "execution_time_ms": execution_time,
            "rows_returned": rows_returned,
            "success": success,
            "query_length": len(query)
        }
        
        self.query_metrics.append(metric)
        self.current_query_start = None
        
        return execution_time
    
    def get_statistics(self) -> Dict:
        """Get performance statistics."""
        if not self.query_metrics:
            return {"message": "No queries executed yet"}
        
        execution_times = [m["execution_time_ms"] for m in self.query_metrics if m["success"]]
        rows_returned = [m["rows_returned"] for m in self.query_metrics if m["success"]]
        
        if not execution_times:
            return {"message": "No successful queries"}
        
        return {
            "total_queries": len(self.query_metrics),
            "successful_queries": len(execution_times),
            "failed_queries": len(self.query_metrics) - len(execution_times),
            "avg_execution_time_ms": round(statistics.mean(execution_times), 2),
            "min_execution_time_ms": round(min(execution_times), 2),
            "max_execution_time_ms": round(max(execution_times), 2),
            "median_execution_time_ms": round(statistics.median(execution_times), 2),
            "avg_rows_returned": round(statistics.mean(rows_returned), 2) if rows_returned else 0,
            "total_rows_returned": sum(rows_returned)
        }
    
    def get_slow_queries(self, threshold_ms: float = 1000.0) -> List[Dict]:
        """Get queries slower than threshold."""
        return [
            m for m in self.query_metrics 
            if m["success"] and m["execution_time_ms"] > threshold_ms
        ]
    
    def get_recommendations(self) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []
        stats = self.get_statistics()
        
        if isinstance(stats, dict) and "avg_execution_time_ms" in stats:
            # Check average execution time
            if stats["avg_execution_time_ms"] > 2000:
                recommendations.append("⚠️ Average query time is high (>2s). Consider adding indexes or optimizing queries.")
            
            # Check for slow queries
            slow_queries = self.get_slow_queries(1000)
            if len(slow_queries) > 5:
                recommendations.append(f"🐌 Found {len(slow_queries)} slow queries (>1s). Review and optimize.")
            
            # Check failure rate
            if stats["failed_queries"] > stats["successful_queries"] * 0.1:
                recommendations.append("❌ High query failure rate (>10%). Check query generation logic.")
            
            # Check result size
            if stats["avg_rows_returned"] > 10000:
                recommendations.append("📊 Large result sets detected. Consider adding LIMIT clauses or pagination.")
        
        if not recommendations:
            recommendations.append("✅ Performance looks good!")
        
        return recommendations
    
    def format_report(self) -> str:
        """Format performance report."""
        stats = self.get_statistics()
        
        if "message" in stats:
            return stats["message"]
        
        lines = []
        lines.append("\n" + "="*80)
        lines.append("⚡ PERFORMANCE REPORT")
        lines.append("="*80)
        
        lines.append(f"\n📊 Query Statistics:")
        lines.append(f"   Total Queries: {stats['total_queries']}")
        lines.append(f"   Successful: {stats['successful_queries']}")
        lines.append(f"   Failed: {stats['failed_queries']}")
        
        lines.append(f"\n⏱️  Execution Times:")
        lines.append(f"   Average: {stats['avg_execution_time_ms']:.2f} ms")
        lines.append(f"   Median: {stats['median_execution_time_ms']:.2f} ms")
        lines.append(f"   Min: {stats['min_execution_time_ms']:.2f} ms")
        lines.append(f"   Max: {stats['max_execution_time_ms']:.2f} ms")
        
        lines.append(f"\n📈 Data Volume:")
        lines.append(f"   Total Rows: {stats['total_rows_returned']:,}")
        lines.append(f"   Avg Rows/Query: {stats['avg_rows_returned']:.0f}")
        
        # Recommendations
        recommendations = self.get_recommendations()
        lines.append(f"\n💡 Recommendations:")
        for rec in recommendations:
            lines.append(f"   {rec}")
        
        lines.append("\n" + "="*80)
        
        return "\n".join(lines)
