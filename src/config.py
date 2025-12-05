"""Configuration management using Pydantic Settings."""

from typing import Optional, List, Dict, Any
from pathlib import Path
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TorConfig(BaseSettings):
    """Tor connection configuration."""
    
    model_config = SettingsConfigDict(env_prefix="TOR_")
    
    host: str = Field(default="127.0.0.1", description="Tor SOCKS proxy host")
    port: int = Field(default=9050, description="Tor SOCKS proxy port")
    control_port: int = Field(default=9051, description="Tor control port")
    control_password: Optional[str] = Field(default=None, description="Tor control password")
    circuit_rotation_interval: int = Field(default=600, description="Circuit rotation interval in seconds")
    timeout: int = Field(default=30, description="Connection timeout")
    max_retries: int = Field(default=3, description="Maximum connection retries")


class LLMConfig(BaseSettings):
    """LLM provider configuration."""
    
    model_config = SettingsConfigDict(env_prefix="LLM_")
    
    default_provider: str = Field(default="openai", description="Default LLM provider")
    default_model: str = Field(default="gemini-flash-latest", description="Default model")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=4000, description="Maximum tokens")
    streaming: bool = Field(default=True, description="Enable streaming")
    
    # API Keys (loaded from environment)
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    
    # Ollama
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")


class SearchConfig(BaseSettings):
    """Search engine configuration."""
    
    model_config = SettingsConfigDict(env_prefix="SEARCH_")
    
    default_engines: List[str] = Field(
        default=["ahmia", "torch", "haystak", "excavator"],
        description="Default search engines"
    )
    max_results_per_engine: int = Field(default=50, description="Max results per engine")
    timeout: int = Field(default=30, description="Search timeout")
    max_workers: int = Field(default=5, description="Max parallel searches")
    enable_deduplication: bool = Field(default=True, description="Remove duplicate results")


class ScrapeConfig(BaseSettings):
    """Scraping configuration."""
    
    model_config = SettingsConfigDict(env_prefix="SCRAPE_")
    
    max_pages: int = Field(default=10, description="Max pages to scrape per investigation")
    timeout: int = Field(default=30, description="Scrape timeout per page")
    max_workers: int = Field(default=5, description="Max parallel scrapes")
    max_content_length: int = Field(default=1000000, description="Max content length in bytes")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/109.0",
        description="User agent string"
    )


class CacheConfig(BaseSettings):
    """Cache configuration."""
    
    model_config = SettingsConfigDict(env_prefix="CACHE_")
    
    backend: str = Field(default="sqlite", description="Cache backend: memory, sqlite, redis")
    default_ttl: int = Field(default=3600, description="Default TTL in seconds")
    max_size: int = Field(default=10000, description="Max cache entries (memory cache)")
    
    # SQLite cache
    sqlite_path: str = Field(default="cache.db", description="SQLite cache database path")
    
    # Redis cache (optional)
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")


class StorageConfig(BaseSettings):
    """Storage configuration."""
    
    model_config = SettingsConfigDict(env_prefix="STORAGE_")
    
    backend: str = Field(default="sqlite", description="Storage backend: sqlite, json")
    sqlite_path: str = Field(default="robin_data.db", description="SQLite database path")
    json_path: str = Field(default="./data", description="JSON storage directory")


class APIConfig(BaseSettings):
    """API configuration."""
    
    model_config = SettingsConfigDict(env_prefix="API_")
    
    host: str = Field(default="127.0.0.1", description="API host")
    port: int = Field(default=8080, description="API port")
    debug: bool = Field(default=False, description="Debug mode")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    rate_limit: int = Field(default=60, description="Requests per minute")
    api_keys: List[str] = Field(default=[], description="Valid API keys")


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    
    model_config = SettingsConfigDict(env_prefix="LOG_")
    
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="text", description="Log format: text, json")
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_file_size: int = Field(default=10485760, description="Max log file size")
    backup_count: int = Field(default=5, description="Number of backup files")


class RobinConfig(BaseSettings):
    """Main Robin configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Sub-configurations
    tor: TorConfig = Field(default_factory=TorConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    scrape: ScrapeConfig = Field(default_factory=ScrapeConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Application settings
    app_name: str = Field(default="Robin", description="Application name")
    version: str = Field(default="2.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    data_dir: str = Field(default="./data", description="Data directory")
    plugins_dir: str = Field(default="./plugins", description="Plugins directory")


# Global configuration instance
_config: Optional[RobinConfig] = None


def get_config() -> RobinConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = RobinConfig()
    return _config


def load_config(config_path: Optional[str] = None) -> RobinConfig:
    """Load configuration from a file or environment."""
    global _config
    
    if config_path and Path(config_path).exists():
        # Load from YAML or JSON config file
        import yaml
        import json
        
        with open(config_path) as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        _config = RobinConfig(**data)
    else:
        _config = RobinConfig()
    
    return _config
