"""Structured logging with correlation IDs and multiple outputs."""

import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
from contextvars import ContextVar
from uuid import uuid4


# Context variable for correlation ID
_correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')


class CorrelationContext:
    """Context manager for correlation ID tracking."""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid4())[:8]
        self._token = None
    
    def __enter__(self) -> str:
        self._token = _correlation_id.set(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, *args):
        if self._token:
            _correlation_id.reset(self._token)
    
    @staticmethod
    def get_current() -> str:
        return _correlation_id.get()


@dataclass
class LogConfig:
    """Configuration for logging."""
    level: str = "INFO"
    format: str = "json"  # "json" or "text"
    console_output: bool = True
    file_output: bool = False
    file_path: Optional[Path] = None
    max_file_size_mb: int = 10
    backup_count: int = 5
    include_timestamp: bool = True
    include_correlation_id: bool = True
    include_source: bool = True
    extra_fields: Dict[str, Any] = field(default_factory=dict)


class JsonFormatter(logging.Formatter):
    """JSON log formatter with structured output."""
    
    def __init__(self, config: LogConfig):
        super().__init__()
        self.config = config
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        if self.config.include_timestamp:
            log_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        if self.config.include_correlation_id:
            correlation_id = CorrelationContext.get_current()
            if correlation_id:
                log_data["correlation_id"] = correlation_id
        
        if self.config.include_source:
            log_data["source"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in (
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                'message', 'taskName'
            ):
                log_data[key] = value
        
        # Add configured extra fields
        log_data.update(self.config.extra_fields)
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Text log formatter with colored output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def __init__(self, config: LogConfig, use_colors: bool = True):
        super().__init__()
        self.config = config
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        parts = []
        
        if self.config.include_timestamp:
            parts.append(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Level with optional color
        level = record.levelname
        if self.use_colors and level in self.COLORS:
            level = f"{self.COLORS[level]}{level}{self.RESET}"
        parts.append(f"[{level:^8}]")
        
        if self.config.include_correlation_id:
            correlation_id = CorrelationContext.get_current()
            if correlation_id:
                parts.append(f"[{correlation_id}]")
        
        parts.append(f"{record.name}:")
        parts.append(record.getMessage())
        
        result = " ".join(parts)
        
        if record.exc_info:
            result += "\n" + self.formatException(record.exc_info)
        
        return result


class RobinLogger(logging.Logger):
    """Custom logger with additional methods for Robin."""
    
    def investigation_start(self, investigation_id: str, query: str, **kwargs):
        """Log the start of an investigation."""
        self.info(
            f"Investigation started: {query}",
            extra={"investigation_id": investigation_id, "event": "investigation_start", **kwargs}
        )
    
    def investigation_end(
        self,
        investigation_id: str,
        status: str,
        duration_seconds: float,
        **kwargs
    ):
        """Log the end of an investigation."""
        self.info(
            f"Investigation completed: {status}",
            extra={
                "investigation_id": investigation_id,
                "event": "investigation_end",
                "status": status,
                "duration_seconds": duration_seconds,
                **kwargs
            }
        )
    
    def search_engine_query(
        self,
        engine: str,
        query: str,
        results_count: int,
        duration_ms: float,
        **kwargs
    ):
        """Log a search engine query."""
        self.debug(
            f"Search query to {engine}: {results_count} results in {duration_ms:.0f}ms",
            extra={
                "event": "search_query",
                "engine": engine,
                "query": query,
                "results_count": results_count,
                "duration_ms": duration_ms,
                **kwargs
            }
        )
    
    def entity_extracted(self, entity_type: str, count: int, **kwargs):
        """Log extracted entities."""
        self.debug(
            f"Extracted {count} {entity_type} entities",
            extra={"event": "entity_extraction", "entity_type": entity_type, "count": count, **kwargs}
        )
    
    def llm_request(
        self,
        model: str,
        tokens_used: int,
        duration_ms: float,
        **kwargs
    ):
        """Log an LLM request."""
        self.debug(
            f"LLM request to {model}: {tokens_used} tokens in {duration_ms:.0f}ms",
            extra={
                "event": "llm_request",
                "model": model,
                "tokens_used": tokens_used,
                "duration_ms": duration_ms,
                **kwargs
            }
        )


# Set custom logger class
logging.setLoggerClass(RobinLogger)


def setup_logging(config: Optional[LogConfig] = None) -> None:
    """
    Set up logging with the given configuration.
    
    Args:
        config: Logging configuration
    """
    config = config or LogConfig()
    
    # Get root logger for Robin
    root_logger = logging.getLogger("robin")
    root_logger.setLevel(getattr(logging, config.level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if config.console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        if config.format == "json":
            console_handler.setFormatter(JsonFormatter(config))
        else:
            console_handler.setFormatter(TextFormatter(config, use_colors=True))
        
        root_logger.addHandler(console_handler)
    
    # File handler
    if config.file_output and config.file_path:
        from logging.handlers import RotatingFileHandler
        
        config.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            config.file_path,
            maxBytes=config.max_file_size_mb * 1024 * 1024,
            backupCount=config.backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Always use JSON for file output
        file_handler.setFormatter(JsonFormatter(config))
        
        root_logger.addHandler(file_handler)


def get_logger(name: str = "robin") -> RobinLogger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (will be prefixed with 'robin.')
        
    Returns:
        Configured logger instance
    """
    if not name.startswith("robin"):
        name = f"robin.{name}"
    return logging.getLogger(name)
