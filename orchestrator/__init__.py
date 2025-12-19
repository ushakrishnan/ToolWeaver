"""
ToolWeaver - Package-first tool orchestration library.

A lightweight, composable package for registering and managing tools
that can be called by LLMs, APIs, CLI, or any Python application.

Philosophy: Users pip install toolweaver and use it in their own apps.
Not a framework—you control your architecture.

Package Users:
    from orchestrator import mcp_tool, search_tools
    
    @mcp_tool(domain="finance")
    async def get_balance(account: str) -> dict: ...

Contributors:
    Modify source via PR to add core features.
    Everything else is in orchestrator._internal (not part of public API).
"""

from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Protocol, Tuple, Union

__version__ = "0.3.0"

# ---------------------------------------------------------------------------
# Public API placeholders (Phase 0 readiness)
# These stubs avoid import errors while the new surfaces are built in later
# phases. They deliberately raise NotImplementedError to signal planned work.
# ---------------------------------------------------------------------------

def mcp_tool(*args: Any, **kwargs: Any) -> Callable[[Callable[..., Awaitable[Dict[str, Any]]]], Callable[..., Awaitable[Dict[str, Any]]]]:
    """Placeholder decorator for MCP tools (Phase 2)."""
    raise NotImplementedError("mcp_tool decorator will ship in Phase 2")


def a2a_agent(*args: Any, **kwargs: Any) -> Callable[[Callable[..., Awaitable[Dict[str, Any]]]], Callable[..., Awaitable[Dict[str, Any]]]]:
    """Placeholder decorator for agent-to-agent tools (Phase 2)."""
    raise NotImplementedError("a2a_agent decorator will ship in Phase 2")


class ToolTemplate:
    """Abstract base placeholder for tool templates (Phase 1)."""

    def execute(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - placeholder
        raise NotImplementedError("ToolTemplate.execute will ship in Phase 1")


class MCPToolTemplate(ToolTemplate):
    """Placeholder MCP tool template (Phase 1)."""


class A2AAgentTemplate(ToolTemplate):
    """Placeholder agent template (Phase 1)."""


def get_available_tools(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
    """Placeholder discovery API (Phase 1.6)."""
    raise NotImplementedError("Discovery API will ship in Phase 1.6")


def search_tools(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
    """Placeholder discovery API (Phase 1.6)."""
    raise NotImplementedError("Discovery API will ship in Phase 1.6")


def get_tool_info(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Placeholder discovery API (Phase 1.6)."""
    raise NotImplementedError("Discovery API will ship in Phase 1.6")


def save_as_skill(*args: Any, **kwargs: Any) -> str:
    """Placeholder skill bridge (Phase 1.5)."""
    raise NotImplementedError("Skill bridge will ship in Phase 1.5")


def load_from_skill(*args: Any, **kwargs: Any) -> Any:
    """Placeholder skill bridge (Phase 1.5)."""
    raise NotImplementedError("Skill bridge will ship in Phase 1.5")


class ToolError(Exception):
    """Base placeholder for tool-related errors (Phase 1.b)."""


class ToolNotFoundError(ToolError):
    """Placeholder for missing tool error (Phase 1.b)."""


class InvalidParametersError(ToolError):
    """Placeholder for invalid params error (Phase 1.b)."""


class ToolTimeoutError(ToolError):
    """Placeholder for timeout error (Phase 1.b)."""


class ToolExecutionError(ToolError):
    """Placeholder for execution error (Phase 1.b)."""


def get_tool_health(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Placeholder diagnostics (Phase 1.c)."""
    raise NotImplementedError("Diagnostics will ship in Phase 1.c")


def get_execution_stats(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Placeholder diagnostics (Phase 1.c)."""
    raise NotImplementedError("Diagnostics will ship in Phase 1.c")

# ============================================================
# Phase 0 (Package Infrastructure) - Clean Public API
# ============================================================
# Only export what users should use. Everything else lives in _internal.
# This makes it clear what's safe to import and what might change.

# === Core Tool Registration (Phase 2) ===
# Phase 1: Minimal decorator available now
from .tools.decorators import tool
from .tools.templates import (
    BaseTemplate,
    FunctionToolTemplate,
    MCPToolTemplate,
    CodeExecToolTemplate,
    AgentTemplate,
    register_template,
)
from .tools.discovery_api import (
    get_available_tools,
    search_tools,
    get_tool_info,
    list_tools_by_domain,
    semantic_search_tools,
    browse_tools,
)

# === Template Base Classes (Phase 1) ===
# TODO: These will be imported from .tools.templates after Phase 1
# from .tools.templates import ToolTemplate, MCPToolTemplate, A2AAgentTemplate

# === Tool Discovery (Phase 1.6) ===
# TODO: These will be imported from .tools.discovery_api after Phase 1.6
# from .tools import get_available_tools, search_tools, get_tool_info

# === Skill Bridge (Phase 1.5) ===
# ✅ DONE: Phase 1.5 complete - Connect tools to skill library
from .tools.skill_bridge import (
    save_tool_as_skill,
    load_tool_from_skill,
    get_tool_skill,
    sync_tool_with_skill,
    get_skill_backed_tools,
)

# === Plugin Registry (Phase 0.e) ===
# ✅ DONE: Phase 0.e complete - Plugin system for 3rd-party extensions
from orchestrator.plugins import register_plugin, unregister_plugin, get_plugin, list_plugins, discover_plugins

# === Configuration (Phase 0.c) ===
# ✅ DONE: Phase 0.c complete - Environment variable configuration
from orchestrator.config import get_config, reset_config, validate_config
# from .config import get_config, config

# === Logging (Phase 0.l) ===
# ✅ DONE: Phase 0.l complete
from ._internal.logger import get_logger, set_log_level, enable_debug_mode

# === Error Types (Phase 1.b) ===
# TODO: These will be imported from ._internal.exceptions after Phase 1.b
# ToolError, ToolNotFoundError, InvalidParametersError, etc.

# === Diagnostics (Phase 1.c) ===
# TODO: This will be imported from .diagnostics after Phase 1.c
# from .diagnostics import get_tool_health, get_execution_stats

# ============================================================
# Temporary: Legacy surfaces via internal shim (compatibility only)
# (These will be phased out as new APIs land.)
# ============================================================

try:
    from ._internal.public_legacy import *  # noqa: F401, F403
except Exception:
    # Optional legacy features not available
    pass

# ============================================================
# Public API Definition
# ============================================================
# This is what users can safely import.
# Anything not listed here might change between versions.

__all__ = [
    # TODO Phase 0: Add these as phases complete
    # Tool registration
    "mcp_tool",
    "a2a_agent",
    "tool",
    "BaseTemplate",
    "FunctionToolTemplate",
    "MCPToolTemplate",
    "CodeExecToolTemplate",
    "AgentTemplate",
    "register_template",
    # Discovery API
    "get_available_tools",
    "search_tools",
    "get_tool_info",
    "list_tools_by_domain",
    "semantic_search_tools",
    "browse_tools",
    # Templates
    "ToolTemplate",
    "MCPToolTemplate",
    "A2AAgentTemplate",
    # Discovery & querying
    "get_available_tools",
    "search_tools",
    "get_tool_info",
    "semantic_search_tools",
    # Skill bridge
    "save_tool_as_skill",
    "load_tool_from_skill",
    "get_tool_skill",
    "sync_tool_with_skill",
    "get_skill_backed_tools",
    # Plugins
    "register_plugin",
    "unregister_plugin",
    "get_plugin",
    "list_plugins",
    "discover_plugins",
    # Configuration
    "get_config",
    "reset_config",
    "validate_config",
    # Logging
    "get_logger",
    "set_log_level",
    "enable_debug_mode",
    # Diagnostics
    "get_tool_health",
    "get_execution_stats",
    # Error types
    "ToolError",
    "ToolNotFoundError",
    "InvalidParametersError",
    "ToolTimeoutError",
    "ToolExecutionError",
]

# ============================================================
# Important: Do not import from orchestrator._internal
# ============================================================
# Users: These are internal implementation details that might change.
# Contributors: Put helper code in _internal, not in public API.
