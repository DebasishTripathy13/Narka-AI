"""Threat analyzer service - analyzes content for threat indicators."""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from ..entities import (
    ThreatIntelligence,
    ThreatLevel,
    IOC,
    IOCType,
    ExtractedEntity,
    EntityType,
)
from .entity_extractor import EntityExtractor, ExtractionResult


@dataclass
class ThreatAnalysisConfig:
    """Configuration for threat analysis."""
    calculate_threat_score: bool = True
    extract_entities: bool = True
    generate_iocs: bool = True
    min_confidence: float = 0.5


class ThreatAnalyzer:
    """
    Analyzes dark web content for threat intelligence.
    
    Combines entity extraction with threat scoring and IOC generation.
    """
    
    # Mapping from entity types to IOC types
    ENTITY_TO_IOC_MAP = {
        EntityType.EMAIL: IOCType.EMAIL,
        EntityType.DOMAIN: IOCType.DOMAIN,
        EntityType.IP_ADDRESS: IOCType.IP_ADDRESS,
        EntityType.CRYPTO_WALLET: IOCType.CRYPTO_WALLET,
        EntityType.CVE: IOCType.CVE,
        EntityType.ONION_URL: IOCType.URL,
    }
    
    # Keywords that indicate higher threat levels
    HIGH_THREAT_KEYWORDS = {
        'ransomware', 'malware', 'exploit', 'zero-day', '0day',
        'credentials', 'leaked', 'dump', 'breach', 'hacked',
        'carding', 'fullz', 'cvv', 'bank', 'fraud',
        'botnet', 'ddos', 'rat', 'trojan', 'keylogger',
    }
    
    MEDIUM_THREAT_KEYWORDS = {
        'database', 'login', 'password', 'account', 'access',
        'vpn', 'rdp', 'ssh', 'shell', 'server',
        'tutorial', 'guide', 'method', 'tool', 'software',
    }
    
    def __init__(
        self,
        entity_extractor: Optional[EntityExtractor] = None,
        config: Optional[ThreatAnalysisConfig] = None
    ):
        """
        Initialize the threat analyzer.
        
        Args:
            entity_extractor: Optional custom entity extractor
            config: Optional analysis configuration
        """
        self.extractor = entity_extractor or EntityExtractor()
        self.config = config or ThreatAnalysisConfig()
    
    def analyze(
        self,
        investigation_id: str,
        scraped_content: Dict[str, str],
        query: Optional[str] = None
    ) -> ThreatIntelligence:
        """
        Analyze scraped content for threat intelligence.
        
        Args:
            investigation_id: ID of the parent investigation
            scraped_content: Dict mapping URLs to content
            query: Optional original search query
            
        Returns:
            ThreatIntelligence with analysis results
        """
        threat_intel = ThreatIntelligence(investigation_id=investigation_id)
        threat_intel.data_sources = list(scraped_content.keys())
        
        all_entities: List[ExtractedEntity] = []
        
        # Extract entities from all content
        if self.config.extract_entities:
            extraction_result = self.extractor.extract_from_multiple(scraped_content)
            all_entities = extraction_result.entities
        
        # Generate IOCs from entities
        if self.config.generate_iocs:
            self._generate_iocs(threat_intel, all_entities)
        
        # Analyze content for threat indicators
        combined_text = ' '.join(scraped_content.values())
        self._analyze_threat_level(threat_intel, combined_text, query)
        
        # Calculate final threat score
        if self.config.calculate_threat_score:
            threat_intel.calculate_threat_score()
        
        return threat_intel
    
    def _generate_iocs(
        self,
        threat_intel: ThreatIntelligence,
        entities: List[ExtractedEntity]
    ) -> None:
        """Generate IOCs from extracted entities."""
        for entity in entities:
            if entity.confidence < self.config.min_confidence:
                continue
            
            ioc_type = self.ENTITY_TO_IOC_MAP.get(entity.entity_type)
            if not ioc_type:
                # Handle hash types specially
                if entity.entity_type == EntityType.HASH:
                    hash_type = entity.metadata.get('hash_type', '').upper()
                    if hash_type == 'MD5':
                        ioc_type = IOCType.FILE_HASH_MD5
                    elif hash_type == 'SHA1':
                        ioc_type = IOCType.FILE_HASH_SHA1
                    elif hash_type == 'SHA256':
                        ioc_type = IOCType.FILE_HASH_SHA256
                    else:
                        continue
                else:
                    continue
            
            ioc = IOC(
                ioc_type=ioc_type,
                value=entity.value,
                confidence=entity.confidence,
                source=entity.source_url,
                description=entity.context,
            )
            
            threat_intel.add_ioc(ioc)
    
    def _analyze_threat_level(
        self,
        threat_intel: ThreatIntelligence,
        text: str,
        query: Optional[str]
    ) -> None:
        """Analyze text content for threat level indicators."""
        text_lower = text.lower()
        query_lower = (query or '').lower()
        
        high_matches = []
        medium_matches = []
        
        # Check for high threat keywords
        for keyword in self.HIGH_THREAT_KEYWORDS:
            if keyword in text_lower or keyword in query_lower:
                high_matches.append(keyword)
        
        # Check for medium threat keywords
        for keyword in self.MEDIUM_THREAT_KEYWORDS:
            if keyword in text_lower or keyword in query_lower:
                medium_matches.append(keyword)
        
        # Update threat intel with findings
        if high_matches:
            threat_intel.key_findings.append(
                f"High-threat indicators found: {', '.join(high_matches[:5])}"
            )
        
        if medium_matches:
            threat_intel.key_findings.append(
                f"Medium-threat indicators found: {', '.join(medium_matches[:5])}"
            )
        
        # Set IOC threat levels based on context
        for ioc in threat_intel.iocs:
            if any(kw in (ioc.description or '').lower() for kw in self.HIGH_THREAT_KEYWORDS):
                ioc.threat_level = ThreatLevel.HIGH
            elif any(kw in (ioc.description or '').lower() for kw in self.MEDIUM_THREAT_KEYWORDS):
                ioc.threat_level = ThreatLevel.MEDIUM
            else:
                ioc.threat_level = ThreatLevel.LOW
    
    def analyze_single(
        self,
        investigation_id: str,
        url: str,
        content: str
    ) -> ThreatIntelligence:
        """Analyze a single piece of content."""
        return self.analyze(investigation_id, {url: content})
    
    def get_statistics(
        self,
        threat_intel: ThreatIntelligence
    ) -> Dict[str, Any]:
        """Get statistics about the threat intelligence."""
        ioc_by_type = {}
        ioc_by_threat_level = {}
        
        for ioc in threat_intel.iocs:
            # Count by type
            type_name = ioc.ioc_type.value
            ioc_by_type[type_name] = ioc_by_type.get(type_name, 0) + 1
            
            # Count by threat level
            level_name = ioc.threat_level.value
            ioc_by_threat_level[level_name] = ioc_by_threat_level.get(level_name, 0) + 1
        
        return {
            "total_iocs": len(threat_intel.iocs),
            "iocs_by_type": ioc_by_type,
            "iocs_by_threat_level": ioc_by_threat_level,
            "threat_score": threat_intel.threat_score,
            "overall_threat_level": threat_intel.overall_threat_level.value,
            "key_findings_count": len(threat_intel.key_findings),
            "data_sources_count": len(threat_intel.data_sources),
        }
