"""Tests for cache implementations."""

import pytest
import time
import tempfile
import os

from src.infrastructure.cache.memory import MemoryCache
from src.infrastructure.cache.sqlite import SQLiteCache


class TestMemoryCache:
    """Tests for MemoryCache."""
    
    @pytest.fixture
    def cache(self):
        """Create a cache instance."""
        return MemoryCache(max_size=100, default_ttl=60)
    
    def test_set_and_get(self, cache):
        """Test basic set and get."""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_get_missing_key(self, cache):
        """Test getting a missing key."""
        assert cache.get("nonexistent") is None
        assert cache.get("nonexistent", "default") == "default"
    
    def test_delete(self, cache):
        """Test deleting a key."""
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
    
    def test_delete_missing(self, cache):
        """Test deleting a missing key."""
        assert cache.delete("nonexistent") is False
    
    def test_exists(self, cache):
        """Test checking key existence."""
        cache.set("key1", "value1")
        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False
    
    def test_clear(self, cache):
        """Test clearing the cache."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_ttl_expiry(self):
        """Test TTL expiry."""
        cache = MemoryCache(max_size=100, default_ttl=1)
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"
        time.sleep(1.5)
        assert cache.get("key1") is None
    
    def test_custom_ttl(self, cache):
        """Test custom TTL on set."""
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"
        time.sleep(1.5)
        assert cache.get("key1") is None
    
    def test_max_size_eviction(self):
        """Test LRU eviction when max size reached."""
        cache = MemoryCache(max_size=3, default_ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"
    
    def test_complex_values(self, cache):
        """Test storing complex values."""
        data = {
            "list": [1, 2, 3],
            "nested": {"a": 1, "b": 2},
            "tuple": (1, 2, 3),
        }
        cache.set("complex", data)
        retrieved = cache.get("complex")
        assert retrieved == data


class TestSQLiteCache:
    """Tests for SQLiteCache."""
    
    @pytest.fixture
    def cache(self):
        """Create a cache instance with temp database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        cache = SQLiteCache(db_path=path, default_ttl=60)
        cache.initialize()
        yield cache
        cache.close()
        os.unlink(path)
    
    def test_set_and_get(self, cache):
        """Test basic set and get."""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_get_missing_key(self, cache):
        """Test getting a missing key."""
        assert cache.get("nonexistent") is None
        assert cache.get("nonexistent", "default") == "default"
    
    def test_delete(self, cache):
        """Test deleting a key."""
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
    
    def test_exists(self, cache):
        """Test checking key existence."""
        cache.set("key1", "value1")
        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False
    
    def test_clear(self, cache):
        """Test clearing the cache."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_ttl_expiry(self):
        """Test TTL expiry."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        cache = SQLiteCache(db_path=path, default_ttl=1)
        cache.initialize()
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        time.sleep(1.5)
        assert cache.get("key1") is None
        
        cache.close()
        os.unlink(path)
    
    def test_complex_values(self, cache):
        """Test storing complex values."""
        data = {
            "list": [1, 2, 3],
            "nested": {"a": 1, "b": 2},
        }
        cache.set("complex", data)
        retrieved = cache.get("complex")
        assert retrieved == data
    
    def test_persistence(self):
        """Test that data persists across cache instances."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        # Write data
        cache1 = SQLiteCache(db_path=path, default_ttl=60)
        cache1.initialize()
        cache1.set("persistent", "value")
        cache1.close()
        
        # Read data in new instance
        cache2 = SQLiteCache(db_path=path, default_ttl=60)
        cache2.initialize()
        assert cache2.get("persistent") == "value"
        cache2.close()
        
        os.unlink(path)
