"""STIX 2.1 export adapter for threat intelligence sharing."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import uuid
from pathlib import Path

from ...core.interfaces.export import ExportProvider
from ...core.entities.investigation import Investigation


class STIXExporter(ExportProvider):
    """
    STIX 2.1 export implementation.
    
    Exports investigation data in STIX 2.1 format for
    threat intelligence sharing via TAXII or other means.
    """
    
    STIX_VERSION = "2.1"
    
    @property
    def format_name(self) -> str:
        return "stix"
    
    @property
    def file_extension(self) -> str:
        return ".json"
    
    @property
    def mime_type(self) -> str:
        return "application/stix+json"
    
    def export(
        self,
        investigation: Investigation,
        output_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Export investigation to STIX 2.1 bundle."""
        try:
            bundle = self._create_stix_bundle(investigation, options)
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(bundle, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def export_bytes(
        self,
        investigation: Investigation,
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Export investigation to STIX 2.1 bytes."""
        bundle = self._create_stix_bundle(investigation, options)
        return json.dumps(bundle, indent=2, default=str).encode("utf-8")
    
    def _create_stix_bundle(
        self,
        investigation: Investigation,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a STIX 2.1 bundle from the investigation."""
        options = options or {}
        
        objects = []
        
        # Create identity for the tool
        identity = self._create_identity()
        objects.append(identity)
        
        # Create report for the investigation
        report = self._create_report(investigation, identity["id"])
        objects.append(report)
        
        # Convert entities to STIX objects
        entity_refs = []
        for entity in investigation.extracted_entities:
            stix_obj = self._entity_to_stix(entity, identity["id"])
            if stix_obj:
                objects.append(stix_obj)
                entity_refs.append(stix_obj["id"])
        
        # Create indicators for URLs
        for result in investigation.search_results:
            indicator = self._url_to_indicator(result, identity["id"])
            if indicator:
                objects.append(indicator)
                entity_refs.append(indicator["id"])
        
        # Update report with object references
        report["object_refs"] = entity_refs
        
        return {
            "type": "bundle",
            "id": f"bundle--{uuid.uuid4()}",
            "objects": objects,
        }
    
    def _create_identity(self) -> Dict[str, Any]:
        """Create STIX identity for Robin."""
        return {
            "type": "identity",
            "spec_version": self.STIX_VERSION,
            "id": f"identity--{uuid.uuid4()}",
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
            "name": "Robin Dark Web OSINT Tool",
            "identity_class": "system",
            "description": "Automated dark web intelligence collection tool",
        }
    
    def _create_report(
        self,
        investigation: Investigation,
        identity_id: str
    ) -> Dict[str, Any]:
        """Create STIX report for the investigation."""
        return {
            "type": "report",
            "spec_version": self.STIX_VERSION,
            "id": f"report--{investigation.id}",
            "created": investigation.created_at.isoformat() + "Z" if investigation.created_at else datetime.utcnow().isoformat() + "Z",
            "modified": investigation.updated_at.isoformat() + "Z" if investigation.updated_at else datetime.utcnow().isoformat() + "Z",
            "name": f"Dark Web Investigation: {investigation.query}",
            "description": investigation.summary or f"Investigation results for query: {investigation.query}",
            "published": datetime.utcnow().isoformat() + "Z",
            "created_by_ref": identity_id,
            "labels": investigation.tags or ["dark-web", "osint"],
            "object_refs": [],  # Will be populated later
        }
    
    def _entity_to_stix(self, entity, identity_id: str) -> Optional[Dict[str, Any]]:
        """Convert an extracted entity to a STIX object."""
        entity_type = entity.entity_type.lower()
        
        # Map entity types to STIX types
        if entity_type == "email":
            return self._create_email_addr(entity, identity_id)
        elif entity_type == "crypto_wallet":
            return self._create_cryptocurrency_wallet(entity, identity_id)
        elif entity_type == "domain":
            return self._create_domain_name(entity, identity_id)
        elif entity_type == "ip_address":
            return self._create_ipv4_addr(entity, identity_id)
        elif entity_type == "url":
            return self._create_url(entity, identity_id)
        elif entity_type == "hash":
            return self._create_file_hash(entity, identity_id)
        
        return None
    
    def _create_email_addr(self, entity, identity_id: str) -> Dict[str, Any]:
        """Create STIX email-addr object."""
        return {
            "type": "email-addr",
            "spec_version": self.STIX_VERSION,
            "id": f"email-addr--{uuid.uuid4()}",
            "value": entity.value,
        }
    
    def _create_cryptocurrency_wallet(self, entity, identity_id: str) -> Dict[str, Any]:
        """Create STIX custom cryptocurrency wallet object."""
        return {
            "type": "x-cryptocurrency-wallet",
            "spec_version": self.STIX_VERSION,
            "id": f"x-cryptocurrency-wallet--{uuid.uuid4()}",
            "address": entity.value,
            "currency": entity.metadata.get("currency", "unknown") if hasattr(entity, 'metadata') else "unknown",
        }
    
    def _create_domain_name(self, entity, identity_id: str) -> Dict[str, Any]:
        """Create STIX domain-name object."""
        return {
            "type": "domain-name",
            "spec_version": self.STIX_VERSION,
            "id": f"domain-name--{uuid.uuid4()}",
            "value": entity.value,
        }
    
    def _create_ipv4_addr(self, entity, identity_id: str) -> Dict[str, Any]:
        """Create STIX ipv4-addr object."""
        return {
            "type": "ipv4-addr",
            "spec_version": self.STIX_VERSION,
            "id": f"ipv4-addr--{uuid.uuid4()}",
            "value": entity.value,
        }
    
    def _create_url(self, entity, identity_id: str) -> Dict[str, Any]:
        """Create STIX url object."""
        return {
            "type": "url",
            "spec_version": self.STIX_VERSION,
            "id": f"url--{uuid.uuid4()}",
            "value": entity.value,
        }
    
    def _create_file_hash(self, entity, identity_id: str) -> Dict[str, Any]:
        """Create STIX file object with hash."""
        hash_type = self._detect_hash_type(entity.value)
        
        return {
            "type": "file",
            "spec_version": self.STIX_VERSION,
            "id": f"file--{uuid.uuid4()}",
            "hashes": {
                hash_type: entity.value,
            },
        }
    
    def _url_to_indicator(self, result, identity_id: str) -> Optional[Dict[str, Any]]:
        """Convert a search result URL to a STIX indicator."""
        if not result.url or not ".onion" in result.url:
            return None
        
        return {
            "type": "indicator",
            "spec_version": self.STIX_VERSION,
            "id": f"indicator--{uuid.uuid4()}",
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
            "name": result.title or "Dark Web URL",
            "description": result.description or f"Dark web URL discovered: {result.url}",
            "indicator_types": ["unknown"],
            "pattern": f"[url:value = '{result.url}']",
            "pattern_type": "stix",
            "valid_from": datetime.utcnow().isoformat() + "Z",
            "created_by_ref": identity_id,
        }
    
    def _detect_hash_type(self, hash_value: str) -> str:
        """Detect hash type based on length."""
        length = len(hash_value)
        
        if length == 32:
            return "MD5"
        elif length == 40:
            return "SHA-1"
        elif length == 64:
            return "SHA-256"
        elif length == 128:
            return "SHA-512"
        
        return "unknown"
