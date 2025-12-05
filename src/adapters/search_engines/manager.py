"""Search engine manager for coordinating multiple engines."""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .base import BaseSearchEngine, SearchEngineStatus
from ...core.entities.search_result import SearchResult


@dataclass
class SearchManagerConfig:
    """Configuration for the search manager."""
    max_workers: int = 5
    timeout_per_engine: int = 60
    enable_deduplication: bool = True
    min_engines_required: int = 1


class SearchEngineManager:
    """
    Manager for coordinating searches across multiple engines.
    
    Features:
    - Parallel search across multiple engines
    - Health monitoring
    - Result deduplication
    - Automatic failover
    """
    
    def __init__(self, config: Optional[SearchManagerConfig] = None):
        self._config = config or SearchManagerConfig()
        self._engines: Dict[str, BaseSearchEngine] = {}
        self._logger = logging.getLogger("robin.search.manager")
        self._engine_stats: Dict[str, Dict] = {}
    
    def register_engine(self, engine: BaseSearchEngine) -> None:
        """Register a search engine."""
        self._engines[engine.engine_name] = engine
        self._engine_stats[engine.engine_name] = {
            "total_searches": 0,
            "successful_searches": 0,
            "total_results": 0,
            "last_search": None,
        }
        self._logger.info(f"Registered search engine: {engine.engine_name}")
    
    def unregister_engine(self, engine_name: str) -> None:
        """Unregister a search engine."""
        if engine_name in self._engines:
            del self._engines[engine_name]
            del self._engine_stats[engine_name]
            self._logger.info(f"Unregistered search engine: {engine_name}")
    
    def get_engine(self, engine_name: str) -> Optional[BaseSearchEngine]:
        """Get a specific engine by name."""
        return self._engines.get(engine_name)
    
    def list_engines(self) -> List[str]:
        """List all registered engine names."""
        return list(self._engines.keys())
    
    def health_check_all(self) -> Dict[str, SearchEngineStatus]:
        """Run health checks on all engines."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self._config.max_workers) as executor:
            future_to_engine = {
                executor.submit(engine.health_check): name
                for name, engine in self._engines.items()
            }
            
            for future in as_completed(future_to_engine):
                engine_name = future_to_engine[future]
                try:
                    is_healthy = future.result()
                    engine = self._engines.get(engine_name)
                    if engine:
                        results[engine_name] = engine.get_status()
                except Exception as e:
                    results[engine_name] = SearchEngineStatus(
                        engine_name=engine_name,
                        is_available=False,
                        last_check=datetime.now(),
                        error_message=str(e)
                    )
        
        return results
    
    def get_available_engines(self) -> List[str]:
        """Get list of engines that passed the last health check."""
        available = []
        for name, engine in self._engines.items():
            status = engine.get_status()
            if status and status.is_available:
                available.append(name)
        return available
    
    def search(
        self,
        query: str,
        engines: Optional[List[str]] = None,
        max_results_per_engine: int = 50
    ) -> List[SearchResult]:
        """
        Execute a search across multiple engines.
        
        Args:
            query: Search query
            engines: Specific engines to use (all if None)
            max_results_per_engine: Maximum results per engine
            
        Returns:
            Combined and deduplicated results
        """
        target_engines = engines or list(self._engines.keys())
        
        # Filter to only registered engines
        target_engines = [e for e in target_engines if e in self._engines]
        
        if not target_engines:
            self._logger.warning("No valid engines available for search")
            return []
        
        self._logger.info(f"Searching '{query}' across {len(target_engines)} engines")
        
        all_results: List[SearchResult] = []
        seen_urls: Set[str] = set()
        
        def search_engine(engine_name: str) -> List[SearchResult]:
            engine = self._engines[engine_name]
            try:
                results = engine.search(query, max_results_per_engine)
                
                # Update stats
                self._engine_stats[engine_name]["total_searches"] += 1
                self._engine_stats[engine_name]["successful_searches"] += 1
                self._engine_stats[engine_name]["total_results"] += len(results)
                self._engine_stats[engine_name]["last_search"] = datetime.now()
                
                return results
            except Exception as e:
                self._logger.error(f"Search failed on {engine_name}: {e}")
                self._engine_stats[engine_name]["total_searches"] += 1
                return []
        
        # Execute searches in parallel
        with ThreadPoolExecutor(max_workers=self._config.max_workers) as executor:
            future_to_engine = {
                executor.submit(search_engine, name): name
                for name in target_engines
            }
            
            for future in as_completed(future_to_engine, timeout=self._config.timeout_per_engine):
                engine_name = future_to_engine[future]
                try:
                    results = future.result()
                    
                    for result in results:
                        # Deduplication
                        if self._config.enable_deduplication:
                            if result.url in seen_urls:
                                continue
                            seen_urls.add(result.url)
                        
                        all_results.append(result)
                        
                except Exception as e:
                    self._logger.error(f"Failed to get results from {engine_name}: {e}")
        
        self._logger.info(f"Total results collected: {len(all_results)}")
        
        return all_results
    
    def get_stats(self) -> Dict[str, Dict]:
        """Get statistics for all engines."""
        return self._engine_stats.copy()
    
    def set_session_all(self, session) -> None:
        """Set HTTP session for all engines."""
        for engine in self._engines.values():
            engine.set_session(session)
