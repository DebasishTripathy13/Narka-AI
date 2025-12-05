"""Base search engine adapter with common functionality."""

from abc import abstractmethod
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging
import hashlib

from ...core.interfaces.search_engine import SearchEngineProvider
from ...core.entities.search_result import SearchResult


@dataclass
class SearchEngineStatus:
    """Status of a search engine."""
    engine_name: str
    is_available: bool
    last_check: datetime
    response_time: Optional[float] = None
    error_message: Optional[str] = None


class BaseSearchEngine(SearchEngineProvider):
    """
    Base implementation for search engine providers.
    
    Provides common functionality for all search engine adapters.
    """
    
    def __init__(
        self,
        session=None,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/109.0"
    ):
        self._session = session
        self._timeout = timeout
        self._max_retries = max_retries
        self._user_agent = user_agent
        self._logger = logging.getLogger(f"robin.search.{self.engine_name}")
        self._last_status: Optional[SearchEngineStatus] = None
    
    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Name of the search engine."""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL of the search engine."""
        pass
    
    @property
    def is_tor_required(self) -> bool:
        """Whether this engine requires Tor."""
        return ".onion" in self.base_url
    
    def set_session(self, session) -> None:
        """Set the HTTP session to use."""
        self._session = session
    
    def _generate_result_id(self, url: str) -> str:
        """Generate a unique ID for a result."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    def _make_request(
        self,
        url: str,
        params: Optional[dict] = None,
        method: str = "GET"
    ):
        """Make an HTTP request with retry logic."""
        if self._session is None:
            raise RuntimeError("No HTTP session configured. Call set_session() first.")
        
        headers = {"User-Agent": self._user_agent}
        
        for attempt in range(self._max_retries):
            try:
                if method.upper() == "GET":
                    response = self._session.get(
                        url,
                        params=params,
                        headers=headers,
                        timeout=self._timeout
                    )
                else:
                    response = self._session.post(
                        url,
                        data=params,
                        headers=headers,
                        timeout=self._timeout
                    )
                
                response.raise_for_status()
                return response
                
            except Exception as e:
                self._logger.warning(
                    f"Request attempt {attempt + 1}/{self._max_retries} failed: {e}"
                )
                if attempt == self._max_retries - 1:
                    raise
        
        return None
    
    def health_check(self) -> bool:
        """Check if the search engine is accessible."""
        try:
            start_time = datetime.now()
            
            response = self._make_request(self.base_url)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            is_available = response is not None and response.status_code == 200
            
            self._last_status = SearchEngineStatus(
                engine_name=self.engine_name,
                is_available=is_available,
                last_check=datetime.now(),
                response_time=response_time
            )
            
            return is_available
            
        except Exception as e:
            self._last_status = SearchEngineStatus(
                engine_name=self.engine_name,
                is_available=False,
                last_check=datetime.now(),
                error_message=str(e)
            )
            return False
    
    def get_status(self) -> Optional[SearchEngineStatus]:
        """Get the last health check status."""
        return self._last_status
    
    def _parse_results(self, html: str, query: str) -> List[SearchResult]:
        """
        Parse HTML response to extract search results.
        
        Override in subclasses to implement engine-specific parsing.
        """
        raise NotImplementedError("Subclasses must implement _parse_results")
    
    def search(self, query: str, max_results: int = 50) -> List[SearchResult]:
        """Execute a search query."""
        self._logger.info(f"Searching '{query}' on {self.engine_name}")
        
        try:
            search_url = self.build_search_url(query)
            response = self._make_request(search_url)
            
            if response is None:
                self._logger.error(f"No response from {self.engine_name}")
                return []
            
            results = self._parse_results(response.text, query)
            
            self._logger.info(f"Found {len(results)} results from {self.engine_name}")
            
            return results[:max_results]
            
        except Exception as e:
            self._logger.error(f"Search failed on {self.engine_name}: {e}")
            return []
    
    @abstractmethod
    def build_search_url(self, query: str) -> str:
        """Build the search URL for a query."""
        pass
