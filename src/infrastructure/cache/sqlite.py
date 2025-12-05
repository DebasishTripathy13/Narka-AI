"""SQLite-based cache implementation."""

import sqlite3
import json
import time
import pickle
from typing import Optional, Any
from datetime import timedelta
from pathlib import Path
from threading import Lock

from ...core.interfaces.cache import CacheProvider


class SQLiteCache(CacheProvider):
    """
    SQLite-based persistent cache implementation.
    
    Good for single-process deployments needing persistence.
    """
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        table_name: str = "cache"
    ):
        """
        Initialize SQLite cache.
        
        Args:
            db_path: Path to SQLite database file (None for in-memory)
            table_name: Name of the cache table
        """
        self._db_path = str(db_path) if db_path else ":memory:"
        self._table_name = table_name
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
    
    def initialize(self) -> None:
        """Initialize the cache database."""
        with self._lock:
            self._connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False
            )
            
            # Create cache table
            self._connection.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    expires_at REAL,
                    created_at REAL
                )
            """)
            
            # Create index on expires_at for efficient cleanup
            self._connection.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self._table_name}_expires
                ON {self._table_name} (expires_at)
            """)
            
            self._connection.commit()
    
    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        self._ensure_connected()
        
        with self._lock:
            cursor = self._connection.execute(
                f"SELECT value, expires_at FROM {self._table_name} WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if row is None:
                self._misses += 1
                return None
            
            value_blob, expires_at = row
            
            # Check expiration
            if expires_at is not None and time.time() > expires_at:
                self._connection.execute(
                    f"DELETE FROM {self._table_name} WHERE key = ?",
                    (key,)
                )
                self._connection.commit()
                self._misses += 1
                return None
            
            self._hits += 1
            return pickle.loads(value_blob)
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Set a value in cache."""
        self._ensure_connected()
        
        with self._lock:
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl.total_seconds()
            
            value_blob = pickle.dumps(value)
            
            self._connection.execute(
                f"""
                INSERT OR REPLACE INTO {self._table_name}
                (key, value, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (key, value_blob, expires_at, time.time())
            )
            self._connection.commit()
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        self._ensure_connected()
        
        with self._lock:
            cursor = self._connection.execute(
                f"DELETE FROM {self._table_name} WHERE key = ?",
                (key,)
            )
            self._connection.commit()
            
            return cursor.rowcount > 0
    
    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        self._ensure_connected()
        
        with self._lock:
            cursor = self._connection.execute(
                f"SELECT expires_at FROM {self._table_name} WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return False
            
            expires_at = row[0]
            if expires_at is not None and time.time() > expires_at:
                self._connection.execute(
                    f"DELETE FROM {self._table_name} WHERE key = ?",
                    (key,)
                )
                self._connection.commit()
                return False
            
            return True
    
    def clear(self) -> None:
        """Clear all cached items."""
        self._ensure_connected()
        
        with self._lock:
            self._connection.execute(f"DELETE FROM {self._table_name}")
            self._connection.commit()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        self._ensure_connected()
        
        with self._lock:
            cursor = self._connection.execute(
                f"SELECT COUNT(*) FROM {self._table_name}"
            )
            size = cursor.fetchone()[0]
            
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                "type": "sqlite",
                "db_path": self._db_path,
                "size": size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
            }
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        self._ensure_connected()
        
        # Convert glob pattern to SQL LIKE pattern
        sql_pattern = pattern.replace("*", "%").replace("?", "_")
        
        with self._lock:
            cursor = self._connection.execute(
                f"DELETE FROM {self._table_name} WHERE key LIKE ?",
                (sql_pattern,)
            )
            self._connection.commit()
            
            return cursor.rowcount
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        self._ensure_connected()
        
        with self._lock:
            cursor = self._connection.execute(
                f"""
                DELETE FROM {self._table_name}
                WHERE expires_at IS NOT NULL AND expires_at < ?
                """,
                (time.time(),)
            )
            self._connection.commit()
            
            return cursor.rowcount
    
    def _ensure_connected(self) -> None:
        """Ensure database connection is active."""
        if self._connection is None:
            self.initialize()
