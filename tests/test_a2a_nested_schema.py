
import asyncio

from orchestrator._internal.infra.a2a_client import A2AClient, AgentCapability


def test_a2a_capability_nested_schema_roundtrip():
    client = A2AClient()

    nested_in = {
        "type": "object",
        "properties": {
            "session": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "context": {
                        "type": "object",
                        "properties": {
                            "user": {"type": "string"},
                            "roles": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "required": ["id"],
            }
        },
        "required": ["session"],
    }

    nested_out = {
        "type": "object",
        "properties": {
            "result": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "data": {"type": "object"},
                },
                "required": ["status"],
            }
        },
        "required": ["result"],
    }

    cap = AgentCapability(
        name="chat_agent",
        description="Handles chat with nested context",
        agent_id="agent-1",
        endpoint="http://localhost:9999/agent",
        protocol="http",
        capabilities=["chat"],
        input_schema=nested_in,
        output_schema=nested_out,
        supports_streaming=True,
        supports_http_streaming=True,
    )

    client.register_agent(cap)

    agents = asyncio.run(client.discover_agents())
    assert len(agents) == 1
    a = agents[0]
    assert a.input_schema == nested_in
    assert a.output_schema == nested_out
