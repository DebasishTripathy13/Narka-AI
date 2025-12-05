"""Scraped content entity - represents scraped web page content."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4
import hashlib


@dataclass
class ScrapedContent:
    """
    Represents scraped content from a dark web page.
    
    Attributes:
        id: Unique identifier
        url: Original URL that was scraped
        title: Page title
        raw_text: Extracted text content
        html_content: Raw HTML (optional, for archiving)
        content_hash: SHA256 hash of content for deduplication
        word_count: Number of words in content
        language: Detected language
        scraped_at: Timestamp of scraping
        http_status: HTTP status code received
        response_time_ms: Response time in milliseconds
        is_accessible: Whether the page was accessible
        error_message: Error message if scraping failed
        metadata: Additional metadata (headers, etc.)
    """
    
    url: str
    id: str = field(default_factory=lambda: str(uuid4()))
    title: Optional[str] = None
    raw_text: Optional[str] = None
    html_content: Optional[str] = None
    content_hash: Optional[str] = None
    word_count: int = 0
    language: Optional[str] = None
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    http_status: Optional[int] = None
    response_time_ms: Optional[float] = None
    is_accessible: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Content analysis
    links_found: List[str] = field(default_factory=list)
    images_found: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate derived fields after initialization."""
        if self.raw_text:
            self.word_count = len(self.raw_text.split())
            self.content_hash = hashlib.sha256(self.raw_text.encode()).hexdigest()
    
    def update_content(self, raw_text: str, title: Optional[str] = None) -> None:
        """Update the content and recalculate derived fields."""
        self.raw_text = raw_text
        if title:
            self.title = title
        self.word_count = len(raw_text.split())
        self.content_hash = hashlib.sha256(raw_text.encode()).hexdigest()
        self.scraped_at = datetime.utcnow()
    
    def truncate(self, max_chars: int = 1200) -> str:
        """Get truncated content for LLM processing."""
        if not self.raw_text:
            return self.title or ""
        combined = f"{self.title or ''} {self.raw_text}"
        return combined[:max_chars] if len(combined) > max_chars else combined
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "raw_text": self.raw_text,
            "content_hash": self.content_hash,
            "word_count": self.word_count,
            "language": self.language,
            "scraped_at": self.scraped_at.isoformat(),
            "http_status": self.http_status,
            "response_time_ms": self.response_time_ms,
            "is_accessible": self.is_accessible,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "links_found": self.links_found,
            "images_found": self.images_found,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScrapedContent":
        """Create from dictionary."""
        content = cls(
            id=data.get("id", str(uuid4())),
            url=data["url"],
            title=data.get("title"),
            raw_text=data.get("raw_text"),
            html_content=data.get("html_content"),
            language=data.get("language"),
            http_status=data.get("http_status"),
            response_time_ms=data.get("response_time_ms"),
            is_accessible=data.get("is_accessible", True),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {}),
            links_found=data.get("links_found", []),
            images_found=data.get("images_found", []),
        )
        if data.get("scraped_at"):
            content.scraped_at = datetime.fromisoformat(data["scraped_at"])
        return content
    
    @property
    def is_empty(self) -> bool:
        """Check if content is essentially empty."""
        return not self.raw_text or self.word_count < 10
    
    @property
    def domain(self) -> Optional[str]:
        """Extract domain from URL."""
        import re
        match = re.search(r'([a-z2-7]{16,56}\.onion)', self.url)
        return match.group(1) if match else None
