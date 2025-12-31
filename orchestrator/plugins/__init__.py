"""
Plugin system for ToolWeaver.

Allows 3rd-party packages to register tools without modifying ToolWeaver source.

Usage (in your package):
    from orchestrator.plugins import register_plugin
    from .my_tools import MyToolPlugin
    
    register_plugin("my-tools", MyToolPlugin)

Usage (in ToolWeaver):
    from orchestrator.plugins import get_plugin, list_plugins
    
    plugin = get_plugin("my-tools")
    all_plugins = list_plugins()
"""

from orchestrator.plugins.registry import (
    InvalidPluginError,
    PluginAlreadyRegisteredError,
    PluginError,
    PluginNotFoundError,
    PluginRegistry,
    discover_plugins,
    get_plugin,
    get_registry,
    list_plugins,
    register_plugin,
    unregister_plugin,
)

__all__ = [
    "register_plugin",
    "unregister_plugin",
    "get_plugin",
    "list_plugins",
    "discover_plugins",
    "get_registry",
    "PluginRegistry",
    "PluginError",
    "PluginNotFoundError",
    "PluginAlreadyRegisteredError",
    "InvalidPluginError",
]
