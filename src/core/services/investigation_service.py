"""Investigation service - orchestrates the full investigation workflow."""

from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass
from datetime import datetime

from ..entities import (
    Investigation,
    InvestigationStatus,
    SearchResult,
    ScrapedContent,
    ThreatIntelligence,
)
from ..interfaces import (
    LLMProvider,
    SearchEngineProvider,
    StorageProvider,
    CacheProvider,
)
from .query_refiner import QueryRefiner
from .result_filter import ResultFilter
from .summarizer import Summarizer
from .entity_extractor import EntityExtractor
from .threat_analyzer import ThreatAnalyzer


@dataclass
class InvestigationConfig:
    """Configuration for investigation workflow."""
    max_search_results: int = 100
    max_filtered_results: int = 20
    scrape_threads: int = 5
    scrape_timeout: int = 30
    max_content_chars: int = 1200
    enable_entity_extraction: bool = True
    enable_threat_analysis: bool = True
    enable_caching: bool = True
    cache_ttl_hours: int = 24


class InvestigationService:
    """
    Orchestrates the complete dark web OSINT investigation workflow.
    
    Coordinates:
    - Query refinement
    - Multi-engine search
    - Result filtering
    - Content scraping
    - Entity extraction
    - Threat analysis
    - Summary generation
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        search_engines: List[SearchEngineProvider],
        storage: Optional[StorageProvider] = None,
        cache: Optional[CacheProvider] = None,
        config: Optional[InvestigationConfig] = None,
    ):
        """
        Initialize the investigation service.
        
        Args:
            llm_provider: LLM provider for AI operations
            search_engines: List of search engine providers
            storage: Optional storage for persistence
            cache: Optional cache for performance
            config: Optional configuration
        """
        self.llm = llm_provider
        self.search_engines = search_engines
        self.storage = storage
        self.cache = cache
        self.config = config or InvestigationConfig()
        
        # Initialize sub-services
        self.query_refiner = QueryRefiner(llm_provider)
        self.result_filter = ResultFilter(llm_provider)
        self.summarizer = Summarizer(llm_provider)
        self.entity_extractor = EntityExtractor()
        self.threat_analyzer = ThreatAnalyzer(self.entity_extractor)
    
    def investigate(
        self,
        query: str,
        model: str = "gpt-4.1",
        progress_callback: Optional[Callable[[str, float], None]] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
    ) -> Investigation:
        """
        Run a complete investigation.
        
        Args:
            query: The search query
            model: LLM model to use
            progress_callback: Optional callback for progress updates (stage, percent)
            stream_callback: Optional callback for streaming summary output
            
        Returns:
            Completed Investigation with all results
        """
        # Create investigation
        investigation = Investigation(
            original_query=query,
            model=model,
        )
        
        try:
            # Stage 1: Refine query
            self._update_progress(progress_callback, "Refining query", 0.1)
            investigation.update_status(InvestigationStatus.REFINING_QUERY)
            investigation.refined_query = self.query_refiner.refine(query)
            
            # Stage 2: Search
            self._update_progress(progress_callback, "Searching dark web", 0.2)
            investigation.update_status(InvestigationStatus.SEARCHING)
            search_results = self._search_all_engines(investigation.refined_query)
            investigation.search_results_count = len(search_results)
            
            # Stage 3: Filter results
            self._update_progress(progress_callback, "Filtering results", 0.4)
            investigation.update_status(InvestigationStatus.FILTERING)
            filtered_results = self.result_filter.filter(
                investigation.refined_query,
                search_results
            )
            investigation.filtered_results_count = len(filtered_results)
            
            # Stage 4: Scrape content
            self._update_progress(progress_callback, "Scraping content", 0.5)
            investigation.update_status(InvestigationStatus.SCRAPING)
            scraped_content = self._scrape_content(filtered_results)
            investigation.scraped_count = len(scraped_content)
            
            # Stage 5: Extract entities
            if self.config.enable_entity_extraction:
                self._update_progress(progress_callback, "Extracting entities", 0.7)
                investigation.update_status(InvestigationStatus.EXTRACTING)
                extraction_result = self.entity_extractor.extract_from_multiple(scraped_content)
                investigation.entities_extracted = extraction_result.entity_counts
            
            # Stage 6: Analyze threats
            if self.config.enable_threat_analysis:
                self._update_progress(progress_callback, "Analyzing threats", 0.8)
                investigation.update_status(InvestigationStatus.ANALYZING)
                threat_intel = self.threat_analyzer.analyze(
                    investigation.id,
                    scraped_content,
                    query
                )
                investigation.threat_score = threat_intel.threat_score
            
            # Stage 7: Generate summary
            self._update_progress(progress_callback, "Generating summary", 0.9)
            investigation.summary = self.summarizer.summarize(
                query,
                scraped_content,
                stream_callback=stream_callback
            )
            
            # Complete
            investigation.update_status(InvestigationStatus.COMPLETED)
            self._update_progress(progress_callback, "Complete", 1.0)
            
            # Save to storage
            if self.storage:
                self.storage.save(investigation)
            
        except Exception as e:
            investigation.add_error(
                stage=investigation.status.value,
                error=str(e)
            )
            investigation.update_status(InvestigationStatus.FAILED)
            raise
        
        return investigation
    
    def _search_all_engines(self, query: str) -> List[Dict[str, str]]:
        """Search all configured engines and combine results."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from ..interfaces.search_engine import SearchQuery
        
        all_results = []
        search_query = SearchQuery(
            query=query,
            max_results=self.config.max_search_results
        )
        
        proxies = {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050"
        }
        
        with ThreadPoolExecutor(max_workers=len(self.search_engines)) as executor:
            futures = {
                executor.submit(engine.search, search_query, proxies): engine
                for engine in self.search_engines
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result.is_success:
                        all_results.extend(result.results)
                except Exception:
                    continue
        
        # Deduplicate by link
        seen = set()
        unique_results = []
        for res in all_results:
            link = res.get("link", "")
            if link and link not in seen:
                seen.add(link)
                unique_results.append(res)
        
        return unique_results
    
    def _scrape_content(
        self,
        results: List[Dict[str, str]]
    ) -> Dict[str, str]:
        """Scrape content from filtered results."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import requests
        from bs4 import BeautifulSoup
        import random
        
        USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0",
        ]
        
        proxies = {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050"
        }
        
        def scrape_single(url_data: Dict[str, str]) -> tuple:
            url = url_data.get("link", "")
            title = url_data.get("title", "")
            
            try:
                response = requests.get(
                    url,
                    headers={"User-Agent": random.choice(USER_AGENTS)},
                    proxies=proxies if ".onion" in url else None,
                    timeout=self.config.scrape_timeout
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    text = soup.get_text(separator=' ', strip=True)
                    content = f"{title} {text}"
                    return url, content[:self.config.max_content_chars]
                    
            except Exception:
                pass
            
            return url, title
        
        scraped = {}
        
        with ThreadPoolExecutor(max_workers=self.config.scrape_threads) as executor:
            futures = {
                executor.submit(scrape_single, result): result
                for result in results
            }
            
            for future in as_completed(futures):
                try:
                    url, content = future.result()
                    if content:
                        scraped[url] = content
                except Exception:
                    continue
        
        return scraped
    
    def _update_progress(
        self,
        callback: Optional[Callable[[str, float], None]],
        stage: str,
        percent: float
    ) -> None:
        """Update progress if callback is provided."""
        if callback:
            callback(stage, percent)
    
    async def ainvestigate(
        self,
        query: str,
        model: str = "gpt-4.1",
    ) -> Investigation:
        """Async version of investigate."""
        # For now, run sync version
        # TODO: Implement fully async pipeline
        return self.investigate(query, model)
    
    def get_investigation(self, investigation_id: str) -> Optional[Investigation]:
        """Retrieve a previous investigation by ID."""
        if self.storage:
            return self.storage.get(investigation_id)
        return None
    
    def list_investigations(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[Investigation]:
        """List recent investigations."""
        if self.storage:
            return self.storage.list(limit=limit, offset=offset)
        return []
