"""
Plugin registry for ToolWeaver.

Phase 0.e: Allow 3rd-party packages to register tools without modifying source.

Features:
- Runtime registration: register_plugin(name, plugin_class)
- Discovery: Auto-discover plugins via entry points
- Validation: Ensure plugins implement required interface
- Thread-safe: Use locks for concurrent access

Entry Point Pattern (pyproject.toml):
    [project.entry-points."toolweaver.plugins"]
    jira = "toolweaver_jira:JiraPlugin"
    slack = "toolweaver_slack:SlackPlugin"

Plugin Interface:
    class MyPlugin:
        def get_tools(self) -> list[dict]:
            '''Return list of tool definitions'''
            return [{"name": "...", "description": "...", "parameters": {...}}]
        
        async def execute(self, tool_name: str, params: dict) -> dict:
            '''Execute a tool by name'''
            ...
"""

from __future__ import annotations

import sys
from typing import Any, Optional, List, Protocol, runtime_checkable, Dict
from threading import Lock
from orchestrator._internal.logger import get_logger
from orchestrator._internal.errors import ToolWeaverError


logger = get_logger(__name__)


# ============================================================
# Plugin Errors
# ============================================================

class PluginError(ToolWeaverError):
    """Base exception for plugin-related errors."""
    pass


class PluginNotFoundError(PluginError):
    """Plugin not found in registry."""
    pass


class PluginAlreadyRegisteredError(PluginError):
    """Plugin already registered with this name."""
    pass


class InvalidPluginError(PluginError):
    """Plugin does not implement required interface."""
    pass


class DuplicateToolNameError(PluginError):
    """A plugin attempted to register tools with duplicate names."""
    pass


# ============================================================
# Plugin Registry
# ============================================================

@runtime_checkable
class PluginProtocol(Protocol):
    def get_tools(self) -> List[Dict[str, Any]]: ...
    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Any: ...


class PluginRegistry:
    """
    Thread-safe registry for tool plugins.
    
    Plugins can be registered at runtime or discovered via entry points.
    
    Example:
        >>> registry = PluginRegistry()
        >>> registry.register("jira", JiraPlugin())
        >>> plugin = registry.get("jira")
        >>> tools = plugin.get_tools()
    """
    
    def __init__(self) -> None:
        """Initialize empty registry."""
        self._plugins: dict[str, PluginProtocol] = {}
        self._lock = Lock()
        logger.debug("Initialized PluginRegistry")
    
    def register(
        self, 
        name: str, 
        plugin: PluginProtocol,
        replace: bool = False
    ) -> None:
        """
        Register a plugin.
        
        Args:
            name: Unique plugin identifier
            plugin: Plugin instance (must have get_tools() and execute() methods)
            replace: If True, replace existing plugin with same name
            
        Raises:
            PluginAlreadyRegisteredError: If plugin exists and replace=False
            InvalidPluginError: If plugin missing required methods
            
        Example:
            >>> from my_package import JiraPlugin
            >>> registry.register("jira", JiraPlugin())
        """
        # Validate plugin interface
        if not hasattr(plugin, "get_tools") or not callable(plugin.get_tools):
            raise InvalidPluginError(
                f"Plugin '{name}' must implement get_tools() method"
            )
        
        if not hasattr(plugin, "execute") or not callable(plugin.execute):
            raise InvalidPluginError(
                f"Plugin '{name}' must implement execute() method"
            )
        
        # Validate tool definitions for uniqueness and shape
        self._validate_plugin_tools(name=name, plugin=plugin)

        with self._lock:
            if name in self._plugins and not replace:
                raise PluginAlreadyRegisteredError(
                    f"Plugin '{name}' already registered. "
                    f"Use replace=True to override."
                )
            
            self._plugins[name] = plugin
            logger.info(f"Registered plugin: {name}")

    def _validate_plugin_tools(self, name: str, plugin: PluginProtocol) -> None:
        """Validate that a plugin's tools are well-formed and deduplicated across registry."""
        try:
            tools = plugin.get_tools()
        except Exception as exc:  # noqa: BLE001
            raise InvalidPluginError(f"Plugin '{name}' get_tools() failed: {exc}") from exc

        if not isinstance(tools, list):
            raise InvalidPluginError(f"Plugin '{name}' get_tools() must return a list, got {type(tools).__name__}")

        seen_local: set[str] = set()
        for tool in tools:
            if not isinstance(tool, dict):
                raise InvalidPluginError(
                    f"Plugin '{name}' get_tools() entries must be dicts, got {type(tool).__name__}"
                )
            tool_name = tool.get("name")
            if not tool_name or not isinstance(tool_name, str):
                raise InvalidPluginError(f"Plugin '{name}' tool missing string 'name' field")
            if tool_name in seen_local:
                raise DuplicateToolNameError(
                    f"Plugin '{name}' defines duplicate tool name '{tool_name}'"
                )
            seen_local.add(tool_name)

        # Cross-plugin duplicate detection
        with self._lock:
            existing_names = {
                t.get("name")
                for p in self._plugins.values()
                for t in (p.get_tools() or [])
                if isinstance(t, dict) and t.get("name")
            }
        dup = seen_local.intersection(existing_names)
        if dup:
            raise DuplicateToolNameError(
                f"Plugin '{name}' tool names collide with existing registry: {', '.join(sorted(dup))}"
            )
    
    def unregister(self, name: str) -> None:
        """
        Unregister a plugin.
        
        Args:
            name: Plugin identifier
            
        Raises:
            PluginNotFoundError: If plugin not found
            
        Example:
            >>> registry.unregister("jira")
        """
        with self._lock:
            if name not in self._plugins:
                raise PluginNotFoundError(f"Plugin '{name}' not found")
            
            del self._plugins[name]
            logger.info(f"Unregistered plugin: {name}")
    
    def get(self, name: str) -> PluginProtocol:
        """
        Get a plugin by name.
        
        Args:
            name: Plugin identifier
            
        Returns:
            Plugin instance
            
        Raises:
            PluginNotFoundError: If plugin not found
            
        Example:
            >>> plugin = registry.get("jira")
            >>> tools = plugin.get_tools()
        """
        with self._lock:
            if name not in self._plugins:
                raise PluginNotFoundError(
                    f"Plugin '{name}' not found. "
                    f"Available plugins: {', '.join(self._plugins.keys())}"
                )
            
            return self._plugins[name]
    
    def list(self) -> list[str]:
        """
        List all registered plugin names.
        
        Returns:
            List of plugin names
            
        Example:
            >>> registry.list()
            ['jira', 'slack', 'github']
        """
        with self._lock:
            return list(self._plugins.keys())
    
    def has(self, name: str) -> bool:
        """
        Check if plugin is registered.
        
        Args:
            name: Plugin identifier
            
        Returns:
            True if plugin exists
            
        Example:
            >>> if registry.has("jira"):
            ...     plugin = registry.get("jira")
        """
        with self._lock:
            return name in self._plugins
    
    def clear(self) -> None:
        """
        Clear all plugins (mainly for testing).
        
        Example:
            >>> registry.clear()
            >>> assert registry.list() == []
        """
        with self._lock:
            self._plugins.clear()
            logger.debug("Cleared all plugins")
    
    def get_all_tools(self) -> dict[str, List[Dict[str, Any]]]:
        """
        Get all tools from all plugins.
        
        Returns:
            Dict mapping plugin name to list of tools
            
        Example:
            >>> tools = registry.get_all_tools()
            >>> print(tools)
            {
                'jira': [{'name': 'create_issue', ...}],
                'slack': [{'name': 'send_message', ...}]
            }
        """
        with self._lock:
            all_tools = {}
            for name, plugin in self._plugins.items():
                try:
                    tools = plugin.get_tools()
                    all_tools[name] = tools
                except Exception as e:
                    logger.error(f"Error getting tools from plugin '{name}': {e}")
                    all_tools[name] = []
            
            return all_tools


# ============================================================
# Global Registry Singleton
# ============================================================

_global_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """
    Get the global plugin registry.
    
    Returns:
        Global PluginRegistry instance
        
    Example:
        >>> registry = get_registry()
        >>> registry.register("jira", JiraPlugin())
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = PluginRegistry()
    
    return _global_registry


# ============================================================
# Convenience Functions
# ============================================================

def register_plugin(
    name: str, 
    plugin: PluginProtocol,
    replace: bool = False
) -> None:
    """
    Register a plugin in the global registry.
    
    Args:
        name: Unique plugin identifier
        plugin: Plugin instance
        replace: If True, replace existing plugin
        
    Example:
        >>> from orchestrator.plugins import register_plugin
        >>> from my_package import JiraPlugin
        >>> 
        >>> register_plugin("jira", JiraPlugin())
    """
    registry = get_registry()
    registry.register(name, plugin, replace=replace)


def unregister_plugin(name: str) -> None:
    """
    Unregister a plugin from the global registry.
    
    Args:
        name: Plugin identifier
        
    Example:
        >>> from orchestrator.plugins import unregister_plugin
        >>> unregister_plugin("jira")
    """
    registry = get_registry()
    registry.unregister(name)


def get_plugin(name: str) -> PluginProtocol:
    """
    Get a plugin from the global registry.
    
    Args:
        name: Plugin identifier
        
    Returns:
        Plugin instance
        
    Example:
        >>> from orchestrator.plugins import get_plugin
        >>> plugin = get_plugin("jira")
        >>> tools = plugin.get_tools()
    """
    registry = get_registry()
    return registry.get(name)


def list_plugins() -> list[str]:
    """
    List all registered plugins.
    
    Returns:
        List of plugin names
        
    Example:
        >>> from orchestrator.plugins import list_plugins
        >>> plugins = list_plugins()
        >>> print(f"Available plugins: {', '.join(plugins)}")
    """
    registry = get_registry()
    return registry.list()


# ============================================================
# Entry Point Discovery
# ============================================================

def discover_plugins() -> dict[str, PluginProtocol]:
    """
    Discover and load plugins via entry points.
    
    Looks for entry points in the 'toolweaver.plugins' group.
    
    Returns:
        Dict mapping plugin name to plugin instance
        
    Example:
        >>> from orchestrator.plugins import discover_plugins
        >>> discovered = discover_plugins()
        >>> print(f"Found {len(discovered)} plugins")
        
    Entry Point Example (pyproject.toml):
        [project.entry-points."toolweaver.plugins"]
        jira = "toolweaver_jira:JiraPlugin"
    """
    discovered = {}
    
    # Python 3.10+ has importlib.metadata
    if sys.version_info >= (3, 10):
        try:
            from importlib.metadata import entry_points
            
            # Get entry points for toolweaver.plugins group
            eps = entry_points(group='toolweaver.plugins')
            
            for ep in eps:
                try:
                    # Load the entry point
                    plugin_class = ep.load()
                    
                    # Instantiate if it's a class
                    if isinstance(plugin_class, type):
                        plugin: PluginProtocol = plugin_class()  # type: ignore[call-arg]
                    else:
                        plugin = plugin_class  # type: ignore[assignment]
                    
                    # Register in global registry
                    register_plugin(ep.name, plugin)
                    discovered[ep.name] = plugin
                    
                    logger.info(f"Discovered and registered plugin: {ep.name}")
                
                except Exception as e:
                    logger.error(f"Failed to load plugin '{ep.name}': {e}")
        
        except Exception as e:
            logger.error(f"Failed to discover plugins: {e}")
    
    else:
        logger.warning(
            "Plugin discovery requires Python 3.10+. "
            "Plugins must be registered manually."
        )
    
    return discovered


# ============================================================
# Export
# ============================================================

__all__ = [
    # Errors
    "PluginError",
    "PluginNotFoundError",
    "PluginAlreadyRegisteredError",
    "InvalidPluginError",
    # Registry
    "PluginRegistry",
    "PluginProtocol",
    "get_registry",
    # Convenience functions
    "register_plugin",
    "unregister_plugin",
    "get_plugin",
    "list_plugins",
    "discover_plugins",
]
