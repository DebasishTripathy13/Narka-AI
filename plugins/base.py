"""Base plugin class and metadata."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class PluginMetadata:
    """Plugin metadata."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: str  # "search_engine", "llm_provider", "exporter", "analyzer"
    dependencies: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None


class BasePlugin(ABC):
    """
    Base class for all Robin plugins.
    
    All plugins must inherit from this class and implement
    the required methods.
    """
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Clean up plugin resources."""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True
    
    def health_check(self) -> bool:
        """
        Check if the plugin is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        return True


class SearchEnginePlugin(BasePlugin):
    """Base class for search engine plugins."""
    
    @abstractmethod
    def search(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Execute a search query.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of search result dictionaries
        """
        pass
    
    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Name of the search engine."""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL of the search engine."""
        pass


class LLMPlugin(BasePlugin):
    """Base class for LLM provider plugins."""
    
    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate a completion.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the model."""
        pass


class ExporterPlugin(BasePlugin):
    """Base class for exporter plugins."""
    
    @abstractmethod
    def export(
        self,
        data: Dict[str, Any],
        output_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Export data to a file.
        
        Args:
            data: Data to export
            output_path: Output file path
            options: Export options
            
        Returns:
            True if successful
        """
        pass
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Name of the export format."""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for exports."""
        pass


class AnalyzerPlugin(BasePlugin):
    """Base class for analyzer plugins."""
    
    @abstractmethod
    def analyze(
        self,
        content: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze content.
        
        Args:
            content: Content to analyze
            options: Analysis options
            
        Returns:
            Analysis results dictionary
        """
        pass
    
    @property
    @abstractmethod
    def analyzer_name(self) -> str:
        """Name of the analyzer."""
        pass
