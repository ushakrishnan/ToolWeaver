import pytest

from orchestrator._internal.infra.a2a_client import A2AClient, AgentCapability
from orchestrator.tools.agent_discovery import AgentDiscoverer


@pytest.mark.asyncio
async def test_agent_discovery_converts_to_tool_definitions():
    client = A2AClient()
    client.register_agent(
        AgentCapability(
            agent_id="analytics",
            name="Analytics Agent",
            description="Performs analytics",
            endpoint="http://example.com/analytics",
            protocol="http",
            capabilities=["data_analysis"],
            input_schema={
                "type": "object",
                "properties": {
                    "dataset": {"type": "string", "description": "Dataset URI"},
                    "mode": {"type": "string", "description": "Analysis mode"},
                },
                "required": ["dataset"],
            },
            metadata={"tags": ["analytics"]},
        )
    )

    discoverer = AgentDiscoverer(client)
    discovered = await discoverer.discover()

    assert "agent_analytics" in discovered
    tool_def = discovered["agent_analytics"]
    assert tool_def.type == "agent"
    assert tool_def.metadata["agent_id"] == "analytics"
    assert any(p.name == "dataset" and p.required for p in tool_def.parameters)


@pytest.mark.asyncio
async def test_agent_discovery_falls_back_to_default_params_when_no_schema():
    client = A2AClient()
    client.register_agent(
        AgentCapability(
            agent_id="no_schema",
            name="No Schema Agent",
            description="",
            endpoint="http://example.com/no-schema",
        )
    )

    discoverer = AgentDiscoverer(client)
    discovered = await discoverer.discover()

    tool_def = discovered["agent_no_schema"]
    param_names = {p.name for p in tool_def.parameters}
    assert {"task", "context"} <= param_names
    assert tool_def.type == "agent"
