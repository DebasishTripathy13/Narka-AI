"""Plugin system for Robin extensibility."""

from .loader import PluginLoader, PluginManager
from .base import BasePlugin, PluginMetadata

__all__ = [
    "PluginLoader",
    "PluginManager",
    "BasePlugin",
    "PluginMetadata",
]
