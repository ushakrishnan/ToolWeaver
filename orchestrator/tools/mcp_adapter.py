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

    async def execute_stream(
        self, tool_name: str, params: Dict[str, Any], protocol: str = "http"
    ):
        """Stream responses from a tool as an async generator.

        Supports http (chunked), sse, and websocket protocols.
        """
        if protocol == "http":
            async for chunk in self._stream_http(tool_name, params):
                yield chunk
        elif protocol == "sse":
            async for chunk in self._stream_sse(tool_name, params):
                yield chunk
        elif protocol == "websocket":
            async for chunk in self._stream_websocket(tool_name, params):
                yield chunk
        else:
            raise ValueError(f"Unsupported streaming protocol: {protocol}")

    async def _stream_http(self, tool_name: str, params: Dict[str, Any]):
        """Stream chunked response from HTTP endpoint."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/execute",
                json={"name": tool_name, "params": params},
            ) as resp:
                resp.raise_for_status()
                async for chunk in resp.content.iter_chunked(1024):
                    if chunk:
                        yield chunk.decode()

    async def _stream_sse(self, tool_name: str, params: Dict[str, Any]):
        """Stream SSE messages from endpoint."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/execute/sse"
            async with session.post(
                url,
                json={"name": tool_name, "params": params},
                headers={"Accept": "text/event-stream"},
            ) as resp:
                resp.raise_for_status()
                buffer = ""
                async for chunk in resp.content.iter_chunked(1024):
                    if not chunk:
                        continue
                    buffer += chunk.decode()
                    while "\n\n" in buffer:
                        event, buffer = buffer.split("\n\n", 1)
                        data_lines = []
                        for line in event.splitlines():
                            if line.startswith("data:"):
                                data_lines.append(line[len("data:"):].lstrip())
                        if data_lines:
                            yield "\n".join(data_lines)

    async def _stream_websocket(self, tool_name: str, params: Dict[str, Any]):
        """Stream messages via WebSocket connection."""
        from aiohttp import WSMsgType

        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/execute/ws"

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                await ws.send_json({"name": tool_name, "params": params})
                async for msg in ws:
                    if msg.type == WSMsgType.TEXT:
                        yield msg.data
                    elif msg.type == WSMsgType.BINARY:
                        yield msg.data
                    elif msg.type in (WSMsgType.CLOSED, WSMsgType.CLOSING, WSMsgType.ERROR):
                        break


def register_mcp_http_adapter(name: str, base_url: str) -> MCPHttpAdapterPlugin:
    plugin = MCPHttpAdapterPlugin(base_url)
    register_plugin(name, plugin)
    return plugin
