"""Abstract interface for dark web search engines."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SearchEngineStatus(Enum):
    """Status of a search engine."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class SearchEngineHealth:
    """Health status of a search engine."""
    status: SearchEngineStatus = SearchEngineStatus.UNKNOWN
    last_check: Optional[datetime] = None
    response_time_ms: Optional[float] = None
    success_rate: float = 0.0  # Last 100 requests
    error_message: Optional[str] = None
    consecutive_failures: int = 0


@dataclass
class SearchQuery:
    """Represents a search query."""
    query: str
    max_results: int = 100
    timeout: int = 30
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchEngineResult:
    """Result from a single search engine."""
    engine_name: str
    results: List[Dict[str, str]]  # List of {title, link, snippet}
    query: str
    total_found: int = 0
    search_time_ms: float = 0.0
    is_success: bool = True
    error_message: Optional[str] = None


class SearchEngineProvider(ABC):
    """
    Abstract base class for dark web search engine providers.
    
    Each implementation handles a specific search engine (Ahmia, OnionLand, etc.)
    """
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.health = SearchEngineHealth()
        self._is_initialized = False
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this search engine."""
        pass
    
    @property
    @abstractmethod
    def search_url_template(self) -> str:
        """Return the URL template for searches. Use {query} as placeholder."""
        pass
    
    @abstractmethod
    def parse_results(self, html_content: str) -> List[Dict[str, str]]:
        """
        Parse search results from HTML content.
        
        Args:
            html_content: Raw HTML from search engine
            
        Returns:
            List of dicts with 'title', 'link', and optionally 'snippet' keys
        """
        pass
    
    def initialize(self) -> None:
        """Initialize the search engine (check connectivity, etc.)."""
        self._is_initialized = True
        self.check_health()
    
    def search(
        self,
        query: SearchQuery,
        proxies: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> SearchEngineResult:
        """
        Execute a search query against this engine.
        
        Args:
            query: The search query
            proxies: Proxy configuration (typically Tor)
            headers: HTTP headers to use
            
        Returns:
            SearchEngineResult with results or error
        """
        import requests
        import time
        
        url = self.search_url_template.format(query=query.query.replace(" ", "+"))
        start_time = time.time()
        
        try:
            response = requests.get(
                url,
                proxies=proxies,
                headers=headers or self._default_headers(),
                timeout=query.timeout or self.timeout
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                results = self.parse_results(response.text)
                self._record_success(elapsed_ms)
                
                return SearchEngineResult(
                    engine_name=self.name,
                    results=results[:query.max_results],
                    query=query.query,
                    total_found=len(results),
                    search_time_ms=elapsed_ms,
                    is_success=True
                )
            else:
                self._record_failure(f"HTTP {response.status_code}")
                return SearchEngineResult(
                    engine_name=self.name,
                    results=[],
                    query=query.query,
                    search_time_ms=elapsed_ms,
                    is_success=False,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except requests.Timeout:
            self._record_failure("Timeout")
            return SearchEngineResult(
                engine_name=self.name,
                results=[],
                query=query.query,
                is_success=False,
                error_message="Request timeout"
            )
        except Exception as e:
            self._record_failure(str(e))
            return SearchEngineResult(
                engine_name=self.name,
                results=[],
                query=query.query,
                is_success=False,
                error_message=str(e)
            )
    
    async def asearch(
        self,
        query: SearchQuery,
        proxies: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> SearchEngineResult:
        """Async version of search."""
        import aiohttp
        import time
        
        url = self.search_url_template.format(query=query.query.replace(" ", "+"))
        start_time = time.time()
        
        try:
            connector = None
            if proxies and 'http' in proxies:
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(proxies['http'])
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    url,
                    headers=headers or self._default_headers(),
                    timeout=aiohttp.ClientTimeout(total=query.timeout or self.timeout)
                ) as response:
                    elapsed_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        html = await response.text()
                        results = self.parse_results(html)
                        self._record_success(elapsed_ms)
                        
                        return SearchEngineResult(
                            engine_name=self.name,
                            results=results[:query.max_results],
                            query=query.query,
                            total_found=len(results),
                            search_time_ms=elapsed_ms,
                            is_success=True
                        )
                    else:
                        self._record_failure(f"HTTP {response.status}")
                        return SearchEngineResult(
                            engine_name=self.name,
                            results=[],
                            query=query.query,
                            is_success=False,
                            error_message=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            self._record_failure(str(e))
            return SearchEngineResult(
                engine_name=self.name,
                results=[],
                query=query.query,
                is_success=False,
                error_message=str(e)
            )
    
    def check_health(self) -> SearchEngineHealth:
        """Check the health of this search engine."""
        import requests
        import time
        
        start_time = time.time()
        try:
            response = requests.get(
                self.base_url,
                proxies={"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"},
                timeout=15
            )
            elapsed_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                self.health.status = SearchEngineStatus.ONLINE
                self.health.response_time_ms = elapsed_ms
                self.health.consecutive_failures = 0
            else:
                self.health.status = SearchEngineStatus.DEGRADED
                self.health.error_message = f"HTTP {response.status_code}"
                
        except Exception as e:
            self.health.status = SearchEngineStatus.OFFLINE
            self.health.error_message = str(e)
            self.health.consecutive_failures += 1
        
        self.health.last_check = datetime.utcnow()
        return self.health
    
    def _default_headers(self) -> Dict[str, str]:
        """Return default HTTP headers."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    def _record_success(self, response_time_ms: float) -> None:
        """Record a successful request."""
        self.health.status = SearchEngineStatus.ONLINE
        self.health.response_time_ms = response_time_ms
        self.health.consecutive_failures = 0
        self.health.last_check = datetime.utcnow()
    
    def _record_failure(self, error: str) -> None:
        """Record a failed request."""
        self.health.consecutive_failures += 1
        self.health.error_message = error
        self.health.last_check = datetime.utcnow()
        
        if self.health.consecutive_failures >= 3:
            self.health.status = SearchEngineStatus.OFFLINE
        else:
            self.health.status = SearchEngineStatus.DEGRADED
