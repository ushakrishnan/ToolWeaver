"""Agent discovery via A2A client (treat agents as capabilities)."""

from __future__ import annotations

from typing import Any, cast

from ..infra.a2a_client import A2AClient, AgentCapability
from ..shared.models import ToolDefinition, ToolParameter
from .tool_discovery import ToolDiscoveryService


class AgentDiscoverer(ToolDiscoveryService):
    """
    Discover external agents via A2A and present them as capabilities.

    Agents are converted to ToolDefinition entries with type "agent",
    so they can be searched, ranked, and selected alongside tools.
    """

    def __init__(self, a2a_client: A2AClient) -> None:
        super().__init__("a2a")
        self.a2a_client: A2AClient = a2a_client

    async def discover(self) -> dict[str, ToolDefinition]:
        discovered: dict[str, ToolDefinition] = {}
        agents: list[Any] = await self.a2a_client.discover_agents()

        for raw_agent in agents:
            agent: AgentCapability = self._coerce_agent(raw_agent)
            tool_def: ToolDefinition = self._agent_to_tool_definition(agent)
            discovered[tool_def.name] = tool_def

        return discovered

    def _coerce_agent(self, raw: object) -> AgentCapability:
        """Coerce dicts from mocks into AgentCapability instances."""
        if isinstance(raw, AgentCapability):
            return raw
        if isinstance(raw, dict):
            # Extract streaming flags from nested capability objects, if present
            caps: Any = raw.get("capabilities", [])
            supports_streaming: bool = any(getattr(c, "supports_streaming", False) for c in caps)
            supports_http_streaming: bool = any(getattr(c, "supports_http_streaming", False) for c in caps)
            supports_sse: bool = any(getattr(c, "supports_sse", False) for c in caps)
            supports_websocket: bool = any(getattr(c, "supports_websocket", False) for c in caps)

            metadata: dict[str, Any] = dict(raw.get("metadata", {}))
            metadata.setdefault("supports_streaming", supports_streaming)
            metadata.setdefault("supports_http_streaming", supports_http_streaming)
            metadata.setdefault("supports_sse", supports_sse)
            metadata.setdefault("supports_websocket", supports_websocket)

            return AgentCapability(
                name=cast(str, raw.get("name", "unknown")),
                description=cast(str, raw.get("description", "")),
                agent_id=cast(str | None, raw.get("agent_id") or raw.get("id")),
                endpoint=cast(str | None, raw.get("endpoint")),
                protocol=cast(str, raw.get("protocol", "http")),
                capabilities=cast(list[str], raw.get("capabilities", [])),
                input_schema=cast(dict[str, Any], raw.get("input_schema", {})),
                output_schema=cast(dict[str, Any], raw.get("output_schema", {})),
                metadata=metadata,
            )
        raise TypeError(f"Unsupported agent type: {type(raw)}")

    def _agent_to_tool_definition(self, agent: AgentCapability) -> ToolDefinition:
        parameters: list[ToolParameter] = []

        # If input_schema is provided, derive parameters from it
        if agent.input_schema:
            required: set[str] = set(agent.input_schema.get("required", []))
            for param_name, param_spec in agent.input_schema.get("properties", {}).items():
                parameters.append(
                    ToolParameter(
                        name=cast(str, param_name),
                        type=cast(str, param_spec.get("type", "string")),
                        description=cast(str, param_spec.get("description", param_name)),
                        required=param_name in required,
                    )
                )
        else:
            # Minimal schema
            parameters = [
                ToolParameter(
                    name="task",
                    type="string",
                    description="Task description for the agent",
                    required=True,
                ),
                ToolParameter(
                    name="context",
                    type="object",
                    description="Additional context for the agent",
                    required=False,
                ),
            ]

        return ToolDefinition(
            name=f"agent_{agent.agent_id}",
            type="agent",
            description=agent.description or agent.name,
            parameters=parameters,
            source=self.source_name,
            input_schema=agent.input_schema,
            output_schema=agent.output_schema,
            metadata={
                "agent_id": agent.agent_id,
                "capabilities": agent.capabilities,
                "protocol": agent.protocol,
                "endpoint": agent.endpoint,
                "cost_estimate": agent.cost_estimate,
                "latency_estimate": agent.latency_estimate,
                # Streaming metadata
                "supports_streaming": bool(agent.metadata.get("supports_streaming", False)),
                "supports_http_streaming": bool(agent.metadata.get("supports_http_streaming", False)),
                "supports_sse": bool(agent.metadata.get("supports_sse", False)),
                "supports_websocket": bool(agent.metadata.get("supports_websocket", False)),
                # Execution characteristics
                "execution_time_ms": agent.metadata.get("execution_time_ms", 3000),
                "cost_per_call_usd": agent.metadata.get("cost_per_call_usd", 0.05),
                # Merge additional metadata
                **agent.metadata,
            },
        )
