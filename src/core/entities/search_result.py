"""Search result entity - represents a result from dark web search engines."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4


@dataclass
class SearchResult:
    """
    Represents a single search result from a dark web search engine.
    
    Attributes:
        id: Unique identifier for this result
        title: Title of the result
        link: URL/onion link
        snippet: Preview snippet text
        source_engine: Which search engine returned this result
        rank: Position in original search results
        relevance_score: AI-assigned relevance score (0-1)
        is_filtered: Whether this result passed filtering
        discovered_at: When this result was found
        last_seen_at: Last time this URL was seen
        metadata: Additional metadata
    """
    
    title: str
    link: str
    id: str = field(default_factory=lambda: str(uuid4()))
    snippet: Optional[str] = None
    source_engine: Optional[str] = None
    rank: Optional[int] = None
    relevance_score: Optional[float] = None
    is_filtered: bool = False
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_seen_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def domain(self) -> Optional[str]:
        """Extract the .onion domain from the link."""
        import re
        match = re.search(r'([a-z2-7]{16,56}\.onion)', self.link)
        return match.group(1) if match else None
    
    @property
    def is_onion(self) -> bool:
        """Check if this is a .onion link."""
        return '.onion' in self.link
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "link": self.link,
            "snippet": self.snippet,
            "source_engine": self.source_engine,
            "rank": self.rank,
            "relevance_score": self.relevance_score,
            "is_filtered": self.is_filtered,
            "discovered_at": self.discovered_at.isoformat(),
            "last_seen_at": self.last_seen_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        """Create a SearchResult from a dictionary."""
        return cls(
            id=data.get("id", str(uuid4())),
            title=data["title"],
            link=data["link"],
            snippet=data.get("snippet"),
            source_engine=data.get("source_engine"),
            rank=data.get("rank"),
            relevance_score=data.get("relevance_score"),
            is_filtered=data.get("is_filtered", False),
            discovered_at=datetime.fromisoformat(data["discovered_at"]) if data.get("discovered_at") else datetime.utcnow(),
            last_seen_at=datetime.fromisoformat(data["last_seen_at"]) if data.get("last_seen_at") else datetime.utcnow(),
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def from_legacy(cls, legacy_data: Dict[str, str]) -> "SearchResult":
        """Create from legacy format (title, link dict)."""
        return cls(
            title=legacy_data.get("title", ""),
            link=legacy_data.get("link", ""),
        )


@dataclass 
class SearchResultBatch:
    """A batch of search results with metadata."""
    
    results: List[SearchResult] = field(default_factory=list)
    query: str = ""
    total_found: int = 0
    engines_queried: List[str] = field(default_factory=list)
    engines_failed: List[str] = field(default_factory=list)
    search_duration_ms: Optional[float] = None
    
    def add_result(self, result: SearchResult) -> None:
        """Add a result to the batch."""
        self.results.append(result)
        self.total_found = len(self.results)
    
    def deduplicate(self) -> "SearchResultBatch":
        """Remove duplicate results based on link."""
        seen_links = set()
        unique_results = []
        for result in self.results:
            if result.link not in seen_links:
                seen_links.add(result.link)
                unique_results.append(result)
        self.results = unique_results
        self.total_found = len(self.results)
        return self
    
    def filter_by_relevance(self, min_score: float = 0.5) -> List[SearchResult]:
        """Get results above a relevance threshold."""
        return [r for r in self.results if r.relevance_score and r.relevance_score >= min_score]
