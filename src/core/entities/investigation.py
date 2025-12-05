"""Investigation entity - represents a dark web OSINT investigation."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import uuid4


class InvestigationStatus(Enum):
    """Status of an investigation."""
    PENDING = "pending"
    REFINING_QUERY = "refining_query"
    SEARCHING = "searching"
    FILTERING = "filtering"
    SCRAPING = "scraping"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Investigation:
    """
    Represents a complete OSINT investigation session.
    
    Attributes:
        id: Unique identifier for the investigation
        original_query: The user's original search query
        refined_query: The AI-refined query for dark web search
        status: Current status of the investigation
        model: LLM model used for analysis
        created_at: Timestamp when investigation was created
        updated_at: Timestamp of last update
        completed_at: Timestamp when investigation completed
        search_results_count: Number of search results found
        filtered_results_count: Number of results after filtering
        scraped_count: Number of pages successfully scraped
        entities_extracted: Count of extracted entities by type
        summary: Final intelligence summary
        threat_score: Calculated threat score (0-100)
        tags: User-defined tags for organization
        notes: Additional notes
        metadata: Additional metadata
    """
    
    original_query: str
    model: str = "gpt-4.1"
    id: str = field(default_factory=lambda: str(uuid4()))
    refined_query: Optional[str] = None
    status: InvestigationStatus = InvestigationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Results tracking
    search_results_count: int = 0
    filtered_results_count: int = 0
    scraped_count: int = 0
    entities_extracted: Dict[str, int] = field(default_factory=dict)
    
    # Output
    summary: Optional[str] = None
    threat_score: Optional[float] = None
    
    # Organization
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def update_status(self, new_status: InvestigationStatus) -> None:
        """Update the investigation status and timestamp."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        if new_status in (InvestigationStatus.COMPLETED, InvestigationStatus.FAILED):
            self.completed_at = datetime.utcnow()
    
    def add_error(self, stage: str, error: str, details: Optional[Dict] = None) -> None:
        """Record an error that occurred during investigation."""
        self.errors.append({
            "stage": stage,
            "error": error,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the investigation."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the investigation."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert investigation to dictionary for serialization."""
        return {
            "id": self.id,
            "original_query": self.original_query,
            "refined_query": self.refined_query,
            "model": self.model,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "search_results_count": self.search_results_count,
            "filtered_results_count": self.filtered_results_count,
            "scraped_count": self.scraped_count,
            "entities_extracted": self.entities_extracted,
            "summary": self.summary,
            "threat_score": self.threat_score,
            "tags": self.tags,
            "notes": self.notes,
            "metadata": self.metadata,
            "errors": self.errors,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Investigation":
        """Create an Investigation from a dictionary."""
        investigation = cls(
            original_query=data["original_query"],
            model=data.get("model", "gpt-4.1"),
            id=data.get("id", str(uuid4())),
        )
        investigation.refined_query = data.get("refined_query")
        investigation.status = InvestigationStatus(data.get("status", "pending"))
        investigation.created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow()
        investigation.updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow()
        investigation.completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        investigation.search_results_count = data.get("search_results_count", 0)
        investigation.filtered_results_count = data.get("filtered_results_count", 0)
        investigation.scraped_count = data.get("scraped_count", 0)
        investigation.entities_extracted = data.get("entities_extracted", {})
        investigation.summary = data.get("summary")
        investigation.threat_score = data.get("threat_score")
        investigation.tags = data.get("tags", [])
        investigation.notes = data.get("notes")
        investigation.metadata = data.get("metadata", {})
        investigation.errors = data.get("errors", [])
        return investigation
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate the duration of the investigation in seconds."""
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if investigation is still in progress."""
        return self.status not in (
            InvestigationStatus.COMPLETED,
            InvestigationStatus.FAILED,
            InvestigationStatus.CANCELLED,
        )
