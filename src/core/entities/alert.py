"""Alert entity - for notification and monitoring system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import uuid4


class AlertType(Enum):
    """Types of alerts."""
    KEYWORD_MATCH = "keyword_match"
    NEW_CONTENT = "new_content"
    THREAT_DETECTED = "threat_detected"
    IOC_FOUND = "ioc_found"
    SCHEDULED_SEARCH = "scheduled_search"
    SYSTEM = "system"


class AlertStatus(Enum):
    """Alert status."""
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    DISMISSED = "dismissed"
    FAILED = "failed"


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AlertRule:
    """
    Defines a rule for generating alerts.
    
    Attributes:
        id: Unique identifier
        name: Human-readable name
        description: Rule description
        alert_type: Type of alert to generate
        keywords: Keywords to match (for keyword alerts)
        query: Search query (for scheduled searches)
        schedule_cron: Cron expression for scheduling
        is_active: Whether the rule is active
        notification_channels: Where to send alerts
        created_at: Creation timestamp
        metadata: Additional configuration
    """
    
    name: str
    alert_type: AlertType
    id: str = field(default_factory=lambda: str(uuid4()))
    description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    query: Optional[str] = None
    schedule_cron: Optional[str] = None
    is_active: bool = True
    priority: AlertPriority = AlertPriority.MEDIUM
    notification_channels: List[str] = field(default_factory=list)  # "email", "webhook", "slack"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, text: str) -> bool:
        """Check if text matches the alert rule keywords."""
        if not self.keywords:
            return False
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.keywords)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "alert_type": self.alert_type.value,
            "keywords": self.keywords,
            "query": self.query,
            "schedule_cron": self.schedule_cron,
            "is_active": self.is_active,
            "priority": self.priority.value,
            "notification_channels": self.notification_channels,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertRule":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid4())),
            name=data["name"],
            description=data.get("description"),
            alert_type=AlertType(data["alert_type"]),
            keywords=data.get("keywords", []),
            query=data.get("query"),
            schedule_cron=data.get("schedule_cron"),
            is_active=data.get("is_active", True),
            priority=AlertPriority(data.get("priority", "medium")),
            notification_channels=data.get("notification_channels", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Alert:
    """
    Represents a triggered alert.
    
    Attributes:
        id: Unique identifier
        rule_id: ID of the rule that triggered this alert
        alert_type: Type of alert
        title: Alert title
        message: Alert message
        priority: Alert priority
        status: Current status
        source_url: URL that triggered the alert
        matched_keywords: Keywords that matched
        investigation_id: Related investigation ID
        created_at: When alert was created
        sent_at: When alert was sent
        acknowledged_at: When alert was acknowledged
        metadata: Additional data
    """
    
    title: str
    message: str
    alert_type: AlertType
    id: str = field(default_factory=lambda: str(uuid4()))
    rule_id: Optional[str] = None
    priority: AlertPriority = AlertPriority.MEDIUM
    status: AlertStatus = AlertStatus.PENDING
    source_url: Optional[str] = None
    matched_keywords: List[str] = field(default_factory=list)
    investigation_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def mark_sent(self) -> None:
        """Mark alert as sent."""
        self.status = AlertStatus.SENT
        self.sent_at = datetime.utcnow()
    
    def acknowledge(self) -> None:
        """Acknowledge the alert."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
    
    def dismiss(self) -> None:
        """Dismiss the alert."""
        self.status = AlertStatus.DISMISSED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "alert_type": self.alert_type.value,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "status": self.status.value,
            "source_url": self.source_url,
            "matched_keywords": self.matched_keywords,
            "investigation_id": self.investigation_id,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Alert":
        """Create from dictionary."""
        alert = cls(
            id=data.get("id", str(uuid4())),
            rule_id=data.get("rule_id"),
            alert_type=AlertType(data["alert_type"]),
            title=data["title"],
            message=data["message"],
            priority=AlertPriority(data.get("priority", "medium")),
            status=AlertStatus(data.get("status", "pending")),
            source_url=data.get("source_url"),
            matched_keywords=data.get("matched_keywords", []),
            investigation_id=data.get("investigation_id"),
            metadata=data.get("metadata", {}),
        )
        if data.get("created_at"):
            alert.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("sent_at"):
            alert.sent_at = datetime.fromisoformat(data["sent_at"])
        if data.get("acknowledged_at"):
            alert.acknowledged_at = datetime.fromisoformat(data["acknowledged_at"])
        return alert
