from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from .mcp_adapter import (
    register_mcp_http_adapter,
    register_mcp_jsonrpc_http_adapter,
    register_mcp_ws_adapter,
)


def load_mcp_servers_from_json(config_path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Load MCP server definitions from a JSON config and register HTTP adapters.

    Supported formats (Claude-compatible):
    - Claude array format:
        {
          "mcpServers": [
            {
              "name": "github",
              "url": "https://...",
              "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" },
              "protocol": "http"
            }
          ]
        }
    - Claude map format (legacy):
        {
          "mcpServers": {
            "server-name": { "url": "https://...", "protocol": "http" }
          }
        }
    - Simple list format:
        {
          "servers": [ { "name": "github", "url": "https://...", "protocol": "http" } ]
        }

    The `env` field is for documentation/configuration but doesn't directly affect
    the adapter (token passing is handled via headers/auth mechanisms).

    Environment integration:
    - If `config_path` is None, checks `MCP_SERVERS_FILE` then `CLAUDE_SERVERS_FILE` env vars.

    Returns:
        Dict of registered adapters keyed by server name.
    """
    cfg_path = _resolve_config_path(config_path)
    if cfg_path is None or not Path(cfg_path).exists():
        return {}

    try:
        data = json.loads(Path(cfg_path).read_text())
    except Exception:
        return {}

    adapters: dict[str, Any] = {}

    # Claude-style mcpServers (can be array or object)
    mcp_servers = data.get("mcpServers")

    # Handle array format (modern Claude style)
    if isinstance(mcp_servers, list):
        for entry in mcp_servers:
            name = entry.get("name") or entry.get("id")
            url = _extract_url(entry)
            if not name or not url:
                continue
            headers = _extract_headers(entry)
            timeout_s = _extract_timeout(entry)
            verify_ssl = _extract_verify_ssl(entry)
            protocol = _extract_protocol(entry, url)
            if protocol == "websocket":
                adapters[name] = register_mcp_ws_adapter(
                    name,
                    url,
                    headers=headers,
                    timeout_s=timeout_s,
                    verify_ssl=verify_ssl,
                )
            elif protocol == "json_rpc":
                adapters[name] = register_mcp_jsonrpc_http_adapter(
                    name,
                    url,
                    headers=headers,
                    timeout_s=timeout_s,
                    verify_ssl=verify_ssl,
                )
            else:
                adapters[name] = register_mcp_http_adapter(
                    name,
                    url,
                    headers=headers,
                    timeout_s=timeout_s,
                    verify_ssl=verify_ssl,
                )

    # Handle map format (legacy Claude style)
    elif isinstance(mcp_servers, dict):
        for name, entry in mcp_servers.items():
            url = _extract_url(entry)
            if not url:
                continue
            headers = _extract_headers(entry)
            timeout_s = _extract_timeout(entry)
            verify_ssl = _extract_verify_ssl(entry)
            protocol = _extract_protocol(entry, url)
            if protocol == "websocket":
                adapters[name] = register_mcp_ws_adapter(
                    name,
                    url,
                    headers=headers,
                    timeout_s=timeout_s,
                    verify_ssl=verify_ssl,
                )
            elif protocol == "json_rpc":
                adapters[name] = register_mcp_jsonrpc_http_adapter(
                    name,
                    url,
                    headers=headers,
                    timeout_s=timeout_s,
                    verify_ssl=verify_ssl,
                )
            else:
                adapters[name] = register_mcp_http_adapter(
                    name,
                    url,
                    headers=headers,
                    timeout_s=timeout_s,
                    verify_ssl=verify_ssl,
                )

    # Simple list of servers (fallback)
    servers = data.get("servers")
    if isinstance(servers, list):
        for entry in servers:
            name = entry.get("name") or entry.get("id")
            url = _extract_url(entry)
            if not name or not url:
                continue
            headers = _extract_headers(entry)
            timeout_s = _extract_timeout(entry)
            verify_ssl = _extract_verify_ssl(entry)
            protocol = _extract_protocol(entry, url)
            if protocol == "websocket":
                adapters[name] = register_mcp_ws_adapter(
                    name,
                    url,
                    headers=headers,
                    timeout_s=timeout_s,
                    verify_ssl=verify_ssl,
                )
            elif protocol == "json_rpc":
                adapters[name] = register_mcp_jsonrpc_http_adapter(
                    name,
                    url,
                    headers=headers,
                    timeout_s=timeout_s,
                    verify_ssl=verify_ssl,
                )
            else:
                adapters[name] = register_mcp_http_adapter(
                    name,
                    url,
                    headers=headers,
                    timeout_s=timeout_s,
                    verify_ssl=verify_ssl,
                )

    return adapters


def _resolve_config_path(config_path: str | os.PathLike[str] | None) -> str | None:
    r"""Resolve config path with sensible Windows defaults.

    Lookup order:
      1. Explicit `config_path` argument
      2. `MCP_SERVERS_FILE` env var
      3. `CLAUDE_SERVERS_FILE` env var (Windows: %USERPROFILE%\.claude\config.json)
    """
    if config_path:
        return str(config_path)

    env = os.getenv("MCP_SERVERS_FILE")
    if env:
        return env

    claude_env = os.getenv("CLAUDE_SERVERS_FILE")
    if claude_env:
        return claude_env

    # Windows-friendly default Claude Desktop path
    home = os.path.expanduser("~")
    default_claude = os.path.join(home, ".claude", "config.json")
    return default_claude if os.path.exists(default_claude) else None


def _extract_url(entry: dict[str, Any]) -> str | None:
    """Get base URL from a server entry supporting multiple keys."""
    if not isinstance(entry, dict):
        return None
    for key in ("url", "baseUrl", "base_url"):
        val = entry.get(key)
        if isinstance(val, str) and val:
            return _env_substitute(val)
    return None


def _extract_headers(entry: dict[str, Any]) -> dict[str, str]:
    """Extract headers and perform env substitution like ${ENV_VAR}."""
    headers: dict[str, str] = {}
    raw = entry.get("headers")
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                env_name = v[2:-1]
                env_val = os.getenv(env_name)
                if env_val:
                    # Auto-prefix Bearer for Authorization if missing
                    if k.lower() == "authorization" and not env_val.lower().startswith(("bearer ", "token ")):
                        headers[k] = f"Bearer {env_val}"
                    else:
                        headers[k] = env_val
            elif isinstance(v, str):
                headers[k] = v
    return headers


def _extract_timeout(entry: dict[str, Any]) -> int:
    val = entry.get("timeout_s")
    try:
        return int(val) if val is not None else 15
    except Exception:
        return 15


def _extract_verify_ssl(entry: dict[str, Any]) -> bool:
    val = entry.get("verify_ssl")
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("1", "true", "yes")
    return True


def _extract_protocol(entry: dict[str, Any], url: str | None) -> str:
    """Determine protocol for the adapter.

    Priority:
      1. Explicit 'protocol' field if valid
      2. Auto-detect from URL scheme (ws/wss -> websocket; default http)
    """
    p = entry.get("protocol")
    if isinstance(p, str) and p in {"http", "sse", "websocket", "json_rpc"}:
        return p
    if isinstance(url, str) and url.lower().startswith(("ws://", "wss://")):
        return "websocket"
    return "http"


def _env_substitute(text: str) -> str:
    """Replace ${VAR} occurrences with environment values, preserving unknowns.

    Example: "${JOKES_MCP_URL}" -> os.getenv("JOKES_MCP_URL", "${JOKES_MCP_URL}")
    Supports inline segments too: "https://${HOST}/mcp".
    """
    pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

    def repl(match: re.Match[str]) -> str:
        var = match.group(1)
        return os.getenv(var, match.group(0))

    return pattern.sub(repl, text)
