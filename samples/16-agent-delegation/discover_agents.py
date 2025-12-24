"""
Example 16b: Agent Discovery

Demonstrates how to discover agents and filter by capability or tags.
"""

import asyncio
from orchestrator._internal.infra.a2a_client import A2AClient


async def main():
    """Discover and filter agents."""
    
    async with A2AClient(config_path="examples/16-agent-delegation/agents.yaml") as client:
        
        # Discover all agents
        print("All agents:")
        all_agents = await client.discover_agents()
        for agent in all_agents:
            print(f"  - {agent.name}: {agent.description}")
        
        # Filter by capability
        print("\nAgents with 'data_analysis' capability:")
        analysts = await client.discover_agents(capability="data_analysis")
        for agent in analysts:
            print(f"  - {agent.name}")
        
        # Filter by tags (if configured)
        print("\nAgents tagged 'critical':")
        critical = await client.discover_agents(tags=["critical"])
        if critical:
            for agent in critical:
                print(f"  - {agent.name}")
        else:
            print("  (none)")


if __name__ == "__main__":
    asyncio.run(main())
