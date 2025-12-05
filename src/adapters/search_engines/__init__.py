"""Search engine adapters."""

from .base import BaseSearchEngine
from .ahmia import AhmiaSearchEngine
from .torch import TorchSearchEngine
from .haystak import HaystakSearchEngine
from .excavator import ExcavatorSearchEngine
from .manager import SearchEngineManager
from .factory import create_search_engines

__all__ = [
    "BaseSearchEngine",
    "AhmiaSearchEngine",
    "TorchSearchEngine",
    "HaystakSearchEngine",
    "ExcavatorSearchEngine",
    "SearchEngineManager",
    "create_search_engines",
]
