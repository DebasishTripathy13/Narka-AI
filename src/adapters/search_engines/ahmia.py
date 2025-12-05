"""Ahmia search engine adapter."""

from typing import List
from urllib.parse import quote_plus
from datetime import datetime, timezone
import re

from bs4 import BeautifulSoup

from .base import BaseSearchEngine
from ...core.entities.search_result import SearchResult


class AhmiaSearchEngine(BaseSearchEngine):
    """
    Ahmia search engine adapter.
    
    Ahmia is one of the most popular and reliable .onion search engines.
    It indexes hidden services and provides a clean interface.
    """
    
    @property
    def engine_name(self) -> str:
        return "ahmia"
    
    @property
    def base_url(self) -> str:
        return "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion"
    
    def build_search_url(self, query: str) -> str:
        """Build the search URL for Ahmia."""
        encoded_query = quote_plus(query)
        return f"{self.base_url}/search/?q={encoded_query}"
    
    def _parse_results(self, html: str, query: str) -> List[SearchResult]:
        """Parse Ahmia search results."""
        results = []
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Find result containers
        result_items = soup.find_all("li", class_="result")
        
        for item in result_items:
            try:
                # Extract URL
                link = item.find("a")
                if not link:
                    continue
                
                url = link.get("href", "")
                
                # Extract title
                title = link.get_text(strip=True)
                if not title:
                    title = "Untitled"
                
                # Extract description/snippet
                description_elem = item.find("p")
                description = ""
                if description_elem:
                    description = description_elem.get_text(strip=True)
                
                # Extract date if available
                date_elem = item.find("span", class_="updated")
                discovered_at = None
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    try:
                        discovered_at = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    except ValueError:
                        pass
                
                result = SearchResult(
                    id=self._generate_result_id(url),
                    url=url,
                    title=title,
                    description=description,
                    source_engine=self.engine_name,
                    query=query,
                    discovered_at=discovered_at or datetime.now(timezone.utc),
                    raw_html=str(item),
                )
                
                results.append(result)
                
            except Exception as e:
                self._logger.warning(f"Failed to parse result: {e}")
                continue
        
        return results


class AhmiaClearnetEngine(AhmiaSearchEngine):
    """
    Ahmia clearnet (non-Tor) version.
    
    Uses the clearnet version of Ahmia for faster searches.
    """
    
    @property
    def engine_name(self) -> str:
        return "ahmia_clearnet"
    
    @property
    def base_url(self) -> str:
        return "https://ahmia.fi"
    
    @property
    def is_tor_required(self) -> bool:
        return False
