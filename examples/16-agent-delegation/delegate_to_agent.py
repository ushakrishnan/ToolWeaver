"""
Example 16a: Basic Agent Delegation

Demonstrates how to discover and delegate tasks to external agents.
"""

import asyncio
from orchestrator.infra.a2a_client import A2AClient, AgentDelegationRequest


async def main():
    """Discover agents and delegate a task."""
    
    # Initialize A2A client with config file
    async with A2AClient(config_path="examples/16-agent-delegation/agents.yaml") as client:
        
        # Step 1: Discover available agents
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
        
        # Step 2: Create a delegation request
        print("\nStep 2: Delegating task...")
        
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
            print(f"  ✗ Delegation error: {e}")
        
        # Step 3: Demonstrate idempotency
        print("\nStep 3: Verifying idempotency (same request)...")
        response2 = await client.delegate_to_agent(request)
        print(f"  Response cached: {response.result == response2.result}")


if __name__ == "__main__":
    asyncio.run(main())
