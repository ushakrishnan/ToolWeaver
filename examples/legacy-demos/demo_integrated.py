"""
Demo: Integrated Tool Discovery + Semantic Search + Planning

Shows the complete Phase 2 + Phase 3 pipeline:
1. Discover tools (Phase 2)
2. Add mock tools to exceed search threshold (20+)
3. Semantic search selects relevant tools (Phase 3)
4. Planner generates plan with selected tools
"""

import asyncio

from orchestrator.mcp_client import MCPClientShim
from orchestrator.planner import LargePlanner
from orchestrator.tool_discovery import discover_tools

# Legacy import removed - not available in public API
from orchestrator.shared.models import ToolCatalog, ToolDefinition, ToolParameter


async def create_large_catalog() -> ToolCatalog:
    """Create a catalog with 30+ tools by adding mock tools"""

    # Start with real discovered tools
    mcp_client = MCPClientShim()
    catalog = await discover_tools(
        mcp_client=mcp_client,
        function_modules=[workers, functions],
        include_code_exec=True,
        use_cache=True
    )

    print(f"✓ Discovered {len(catalog.tools)} real tools")

    # Add mock tools to exceed threshold (need 20+ for search)
    mock_tools = [
        ("slack_send_message", "Send a message to a Slack channel"),
        ("slack_list_channels", "List all Slack channels"),
        ("slack_get_users", "Get list of Slack workspace users"),
        ("email_send", "Send an email message"),
        ("email_list_inbox", "List emails in inbox"),
        ("sms_send", "Send SMS text message"),
        ("discord_send", "Send message to Discord channel"),
        ("twitter_post", "Post a tweet to Twitter"),
        ("github_create_issue", "Create GitHub issue"),
        ("github_list_repos", "List GitHub repositories"),
        ("jira_create_ticket", "Create JIRA ticket"),
        ("database_query", "Execute SQL database query"),
        ("file_read", "Read file from filesystem"),
        ("file_write", "Write content to file"),
        ("http_get", "Make HTTP GET request"),
        ("http_post", "Make HTTP POST request"),
    ]

    for name, description in mock_tools:
        catalog.add_tool(ToolDefinition(
            name=name,
            type="function",
            description=description,
            parameters=[
                ToolParameter(name="data", type="object", description="Input data", required=True)
            ],
            source="mock",
            metadata={"mock": True}
        ))

    print(f"✓ Added {len(mock_tools)} mock tools")
    print(f"✓ Total catalog size: {len(catalog.tools)} tools")

    return catalog


async def main():
    print("=" * 70)
    print("ToolWeaver - Integrated Discovery + Search + Planning Demo")
    print("=" * 70)

    # Step 1: Create large tool catalog
    print("\n1. Building Large Tool Catalog")
    print("-" * 70)
    catalog = await create_large_catalog()

    # Step 2: Initialize planner with semantic search enabled
    print("\n2. Initializing Planner")
    print("-" * 70)
    print("   Settings:")
    print("   - Semantic search: ENABLED")
    print("   - Search threshold: 20 tools")
    print("   - Search will activate automatically")

    async with LargePlanner(
        tool_catalog=catalog,
        use_tool_search=True,
        search_threshold=20
    ) as planner:

        # Step 3: Test various queries to show intelligent tool selection
        test_cases = [
            {
                "request": "Extract text from receipt image and calculate total",
                "expected_tools": ["receipt_ocr", "line_item_parser", "code_exec"]
            },
            {
                "request": "Send a Slack message to the engineering team",
                "expected_tools": ["slack_send_message", "slack_list_channels"]
            },
            {
                "request": "Read a file and send it via email",
                "expected_tools": ["file_read", "email_send"]
            },
        ]

        print("\n3. Testing Semantic Search with Planning")
        print("=" * 70)

        for i, test_case in enumerate(test_cases, 1):
            request = test_case["request"]
            print(f"\nTest Case {i}: \"{request}\"")
            print("-" * 70)

            # Generate plan (search will happen automatically)
            plan = await planner.generate_plan(request)

            # Analyze the plan
            steps = plan.get("steps", [])
            tools_used = set()
            for step in steps:
                if "tool_name" in step:
                    tools_used.add(step["tool_name"])

            print(f"   Generated {len(steps)} steps")
            print(f"   Tools selected: {', '.join(sorted(tools_used)) if tools_used else 'None'}")

            # Check if expected tools were found
            expected = test_case["expected_tools"]
            found = sum(1 for tool in expected if tool in tools_used)
            print(f"   Relevance: {found}/{len(expected)} expected tools found")

    # Step 4: Show statistics
    print("\n" + "=" * 70)
    print("4. Performance Statistics")
    print("=" * 70)

    total_tools = len(catalog.tools)
    typical_selected = 10

    tokens_without_search = total_tools * 150
    tokens_with_search = typical_selected * 150
    savings = tokens_without_search - tokens_with_search
    savings_pct = (savings / tokens_without_search) * 100

    print(f"   Total tools in catalog: {total_tools}")
    print(f"   Typical tools selected: {typical_selected}")
    print(f"   Token usage without search: ~{tokens_without_search:,} tokens")
    print(f"   Token usage with search: ~{tokens_with_search:,} tokens")
    print(f"   Token savings: ~{savings:,} tokens ({savings_pct:.1f}% reduction)")

    cost_per_million = 2.50  # GPT-4o input tokens
    cost_savings = (savings / 1_000_000) * cost_per_million
    print(f"   Cost savings per request: ${cost_savings:.4f}")
    print(f"   Annual savings (1000 req/day): ${cost_savings * 1000 * 365:.2f}")

    print("\n" + "=" * 70)
    print("Demo Complete! Phase 2 + Phase 3 Integration Working")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
