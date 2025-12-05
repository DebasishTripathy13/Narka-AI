"""CSV export adapter."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import csv
import io
from pathlib import Path

from ...core.interfaces.export import ExportProvider
from ...core.entities.investigation import Investigation


class CSVExporter(ExportProvider):
    """
    CSV export implementation.
    
    Exports investigation data as CSV files.
    Creates multiple CSV files for different data types.
    """
    
    @property
    def format_name(self) -> str:
        return "csv"
    
    @property
    def file_extension(self) -> str:
        return ".csv"
    
    @property
    def mime_type(self) -> str:
        return "text/csv"
    
    def export(
        self,
        investigation: Investigation,
        output_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Export investigation to CSV files."""
        try:
            options = options or {}
            output_base = Path(output_path).with_suffix("")
            
            # Export search results
            self._export_search_results(
                investigation,
                f"{output_base}_search_results.csv"
            )
            
            # Export scraped content
            self._export_scraped_content(
                investigation,
                f"{output_base}_scraped_content.csv"
            )
            
            # Export entities
            self._export_entities(
                investigation,
                f"{output_base}_entities.csv"
            )
            
            # Export summary
            self._export_summary(
                investigation,
                f"{output_base}_summary.csv"
            )
            
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def export_bytes(
        self,
        investigation: Investigation,
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Export investigation to CSV bytes (search results only)."""
        options = options or {}
        data_type = options.get("data_type", "search_results")
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if data_type == "search_results":
            self._write_search_results(writer, investigation)
        elif data_type == "entities":
            self._write_entities(writer, investigation)
        elif data_type == "scraped_content":
            self._write_scraped_content(writer, investigation)
        
        return output.getvalue().encode("utf-8")
    
    def _export_search_results(self, investigation: Investigation, path: str) -> None:
        """Export search results to CSV."""
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            self._write_search_results(writer, investigation)
    
    def _write_search_results(self, writer, investigation: Investigation) -> None:
        """Write search results to CSV writer."""
        writer.writerow([
            "ID", "URL", "Title", "Description", "Source Engine",
            "Query", "Discovered At", "Relevance Score", "Is Scraped"
        ])
        
        for result in investigation.search_results:
            writer.writerow([
                result.id,
                result.url,
                result.title,
                result.description,
                result.source_engine,
                result.query,
                result.discovered_at.isoformat() if result.discovered_at else "",
                result.relevance_score,
                result.is_scraped,
            ])
    
    def _export_scraped_content(self, investigation: Investigation, path: str) -> None:
        """Export scraped content to CSV."""
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            self._write_scraped_content(writer, investigation)
    
    def _write_scraped_content(self, writer, investigation: Investigation) -> None:
        """Write scraped content to CSV writer."""
        writer.writerow([
            "ID", "URL", "Title", "Clean Text (truncated)", "Scraped At",
            "Status Code", "Content Type", "Language", "Content Length"
        ])
        
        for content in investigation.scraped_content:
            # Truncate text for CSV
            clean_text = content.clean_text or ""
            if len(clean_text) > 500:
                clean_text = clean_text[:500] + "..."
            
            writer.writerow([
                content.id,
                content.url,
                content.title,
                clean_text,
                content.scraped_at.isoformat() if content.scraped_at else "",
                content.status_code,
                content.content_type,
                content.language,
                content.content_length,
            ])
    
    def _export_entities(self, investigation: Investigation, path: str) -> None:
        """Export entities to CSV."""
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            self._write_entities(writer, investigation)
    
    def _write_entities(self, writer, investigation: Investigation) -> None:
        """Write entities to CSV writer."""
        writer.writerow([
            "ID", "Type", "Value", "Confidence", "Context", "Source URL"
        ])
        
        for entity in investigation.extracted_entities:
            writer.writerow([
                entity.id,
                entity.entity_type,
                entity.value,
                entity.confidence,
                entity.context[:200] if entity.context else "",
                entity.source_url,
            ])
    
    def _export_summary(self, investigation: Investigation, path: str) -> None:
        """Export investigation summary to CSV."""
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            writer.writerow(["Field", "Value"])
            writer.writerow(["Investigation ID", investigation.id])
            writer.writerow(["Query", investigation.query])
            writer.writerow(["Status", investigation.status.value])
            writer.writerow(["Created At", investigation.created_at.isoformat() if investigation.created_at else ""])
            writer.writerow(["Updated At", investigation.updated_at.isoformat() if investigation.updated_at else ""])
            writer.writerow(["Completed At", investigation.completed_at.isoformat() if investigation.completed_at else ""])
            writer.writerow(["Search Results Count", len(investigation.search_results)])
            writer.writerow(["Scraped Pages Count", len(investigation.scraped_content)])
            writer.writerow(["Entities Count", len(investigation.extracted_entities)])
            writer.writerow(["Tags", ", ".join(investigation.tags)])
            writer.writerow(["Summary", investigation.summary or ""])
