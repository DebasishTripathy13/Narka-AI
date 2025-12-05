"""Torch search engine adapter."""

from typing import List
from urllib.parse import quote_plus
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from .base import BaseSearchEngine
from ...core.entities.search_result import SearchResult


class TorchSearchEngine(BaseSearchEngine):
    """
    Torch search engine adapter.
    
    Torch is one of the oldest and most well-known dark web search engines.
    """
    
    @property
    def engine_name(self) -> str:
        return "torch"
    
    @property
    def base_url(self) -> str:
        return "http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion"
    
    def build_search_url(self, query: str) -> str:
        """Build the search URL for Torch."""
        encoded_query = quote_plus(query)
        return f"{self.base_url}/cgi-bin/omega/omega?P={encoded_query}"
    
    def _parse_results(self, html: str, query: str) -> List[SearchResult]:
        """Parse Torch search results."""
        results = []
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Find result containers
        result_items = soup.find_all("div", class_="result")
        
        # Alternative selectors
        if not result_items:
            result_items = soup.find_all("table")
        
        for item in result_items:
            try:
                # Extract URL
                link = item.find("a")
                if not link:
                    continue
                
                url = link.get("href", "")
                if not url or not url.startswith("http"):
                    continue
                
                # Extract title
                title = link.get_text(strip=True)
                if not title:
                    title = "Untitled"
                
                # Extract description
                description = ""
                text_content = item.get_text(separator=" ", strip=True)
                # Remove title from description
                description = text_content.replace(title, "").strip()
                description = description[:500]  # Limit length
                
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
