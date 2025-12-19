from __future__ import annotations

from typing import Any, Dict, List, Optional

import aiohttp

from ..plugins.registry import PluginProtocol, register_plugin, get_registry
from ..shared.models import ToolDefinition


class MCPHttpAdapterPlugin:
    """Plugin that discovers tools from a remote MCP-like HTTP server and executes them.

    Expected server endpoints:
    - GET /tools -> [{ToolDefinition-like dict}, ...]
    - POST /execute -> { name: str, params: dict } returns result JSON
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._defs: Dict[str, ToolDefinition] = {}

    def get_tools(self) -> List[Dict[str, Any]]:
        return [td.model_dump() for td in self._defs.values()]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/execute",
                json={"name": tool_name, "params": params},
            ) as resp:
                resp.raise_for_status()
                ct = resp.headers.get("Content-Type", "")
                if ct.startswith("application/json"):
                    return await resp.json()
                return await resp.text()

    async def discover(self) -> Dict[str, ToolDefinition]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/tools") as resp:
                resp.raise_for_status()
                tools = await resp.json()
                self._defs.clear()
                for t in tools:
                    try:
                        td = ToolDefinition.model_validate(t)
                        self._defs[td.name] = td
                    except Exception:
                        # Skip invalid entries
                        continue
        return dict(self._defs)


def register_mcp_http_adapter(name: str, base_url: str) -> MCPHttpAdapterPlugin:
    plugin = MCPHttpAdapterPlugin(base_url)
    register_plugin(name, plugin)
    return plugin
