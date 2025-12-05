"""Haystak search engine adapter."""

from typing import List
from urllib.parse import quote_plus
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from .base import BaseSearchEngine
from ...core.entities.search_result import SearchResult


class HaystakSearchEngine(BaseSearchEngine):
    """
    Haystak search engine adapter.
    
    Haystak claims to have indexed over 1.5 billion pages from the dark web.
    """
    
    @property
    def engine_name(self) -> str:
        return "haystak"
    
    @property
    def base_url(self) -> str:
        return "http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion"
    
    def build_search_url(self, query: str) -> str:
        """Build the search URL for Haystak."""
        encoded_query = quote_plus(query)
        return f"{self.base_url}/?q={encoded_query}"
    
    def _parse_results(self, html: str, query: str) -> List[SearchResult]:
        """Parse Haystak search results."""
        results = []
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Find result containers
        result_items = soup.find_all("div", class_="search-result")
        
        # Alternative: try searching results
        if not result_items:
            result_items = soup.find_all("article")
        
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
                title_elem = item.find("h3") or item.find("h4") or link
                title = title_elem.get_text(strip=True) if title_elem else "Untitled"
                
                # Extract description
                description_elem = item.find("p")
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
