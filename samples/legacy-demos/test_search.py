"""
Test/Demo: Tool Search Engine

Shows how semantic search intelligently selects relevant tools
from a large catalog.
"""

import asyncio

from orchestrator.mcp_client import MCPClientShim
from orchestrator.tool_discovery import discover_tools
from orchestrator.tool_search import ToolSearchEngine

from orchestrator._internal.dispatch import functions, workers


async def main():
    print("=" * 70)
    print("ToolWeaver - Semantic Tool Search Demo")
    print("=" * 70)

    # Step 1: Discover all available tools
    print("\n1. Discovering tools...")
    mcp_client = MCPClientShim()
    catalog = await discover_tools(
        mcp_client=mcp_client,
        function_modules=[workers, functions],
        include_code_exec=True,
        use_cache=True
    )
    print(f"   ✓ Found {len(catalog.tools)} tools")

    # Step 2: Initialize search engine
    print("\n2. Initializing search engine...")
    search_engine = ToolSearchEngine(
        embedding_model="all-MiniLM-L6-v2",
        bm25_weight=0.3,
        embedding_weight=0.7
    )
    print("   ✓ Search engine ready")

    # Step 3: Test various queries
    test_queries = [
        "Extract text from a receipt image",
        "Parse receipt items and calculate total",
        "Apply discount to a price",
        "Categorize expenses",
        "Execute Python code for calculations",
        "Filter items by category",
    ]

    print(f"\n3. Testing {len(test_queries)} queries:")
    print("=" * 70)

    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: \"{query}\"")
        print("-" * 70)

        # Search for relevant tools
        results = search_engine.search(
            query=query,
            catalog=catalog,
            top_k=3,
            min_score=0.3
        )

        # Display results
        if results:
            print(f"Found {len(results)} relevant tools:")
            for rank, (tool, score) in enumerate(results, 1):
                relevance = "🔥" if score > 0.7 else "✓" if score > 0.5 else "~"
                print(f"  {rank}. {relevance} {tool.name:<25} (score: {score:.3f})")
                print(f"      Type: {tool.type:<12} Source: {tool.source}")
                print(f"      {tool.description[:60]}...")
        else:
            print("  No relevant tools found")

    # Step 4: Show search analytics
    print("\n" + "=" * 70)
    print("4. Search Analytics:")
    print("=" * 70)

    # Count cache files
    cache_dir = search_engine.cache_dir
    embedding_caches = list(cache_dir.glob("emb_*.npy"))
    search_caches = list(cache_dir.glob("search_*.pkl"))

    print(f"   Cache directory: {cache_dir}")
    print(f"   Embedding caches: {len(embedding_caches)} files")
    print(f"   Search result caches: {len(search_caches)} files")

    # Estimate token savings
    total_tools = len(catalog.tools)
    tools_per_search = 3
    token_per_tool = 150  # Rough estimate

    without_search_tokens = total_tools * token_per_tool
    with_search_tokens = tools_per_search * token_per_tool
    savings_percent = ((without_search_tokens - with_search_tokens) / without_search_tokens) * 100

    print("\n   Token Usage Estimate:")
    print(f"   - Without search: ~{without_search_tokens:,} tokens ({total_tools} tools)")
    print(f"   - With search: ~{with_search_tokens:,} tokens ({tools_per_search} tools)")
    print(f"   - Savings: {savings_percent:.1f}% reduction")

    print("\n" + "=" * 70)
    print("Demo complete! Semantic search working perfectly.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
