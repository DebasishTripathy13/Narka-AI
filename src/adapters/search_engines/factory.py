"""Factory for creating search engine instances."""

from typing import List, Optional, Type, Dict

from .base import BaseSearchEngine
from .ahmia import AhmiaSearchEngine, AhmiaClearnetEngine
from .torch import TorchSearchEngine
from .haystak import HaystakSearchEngine
from .excavator import ExcavatorSearchEngine


# Registry of all available search engines
SEARCH_ENGINE_REGISTRY: Dict[str, Type[BaseSearchEngine]] = {
    "ahmia": AhmiaSearchEngine,
    "ahmia_clearnet": AhmiaClearnetEngine,
    "torch": TorchSearchEngine,
    "haystak": HaystakSearchEngine,
    "excavator": ExcavatorSearchEngine,
}

# Default engine configuration (name -> priority)
DEFAULT_ENGINES = [
    "ahmia",
    "torch",
    "haystak",
    "excavator",
]


def create_search_engines(
    engines: Optional[List[str]] = None,
    session=None,
    timeout: int = 30,
    max_retries: int = 3
) -> List[BaseSearchEngine]:
    """
    Create search engine instances.
    
    Args:
        engines: List of engine names to create (all if None)
        session: HTTP session to use
        timeout: Request timeout
        max_retries: Maximum retries per request
        
    Returns:
        List of configured search engine instances
    """
    engine_names = engines or DEFAULT_ENGINES
    
    instances = []
    
    for name in engine_names:
        engine_class = SEARCH_ENGINE_REGISTRY.get(name)
        
        if engine_class is None:
            continue
        
        engine = engine_class(
            session=session,
            timeout=timeout,
            max_retries=max_retries
        )
        
        instances.append(engine)
    
    return instances


def register_engine(name: str, engine_class: Type[BaseSearchEngine]) -> None:
    """Register a custom search engine class."""
    SEARCH_ENGINE_REGISTRY[name] = engine_class


def list_available_engines() -> List[str]:
    """List all available engine names."""
    return list(SEARCH_ENGINE_REGISTRY.keys())


def get_engine_class(name: str) -> Optional[Type[BaseSearchEngine]]:
    """Get an engine class by name."""
    return SEARCH_ENGINE_REGISTRY.get(name)
