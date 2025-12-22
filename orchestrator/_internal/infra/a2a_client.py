"""Agent-to-Agent (A2A) client for agent discovery and delegation."""

from __future__ import annotations

import asyncio
import os
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, AsyncGenerator

import aiohttp
from aiohttp import ClientResponseError, ClientError, WSMsgType
import yaml


@dataclass
class AgentCapability:
    """Describes an external agent's capabilities."""

    name: str
    description: str
    agent_id: Optional[str] = None
    endpoint: Optional[str] = None
    protocol: str = "http"
    capabilities: List[str] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    cost_estimate: Optional[float] = None
    latency_estimate: Optional[int] = None
    # Streaming capability flags used by tests and discovery metadata
    supports_streaming: bool = False
    supports_http_streaming: bool = False
    supports_sse: bool = False
    supports_websocket: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDelegationRequest:
    """Request to delegate a task to an agent."""

    agent_id: str
    task: str
    context: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 300
    idempotency_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDelegationResponse:
    """Response returned from an agent after delegation."""

    agent_id: str
    success: bool
    result: Any
    execution_time: float
    cost: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class A2AClient:
    """Client for agent discovery and delegation."""

    def __init__(
        self,
        *,
        config_path: Optional[str] = None,
        registry_url: Optional[str] = None,
        max_idempotency_entries: int = 256,
        idempotency_ttl_s: int = 600,
        max_retries: int = 2,
        retry_backoff_s: float = 0.1,
        circuit_breaker_threshold: int = 3,
        circuit_reset_s: int = 30,
        observer: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.config_path = Path(config_path) if config_path else None
        self.registry_url = registry_url
        self.agent_map: Dict[str, AgentCapability] = {}
        self._idempotency_store: "OrderedDict[str, tuple[float, AgentDelegationResponse]]" = OrderedDict()
        self._max_idempotency_entries = max_idempotency_entries
        self._idempotency_ttl_s = idempotency_ttl_s
        self._max_retries = max_retries
        self._retry_backoff_s = retry_backoff_s
        self._circuit_breaker_threshold = circuit_breaker_threshold
        self._circuit_reset_s = circuit_reset_s
        self._consecutive_failures = 0
        self._circuit_open_until: Optional[float] = None
        self._observer = observer
        self._discovery_cache_agents: Optional[List[AgentCapability]] = None
        self._discovery_cache_ts: Optional[float] = None

    async def __aenter__(self) -> "A2AClient":
        await self.load()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        return None

    async def load(self) -> None:
        """Load agent definitions from config (registry hook reserved)."""
        if self.config_path:
            self._load_from_config(self.config_path)
        # Registry loading can be added later when protocol is defined.

    def _load_from_config(self, config_path: Path) -> None:
        if not config_path.exists():
            return

        data = yaml.safe_load(config_path.read_text()) or {}
        for agent_cfg in data.get("agents", []):
            agent_cfg = self._expand_env(agent_cfg)
            self._validate_agent_cfg(agent_cfg)
            capability = AgentCapability(
                agent_id=agent_cfg["agent_id"],
                name=agent_cfg["name"],
                description=agent_cfg.get("description", ""),
                endpoint=agent_cfg["endpoint"],
                protocol=agent_cfg.get("protocol", "http"),
                capabilities=agent_cfg.get("capabilities", []),
                input_schema=agent_cfg.get("input_schema", {}),
                output_schema=agent_cfg.get("output_schema", {}),
                cost_estimate=agent_cfg.get("cost_estimate"),
                latency_estimate=agent_cfg.get("latency_estimate"),
                metadata=agent_cfg.get("metadata", {}),
            )
            agent_id = capability.agent_id
            if agent_id:  # Guard against None
                self.agent_map[agent_id] = capability

    def _validate_agent_cfg(self, agent_cfg: Dict[str, Any]) -> None:
        required = ["agent_id", "name", "endpoint"]
        missing = [k for k in required if k not in agent_cfg]
        if missing:
            raise ValueError(f"Agent config missing required fields: {missing}")

    def _expand_env(self, value: Any) -> Any:
        """Recursively expand ${VAR} tokens using environment variables."""
        if isinstance(value, str):
            return os.path.expandvars(value)
        if isinstance(value, list):
            return [self._expand_env(v) for v in value]
        if isinstance(value, dict):
            return {k: self._expand_env(v) for k, v in value.items()}
        return value

    async def discover_agents(
        self,
        *,
        capability: Optional[str] = None,
        tags: Optional[List[str]] = None,
        use_cache: bool = True,
        cache_ttl_s: int = 300,
    ) -> List[AgentCapability]:
        """Return agents filtered by capability and/or tags with optional caching."""
        now = time.time()
        cache_valid = (
            use_cache
            and self._discovery_cache_agents is not None
            and self._discovery_cache_ts is not None
            and (now - self._discovery_cache_ts) < cache_ttl_s
        )

        if cache_valid:
            # Guard against None - should be a list if cache is valid
            agents = list(self._discovery_cache_agents) if self._discovery_cache_agents else []
        else:
            agents = list(self.agent_map.values())
            self._discovery_cache_agents = agents
            self._discovery_cache_ts = now

        if capability:
            agents = [a for a in agents if capability in a.capabilities]

        if tags:
            agents = [
                a
                for a in agents
                if any(tag in a.metadata.get("tags", []) for tag in tags)
            ]

        return agents

    def invalidate_discovery_cache(self) -> None:
        """Clear cached discovery results."""
        self._discovery_cache_agents = None
        self._discovery_cache_ts = None

    async def delegate_to_agent(
        self,
        request: AgentDelegationRequest,
    ) -> AgentDelegationResponse:
        """Delegate a task to an agent, with idempotency and timeout handling."""
        cached = self._get_cached_response(request.idempotency_key)
        if cached:
            self._emit("a2a.cache_hit", {"agent_id": request.agent_id, "idempotency_key": request.idempotency_key})
            return cached

        agent = self.agent_map.get(request.agent_id)
        if not agent:
            raise ValueError(f"Agent {request.agent_id} not found")

        if self._is_circuit_open():
            raise RuntimeError("A2A circuit open due to recent failures")

        start = asyncio.get_event_loop().time()
        last_exc: Optional[Exception] = None
        error_type: Optional[str] = None

        self._emit("a2a.start", {
            "agent_id": request.agent_id,
            "protocol": agent.protocol,
            "idempotency_key": request.idempotency_key,
        })

        for attempt in range(self._max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self._delegate_http(agent, request),
                    timeout=request.timeout,
                )
                self._reset_circuit()
                response = AgentDelegationResponse(
                    agent_id=request.agent_id,
                    success=True,
                    result=result,
                    execution_time=asyncio.get_event_loop().time() - start,
                    cost=agent.cost_estimate,
                    metadata={"protocol": agent.protocol, "attempt": attempt + 1},
                )
                self._store_response(request.idempotency_key, response)
                self._emit("a2a.complete", {
                    "agent_id": request.agent_id,
                    "protocol": agent.protocol,
                    "attempt": attempt + 1,
                    "latency_ms": response.execution_time * 1000,
                    "success": True,
                })
                return response
            except asyncio.TimeoutError as exc:
                last_exc = RuntimeError(
                    f"Agent {request.agent_id} timed out after {request.timeout}s"
                )
                error_type = "timeout"
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                error_type = self._classify_error(exc)

            self._consecutive_failures += 1
            if self._consecutive_failures >= self._circuit_breaker_threshold:
                self._open_circuit()
                break

            # Backoff before retrying if more attempts remain
            if attempt < self._max_retries:
                await asyncio.sleep(self._retry_backoff_s * (2 ** attempt))

        # All attempts failed
        if isinstance(last_exc, RuntimeError):
            raise last_exc

        return AgentDelegationResponse(
            agent_id=request.agent_id,
            success=False,
            result=None,
            execution_time=asyncio.get_event_loop().time() - start,
            cost=agent.cost_estimate,
            metadata={
                "error": str(last_exc) if last_exc else "unknown",
                "attempts": self._max_retries + 1,
                "protocol": agent.protocol,
                "error_type": error_type or "unknown",
            },
        )

        self._emit("a2a.complete", {
            "agent_id": request.agent_id,
            "protocol": agent.protocol,
            "attempt": self._max_retries + 1,
            "latency_ms": (asyncio.get_event_loop().time() - start) * 1000,
            "success": False,
            "error_type": error_type or "unknown",
        })

    async def delegate_stream(
        self,
        request: AgentDelegationRequest,
        *,
        chunk_timeout: Optional[float] = None,
    ) -> Any:
        """Stream agent responses as an async generator.

        Notes:
            - Streaming responses are not cached for idempotency.
            - Retries will restart the stream; callers should tolerate duplicate chunks.
        """
        agent = self.agent_map.get(request.agent_id)
        if not agent:
            raise ValueError(f"Agent {request.agent_id} not found")

        if self._is_circuit_open():
            raise RuntimeError("A2A circuit open due to recent failures")

        last_exc: Optional[Exception] = None
        error_type: Optional[str] = None
        self._emit("a2a.stream.start", {
            "agent_id": request.agent_id,
            "protocol": agent.protocol,
        })

        for attempt in range(self._max_retries + 1):
            try:
                async for chunk in self._delegate_stream(agent, request, chunk_timeout):
                    self._emit("a2a.stream.chunk", {
                        "agent_id": request.agent_id,
                        "protocol": agent.protocol,
                        "attempt": attempt + 1,
                    })
                    yield chunk
                self._reset_circuit()
                self._emit("a2a.stream.complete", {
                    "agent_id": request.agent_id,
                    "protocol": agent.protocol,
                    "attempt": attempt + 1,
                    "success": True,
                })
                return
            except asyncio.TimeoutError as exc:
                last_exc = RuntimeError(
                    f"Agent {request.agent_id} timed out after {request.timeout}s"
                )
                error_type = "timeout"
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                error_type = self._classify_error(exc)

            self._consecutive_failures += 1
            if self._consecutive_failures >= self._circuit_breaker_threshold:
                self._open_circuit()
                break

            if attempt < self._max_retries:
                await asyncio.sleep(self._retry_backoff_s * (2 ** attempt))

        self._emit("a2a.stream.complete", {
            "agent_id": request.agent_id,
            "protocol": agent.protocol,
            "attempt": self._max_retries + 1,
            "success": False,
            "error_type": error_type or "unknown",
        })
        if isinstance(last_exc, RuntimeError):
            raise last_exc
        if last_exc:
            raise last_exc
        raise RuntimeError("Agent stream failed for unknown reasons")

    def _classify_error(self, exc: Exception) -> str:
        if isinstance(exc, ClientResponseError):
            if 400 <= exc.status < 500:
                return "client_error"
            if 500 <= exc.status < 600:
                return "server_error"
            return "http_error"
        if isinstance(exc, ClientError):
            return "transport_error"
        if isinstance(exc, ValueError):
            return "schema_error"
        return "unknown"

    def _emit(self, event: str, data: Dict[str, Any]) -> None:
        if self._observer:
            try:
                self._observer(event, data)
            except Exception:
                # Observer should never break execution
                pass

    def _get_cached_response(self, idempotency_key: Optional[str]) -> Optional[AgentDelegationResponse]:
        if not idempotency_key:
            return None
        entry = self._idempotency_store.get(idempotency_key)
        if not entry:
            return None
        ts, resp = entry
        if (time.time() - ts) > self._idempotency_ttl_s:
            # Expired; remove
            self._idempotency_store.pop(idempotency_key, None)
            return None
        # Move to end (recently used)
        self._idempotency_store.move_to_end(idempotency_key)
        return resp

    def _store_response(self, idempotency_key: Optional[str], response: AgentDelegationResponse) -> None:
        if not idempotency_key:
            return
        self._idempotency_store[idempotency_key] = (time.time(), response)
        self._idempotency_store.move_to_end(idempotency_key)
        if len(self._idempotency_store) > self._max_idempotency_entries:
            self._idempotency_store.popitem(last=False)

    def _is_circuit_open(self) -> bool:
        if self._circuit_open_until is None:
            return False
        if time.time() < self._circuit_open_until:
            return True
        self._reset_circuit()
        return False

    def _open_circuit(self) -> None:
        self._circuit_open_until = time.time() + self._circuit_reset_s

    def _reset_circuit(self) -> None:
        self._consecutive_failures = 0
        self._circuit_open_until = None

    async def _delegate_http(
        self,
        agent: AgentCapability,
        request: AgentDelegationRequest,
    ) -> Any:
        """Delegate to an HTTP agent endpoint returning JSON."""
        headers = {"Content-Type": "application/json"}
        auth_cfg = agent.metadata.get("auth") if agent.metadata else None
        if auth_cfg and auth_cfg.get("type") in {"bearer", "api_key"}:
            token_env = auth_cfg.get("token_env")
            token = os.getenv(token_env) if token_env else None
            if token:
                header_name = auth_cfg.get("header", "Authorization")
                header_value = (
                    f"Bearer {token}" if auth_cfg.get("type") == "bearer" else token
                )
                headers[header_name] = header_value

        payload = {
            "task": request.task,
            "context": request.context,
            "metadata": request.metadata,
        }

        endpoint = agent.endpoint
        if not endpoint:
            raise ValueError(f"Agent {agent.name} has no endpoint configured")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                # Prefer JSON; fallback to text if not JSON
                if response.headers.get("Content-Type", "").startswith("application/json"):
                    return await response.json()
                return await response.text()

    async def _delegate_stream(
        self,
        agent: AgentCapability,
        request: AgentDelegationRequest,
        chunk_timeout: Optional[float],
    ) -> Any:
        if agent.protocol == "http":
            async for chunk in self._delegate_http_stream(agent, request, chunk_timeout):
                yield chunk
        elif agent.protocol == "sse":
            async for chunk in self._delegate_sse_stream(agent, request, chunk_timeout):
                yield chunk
        elif agent.protocol == "websocket":
            async for chunk in self._delegate_websocket_stream(agent, request, chunk_timeout):
                yield chunk
        else:
            raise ValueError(f"Unsupported streaming protocol: {agent.protocol}")

    async def _delegate_http_stream(
        self,
        agent: AgentCapability,
        request: AgentDelegationRequest,
        chunk_timeout: Optional[float],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        headers = {"Content-Type": "application/json"}
        auth_cfg = agent.metadata.get("auth") if agent.metadata else None
        if auth_cfg and auth_cfg.get("type") in {"bearer", "api_key"}:
            token_env = auth_cfg.get("token_env")
            token = os.getenv(token_env) if token_env else None
            if token:
                header_name = auth_cfg.get("header", "Authorization")
                header_value = (
                    f"Bearer {token}" if auth_cfg.get("type") == "bearer" else token
                )
                headers[header_name] = header_value

        payload = {
            "task": request.task,
            "context": request.context,
            "metadata": request.metadata,
        }

        endpoint = agent.endpoint
        if not endpoint:
            raise ValueError(f"Agent {agent.name} has no endpoint configured")

        session = aiohttp.ClientSession()
        try:
            async with session.post(
                endpoint,
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                while True:
                    read_future = response.content.readany()
                    if chunk_timeout:
                        chunk = await asyncio.wait_for(read_future, timeout=chunk_timeout)
                    else:
                        chunk = await read_future
                    if not chunk:
                        if response.content.at_eof():
                            break
                        continue
                    yield {"chunk": chunk.decode()}
        finally:
            await session.close()

    async def _delegate_sse_stream(
        self,
        agent: AgentCapability,
        request: AgentDelegationRequest,
        chunk_timeout: Optional[float],
    ) -> Any:
        headers = {"Accept": "text/event-stream"}

        endpoint = agent.endpoint
        if not endpoint:
            raise ValueError(f"Agent {agent.name} has no endpoint configured")

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers) as response:
                response.raise_for_status()
                buffer = ""
                while True:
                    read_future = response.content.readany()
                    if chunk_timeout:
                        chunk = await asyncio.wait_for(read_future, timeout=chunk_timeout)
                    else:
                        chunk = await read_future
                    if not chunk:
                        if response.content.at_eof():
                            break
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

    async def _delegate_websocket_stream(
        self,
        agent: AgentCapability,
        request: AgentDelegationRequest,
        chunk_timeout: Optional[float],
    ) -> Any:
        endpoint = agent.endpoint
        if not endpoint:
            raise ValueError(f"Agent {agent.name} has no endpoint configured")

        async with aiohttp.ClientSession() as session:
            ws = await session.ws_connect(endpoint)
            try:
                while True:
                    recv = ws.receive()
                    if chunk_timeout:
                        msg = await asyncio.wait_for(recv, timeout=chunk_timeout)
                    else:
                        msg = await recv

                    if msg.type == WSMsgType.TEXT:
                        yield msg.data
                    elif msg.type == WSMsgType.BINARY:
                        yield msg.data
                    elif msg.type in (WSMsgType.CLOSED, WSMsgType.CLOSING, WSMsgType.ERROR):
                        break
            finally:
                await ws.close()

    def register_agent(self, capability: AgentCapability) -> None:
        if capability.agent_id:
            self.agent_map[capability.agent_id] = capability
            self.invalidate_discovery_cache()

    def unregister_agent(self, agent_id: str) -> None:
        if agent_id in self.agent_map:
            del self.agent_map[agent_id]
            self.invalidate_discovery_cache()

    def get_agent(self, agent_id: str) -> Optional[AgentCapability]:
        return self.agent_map.get(agent_id)

    def list_agents(self) -> List[AgentCapability]:
        return list(self.agent_map.values())
