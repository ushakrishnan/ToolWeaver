"""Agent discovery via A2A client (treat agents as capabilities)."""

from __future__ import annotations

from typing import Dict, List

from ..infra.a2a_client import A2AClient, AgentCapability
from ..shared.models import ToolDefinition, ToolParameter
from .tool_discovery import ToolDiscoveryService


class AgentDiscoverer(ToolDiscoveryService):
    """
    Discover external agents via A2A and present them as capabilities.

    Agents are converted to ToolDefinition entries with type "agent",
    so they can be searched, ranked, and selected alongside tools.
    """

    def __init__(self, a2a_client: A2AClient):
        super().__init__("a2a")
        self.a2a_client = a2a_client

    async def discover(self) -> Dict[str, ToolDefinition]:
        discovered: Dict[str, ToolDefinition] = {}
        agents = await self.a2a_client.discover_agents()

        for agent in agents:
            tool_def = self._agent_to_tool_definition(agent)
            discovered[tool_def.name] = tool_def

        return discovered

    def _agent_to_tool_definition(self, agent: AgentCapability) -> ToolDefinition:
        parameters: List[ToolParameter] = []

        # If input_schema is provided, derive parameters from it
        if agent.input_schema:
            required = set(agent.input_schema.get("required", []))
            for param_name, param_spec in agent.input_schema.get("properties", {}).items():
                parameters.append(
                    ToolParameter(
                        name=param_name,
                        type=param_spec.get("type", "string"),
                        description=param_spec.get("description", param_name),
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
            metadata={
                "agent_id": agent.agent_id,
                "capabilities": agent.capabilities,
                "protocol": agent.protocol,
                "endpoint": agent.endpoint,
                "cost_estimate": agent.cost_estimate,
                "latency_estimate": agent.latency_estimate,
                "supports_streaming": bool(agent.metadata.get("supports_streaming", False)),
                **agent.metadata,
            },
        )
