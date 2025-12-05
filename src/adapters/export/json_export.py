"""JSON export adapter."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path

from ...core.interfaces.export import ExportProvider
from ...core.entities.investigation import Investigation


class JSONExporter(ExportProvider):
    """
    JSON export implementation.
    
    Exports investigation data as formatted JSON.
    """
    
    @property
    def format_name(self) -> str:
        return "json"
    
    @property
    def file_extension(self) -> str:
        return ".json"
    
    @property
    def mime_type(self) -> str:
        return "application/json"
    
    def export(
        self,
        investigation: Investigation,
        output_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Export investigation to JSON file."""
        try:
            options = options or {}
            indent = options.get("indent", 2)
            include_raw_html = options.get("include_raw_html", False)
            
            data = self.to_dict(investigation, include_raw_html=include_raw_html)
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, default=str, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def export_bytes(
        self,
        investigation: Investigation,
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Export investigation to JSON bytes."""
        options = options or {}
        indent = options.get("indent", 2)
        include_raw_html = options.get("include_raw_html", False)
        
        data = self.to_dict(investigation, include_raw_html=include_raw_html)
        
        return json.dumps(data, indent=indent, default=str, ensure_ascii=False).encode("utf-8")
    
    def to_dict(
        self,
        investigation: Investigation,
        include_raw_html: bool = False
    ) -> Dict[str, Any]:
        """Convert investigation to dictionary."""
        # Search results
        search_results = []
        for result in investigation.search_results:
            result_dict = {
                "id": result.id,
                "url": result.url,
                "title": result.title,
                "description": result.description,
                "source_engine": result.source_engine,
                "discovered_at": result.discovered_at.isoformat() if result.discovered_at else None,
                "relevance_score": result.relevance_score,
            }
            if include_raw_html and result.raw_html:
                result_dict["raw_html"] = result.raw_html
            search_results.append(result_dict)
        
        # Scraped content
        scraped_content = []
        for content in investigation.scraped_content:
            content_dict = {
                "id": content.id,
                "url": content.url,
                "title": content.title,
                "clean_text": content.clean_text,
                "scraped_at": content.scraped_at.isoformat() if content.scraped_at else None,
                "status_code": content.status_code,
                "content_type": content.content_type,
                "language": content.language,
            }
            if include_raw_html and content.raw_html:
                content_dict["raw_html"] = content.raw_html
            scraped_content.append(content_dict)
        
        # Entities
        entities = []
        for entity in investigation.extracted_entities:
            entities.append({
                "id": entity.id,
                "entity_type": entity.entity_type,
                "value": entity.value,
                "confidence": entity.confidence,
                "context": entity.context,
                "source_url": entity.source_url,
            })
        
        return {
            "investigation": {
                "id": investigation.id,
                "query": investigation.query,
                "status": investigation.status.value,
                "created_at": investigation.created_at.isoformat() if investigation.created_at else None,
                "updated_at": investigation.updated_at.isoformat() if investigation.updated_at else None,
                "completed_at": investigation.completed_at.isoformat() if investigation.completed_at else None,
                "summary": investigation.summary,
                "tags": investigation.tags,
                "metadata": investigation.metadata,
            },
            "statistics": {
                "search_results_count": len(search_results),
                "scraped_pages_count": len(scraped_content),
                "entities_count": len(entities),
            },
            "search_results": search_results,
            "scraped_content": scraped_content,
            "extracted_entities": entities,
            "exported_at": datetime.now().isoformat(),
            "export_format": "json",
            "version": "1.0",
        }
