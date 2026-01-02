"""
Example 18: Tool + Agent Hybrid Workflow

Demonstrates combining MCP tools with A2A agents for efficient processing.

In this example:
1. Tool: Fetch CSV data (deterministic MCP tool)
2. Tool: Validate data quality (deterministic MCP tool)
3. Agent: Perform complex analysis (flexible A2A agent)
4. Tool: Format results into report (deterministic MCP tool)
"""

import asyncio

from orchestrator._internal.infra.a2a_client import A2AClient
from orchestrator._internal.infra.mcp_client import MCPClientShim
from orchestrator._internal.runtime.orchestrator import run_step


async def main():
    """Execute a hybrid tool + agent workflow."""

    # Initialize clients
    mcp_client = MCPClientShim()

    async with A2AClient(config_path="examples/18-tool-agent-hybrid/agents.yaml") as a2a_client:

        workflow_outputs = {}

        # Step 1: Tool - Fetch data (mock for demo)
        print("Step 1: Fetching data with MCP tool...")

        try:
            # Simulate tool response
            result1 = {
                "rows": [
                    {"id": 1, "revenue": 1000, "status": "active"},
                    {"id": 2, "revenue": 2000, "status": "active"},
                    {"id": 3, "revenue": 500, "status": "inactive"},
                ]
            }
            workflow_outputs["raw_data"] = result1
            print(f"  ✓ Fetched {len(result1['rows'])} rows")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return

        # Step 2: Tool - Validate data
        print("Step 2: Validating data with MCP tool...")
        try:
            # Simulate validation
            result2 = {
                "valid": True,
                "total_rows": len(result1['rows']),
                "missing_fields": []
            }
            workflow_outputs["validation"] = result2
            print("  ✓ Data validation passed")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return

        # Step 3: Agent - Complex analysis
        print("Step 3: Analyzing data with A2A agent...")
        agent_step = {
            "type": "agent",
            "agent_id": "analytics_agent",
            "task": "Perform revenue analysis and customer segmentation",
            "inputs": ["raw_data"],
            "timeout_s": 120,
        }

        try:
            result3 = await run_step(
                agent_step,
                workflow_outputs,
                mcp_client,
                monitor=None,
                a2a_client=a2a_client
            )
            workflow_outputs["analysis"] = result3 or {
                "segments": ["high_value", "medium_value", "low_value"],
                "recommendations": ["increase engagement for high_value"]
            }
            print("  ✓ Analysis complete")
        except Exception as e:
            print(f"  ✗ Agent analysis failed: {e}")
            # Fallback: use simple analysis from tool
            workflow_outputs["analysis"] = {
                "segments": ["all_customers"],
                "recommendations": ["fallback analysis"]
            }

        # Step 4: Tool - Format report
        print("Step 4: Formatting report with MCP tool...")
        try:
            # Simulate report formatting
            result4 = {
                "report": "# Customer Analysis Report\n\n" +
                          "## Segments: " + ", ".join(workflow_outputs["analysis"].get("segments", [])) + "\n" +
                          "## Recommendations: " + ", ".join(workflow_outputs["analysis"].get("recommendations", [])),
                "format": "markdown"
            }
            workflow_outputs["report"] = result4
            print("  ✓ Report formatted")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return

        # Print final results
        print("\n✓ Hybrid workflow complete!")
        print(f"\nFinal Report:\n{workflow_outputs['report']['report']}")

        # Cost analysis
        print("\nCost Analysis:")
        print("  Tools (fetch, validate, format): ~$0.01 (cached + local)")
        print("  Agent (analysis): ~$0.10")
        print("  Total: ~$0.11")


if __name__ == "__main__":
    asyncio.run(main())
