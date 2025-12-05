"""Excavator search engine adapter."""

from typing import List
from urllib.parse import quote_plus
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from .base import BaseSearchEngine
from ...core.entities.search_result import SearchResult


class ExcavatorSearchEngine(BaseSearchEngine):
    """
    Excavator search engine adapter.
    
    Excavator is a dark web search engine focused on discovering hidden services.
    """
    
    @property
    def engine_name(self) -> str:
        return "excavator"
    
    @property
    def base_url(self) -> str:
        return "http://2fd6cemt4gmccflhm6imvdfvli3nber7sber5gcgwyj5uwwqkipmpoad.onion"
    
    def build_search_url(self, query: str) -> str:
        """Build the search URL for Excavator."""
        encoded_query = quote_plus(query)
        return f"{self.base_url}/search?q={encoded_query}"
    
    def _parse_results(self, html: str, query: str) -> List[SearchResult]:
        """Parse Excavator search results."""
        results = []
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Find result containers (CSS selectors may vary)
        result_items = soup.find_all("div", class_="result") or soup.find_all("div", class_="search-result")
        
        for item in result_items:
            try:
                # Extract URL
                link = item.find("a")
                if not link:
                    continue
                
                url = link.get("href", "")
                if not url:
                    continue
                
                # Extract title
                title = link.get_text(strip=True)
                if not title:
                    title_elem = item.find("h3") or item.find("h4")
                    title = title_elem.get_text(strip=True) if title_elem else "Untitled"
                
                # Extract description
                description_elem = item.find("p") or item.find("span", class_="description")
                description = ""
                if description_elem:
                    description = description_elem.get_text(strip=True)
                
                result = SearchResult(
                    id=self._generate_result_id(url),
                    url=url,
                    title=title,
                    description=description,
                    source_engine=self.engine_name,
                    query=query,
                    discovered_at=datetime.now(timezone.utc),
                    raw_html=str(item),
                )
                
                results.append(result)
                
            except Exception as e:
                self._logger.warning(f"Failed to parse result: {e}")
                continue
        
        return results
