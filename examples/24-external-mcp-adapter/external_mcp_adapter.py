import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp


@dataclass
class AdapterConfig:
    endpoint: str
    timeout: float = 20.0
    auth_token: Optional[str] = None


class ExternalMCPAdapter:
    """
    Minimal external MCP adapter for demo purposes.

    Supports two transport shapes:
    - WebSocket JSON-RPC: send {"jsonrpc":"2.0","id":1,"method":"list_tools"}
    - HTTP: GET <endpoint>/tools and POST <endpoint>/execute
    """

    def __init__(self, config: AdapterConfig) -> None:
        self.config = config

    def _headers(self) -> Dict[str, str]:
        h: Dict[str, str] = {"Content-Type": "application/json"}
        if self.config.auth_token:
            h["Authorization"] = f"Bearer {self.config.auth_token}"
        return h

    def _is_ws(self) -> bool:
        return self.config.endpoint.startswith("ws://") or self.config.endpoint.startswith("wss://")

    async def discover_tools(self) -> List[Dict[str, Any]]:
        if self._is_ws():
            return await self._discover_ws()
        return await self._discover_http()

    async def execute(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._is_ws():
            return await self._execute_ws(name, params)
        return await self._execute_http(name, params)

    # ---------------------- HTTP mode ----------------------
    async def _discover_http(self) -> List[Dict[str, Any]]:
        url = self.config.endpoint.rstrip("/") + "/tools"
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        async with aiohttp.ClientSession(timeout=timeout, headers=self._headers()) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
                # Expecting {"tools": [...]} or list
                if isinstance(data, dict) and "tools" in data:
                    return list(data["tools"])  # type: ignore[return-value]
                if isinstance(data, list):
                    return data
                return []

    async def _execute_http(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = self.config.endpoint.rstrip("/") + "/execute"
        payload = {"name": name, "params": params}
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        async with aiohttp.ClientSession(timeout=timeout, headers=self._headers()) as session:
            async with session.post(url, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                if isinstance(data, dict):
                    return data
                return {"result": data}

    # ---------------------- WebSocket mode ----------------------
    async def _discover_ws(self) -> List[Dict[str, Any]]:
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        async with aiohttp.ClientSession(timeout=timeout, headers=self._headers()) as session:
            async with session.ws_connect(self.config.endpoint) as ws:
                req = {"jsonrpc": "2.0", "id": 1, "method": "list_tools"}
                await ws.send_str(json.dumps(req))
                msg = await ws.receive(timeout=self.config.timeout)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    # Expecting {"result": {"tools": [...]}}
                    result = data.get("result") if isinstance(data, dict) else None
                    if isinstance(result, dict) and "tools" in result:
                        return list(result["tools"])  # type: ignore[return-value]
                    if isinstance(result, list):
                        return result
                return []

    async def _execute_ws(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        async with aiohttp.ClientSession(timeout=timeout, headers=self._headers()) as session:
            async with session.ws_connect(self.config.endpoint) as ws:
                req = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "execute_tool",
                    "params": {"name": name, "params": params},
                }
                await ws.send_str(json.dumps(req))
                msg = await ws.receive(timeout=self.config.timeout)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    # Expecting {"result": {...}}
                    result = data.get("result") if isinstance(data, dict) else None
                    if isinstance(result, dict):
                        return result
                    return {"result": result}
                return {"error": "No response"}
