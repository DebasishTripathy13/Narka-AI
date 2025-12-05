"""Export factory for creating exporters."""

from typing import Dict, Type, List, Optional

from ...core.interfaces.export import ExportProvider
from .json_export import JSONExporter
from .csv_export import CSVExporter
from .stix_export import STIXExporter
from .pdf_export import PDFExporter


# Registry of available exporters
EXPORTER_REGISTRY: Dict[str, Type[ExportProvider]] = {
    "json": JSONExporter,
    "csv": CSVExporter,
    "stix": STIXExporter,
    "pdf": PDFExporter,
}


def get_exporter(format_name: str) -> Optional[ExportProvider]:
    """
    Get an exporter instance by format name.
    
    Args:
        format_name: Name of the export format
        
    Returns:
        Exporter instance or None if format not found
    """
    exporter_class = EXPORTER_REGISTRY.get(format_name.lower())
    
    if exporter_class:
        return exporter_class()
    
    return None


def list_exporters() -> List[str]:
    """List all available export formats."""
    return list(EXPORTER_REGISTRY.keys())


def register_exporter(format_name: str, exporter_class: Type[ExportProvider]) -> None:
    """Register a custom exporter."""
    EXPORTER_REGISTRY[format_name.lower()] = exporter_class
