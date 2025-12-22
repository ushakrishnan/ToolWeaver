import pytest

from orchestrator._internal.infra.a2a_client import A2AClient, AgentCapability


@pytest.mark.asyncio
async def test_discovery_cache_invalidation_on_register():
    client = A2AClient()
    client.register_agent(AgentCapability(
        agent_id="a1",
        name="A1",
        description="",
        endpoint="http://example.com",
    ))

    first = await client.discover_agents()
    assert len(first) == 1

    client.register_agent(AgentCapability(
        agent_id="a2",
        name="A2",
        description="",
        endpoint="http://example.com",
    ))

    # register_agent invalidates cache; new agent should appear without manual invalidation
    refreshed = await client.discover_agents(use_cache=True, cache_ttl_s=300)
    assert len(refreshed) == 2


@pytest.mark.asyncio
async def test_discovery_cache_respects_ttl_zero_refreshes():
    client = A2AClient()
    client.register_agent(AgentCapability(
        agent_id="a1",
        name="A1",
        description="",
        endpoint="http://example.com",
    ))
    await client.discover_agents()

    # No new agents added; TTL zero still refreshes and returns same single agent
    refreshed = await client.discover_agents(use_cache=True, cache_ttl_s=0)
    assert len(refreshed) == 1
