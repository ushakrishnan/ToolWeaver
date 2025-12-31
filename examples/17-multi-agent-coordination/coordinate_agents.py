"""
Example 17: Multi-Agent Coordination

Coordinates multiple agents sequentially to complete a complex task.
"""

import asyncio

from orchestrator._internal.infra.a2a_client import A2AClient, AgentDelegationRequest


async def main():
    """Coordinate multiple agents to build and analyze data."""

    async with A2AClient(config_path="examples/17-multi-agent-coordination/agents.yaml") as client:

        total_cost = 0.0
        total_time = 0.0

        # Step 1: Fetch raw data using data_fetcher agent
        print("Step 1: Fetching raw data...")
        request1 = AgentDelegationRequest(
            agent_id="data_fetcher",
            task="Fetch customer transaction data for Q4 2024",
            context={
                "date_range": "2024-10-01 to 2024-12-31",
                "include_metrics": ["amount", "category", "customer_id"]
            },
            idempotency_key="fetch_q4_data"
        )

        try:
            resp1 = await client.delegate_to_agent(request1)
            if resp1.success:
                raw_data = resp1.result
                total_time += resp1.execution_time
                total_cost += resp1.cost or 0.0
                print(f"  ✓ Data fetched in {resp1.execution_time:.2f}s")
            else:
                print(f"  ✗ Fetch failed: {resp1.metadata.get('error')}")
                return
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return

        # Step 2: Analyze the data
        print("Step 2: Analyzing data...")
        request2 = AgentDelegationRequest(
            agent_id="data_analyst",
            task="Analyze customer spending patterns",
            context={
                "data": raw_data,
                "analysis_type": "spending_patterns"
            },
            idempotency_key="analyze_q4_spending"
        )

        try:
            resp2 = await client.delegate_to_agent(request2)
            if resp2.success:
                insights = resp2.result
                total_time += resp2.execution_time
                total_cost += resp2.cost or 0.0
                print(f"  ✓ Analysis complete in {resp2.execution_time:.2f}s")
            else:
                print(f"  ✗ Analysis failed: {resp2.metadata.get('error')}")
                return
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return

        # Step 3: Generate report
        print("Step 3: Generating report...")
        request3 = AgentDelegationRequest(
            agent_id="report_generator",
            task="Generate executive summary report",
            context={
                "insights": insights,
                "format": "markdown",
                "audience": "executive"
            },
            idempotency_key="report_q4_executive"
        )

        try:
            resp3 = await client.delegate_to_agent(request3)
            if resp3.success:
                report = resp3.result
                total_time += resp3.execution_time
                total_cost += resp3.cost or 0.0
                print(f"  ✓ Report generated in {resp3.execution_time:.2f}s")
                print("\n✓ Multi-agent workflow complete!")
                print(f"  Total time: {total_time:.2f}s")
                print(f"  Total cost: ${total_cost:.4f}")
                print(f"\nReport preview:\n{str(report)[:200]}...")
            else:
                print(f"  ✗ Report generation failed: {resp3.metadata.get('error')}")
        except Exception as e:
            print(f"  ✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
