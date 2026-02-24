"""
Query Cache - High-Performance Result Caching
Dramatically improves performance for repeated queries.
"""

import hashlib
import json
import time
from typing import Optional, Dict, Any, Tuple
from collections import OrderedDict
from dataclasses import dataclass
import pandas as pd


@dataclass
class CacheEntry:
    """Single cache entry"""
    key: str
    data: pd.DataFrame
    sql: str
    timestamp: float
    hit_count: int
    size_bytes: int


class QueryCache:
    """
    LRU cache with TTL for query results.
    Provides dramatic performance improvements for repeated queries.
    """
    
    def __init__(self, max_size_mb: int = 100, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            max_size_mb: Maximum cache size in megabytes
            ttl_seconds: Time-to-live for cache entries (default 1 hour)
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_size_bytes = 0
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_queries': 0
        }
    
    def _generate_key(self, sql: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from SQL and parameters."""
        # Normalize SQL (remove extra whitespace)
        normalized_sql = ' '.join(sql.split())
        
        # Include parameters in key
        if params:
            key_data = f"{normalized_sql}|{json.dumps(params, sort_keys=True)}"
        else:
            key_data = normalized_sql
        
        # Generate hash
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get(self, sql: str, params: Optional[Dict] = None) -> Optional[Tuple[pd.DataFrame, str]]:
        """
        Get cached result.
        
        Args:
            sql: SQL query
            params: Query parameters
            
        Returns:
            Tuple of (DataFrame, cache_status) or None if not cached
        """
        self.stats['total_queries'] += 1
        
        key = self._generate_key(sql, params)
        
        if key in self.cache:
            entry = self.cache[key]
            
            # Check if expired
            if time.time() - entry.timestamp > self.ttl_seconds:
                # Expired - remove from cache
                self._remove_entry(key)
                self.stats['misses'] += 1
                return None
            
            # Cache hit - move to end (most recently used)
            self.cache.move_to_end(key)
            entry.hit_count += 1
            self.stats['hits'] += 1
            
            age_seconds = time.time() - entry.timestamp
            status = f"HIT (age: {age_seconds:.1f}s, hits: {entry.hit_count})"
            
            return entry.data.copy(), status
        
        # Cache miss
        self.stats['misses'] += 1
        return None
    
    def put(self, sql: str, data: pd.DataFrame, params: Optional[Dict] = None):
        """
        Store result in cache.
        
        Args:
            sql: SQL query
            data: Query result DataFrame
            params: Query parameters
        """
        key = self._generate_key(sql, params)
        
        # Calculate size
        size_bytes = data.memory_usage(deep=True).sum()
        
        # Evict if necessary
        while self.current_size_bytes + size_bytes > self.max_size_bytes and self.cache:
            self._evict_lru()
        
        # Don't cache if too large
        if size_bytes > self.max_size_bytes:
            return
        
        # Create entry
        entry = CacheEntry(
            key=key,
            data=data.copy(),
            sql=sql,
            timestamp=time.time(),
            hit_count=0,
            size_bytes=size_bytes
        )
        
        # Add to cache
        self.cache[key] = entry
        self.current_size_bytes += size_bytes
    
    def _remove_entry(self, key: str):
        """Remove entry from cache."""
        if key in self.cache:
            entry = self.cache.pop(key)
            self.current_size_bytes -= entry.size_bytes
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if self.cache:
            key, entry = self.cache.popitem(last=False)  # Remove first (least recent)
            self.current_size_bytes -= entry.size_bytes
            self.stats['evictions'] += 1
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.current_size_bytes = 0
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching SQL pattern."""
        keys_to_remove = []
        for key, entry in self.cache.items():
            if pattern.lower() in entry.sql.lower():
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_entry(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_queries = self.stats['total_queries']
        hit_rate = (self.stats['hits'] / total_queries * 100) if total_queries > 0 else 0
        
        return {
            'total_queries': total_queries,
            'cache_hits': self.stats['hits'],
            'cache_misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.1f}%",
            'evictions': self.stats['evictions'],
            'entries': len(self.cache),
            'size_mb': self.current_size_bytes / (1024 * 1024),
            'max_size_mb': self.max_size_bytes / (1024 * 1024)
        }
    
    def format_stats_report(self) -> str:
        """Format cache statistics for display."""
        stats = self.get_stats()
        
        lines = []
        lines.append("\n📊 QUERY CACHE STATISTICS:")
        lines.append("=" * 80)
        lines.append(f"Total Queries: {stats['total_queries']}")
        lines.append(f"Cache Hits: {stats['cache_hits']}")
        lines.append(f"Cache Misses: {stats['cache_misses']}")
        lines.append(f"Hit Rate: {stats['hit_rate']}")
        lines.append(f"Evictions: {stats['evictions']}")
        lines.append(f"Cached Entries: {stats['entries']}")
        lines.append(f"Cache Size: {stats['size_mb']:.2f} MB / {stats['max_size_mb']:.2f} MB")
        lines.append("=" * 80)
        
        return "\n".join(lines)
