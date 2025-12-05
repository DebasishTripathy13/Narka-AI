"""Abstract interface for export providers."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, BinaryIO
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    STIX = "stix"
    MISP = "misp"
    EXCEL = "xlsx"


@dataclass
class ExportOptions:
    """Options for export operations."""
    format: ExportFormat
    include_raw_data: bool = False
    include_metadata: bool = True
    include_timestamps: bool = True
    compress: bool = False
    template: Optional[str] = None
    custom_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_options is None:
            self.custom_options = {}


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    format: ExportFormat
    file_path: Optional[Path] = None
    content: Optional[bytes] = None
    content_type: str = "application/octet-stream"
    filename: str = "export"
    size_bytes: int = 0
    error_message: Optional[str] = None


class ExportProvider(ABC):
    """
    Abstract base class for export providers.
    
    Each implementation handles a specific export format.
    """
    
    @property
    @abstractmethod
    def format(self) -> ExportFormat:
        """Return the export format this provider handles."""
        pass
    
    @property
    @abstractmethod
    def content_type(self) -> str:
        """Return the MIME content type for this format."""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format."""
        pass
    
    @abstractmethod
    def export_investigation(
        self,
        investigation: Any,
        options: ExportOptions
    ) -> ExportResult:
        """
        Export an investigation to this format.
        
        Args:
            investigation: The Investigation entity to export
            options: Export options
            
        Returns:
            ExportResult with the exported data
        """
        pass
    
    @abstractmethod
    def export_entities(
        self,
        entities: List[Any],
        options: ExportOptions
    ) -> ExportResult:
        """
        Export extracted entities to this format.
        
        Args:
            entities: List of extracted entities
            options: Export options
            
        Returns:
            ExportResult with the exported data
        """
        pass
    
    @abstractmethod
    def export_threat_intel(
        self,
        threat_intel: Any,
        options: ExportOptions
    ) -> ExportResult:
        """
        Export threat intelligence to this format.
        
        Args:
            threat_intel: ThreatIntelligence entity to export
            options: Export options
            
        Returns:
            ExportResult with the exported data
        """
        pass
    
    def export_to_file(
        self,
        data: Any,
        file_path: Path,
        options: ExportOptions
    ) -> ExportResult:
        """
        Export data directly to a file.
        
        Args:
            data: Data to export
            file_path: Path to write to
            options: Export options
            
        Returns:
            ExportResult indicating success/failure
        """
        try:
            if hasattr(data, 'to_dict'):
                result = self.export_investigation(data, options)
            elif isinstance(data, list):
                result = self.export_entities(data, options)
            else:
                return ExportResult(
                    success=False,
                    format=self.format,
                    error_message="Unsupported data type"
                )
            
            if result.success and result.content:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'wb') as f:
                    f.write(result.content)
                result.file_path = file_path
            
            return result
            
        except Exception as e:
            return ExportResult(
                success=False,
                format=self.format,
                error_message=str(e)
            )
    
    def export_to_stream(
        self,
        data: Any,
        stream: BinaryIO,
        options: ExportOptions
    ) -> ExportResult:
        """
        Export data to a binary stream.
        
        Args:
            data: Data to export
            stream: Binary stream to write to
            options: Export options
            
        Returns:
            ExportResult indicating success/failure
        """
        try:
            if hasattr(data, 'to_dict'):
                result = self.export_investigation(data, options)
            elif isinstance(data, list):
                result = self.export_entities(data, options)
            else:
                return ExportResult(
                    success=False,
                    format=self.format,
                    error_message="Unsupported data type"
                )
            
            if result.success and result.content:
                stream.write(result.content)
            
            return result
            
        except Exception as e:
            return ExportResult(
                success=False,
                format=self.format,
                error_message=str(e)
            )
