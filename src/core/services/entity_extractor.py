"""Entity extraction service - extracts intelligence artifacts from text."""

import re
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field

from ..entities import (
    ExtractedEntity,
    EntityType,
    EmailEntity,
    CryptoWalletEntity,
    PhoneEntity,
    DomainEntity,
    IPAddressEntity,
    PGPKeyEntity,
    UsernameEntity,
    CredentialEntity,
)


@dataclass
class ExtractionConfig:
    """Configuration for entity extraction."""
    extract_emails: bool = True
    extract_crypto: bool = True
    extract_phones: bool = True
    extract_domains: bool = True
    extract_ips: bool = True
    extract_pgp: bool = True
    extract_usernames: bool = True
    extract_credentials: bool = True
    extract_hashes: bool = True
    extract_cves: bool = True
    
    # Filtering
    min_confidence: float = 0.5
    deduplicate: bool = True
    
    # Context extraction
    context_chars: int = 100  # Characters of context around each entity


@dataclass
class ExtractionResult:
    """Result of entity extraction."""
    entities: List[ExtractedEntity] = field(default_factory=list)
    entity_counts: Dict[str, int] = field(default_factory=dict)
    source_url: Optional[str] = None
    text_length: int = 0
    
    def add_entity(self, entity: ExtractedEntity) -> None:
        """Add an entity and update counts."""
        self.entities.append(entity)
        entity_type = entity.entity_type.value
        self.entity_counts[entity_type] = self.entity_counts.get(entity_type, 0) + 1
    
    def get_by_type(self, entity_type: EntityType) -> List[ExtractedEntity]:
        """Get all entities of a specific type."""
        return [e for e in self.entities if e.entity_type == entity_type]
    
    @property
    def total_count(self) -> int:
        """Total number of entities extracted."""
        return len(self.entities)


class EntityExtractor:
    """
    Extracts intelligence entities from text content.
    
    Supports extraction of:
    - Email addresses
    - Cryptocurrency wallet addresses (BTC, ETH, XMR, etc.)
    - Phone numbers
    - Domain names and URLs
    - IP addresses
    - PGP keys
    - Usernames/handles
    - Credentials (username:password pairs)
    - File hashes (MD5, SHA1, SHA256)
    - CVE identifiers
    """
    
    # Regex patterns for different entity types
    PATTERNS = {
        'email': re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            re.IGNORECASE
        ),
        
        # Bitcoin addresses (Legacy, SegWit, Bech32)
        'btc_legacy': re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'),
        'btc_segwit': re.compile(r'\bbc1[a-z0-9]{39,59}\b', re.IGNORECASE),
        
        # Ethereum addresses
        'eth': re.compile(r'\b0x[a-fA-F0-9]{40}\b'),
        
        # Monero addresses
        'xmr': re.compile(r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b'),
        
        # Litecoin addresses
        'ltc': re.compile(r'\b[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}\b'),
        
        # Phone numbers (international format)
        'phone': re.compile(
            r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}|\+[1-9]\d{6,14}',
        ),
        
        # Onion domains
        'onion': re.compile(r'\b[a-z2-7]{16,56}\.onion\b', re.IGNORECASE),
        
        # Regular domains
        'domain': re.compile(
            r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
        ),
        
        # IPv4 addresses
        'ipv4': re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        ),
        
        # IPv6 addresses
        'ipv6': re.compile(
            r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
        ),
        
        # PGP public key blocks
        'pgp': re.compile(
            r'-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]*?-----END PGP PUBLIC KEY BLOCK-----',
            re.MULTILINE
        ),
        
        # Credentials (email:password or user:password)
        'credential': re.compile(
            r'\b[A-Za-z0-9._%+-]+(?:@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})?:[^\s:]{4,}\b',
            re.IGNORECASE
        ),
        
        # MD5 hash
        'md5': re.compile(r'\b[a-fA-F0-9]{32}\b'),
        
        # SHA1 hash
        'sha1': re.compile(r'\b[a-fA-F0-9]{40}\b'),
        
        # SHA256 hash
        'sha256': re.compile(r'\b[a-fA-F0-9]{64}\b'),
        
        # CVE identifiers
        'cve': re.compile(r'\bCVE-\d{4}-\d{4,7}\b', re.IGNORECASE),
        
        # Usernames (common patterns)
        'username': re.compile(r'@[A-Za-z0-9_]{3,30}\b'),
    }
    
    # Common false positives to filter out
    FALSE_POSITIVE_DOMAINS = {
        'example.com', 'localhost', 'test.com', 'domain.com',
        'email.com', 'website.com', 'yoursite.com',
    }
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        """Initialize the entity extractor."""
        self.config = config or ExtractionConfig()
        self._seen_values: Set[str] = set()
    
    def extract(
        self,
        text: str,
        source_url: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract all entities from text.
        
        Args:
            text: The text to extract entities from
            source_url: Optional URL where the text was found
            
        Returns:
            ExtractionResult containing all extracted entities
        """
        result = ExtractionResult(source_url=source_url, text_length=len(text))
        self._seen_values.clear()
        
        if self.config.extract_emails:
            self._extract_emails(text, result, source_url)
        
        if self.config.extract_crypto:
            self._extract_crypto_wallets(text, result, source_url)
        
        if self.config.extract_phones:
            self._extract_phones(text, result, source_url)
        
        if self.config.extract_domains:
            self._extract_domains(text, result, source_url)
        
        if self.config.extract_ips:
            self._extract_ips(text, result, source_url)
        
        if self.config.extract_pgp:
            self._extract_pgp_keys(text, result, source_url)
        
        if self.config.extract_credentials:
            self._extract_credentials(text, result, source_url)
        
        if self.config.extract_hashes:
            self._extract_hashes(text, result, source_url)
        
        if self.config.extract_cves:
            self._extract_cves(text, result, source_url)
        
        if self.config.extract_usernames:
            self._extract_usernames(text, result, source_url)
        
        return result
    
    def extract_from_multiple(
        self,
        texts: Dict[str, str]
    ) -> ExtractionResult:
        """
        Extract entities from multiple texts (URL -> content mapping).
        
        Args:
            texts: Dictionary mapping URLs to content
            
        Returns:
            Combined ExtractionResult
        """
        combined = ExtractionResult()
        
        for url, text in texts.items():
            result = self.extract(text, source_url=url)
            for entity in result.entities:
                combined.add_entity(entity)
        
        return combined
    
    def _get_context(self, text: str, match: re.Match) -> str:
        """Extract context around a regex match."""
        start = max(0, match.start() - self.config.context_chars)
        end = min(len(text), match.end() + self.config.context_chars)
        context = text[start:end].strip()
        return re.sub(r'\s+', ' ', context)
    
    def _should_add(self, value: str) -> bool:
        """Check if value should be added (deduplication)."""
        if not self.config.deduplicate:
            return True
        if value.lower() in self._seen_values:
            return False
        self._seen_values.add(value.lower())
        return True
    
    def _extract_emails(
        self,
        text: str,
        result: ExtractionResult,
        source_url: Optional[str]
    ) -> None:
        """Extract email addresses."""
        for match in self.PATTERNS['email'].finditer(text):
            value = match.group().lower()
            if self._should_add(value):
                entity = EmailEntity(
                    value=value,
                    source_url=source_url,
                    context=self._get_context(text, match),
                    confidence=0.9
                )
                result.add_entity(entity)
    
    def _extract_crypto_wallets(
        self,
        text: str,
        result: ExtractionResult,
        source_url: Optional[str]
    ) -> None:
        """Extract cryptocurrency wallet addresses."""
        crypto_patterns = [
            ('btc_legacy', 'BTC'),
            ('btc_segwit', 'BTC'),
            ('eth', 'ETH'),
            ('xmr', 'XMR'),
            ('ltc', 'LTC'),
        ]
        
        for pattern_name, currency in crypto_patterns:
            pattern = self.PATTERNS[pattern_name]
            for match in pattern.finditer(text):
                value = match.group()
                if self._should_add(value):
                    entity = CryptoWalletEntity(
                        value=value,
                        currency=currency,
                        source_url=source_url,
                        context=self._get_context(text, match),
                        confidence=0.85
                    )
                    result.add_entity(entity)
    
    def _extract_phones(
        self,
        text: str,
        result: ExtractionResult,
        source_url: Optional[str]
    ) -> None:
        """Extract phone numbers."""
        for match in self.PATTERNS['phone'].finditer(text):
            value = match.group()
            # Filter out obvious false positives (e.g., years, IDs)
            digits_only = re.sub(r'\D', '', value)
            if len(digits_only) >= 10 and self._should_add(digits_only):
                entity = PhoneEntity(
                    value=value,
                    source_url=source_url,
                    context=self._get_context(text, match),
                    confidence=0.7
                )
                result.add_entity(entity)
    
    def _extract_domains(
        self,
        text: str,
        result: ExtractionResult,
        source_url: Optional[str]
    ) -> None:
        """Extract domain names (including .onion)."""
        # Extract onion domains first (higher confidence)
        for match in self.PATTERNS['onion'].finditer(text):
            value = match.group().lower()
            if self._should_add(value):
                entity = DomainEntity(
                    value=value,
                    is_onion=True,
                    source_url=source_url,
                    context=self._get_context(text, match),
                    confidence=0.95
                )
                result.add_entity(entity)
        
        # Extract regular domains
        for match in self.PATTERNS['domain'].finditer(text):
            value = match.group().lower()
            if value not in self.FALSE_POSITIVE_DOMAINS and self._should_add(value):
                # Skip if it's an onion domain (already extracted)
                if '.onion' not in value:
                    entity = DomainEntity(
                        value=value,
                        is_onion=False,
                        source_url=source_url,
                        context=self._get_context(text, match),
                        confidence=0.75
                    )
                    result.add_entity(entity)
    
    def _extract_ips(
        self,
        text: str,
        result: ExtractionResult,
        source_url: Optional[str]
    ) -> None:
        """Extract IP addresses."""
        for match in self.PATTERNS['ipv4'].finditer(text):
            value = match.group()
            if self._should_add(value):
                entity = IPAddressEntity(
                    value=value,
                    ip_version=4,
                    source_url=source_url,
                    context=self._get_context(text, match),
                    confidence=0.85
                )
                result.add_entity(entity)
        
        for match in self.PATTERNS['ipv6'].finditer(text):
            value = match.group()
            if self._should_add(value):
                entity = IPAddressEntity(
                    value=value,
                    ip_version=6,
                    source_url=source_url,
                    context=self._get_context(text, match),
                    confidence=0.85
                )
                result.add_entity(entity)
    
    def _extract_pgp_keys(
        self,
        text: str,
        result: ExtractionResult,
        source_url: Optional[str]
    ) -> None:
        """Extract PGP public key blocks."""
        for match in self.PATTERNS['pgp'].finditer(text):
            value = match.group()
            if self._should_add(value[:50]):  # Use prefix for dedup
                entity = PGPKeyEntity(
                    value=value,
                    source_url=source_url,
                    confidence=0.95
                )
                result.add_entity(entity)
    
    def _extract_credentials(
        self,
        text: str,
        result: ExtractionResult,
        source_url: Optional[str]
    ) -> None:
        """Extract credential pairs."""
        for match in self.PATTERNS['credential'].finditer(text):
            value = match.group()
            if ':' in value and self._should_add(value):
                entity = CredentialEntity(
                    value=value,
                    source_url=source_url,
                    context=self._get_context(text, match),
                    confidence=0.8
                )
                result.add_entity(entity)
    
    def _extract_hashes(
        self,
        text: str,
        result: ExtractionResult,
        source_url: Optional[str]
    ) -> None:
        """Extract file hashes (MD5, SHA1, SHA256)."""
        # SHA256 first (most specific)
        for match in self.PATTERNS['sha256'].finditer(text):
            value = match.group().lower()
            if self._should_add(value):
                entity = ExtractedEntity(
                    entity_type=EntityType.HASH,
                    value=value,
                    source_url=source_url,
                    context=self._get_context(text, match),
                    confidence=0.8
                )
                entity.metadata['hash_type'] = 'SHA256'
                result.add_entity(entity)
        
        # SHA1
        for match in self.PATTERNS['sha1'].finditer(text):
            value = match.group().lower()
            # Skip if already matched as part of SHA256
            if self._should_add(value):
                entity = ExtractedEntity(
                    entity_type=EntityType.HASH,
                    value=value,
                    source_url=source_url,
                    context=self._get_context(text, match),
                    confidence=0.75
                )
                entity.metadata['hash_type'] = 'SHA1'
                result.add_entity(entity)
        
        # MD5
        for match in self.PATTERNS['md5'].finditer(text):
            value = match.group().lower()
            if self._should_add(value):
                entity = ExtractedEntity(
                    entity_type=EntityType.HASH,
                    value=value,
                    source_url=source_url,
                    context=self._get_context(text, match),
                    confidence=0.7
                )
                entity.metadata['hash_type'] = 'MD5'
                result.add_entity(entity)
    
    def _extract_cves(
        self,
        text: str,
        result: ExtractionResult,
        source_url: Optional[str]
    ) -> None:
        """Extract CVE identifiers."""
        for match in self.PATTERNS['cve'].finditer(text):
            value = match.group().upper()
            if self._should_add(value):
                entity = ExtractedEntity(
                    entity_type=EntityType.CVE,
                    value=value,
                    source_url=source_url,
                    context=self._get_context(text, match),
                    confidence=0.95
                )
                result.add_entity(entity)
    
    def _extract_usernames(
        self,
        text: str,
        result: ExtractionResult,
        source_url: Optional[str]
    ) -> None:
        """Extract usernames/handles."""
        for match in self.PATTERNS['username'].finditer(text):
            value = match.group()
            if self._should_add(value.lower()):
                entity = UsernameEntity(
                    value=value,
                    source_url=source_url,
                    context=self._get_context(text, match),
                    confidence=0.7
                )
                result.add_entity(entity)
