"""Plugin loader and manager."""

import os
import sys
import importlib
import importlib.util
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
import logging

from .base import BasePlugin, PluginMetadata


class PluginLoader:
    """
    Dynamic plugin loader.
    
    Loads plugins from Python files in the plugins directory.
    """
    
    def __init__(self, plugins_dir: str = "plugins"):
        self._plugins_dir = Path(plugins_dir)
        self._logger = logging.getLogger("robin.plugins")
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins.
        
        Returns:
            List of plugin module paths
        """
        plugins = []
        
        if not self._plugins_dir.exists():
            self._logger.warning(f"Plugins directory not found: {self._plugins_dir}")
            return plugins
        
        for item in self._plugins_dir.iterdir():
            # Check for single file plugins
            if item.is_file() and item.suffix == ".py" and not item.name.startswith("_"):
                plugins.append(str(item))
            
            # Check for package plugins
            elif item.is_dir() and (item / "__init__.py").exists():
                plugins.append(str(item))
        
        self._logger.info(f"Discovered {len(plugins)} plugins")
        return plugins
    
    def load_plugin(self, plugin_path: str) -> Optional[Type[BasePlugin]]:
        """
        Load a plugin from a path.
        
        Args:
            plugin_path: Path to plugin file or directory
            
        Returns:
            Plugin class or None if loading failed
        """
        path = Path(plugin_path)
        
        try:
            if path.is_file():
                return self._load_file_plugin(path)
            elif path.is_dir():
                return self._load_package_plugin(path)
            else:
                self._logger.error(f"Invalid plugin path: {plugin_path}")
                return None
                
        except Exception as e:
            self._logger.error(f"Failed to load plugin {plugin_path}: {e}")
            return None
    
    def _load_file_plugin(self, path: Path) -> Optional[Type[BasePlugin]]:
        """Load a single-file plugin."""
        module_name = f"plugins.{path.stem}"
        
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Find plugin class
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type) and
                issubclass(obj, BasePlugin) and
                obj is not BasePlugin
            ):
                return obj
        
        return None
    
    def _load_package_plugin(self, path: Path) -> Optional[Type[BasePlugin]]:
        """Load a package plugin."""
        module_name = f"plugins.{path.name}"
        
        init_file = path / "__init__.py"
        spec = importlib.util.spec_from_file_location(module_name, init_file)
        
        if spec is None or spec.loader is None:
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Find plugin class
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type) and
                issubclass(obj, BasePlugin) and
                obj is not BasePlugin
            ):
                return obj
        
        return None


class PluginManager:
    """
    Plugin manager for loading, initializing, and managing plugins.
    """
    
    def __init__(self, plugins_dir: str = "plugins"):
        self._loader = PluginLoader(plugins_dir)
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_classes: Dict[str, Type[BasePlugin]] = {}
        self._logger = logging.getLogger("robin.plugins.manager")
    
    def load_all(self) -> int:
        """
        Load all available plugins.
        
        Returns:
            Number of plugins loaded
        """
        plugin_paths = self._loader.discover_plugins()
        loaded = 0
        
        for path in plugin_paths:
            plugin_class = self._loader.load_plugin(path)
            if plugin_class:
                try:
                    # Create instance to get metadata
                    temp_instance = plugin_class.__new__(plugin_class)
                    if hasattr(temp_instance, 'metadata'):
                        metadata = temp_instance.metadata
                        self._plugin_classes[metadata.name] = plugin_class
                        loaded += 1
                        self._logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
                except Exception as e:
                    self._logger.error(f"Failed to register plugin: {e}")
        
        return loaded
    
    def initialize_plugin(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[BasePlugin]:
        """
        Initialize a plugin.
        
        Args:
            name: Plugin name
            config: Plugin configuration
            
        Returns:
            Initialized plugin instance or None
        """
        if name not in self._plugin_classes:
            self._logger.error(f"Plugin not found: {name}")
            return None
        
        if name in self._plugins:
            self._logger.warning(f"Plugin already initialized: {name}")
            return self._plugins[name]
        
        try:
            plugin_class = self._plugin_classes[name]
            plugin = plugin_class()
            plugin.initialize(config or {})
            self._plugins[name] = plugin
            self._logger.info(f"Initialized plugin: {name}")
            return plugin
        except Exception as e:
            self._logger.error(f"Failed to initialize plugin {name}: {e}")
            return None
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get an initialized plugin by name."""
        return self._plugins.get(name)
    
    def list_plugins(self) -> List[PluginMetadata]:
        """List all available plugin metadata."""
        metadata_list = []
        
        for name, plugin_class in self._plugin_classes.items():
            try:
                temp_instance = plugin_class.__new__(plugin_class)
                if hasattr(temp_instance, 'metadata'):
                    metadata_list.append(temp_instance.metadata)
            except Exception:
                pass
        
        return metadata_list
    
    def list_initialized(self) -> List[str]:
        """List names of initialized plugins."""
        return list(self._plugins.keys())
    
    def shutdown_plugin(self, name: str) -> bool:
        """Shutdown a plugin."""
        if name not in self._plugins:
            return False
        
        try:
            self._plugins[name].shutdown()
            del self._plugins[name]
            self._logger.info(f"Shutdown plugin: {name}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to shutdown plugin {name}: {e}")
            return False
    
    def shutdown_all(self) -> None:
        """Shutdown all initialized plugins."""
        for name in list(self._plugins.keys()):
            self.shutdown_plugin(name)
    
    def get_plugins_by_type(self, plugin_type: str) -> List[BasePlugin]:
        """Get all initialized plugins of a specific type."""
        plugins = []
        
        for plugin in self._plugins.values():
            if plugin.metadata.plugin_type == plugin_type:
                plugins.append(plugin)
        
        return plugins
