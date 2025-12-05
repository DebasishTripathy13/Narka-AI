"""In-memory cache implementation."""

import time
from typing import Optional, Any, Dict
from datetime import timedelta
from dataclasses import dataclass, field
from threading import Lock

from ...core.interfaces.cache import CacheProvider


@dataclass
class CacheEntry:
    """A single cache entry with expiration."""
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class MemoryCache(CacheProvider):
    """
    Thread-safe in-memory cache implementation.
    
    Good for development and single-process deployments.
    Not suitable for distributed systems.
    """
    
    def __init__(self, max_size: int = 10000, cleanup_interval: int = 300):
        """
        Initialize memory cache.
        
        Args:
            max_size: Maximum number of entries
            cleanup_interval: Seconds between cleanup runs
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._max_size = max_size
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()
        
        # Statistics
        self._hits = 0
        self._misses = 0
    
    def initialize(self) -> None:
        """Initialize the cache."""
        pass  # Nothing to initialize for memory cache
    
    def close(self) -> None:
        """Close the cache."""
        self.clear()
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        self._maybe_cleanup()
        
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None
            
            self._hits += 1
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Set a value in cache."""
        self._maybe_cleanup()
        
        with self._lock:
            # Check size limit
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_oldest()
            
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl.total_seconds()
            
            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                expires_at=expires_at
            )
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired:
                del self._cache[key]
                return False
            return True
    
    def clear(self) -> None:
        """Clear all cached items."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                "type": "memory",
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
            }
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        import fnmatch
        
        with self._lock:
            keys_to_delete = [
                k for k in self._cache.keys()
                if fnmatch.fnmatch(k, pattern)
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            return len(keys_to_delete)
    
    def _maybe_cleanup(self) -> None:
        """Run cleanup if enough time has passed."""
        if time.time() - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
    
    def _cleanup_expired(self) -> None:
        """Remove all expired entries."""
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if v.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            self._last_cleanup = time.time()
    
    def _evict_oldest(self) -> None:
        """Evict the oldest entry to make room."""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        del self._cache[oldest_key]
