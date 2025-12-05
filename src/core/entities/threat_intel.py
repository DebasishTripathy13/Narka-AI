"""Threat intelligence entities - IOCs and threat data."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import uuid4


class ThreatLevel(Enum):
    """Threat severity levels."""
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IOCType(Enum):
    """Indicator of Compromise types."""
    IP_ADDRESS = "ip"
    DOMAIN = "domain"
    URL = "url"
    EMAIL = "email"
    FILE_HASH_MD5 = "md5"
    FILE_HASH_SHA1 = "sha1"
    FILE_HASH_SHA256 = "sha256"
    CRYPTO_WALLET = "crypto_wallet"
    CVE = "cve"
    YARA_RULE = "yara"
    SIGMA_RULE = "sigma"


@dataclass
class IOC:
    """
    Indicator of Compromise.
    
    Represents a technical artifact that indicates potential malicious activity.
    """
    
    ioc_type: IOCType
    value: str
    id: str = field(default_factory=lambda: str(uuid4()))
    confidence: float = 0.8
    threat_level: ThreatLevel = ThreatLevel.UNKNOWN
    description: Optional[str] = None
    source: Optional[str] = None
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    related_iocs: List[str] = field(default_factory=list)  # IDs of related IOCs
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "ioc_type": self.ioc_type.value,
            "value": self.value,
            "confidence": self.confidence,
            "threat_level": self.threat_level.value,
            "description": self.description,
            "source": self.source,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "tags": self.tags,
            "related_iocs": self.related_iocs,
            "metadata": self.metadata,
        }
    
    def to_stix(self) -> Dict[str, Any]:
        """Convert to STIX 2.1 format."""
        stix_type_map = {
            IOCType.IP_ADDRESS: "ipv4-addr",
            IOCType.DOMAIN: "domain-name",
            IOCType.URL: "url",
            IOCType.EMAIL: "email-addr",
            IOCType.FILE_HASH_MD5: "file",
            IOCType.FILE_HASH_SHA1: "file",
            IOCType.FILE_HASH_SHA256: "file",
        }
        
        indicator = {
            "type": "indicator",
            "spec_version": "2.1",
            "id": f"indicator--{self.id}",
            "created": self.first_seen.isoformat() + "Z",
            "modified": self.last_seen.isoformat() + "Z",
            "name": f"{self.ioc_type.value}: {self.value[:50]}",
            "description": self.description or f"IOC extracted by Robin",
            "indicator_types": ["malicious-activity"],
            "pattern_type": "stix",
            "valid_from": self.first_seen.isoformat() + "Z",
            "confidence": int(self.confidence * 100),
            "labels": self.tags,
        }
        
        # Build pattern based on IOC type
        stix_type = stix_type_map.get(self.ioc_type, "artifact")
        if self.ioc_type in (IOCType.FILE_HASH_MD5, IOCType.FILE_HASH_SHA1, IOCType.FILE_HASH_SHA256):
            hash_type = self.ioc_type.value.upper()
            indicator["pattern"] = f"[file:hashes.'{hash_type}' = '{self.value}']"
        elif self.ioc_type == IOCType.IP_ADDRESS:
            indicator["pattern"] = f"[ipv4-addr:value = '{self.value}']"
        elif self.ioc_type == IOCType.DOMAIN:
            indicator["pattern"] = f"[domain-name:value = '{self.value}']"
        elif self.ioc_type == IOCType.URL:
            indicator["pattern"] = f"[url:value = '{self.value}']"
        elif self.ioc_type == IOCType.EMAIL:
            indicator["pattern"] = f"[email-addr:value = '{self.value}']"
        else:
            indicator["pattern"] = f"[artifact:payload_bin = '{self.value}']"
        
        return indicator


@dataclass
class ThreatIntelligence:
    """
    Aggregated threat intelligence from an investigation.
    
    Contains analysis results, IOCs, and threat assessment.
    """
    
    investigation_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    
    # Threat assessment
    overall_threat_level: ThreatLevel = ThreatLevel.UNKNOWN
    threat_score: float = 0.0  # 0-100
    
    # Analysis results
    summary: Optional[str] = None
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Indicators
    iocs: List[IOC] = field(default_factory=list)
    
    # Threat actor information
    threat_actors: List[Dict[str, Any]] = field(default_factory=list)
    ttps: List[str] = field(default_factory=list)  # Tactics, Techniques, Procedures
    malware_families: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    data_sources: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_ioc(self, ioc: IOC) -> None:
        """Add an IOC to the intelligence."""
        self.iocs.append(ioc)
        self.updated_at = datetime.utcnow()
    
    def calculate_threat_score(self) -> float:
        """Calculate overall threat score based on IOCs and findings."""
        if not self.iocs:
            return 0.0
        
        # Weight factors
        level_weights = {
            ThreatLevel.UNKNOWN: 0.1,
            ThreatLevel.LOW: 0.25,
            ThreatLevel.MEDIUM: 0.5,
            ThreatLevel.HIGH: 0.75,
            ThreatLevel.CRITICAL: 1.0,
        }
        
        # Calculate weighted score
        total_weight = sum(
            level_weights[ioc.threat_level] * ioc.confidence 
            for ioc in self.iocs
        )
        
        # Normalize to 0-100
        max_possible = len(self.iocs) * 1.0  # Maximum if all critical with confidence 1
        self.threat_score = min(100, (total_weight / max(max_possible, 1)) * 100)
        
        # Set overall threat level
        if self.threat_score >= 80:
            self.overall_threat_level = ThreatLevel.CRITICAL
        elif self.threat_score >= 60:
            self.overall_threat_level = ThreatLevel.HIGH
        elif self.threat_score >= 40:
            self.overall_threat_level = ThreatLevel.MEDIUM
        elif self.threat_score >= 20:
            self.overall_threat_level = ThreatLevel.LOW
        else:
            self.overall_threat_level = ThreatLevel.UNKNOWN
        
        return self.threat_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "investigation_id": self.investigation_id,
            "overall_threat_level": self.overall_threat_level.value,
            "threat_score": self.threat_score,
            "summary": self.summary,
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "iocs": [ioc.to_dict() for ioc in self.iocs],
            "threat_actors": self.threat_actors,
            "ttps": self.ttps,
            "malware_families": self.malware_families,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "data_sources": self.data_sources,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    def to_stix_bundle(self) -> Dict[str, Any]:
        """Export as STIX 2.1 bundle."""
        objects = [ioc.to_stix() for ioc in self.iocs]
        
        return {
            "type": "bundle",
            "id": f"bundle--{self.id}",
            "objects": objects,
        }
