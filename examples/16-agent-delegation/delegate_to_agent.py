"""
Example 16: Agent Delegation with A2A (Agent-to-Agent)

Demonstrates discovering and delegating tasks to external agents.
"""

import asyncio
from pathlib import Path
from orchestrator._internal.infra.a2a_client import A2AClient, AgentDelegationRequest


async def main():
    """Discover agents and delegate a task."""
    
    # Get path to agents.yaml in same directory
    config_file = Path(__file__).parent / "agents.yaml"
    
    # Initialize A2A client with config file
    async with A2AClient(config_path=str(config_file)) as client:
        
        # Step 1: Discover available agents
        print("="*70)
        print("EXAMPLE 16: Agent Delegation")
        print("="*70)
        print()
        
        print("Step 1: Discovering agents...")
        agents = await client.discover_agents()
        
        if not agents:
            print("  No agents configured. Update agents.yaml and try again.")
            print("  See README.md for configuration details.")
            return
        
        print(f"  Found {len(agents)} agent(s):")
        for agent in agents:
            print(f"    - {agent.name} ({agent.agent_id})")
            print(f"      Capabilities: {', '.join(agent.capabilities)}")
        print()
        
        # Step 2: Create a delegation request
        print("Step 2: Delegating task...")
        print()
        
        agent_id = agents[0].agent_id
        request = AgentDelegationRequest(
            agent_id=agent_id,
            task="Analyze customer churn patterns",
            context={
                "dataset": "customer_data.csv",
                "metrics": ["churn_rate", "customer_lifetime_value"]
            },
            timeout=120,
            idempotency_key="churn_analysis_001",
            metadata={"priority": "high"}
        )
        
        try:
            response = await client.delegate_to_agent(request)
            
            if response.success:
                print(f"  ✓ Task completed in {response.execution_time:.2f}s")
                if response.cost:
                    print(f"  Cost: ${response.cost:.4f}")
                print(f"  Result: {response.result}")
            else:
                print(f"  ✗ Task failed: {response.metadata.get('error')}")
        
        except Exception as e:
            print(f"  Note: Task delegation requires actual agent endpoints.")
            print(f"  Error: {str(e)[:100]}...")
        
        print()
        
        # Step 3: Show available capabilities
        print("Step 3: Available Agent Capabilities")
        print("-"*70)
        for agent in agents:
            print(f"  {agent.name}:")
            for cap in agent.capabilities:
                print(f"    • {cap}")
        print()
        
        print("="*70)
        print("✓ Agent discovery demonstration complete!")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
