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

from collections.abc import Awaitable, Callable, Iterable
from typing import Any, Optional, Protocol, Union

__version__ = "0.13.0"


# ============================================================
# Phase 0 (Package Infrastructure) - Clean Public API
# ============================================================
# Only export what users should use. Everything else lives in _internal.
# This makes it clear what's safe to import and what might change.

# === Core Tool Registration (Phase 2) ===
# Phase 2: Decorators available for function, MCP, and agent tools
# === Agent-to-Agent (A2A) Client (Phase 1.7) ===
# ✅ DONE: Agent delegation and discovery
# === Skill Bridge (Phase 1.5) ===
# ✅ DONE: Phase 1.5 complete - Connect tools to skill library
from ._internal.execution import skill_library

# === Sandbox Execution (Phase 1.8) ===
# ✅ DONE: Sandboxed code execution
from ._internal.execution.sandbox import SandboxEnvironment
from ._internal.infra.a2a_client import (
    A2AClient,
    AgentCapability,
    AgentDelegationRequest,
    AgentDelegationResponse,
)

# === MCP Client (Phase 1) ===
# ✅ DONE: MCP tool execution and registration
from ._internal.infra.mcp_client import MCPClientShim

# === Logging (Phase 0.l) ===
# ✅ DONE: Phase 0.l complete
from ._internal.logger import enable_debug_mode, get_logger, set_log_level
from ._internal.security.secrets_redactor import install_secrets_redactor

# === Configuration (Phase 0.c) ===
# ✅ DONE: Phase 0.c complete - Environment variable configuration
from .config import get_config, reset_config, validate_config

# === Plugin Registry (Phase 0.e) ===
# ✅ DONE: Phase 0.e complete - Plugin system for 3rd-party extensions
from .plugins import discover_plugins, get_plugin, list_plugins, register_plugin, unregister_plugin
from .tools.decorators import a2a_agent, mcp_tool, tool
from .tools.discovery_api import (
    browse_tools,
    get_available_tools,
    get_tool_info,
    list_tools_by_domain,
    search_tools,
    semantic_search_tools,
)

# === YAML Loader (Phase 3) ===
# ✅ DONE: Phase 3 complete - YAML-based tool registration
from .tools.loaders import (
    WorkerResolutionError,
    YAMLLoaderError,
    YAMLValidationError,
    load_tools_from_directory,
    load_tools_from_yaml,
)
from .tools.skill_bridge import (
    get_skill_backed_tools,
    get_tool_skill,
    load_tool_from_skill,
    save_tool_as_skill,
    sync_tool_with_skill,
)
from .tools.templates import (
    AgentTemplate,
    BaseTemplate,
    CodeExecToolTemplate,
    FunctionToolTemplate,
    MCPToolTemplate,
    register_template,
)

# ============================================================
# Public API Definition
# ============================================================
# This is what users can safely import.
# Anything not listed here might change between versions.

__all__ = [
    # Version
    "__version__",

    # Core Decorators (Phase 2)
    "tool",
    "mcp_tool",
    "a2a_agent",

    # Template Classes (Phase 1)
    "BaseTemplate",
    "FunctionToolTemplate",
    "MCPToolTemplate",
    "CodeExecToolTemplate",
    "AgentTemplate",
    "register_template",

    # YAML Loader (Phase 3)
    "load_tools_from_yaml",
    "load_tools_from_directory",
    "YAMLLoaderError",
    "YAMLValidationError",
    "WorkerResolutionError",

    # Skill Bridge (Phase 1.5)
    "save_tool_as_skill",
    "load_tool_from_skill",
    "get_tool_skill",
    "sync_tool_with_skill",
    "get_skill_backed_tools",

    # Discovery API (Phase 1.6)
    "get_available_tools",
    "search_tools",
    "get_tool_info",
    "list_tools_by_domain",
    "semantic_search_tools",
    "browse_tools",

    # Plugins (Phase 0.e)
    "register_plugin",
    "unregister_plugin",
    "get_plugin",
    "list_plugins",
    "discover_plugins",

    # Configuration (Phase 0.c)
    "get_config",
    "reset_config",
    "validate_config",

    # Logging (Phase 0.l)
    "get_logger",
    "set_log_level",
    "enable_debug_mode",

    # Agent-to-Agent (A2A) Client (Phase 1.7)
    "AgentCapability",
    "AgentDelegationRequest",
    "AgentDelegationResponse",
    "A2AClient",

    # MCP Client (Phase 1)
    "MCPClientShim",

    # Skill Library (Phase 1.5)
    "skill_library",

    # Sandbox Execution (Phase 1.8)
    "SandboxEnvironment",
]

# Auto-install secrets redaction on root logger to prevent credential leakage in logs.
install_secrets_redactor()

# ============================================================
# Important: Do not import from orchestrator._internal
# ============================================================
# Users: These are internal implementation details that might change.
# Contributors: Put helper code in _internal, not in public API.
