"""Extracted entity types - represents intelligence artifacts extracted from content."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import uuid4
import re


class EntityType(Enum):
    """Types of entities that can be extracted."""
    EMAIL = "email"
    CRYPTO_WALLET = "crypto_wallet"
    PHONE = "phone"
    DOMAIN = "domain"
    IP_ADDRESS = "ip_address"
    PGP_KEY = "pgp_key"
    USERNAME = "username"
    CREDENTIAL = "credential"
    ONION_URL = "onion_url"
    HASH = "hash"
    CVE = "cve"
    MALWARE = "malware"
    THREAT_ACTOR = "threat_actor"
    CUSTOM = "custom"


@dataclass
class ExtractedEntity:
    """
    Base class for extracted intelligence entities.
    
    Attributes:
        id: Unique identifier
        entity_type: Type of entity
        value: The extracted value
        confidence: Confidence score (0-1)
        source_url: URL where entity was found
        context: Surrounding text context
        first_seen: First time entity was seen
        last_seen: Most recent sighting
        occurrence_count: Number of times seen
        tags: Associated tags
        metadata: Additional metadata
    """
    
    entity_type: EntityType
    value: str
    id: str = field(default_factory=lambda: str(uuid4()))
    confidence: float = 1.0
    source_url: Optional[str] = None
    context: Optional[str] = None
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    occurrence_count: int = 1
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def record_occurrence(self, source_url: Optional[str] = None) -> None:
        """Record another occurrence of this entity."""
        self.occurrence_count += 1
        self.last_seen = datetime.utcnow()
        if source_url and source_url not in self.metadata.get("source_urls", []):
            if "source_urls" not in self.metadata:
                self.metadata["source_urls"] = []
            self.metadata["source_urls"].append(source_url)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "entity_type": self.entity_type.value,
            "value": self.value,
            "confidence": self.confidence,
            "source_url": self.source_url,
            "context": self.context,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "occurrence_count": self.occurrence_count,
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class EmailEntity(ExtractedEntity):
    """Email address entity."""
    
    entity_type: EntityType = field(default=EntityType.EMAIL, init=False)
    
    @property
    def domain(self) -> Optional[str]:
        """Extract email domain."""
        if "@" in self.value:
            return self.value.split("@")[1].lower()
        return None
    
    @property
    def local_part(self) -> Optional[str]:
        """Extract local part of email."""
        if "@" in self.value:
            return self.value.split("@")[0]
        return None
    
    @property
    def is_disposable(self) -> bool:
        """Check if email uses a known disposable domain."""
        disposable_domains = {
            "tempmail.com", "throwaway.email", "mailinator.com",
            "guerrillamail.com", "10minutemail.com", "temp-mail.org"
        }
        return self.domain in disposable_domains if self.domain else False


@dataclass
class CryptoWalletEntity(ExtractedEntity):
    """Cryptocurrency wallet address entity."""
    
    entity_type: EntityType = field(default=EntityType.CRYPTO_WALLET, init=False)
    currency: Optional[str] = None
    
    def __post_init__(self):
        """Detect cryptocurrency type from address format."""
        if not self.currency:
            self.currency = self._detect_currency()
    
    def _detect_currency(self) -> str:
        """Detect cryptocurrency based on address format."""
        value = self.value
        
        # Bitcoin (Legacy)
        if re.match(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$', value):
            return "BTC"
        # Bitcoin (SegWit)
        if re.match(r'^bc1[a-z0-9]{39,59}$', value, re.IGNORECASE):
            return "BTC"
        # Ethereum
        if re.match(r'^0x[a-fA-F0-9]{40}$', value):
            return "ETH"
        # Monero
        if re.match(r'^4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}$', value):
            return "XMR"
        # Litecoin
        if re.match(r'^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$', value):
            return "LTC"
        # Bitcoin Cash
        if re.match(r'^(bitcoincash:)?[qp][a-z0-9]{41}$', value):
            return "BCH"
        # Dash
        if re.match(r'^X[1-9A-HJ-NP-Za-km-z]{33}$', value):
            return "DASH"
        
        return "UNKNOWN"


@dataclass
class PhoneEntity(ExtractedEntity):
    """Phone number entity."""
    
    entity_type: EntityType = field(default=EntityType.PHONE, init=False)
    country_code: Optional[str] = None
    formatted: Optional[str] = None
    
    def normalize(self) -> str:
        """Normalize phone number to E.164 format."""
        digits = re.sub(r'\D', '', self.value)
        if len(digits) == 10:
            return f"+1{digits}"  # Assume US
        return f"+{digits}"


@dataclass
class DomainEntity(ExtractedEntity):
    """Domain/URL entity."""
    
    entity_type: EntityType = field(default=EntityType.DOMAIN, init=False)
    is_onion: bool = False
    
    def __post_init__(self):
        """Detect if this is an onion domain."""
        self.is_onion = ".onion" in self.value.lower()


@dataclass
class IPAddressEntity(ExtractedEntity):
    """IP address entity."""
    
    entity_type: EntityType = field(default=EntityType.IP_ADDRESS, init=False)
    ip_version: int = 4
    
    def __post_init__(self):
        """Detect IP version."""
        self.ip_version = 6 if ":" in self.value else 4
    
    @property
    def is_private(self) -> bool:
        """Check if IP is in private range."""
        import ipaddress
        try:
            ip = ipaddress.ip_address(self.value)
            return ip.is_private
        except ValueError:
            return False


@dataclass
class PGPKeyEntity(ExtractedEntity):
    """PGP public key entity."""
    
    entity_type: EntityType = field(default=EntityType.PGP_KEY, init=False)
    key_id: Optional[str] = None
    fingerprint: Optional[str] = None
    
    @property
    def is_public_key(self) -> bool:
        """Check if this is a public key block."""
        return "BEGIN PGP PUBLIC KEY" in self.value


@dataclass
class UsernameEntity(ExtractedEntity):
    """Username/handle entity."""
    
    entity_type: EntityType = field(default=EntityType.USERNAME, init=False)
    platform: Optional[str] = None


@dataclass
class CredentialEntity(ExtractedEntity):
    """Credential pair entity (username:password or email:password)."""
    
    entity_type: EntityType = field(default=EntityType.CREDENTIAL, init=False)
    username: Optional[str] = None
    password: Optional[str] = None
    password_hash: Optional[str] = None
    
    def __post_init__(self):
        """Parse credential pair."""
        if ":" in self.value:
            parts = self.value.split(":", 1)
            self.username = parts[0]
            self.password = parts[1] if len(parts) > 1 else None
