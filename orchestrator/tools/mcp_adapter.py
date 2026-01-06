from __future__ import annotations

import json
from typing import Any

import aiohttp
from aiohttp import TCPConnector

from ..plugins.registry import register_plugin
from ..shared.models import ToolDefinition


class MCPHttpAdapterPlugin:
    """Plugin that discovers tools from a remote MCP-like HTTP server and executes them.

    Expected server endpoints:
    - GET /tools -> [{ToolDefinition-like dict}, ...]
    - POST /execute -> { name: str, params: dict } returns result JSON
    """

    def __init__(
        self,
        base_url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout_s: int = 15,
        verify_ssl: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._defs: dict[str, ToolDefinition] = {}
        self.headers: dict[str, str] = headers or {}
        self.timeout_s = timeout_s
        self.verify_ssl = verify_ssl

    def get_tools(self) -> list[dict[str, Any]]:
        return [td.model_dump() for td in self._defs.values()]

    async def execute(self, tool_name: str, params: dict[str, Any]) -> Any:
        connector = TCPConnector(ssl=self.verify_ssl)
        timeout = aiohttp.ClientTimeout(total=self.timeout_s)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/execute",
                json={"name": tool_name, "params": params},
                headers=self.headers,
            ) as resp:
                resp.raise_for_status()
                ct = resp.headers.get("Content-Type", "")
                if ct.startswith("application/json"):
                    return await resp.json()
                return await resp.text()

    async def discover(self) -> dict[str, ToolDefinition]:
        connector = TCPConnector(ssl=self.verify_ssl)
        timeout = aiohttp.ClientTimeout(total=self.timeout_s)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(f"{self.base_url}/tools", headers=self.headers) as resp:
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
        self, tool_name: str, params: dict[str, Any], protocol: str = "http"
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

    async def _stream_http(self, tool_name: str, params: dict[str, Any]):
        """Stream chunked response from HTTP endpoint."""
        connector = TCPConnector(ssl=self.verify_ssl)
        timeout = aiohttp.ClientTimeout(total=self.timeout_s)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/execute",
                json={"name": tool_name, "params": params},
                headers=self.headers,
            ) as resp:
                resp.raise_for_status()
                async for chunk in resp.content.iter_chunked(1024):
                    if chunk:
                        yield chunk.decode()

    async def _stream_sse(self, tool_name: str, params: dict[str, Any]):
        """Stream SSE messages from endpoint."""
        connector = TCPConnector(ssl=self.verify_ssl)
        timeout = aiohttp.ClientTimeout(total=self.timeout_s)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            url = f"{self.base_url}/execute/sse"
            async with session.post(
                url,
                json={"name": tool_name, "params": params},
                headers={"Accept": "text/event-stream", **self.headers},
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

    async def _stream_websocket(self, tool_name: str, params: dict[str, Any]):
        """Stream messages via WebSocket connection."""
        from aiohttp import WSMsgType

        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/execute/ws"

        connector = TCPConnector(ssl=self.verify_ssl)
        timeout = aiohttp.ClientTimeout(total=self.timeout_s)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.ws_connect(ws_url, headers=self.headers) as ws:
                await ws.send_json({"name": tool_name, "params": params})
                async for msg in ws:
                    if msg.type == WSMsgType.TEXT:
                        yield msg.data
                    elif msg.type == WSMsgType.BINARY:
                        yield msg.data
                    elif msg.type in (WSMsgType.CLOSED, WSMsgType.CLOSING, WSMsgType.ERROR):
                        break


def register_mcp_http_adapter(
    name: str,
    base_url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout_s: int = 15,
    verify_ssl: bool = True,
) -> MCPHttpAdapterPlugin:
    plugin = MCPHttpAdapterPlugin(base_url, headers=headers, timeout_s=timeout_s, verify_ssl=verify_ssl)
    register_plugin(name, plugin)
    return plugin


class MCPWebSocketAdapterPlugin:
    """Plugin that discovers tools from an MCP WebSocket JSON-RPC server and executes them.

    Expected behavior (MCP JSON-RPC over WebSocket):
    - Connect to provided ws/wss URL (no path rewriting)
    - Send {"jsonrpc":"2.0","id":1,"method":"tools/list"} to discover tools
    - Send {"jsonrpc":"2.0","id":X,"method":"tools/call","params":{"name": str, "arguments": dict}} to execute
    """

    def __init__(
        self,
        base_url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout_s: int = 15,
        verify_ssl: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._defs: dict[str, ToolDefinition] = {}
        self.headers: dict[str, str] = headers or {}
        self.timeout_s = timeout_s
        self.verify_ssl = verify_ssl

    def get_tools(self) -> list[dict[str, Any]]:
        return [td.model_dump() for td in self._defs.values()]

    async def discover(self) -> dict[str, ToolDefinition]:
        connector = TCPConnector(ssl=self.verify_ssl)
        timeout = aiohttp.ClientTimeout(total=self.timeout_s)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.ws_connect(self.base_url, headers=self.headers) as ws:
                await ws.send_json({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
                # Await a single response with result
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            payload = json.loads(msg.data)
                        except Exception:
                            break
                        if isinstance(payload, dict) and payload.get("result") is not None:
                            tools = payload["result"]
                            self._defs.clear()
                            for t in tools or []:
                                try:
                                    td = ToolDefinition.model_validate(t)
                                    self._defs[td.name] = td
                                except Exception:
                                    continue
                            break
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.ERROR):
                        break
        return dict(self._defs)

    async def execute(self, tool_name: str, params: dict[str, Any]) -> Any:
        connector = TCPConnector(ssl=self.verify_ssl)
        timeout = aiohttp.ClientTimeout(total=self.timeout_s)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.ws_connect(self.base_url, headers=self.headers) as ws:
                req = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": params},
                }
                await ws.send_json(req)
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            payload = json.loads(msg.data)
                            if isinstance(payload, dict) and (payload.get("result") is not None or payload.get("error") is not None):
                                return payload
                        except Exception:
                            return msg.data
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.ERROR):
                        break
        return None


def register_mcp_ws_adapter(
    name: str,
    base_url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout_s: int = 15,
    verify_ssl: bool = True,
) -> MCPWebSocketAdapterPlugin:
    plugin = MCPWebSocketAdapterPlugin(base_url, headers=headers, timeout_s=timeout_s, verify_ssl=verify_ssl)
    register_plugin(name, plugin)
    return plugin


class MCPJsonRpcHttpAdapterPlugin:
    """Plugin for JSON-RPC over HTTP with SSE responses (e.g., MCP servers).

    Expected behavior:
    - POST to base_url with JSON-RPC request: {"jsonrpc": "2.0", "id": X, "method": "...", "params": {...}}
    - Response comes as SSE: "event: message\\ndata: {...}\\n\\n"
    - Methods: "tools/list" for discovery, "tools/call" for execution
    - Requires Accept header: "application/json, text/event-stream"
    """

    def __init__(
        self,
        base_url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout_s: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._defs: dict[str, ToolDefinition] = {}
        self.headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            **(headers or {}),
        }
        self.timeout_s = timeout_s
        self.verify_ssl = verify_ssl
        self._request_id = 0

    def get_tools(self) -> list[dict[str, Any]]:
        return [td.model_dump() for td in self._defs.values()]

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _parse_sse_response(self, text: str) -> dict[str, Any] | None:
        """Parse SSE formatted response and extract JSON-RPC data."""
        for line in text.strip().split("\n"):
            if line.startswith("data:"):
                data_str = line[5:].strip()
                try:
                    result: dict[str, Any] = json.loads(data_str)
                    return result
                except Exception:
                    continue
        return None

    async def discover(self) -> dict[str, ToolDefinition]:
        """Discover tools using JSON-RPC tools/list method."""
        connector = TCPConnector(ssl=self.verify_ssl)
        timeout = aiohttp.ClientTimeout(total=self.timeout_s)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            req = {"jsonrpc": "2.0", "id": self._next_id(), "method": "tools/list"}
            async with session.post(self.base_url, json=req, headers=self.headers) as resp:
                resp.raise_for_status()
                content = await resp.text()
                data = self._parse_sse_response(content)

                if not data or "result" not in data:
                    return {}

                result = data["result"]
                tools_list = result.get("tools", [])

                self._defs.clear()
                for tool_data in tools_list:
                    try:
                        # Convert MCP format to ToolDefinition
                        td = ToolDefinition(
                            name=tool_data["name"],
                            type="mcp",
                            description=tool_data.get("description", ""),
                            input_schema=tool_data.get("inputSchema", {"type": "object", "properties": {}}),
                        )
                        self._defs[td.name] = td
                    except Exception:
                        continue

        return dict(self._defs)

    async def execute(self, tool_name: str, params: dict[str, Any]) -> Any:
        """Execute tool using JSON-RPC tools/call method."""
        connector = TCPConnector(ssl=self.verify_ssl)
        timeout = aiohttp.ClientTimeout(total=self.timeout_s)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            req = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": params},
            }
            async with session.post(self.base_url, json=req, headers=self.headers) as resp:
                resp.raise_for_status()
                content = await resp.text()
                data = self._parse_sse_response(content)

                if not data:
                    return {"error": "Failed to parse response"}

                if "error" in data:
                    return data

                return data.get("result", {})


def register_mcp_jsonrpc_http_adapter(
    name: str,
    base_url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout_s: int = 30,
    verify_ssl: bool = True,
) -> MCPJsonRpcHttpAdapterPlugin:
    plugin = MCPJsonRpcHttpAdapterPlugin(base_url, headers=headers, timeout_s=timeout_s, verify_ssl=verify_ssl)
    register_plugin(name, plugin)
    return plugin
