"""Abstract interface for cache providers."""

from abc import ABC, abstractmethod
from typing import Optional, Any, List
from datetime import timedelta
import json
import hashlib


class CacheProvider(ABC):
    """
    Abstract base class for cache providers.
    
    Implementations can use Redis, SQLite, in-memory, etc.
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the cache connection."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the cache connection."""
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        pass
    
    @abstractmethod
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live (None for no expiration)
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cached items."""
        pass
    
    @abstractmethod
    def get_stats(self) -> dict:
        """Get cache statistics (hits, misses, size, etc.)."""
        pass
    
    def get_or_set(
        self,
        key: str,
        factory: callable,
        ttl: Optional[timedelta] = None
    ) -> Any:
        """
        Get from cache or compute and store.
        
        Args:
            key: The cache key
            factory: Function to call if key not found
            ttl: Time to live for newly cached value
            
        Returns:
            The cached or computed value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value, ttl)
        return value
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        Override for implementations that support pattern deletion.
        
        Args:
            pattern: Glob-style pattern
            
        Returns:
            Number of keys deleted
        """
        raise NotImplementedError("Pattern deletion not supported")
    
    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """
        Generate a cache key from arguments.
        
        Useful for creating consistent keys from function arguments.
        """
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_json = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_json.encode()).hexdigest()[:32]


class SearchResultCache(CacheProvider):
    """Specialized cache for search results."""
    
    def cache_search_results(
        self,
        query: str,
        engine: str,
        results: List[dict],
        ttl: timedelta = timedelta(hours=1)
    ) -> bool:
        """Cache search results for a specific query and engine."""
        key = f"search:{engine}:{self.generate_key(query)}"
        return self.set(key, results, ttl)
    
    def get_search_results(
        self,
        query: str,
        engine: str
    ) -> Optional[List[dict]]:
        """Get cached search results."""
        key = f"search:{engine}:{self.generate_key(query)}"
        return self.get(key)
    
    def invalidate_engine(self, engine: str) -> int:
        """Invalidate all cached results for an engine."""
        return self.delete_pattern(f"search:{engine}:*")


class LLMResponseCache(CacheProvider):
    """Specialized cache for LLM responses."""
    
    def cache_response(
        self,
        prompt: str,
        model: str,
        response: str,
        ttl: timedelta = timedelta(hours=24)
    ) -> bool:
        """Cache an LLM response."""
        key = f"llm:{model}:{self.generate_key(prompt)}"
        return self.set(key, response, ttl)
    
    def get_response(self, prompt: str, model: str) -> Optional[str]:
        """Get cached LLM response."""
        key = f"llm:{model}:{self.generate_key(prompt)}"
        return self.get(key)
