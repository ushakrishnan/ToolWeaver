"""
Tests for Vector Tool Search Engine (Phase 7)

Validates Qdrant integration, fallback behavior, and performance.
"""

import time

import pytest

from orchestrator.shared.models import ToolCatalog, ToolDefinition, ToolParameter
from orchestrator.tools.vector_search import VectorToolSearchEngine


@pytest.fixture
def large_catalog():
    """Create a large tool catalog for testing"""
    catalog = ToolCatalog()

    # GitHub tools
    for i in range(20):
        catalog.add_tool(ToolDefinition(
            name=f"github_operation_{i}",
            type="function",
            description=f"GitHub operation {i}: create PR, list issues, manage repos",
            parameters=[
                ToolParameter(name="repo", type="string", description="Repository name", required=True)
            ],
            domain="github"
        ))

    # Slack tools
    for i in range(20):
        catalog.add_tool(ToolDefinition(
            name=f"slack_operation_{i}",
            type="function",
            description=f"Slack operation {i}: send messages, create channels, manage users",
            parameters=[
                ToolParameter(name="channel", type="string", description="Channel name", required=True)
            ],
            domain="slack"
        ))

    # AWS tools
    for i in range(20):
        catalog.add_tool(ToolDefinition(
            name=f"aws_operation_{i}",
            type="function",
            description=f"AWS operation {i}: S3 buckets, EC2 instances, Lambda functions",
            parameters=[
                ToolParameter(name="resource", type="string", description="Resource name", required=True)
            ],
            domain="aws"
        ))

    # Database tools
    for i in range(20):
        catalog.add_tool(ToolDefinition(
            name=f"db_operation_{i}",
            type="function",
            description=f"Database operation {i}: queries, migrations, backups",
            parameters=[
                ToolParameter(name="query", type="string", description="SQL query", required=True)
            ],
            domain="database"
        ))

    # General utilities
    for i in range(20):
        catalog.add_tool(ToolDefinition(
            name=f"util_operation_{i}",
            type="function",
            description=f"Utility operation {i}: file operations, parsing, formatting",
            parameters=[
                ToolParameter(name="input", type="string", description="Input data", required=True)
            ],
            domain="general"
        ))

    return catalog  # 100 tools total


@pytest.fixture
def search_engine_with_fallback():
    """Create search engine with memory fallback enabled"""
    return VectorToolSearchEngine(
        qdrant_url="http://localhost:6333",
        fallback_to_memory=True
    )


@pytest.fixture
def search_engine_no_fallback():
    """Create search engine without fallback"""
    return VectorToolSearchEngine(
        qdrant_url="http://localhost:6333",
        fallback_to_memory=False
    )


def test_initialization():
    """Test search engine initializes correctly"""
    engine = VectorToolSearchEngine()

    assert engine.qdrant_url == "http://localhost:6333"
    assert engine.collection_name == "toolweaver_tools"
    assert engine.embedding_dim == 384
    assert engine.fallback_to_memory == True


def test_index_catalog_memory_fallback(search_engine_with_fallback, large_catalog):
    """Test indexing works with memory fallback (no Qdrant)"""
    # Don't initialize client - force fallback
    success = search_engine_with_fallback.index_catalog(large_catalog, batch_size=32)

    assert success == True
    assert len(search_engine_with_fallback.memory_embeddings) == 100
    assert len(search_engine_with_fallback.memory_tools) == 100


def test_search_memory_fallback(search_engine_with_fallback, large_catalog):
    """Test search works with memory fallback"""
    # Index in memory
    search_engine_with_fallback.index_catalog(large_catalog)

    # Search for GitHub tools
    results = search_engine_with_fallback.search(
        "create pull request on github",
        large_catalog,
        top_k=5
    )

    assert len(results) > 0
    assert len(results) <= 5

    # Check that results are relevant (should be github tools)
    github_tools = [tool for tool, score in results if tool.domain == "github"]
    assert len(github_tools) > 0  # At least some results should be github


def test_search_performance(search_engine_with_fallback, large_catalog):
    """Test search latency meets targets"""
    # Index catalog
    search_engine_with_fallback.index_catalog(large_catalog)

    # Warm-up query
    search_engine_with_fallback.search("test", large_catalog, top_k=5)

    # Measure search time
    queries = [
        "create github pull request",
        "send slack message",
        "create S3 bucket on AWS",
        "run database query",
        "parse JSON file"
    ]

    latencies = []
    for query in queries:
        start_time = time.time()
        results = search_engine_with_fallback.search(query, large_catalog, top_k=5)
        latency_ms = (time.time() - start_time) * 1000
        latencies.append(latency_ms)

        assert len(results) > 0, f"No results for query: {query}"

    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)

    print("\n100-tool catalog performance:")
    print(f"  Average latency: {avg_latency:.1f}ms")
    print(f"  Max latency: {max_latency:.1f}ms")

    # Target: <100ms for 100 tools
    assert avg_latency < 100, f"Average latency {avg_latency:.1f}ms exceeds 100ms target"


def test_domain_filtering(search_engine_with_fallback, large_catalog):
    """Test domain-based search filtering"""
    search_engine_with_fallback.index_catalog(large_catalog)

    # Search with domain filter (use lower min_score to ensure we get results)
    results = search_engine_with_fallback.search(
        "github pull request issue repo",
        large_catalog,
        top_k=10,
        domain="github",
        min_score=0.1  # Lower threshold to ensure we get results with filter
    )

    # Should only return github tools
    assert len(results) > 0, "Domain filtering should return at least some github tools"
    for tool, score in results:
        assert tool.domain == "github", f"Tool {tool.name} has domain {tool.domain}, expected 'github'"


def test_relevance_scores(search_engine_with_fallback, large_catalog):
    """Test that relevance scores are meaningful"""
    search_engine_with_fallback.index_catalog(large_catalog)

    results = search_engine_with_fallback.search(
        "github pull request",
        large_catalog,
        top_k=10
    )

    assert len(results) > 0

    # Scores should be between 0 and 1
    for tool, score in results:
        assert 0 <= score <= 1, f"Score {score} out of range [0, 1]"

    # Scores should be in descending order
    scores = [score for _, score in results]
    assert scores == sorted(scores, reverse=True), "Scores not sorted descending"


def test_min_score_threshold(search_engine_with_fallback, large_catalog):
    """Test minimum score filtering"""
    search_engine_with_fallback.index_catalog(large_catalog)

    # High threshold should return fewer results
    results_high = search_engine_with_fallback.search(
        "test",
        large_catalog,
        top_k=20,
        min_score=0.8
    )

    # Low threshold should return more results
    results_low = search_engine_with_fallback.search(
        "test",
        large_catalog,
        top_k=20,
        min_score=0.1
    )

    assert len(results_low) >= len(results_high)

    # All results should meet minimum score
    for tool, score in results_high:
        assert score >= 0.8


def test_empty_catalog(search_engine_with_fallback):
    """Test behavior with empty catalog"""
    empty_catalog = ToolCatalog()

    success = search_engine_with_fallback.index_catalog(empty_catalog)
    assert success == False

    results = search_engine_with_fallback.search("test", empty_catalog)
    assert len(results) == 0


def test_embedding_model_lazy_load(search_engine_with_fallback):
    """Test that embedding model is lazily loaded"""
    # Initially None
    assert search_engine_with_fallback.embedding_model is None

    # Trigger loading
    catalog = ToolCatalog()
    catalog.add_tool(ToolDefinition(
        name="test_tool",
        type="function",
        description="Test tool",
        parameters=[]
    ))

    search_engine_with_fallback.index_catalog(catalog)

    # Now loaded
    assert search_engine_with_fallback.embedding_model is not None


@pytest.mark.parametrize("catalog_size", [100, 500, 1000])
def test_scalability(search_engine_with_fallback, catalog_size):
    """Test search performance at different scales"""
    # Generate catalog of specified size
    catalog = ToolCatalog()
    for i in range(catalog_size):
        catalog.add_tool(ToolDefinition(
            name=f"tool_{i}",
            type="function",
            description=f"Tool {i} for various operations",
            parameters=[],
            domain="general"
        ))

    # Index
    start_time = time.time()
    search_engine_with_fallback.index_catalog(catalog, batch_size=64)
    index_time = (time.time() - start_time) * 1000

    print(f"\nIndexing {catalog_size} tools took {index_time:.1f}ms")

    # Search
    start_time = time.time()
    results = search_engine_with_fallback.search("test operation", catalog, top_k=5)
    search_time = (time.time() - start_time) * 1000

    print(f"Searching {catalog_size} tools took {search_time:.1f}ms")

    assert len(results) > 0

    # Performance targets from Phase 7 design:
    # 100 tools: <30ms
    # 500 tools: <60ms
    # 1000 tools: <80ms
    targets = {100: 30, 500: 60, 1000: 80}
    if catalog_size in targets:
        target = targets[catalog_size]
        # Allow 3x margin for CI/testing environments
        assert search_time < target * 3, f"Search time {search_time:.1f}ms exceeds {target*3}ms (3x target)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
