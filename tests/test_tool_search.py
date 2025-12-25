"""
Unit Tests for Tool Search Engine (Phase 3)

Tests BM25 search, embedding search, hybrid scoring, caching,
smart routing, score thresholds, and result ranking.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from orchestrator.shared.models import ToolCatalog, ToolDefinition, ToolParameter
from orchestrator.tools.tool_search import ToolSearchEngine, search_tools


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory for tests"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_catalog():
    """Create sample tool catalog for testing"""
    catalog = ToolCatalog(source="test", version="1.0")
    
    # Receipt processing tools
    catalog.add_tool(ToolDefinition(
        name="receipt_ocr",
        type="mcp",
        description="Extract text from receipt images using OCR",
        parameters=[
            ToolParameter(name="image_url", type="string", description="Receipt image URL", required=True)
        ],
        domain="finance",
        source="test"
    ))
    
    catalog.add_tool(ToolDefinition(
        name="line_item_parser",
        type="mcp",
        description="Parse OCR text into structured line items with prices",
        parameters=[
            ToolParameter(name="text", type="string", description="OCR text", required=True)
        ],
        domain="finance",
        source="test"
    ))
    
    # Communication tools
    catalog.add_tool(ToolDefinition(
        name="slack_send_message",
        type="function",
        description="Send a message to a Slack channel",
        parameters=[
            ToolParameter(name="channel", type="string", description="Channel name", required=True),
            ToolParameter(name="message", type="string", description="Message text", required=True)
        ],
        domain="comms",
        source="test"
    ))
    
    catalog.add_tool(ToolDefinition(
        name="email_send",
        type="function",
        description="Send an email message",
        parameters=[
            ToolParameter(name="to", type="string", description="Recipient email", required=True),
            ToolParameter(name="subject", type="string", description="Email subject", required=True),
            ToolParameter(name="body", type="string", description="Email body", required=True)
        ],
        domain="comms",
        source="test"
    ))
    
    # Data tools
    catalog.add_tool(ToolDefinition(
        name="database_query",
        type="function",
        description="Execute SQL database query",
        parameters=[
            ToolParameter(name="sql", type="string", description="SQL query", required=True)
        ],
        domain="data",
        source="test"
    ))
    
    catalog.add_tool(ToolDefinition(
        name="file_read",
        type="function",
        description="Read file from filesystem",
        parameters=[
            ToolParameter(name="path", type="string", description="File path", required=True)
        ],
        domain="data",
        source="test"
    ))
    
    return catalog


class TestToolSearchEngineBasic:
    """Basic functionality tests"""
    
    def test_search_engine_initialization(self, temp_cache_dir):
        """Test search engine can be initialized"""
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        assert engine.embedding_model_name == "all-MiniLM-L6-v2"
        assert engine.bm25_weight == 0.3
        assert engine.embedding_weight == 0.7
        assert engine.cache_dir == temp_cache_dir
    
    def test_custom_weights(self, temp_cache_dir):
        """Test custom BM25 and embedding weights"""
        engine = ToolSearchEngine(
            bm25_weight=0.5,
            embedding_weight=0.5,
            cache_dir=temp_cache_dir
        )
        assert engine.bm25_weight == 0.5
        assert engine.embedding_weight == 0.5
    
    def test_empty_catalog_returns_empty_results(self, temp_cache_dir):
        """Test search with empty catalog returns empty list"""
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        empty_catalog = ToolCatalog(source="test")
        
        results = engine.search("test query", empty_catalog, top_k=5)
        assert results == []


class TestSmartRouting:
    """Test smart routing for small catalogs"""
    
    def test_small_catalog_skips_search(self, sample_catalog, temp_cache_dir):
        """Test that catalogs with ≤20 tools skip search"""
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        
        # Sample catalog has 6 tools (< 20)
        results = engine.search("receipt processing", sample_catalog, top_k=3)
        
        # Should return top_k tools with score 1.0 (no actual search)
        assert len(results) == 3
        for tool, score in results:
            assert score == 1.0
    
    def test_large_catalog_uses_search(self, temp_cache_dir):
        """Test that catalogs with >20 tools use search"""
        # Create catalog with 25 tools
        large_catalog = ToolCatalog(source="test")
        for i in range(25):
            large_catalog.add_tool(ToolDefinition(
                name=f"tool_{i}",
                type="function",
                description=f"Tool number {i} for testing",
                parameters=[],
                source="test"
            ))
        
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        results = engine.search("tool 5", large_catalog, top_k=5)
        
        # Should perform actual search (scores vary)
        assert len(results) <= 5
        # Scores should not all be 1.0
        scores = [score for _, score in results]
        assert not all(s == 1.0 for s in scores)


class TestBM25Search:
    """Test BM25 keyword-based search"""
    
    def test_bm25_exact_match(self, sample_catalog, temp_cache_dir):
        """Test BM25 finds exact keyword matches"""
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        tools = list(sample_catalog.tools.values())
        
        # Search for "receipt" - should match receipt_ocr highly
        scores = engine._bm25_search("receipt ocr", tools)
        
        # Find receipt_ocr index
        receipt_idx = next(i for i, t in enumerate(tools) if t.name == "receipt_ocr")
        
        # Should have high score for receipt_ocr
        assert scores[receipt_idx] > 0.5
    
    def test_bm25_normalization(self, sample_catalog, temp_cache_dir):
        """Test BM25 scores are normalized to 0-1"""
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        tools = list(sample_catalog.tools.values())
        
        scores = engine._bm25_search("test query", tools)
        
        assert all(0 <= s <= 1 for s in scores)
        assert max(scores) <= 1.0


class TestEmbeddingSearch:
    """Test embedding-based semantic search"""
    
    def test_embedding_initialization(self, sample_catalog, temp_cache_dir):
        """Test embedding model is lazy loaded"""
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        assert engine.embedding_model is None
        
        # Trigger embedding search
        tools = list(sample_catalog.tools.values())
        engine._embedding_search("test", tools)
        
        # Model should now be loaded
        assert engine.embedding_model is not None
    
    def test_embedding_semantic_match(self, sample_catalog, temp_cache_dir):
        """Test embeddings find semantically similar tools"""
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        tools = list(sample_catalog.tools.values())
        
        # Search for "communication" - should match slack/email
        scores = engine._embedding_search("send communication message", tools)
        
        # Find slack and email indices
        slack_idx = next(i for i, t in enumerate(tools) if "slack" in t.name)
        email_idx = next(i for i, t in enumerate(tools) if "email" in t.name)
        
        # Communication tools should score higher than database tools
        db_idx = next(i for i, t in enumerate(tools) if "database" in t.name)
        
        assert scores[slack_idx] > scores[db_idx]
        assert scores[email_idx] > scores[db_idx]
    
    def test_embedding_scores_normalized(self, sample_catalog, temp_cache_dir):
        """Test embedding scores are in 0-1 range"""
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        tools = list(sample_catalog.tools.values())
        
        scores = engine._embedding_search("test query", tools)
        
        assert all(0 <= s <= 1 for s in scores)


class TestHybridScoring:
    """Test combined BM25 + embedding scoring"""
    
    def test_hybrid_combines_scores(self, temp_cache_dir):
        """Test hybrid scoring combines BM25 and embeddings"""
        # Create catalog with distinguishable tools
        catalog = ToolCatalog(source="test")
        catalog.add_tool(ToolDefinition(
            name="exact_keyword_match",
            type="function",
            description="unique_keyword_12345 for testing",
            parameters=[],
            source="test"
        ))
        catalog.add_tool(ToolDefinition(
            name="semantic_match",
            type="function",
            description="Tool for processing and analyzing data",
            parameters=[],
            source="test"
        ))
        
        # Add 19 more tools to exceed smart routing threshold
        for i in range(19):
            catalog.add_tool(ToolDefinition(
                name=f"filler_tool_{i}",
                type="function",
                description=f"Random tool {i}",
                parameters=[],
                source="test"
            ))
        
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        
        # Search for exact keyword
        results = engine.search("unique_keyword_12345", catalog, top_k=5)
        
        # Should find the exact match tool
        tool_names = [tool.name for tool, score in results]
        assert "exact_keyword_match" in tool_names


class TestCaching:
    """Test embedding and query result caching"""
    
    def test_embedding_caching(self, sample_catalog, temp_cache_dir):
        """Test embeddings are cached and reused"""
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        tools = list(sample_catalog.tools.values())
        
        # First search - computes embeddings
        engine._embedding_search("test", tools)
        
        # Check cache files exist
        cache_files = list(temp_cache_dir.glob("emb_*.npy"))
        assert len(cache_files) > 0
        
        # Second search - should use cached embeddings
        engine._embedding_search("test", tools)
        
        # Cache file count should remain the same
        cache_files_after = list(temp_cache_dir.glob("emb_*.npy"))
        assert len(cache_files_after) == len(cache_files)
    
    def test_query_result_caching(self, sample_catalog, temp_cache_dir):
        """Test query results are cached"""
        # Need >20 tools for actual search
        for i in range(15):
            sample_catalog.add_tool(ToolDefinition(
                name=f"extra_tool_{i}",
                type="function",
                description=f"Extra tool {i}",
                parameters=[],
                source="test"
            ))
        
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        
        # First search
        results1 = engine.search("receipt processing", sample_catalog, top_k=3)
        
        # Check cache file exists
        cache_files = list(temp_cache_dir.glob("search_*.pkl"))
        assert len(cache_files) > 0
        
        # Second search with same query
        results2 = engine.search("receipt processing", sample_catalog, top_k=3)
        
        # Results should be identical
        assert len(results1) == len(results2)
        for (t1, s1), (t2, s2) in zip(results1, results2):
            assert t1.name == t2.name
            assert s1 == s2


class TestScoreThresholds:
    """Test minimum score filtering"""
    
    def test_min_score_filtering(self, temp_cache_dir):
        """Test results below min_score are filtered out"""
        # Create catalog with many tools
        catalog = ToolCatalog(source="test")
        for i in range(25):
            catalog.add_tool(ToolDefinition(
                name=f"tool_{i}",
                type="function",
                description=f"Generic tool {i}",
                parameters=[],
                source="test"
            ))
        
        # Add one highly relevant tool
        catalog.add_tool(ToolDefinition(
            name="super_specific_unique_tool",
            type="function",
            description="This is a super specific unique tool for testing",
            parameters=[],
            source="test"
        ))
        
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        
        # Search with high min_score
        results = engine.search(
            "super specific unique testing",
            catalog,
            top_k=10,
            min_score=0.5
        )
        
        # Should return fewer than top_k due to filtering
        assert len(results) <= 10
        
        # All results should meet min_score
        for tool, score in results:
            assert score >= 0.5


class TestResultRanking:
    """Test results are properly ranked by relevance"""
    
    def test_results_sorted_by_score(self, temp_cache_dir):
        """Test results are sorted in descending order by score"""
        # Create catalog with 25+ tools
        catalog = ToolCatalog(source="test")
        for i in range(30):
            catalog.add_tool(ToolDefinition(
                name=f"tool_{i}",
                type="function",
                description=f"Tool for purpose {i}",
                parameters=[],
                source="test"
            ))
        
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        results = engine.search("tool purpose", catalog, top_k=10)
        
        # Scores should be in descending order
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_top_k_limit(self, temp_cache_dir):
        """Test only top_k results are returned"""
        catalog = ToolCatalog(source="test")
        for i in range(30):
            catalog.add_tool(ToolDefinition(
                name=f"tool_{i}",
                type="function",
                description=f"Tool {i}",
                parameters=[],
                source="test"
            ))
        
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        
        # Request top 5 - use unique query to avoid cache
        results = engine.search("find tools query one", catalog, top_k=5)
        assert len(results) == 5
        
        # Request top 15 - use different query
        results = engine.search("find tools query two", catalog, top_k=15)
        assert len(results) == 15


class TestConvenienceFunction:
    """Test the search_tools convenience function"""
    
    def test_search_tools_returns_definitions_only(self, sample_catalog, temp_cache_dir):
        """Test convenience function returns tools without scores"""
        tools = search_tools(
            "receipt",
            sample_catalog,
            top_k=3,
            cache_dir=temp_cache_dir
        )
        
        # Should return list of ToolDefinitions
        assert isinstance(tools, list)
        assert all(isinstance(t, ToolDefinition) for t in tools)
        assert len(tools) <= 3

    def test_search_tools_filters_by_domain(self, sample_catalog, temp_cache_dir):
        """Domain filter should return only matching tools and cache separately"""
        finance_tools = search_tools(
            "",
            sample_catalog,
            top_k=10,
            domain="finance",
            cache_dir=temp_cache_dir,
        )

        assert {t.name for t in finance_tools} == {"receipt_ocr", "line_item_parser"}

        comms_tools = search_tools(
            "",
            sample_catalog,
            top_k=10,
            domain="comms",
            cache_dir=temp_cache_dir,
        )

        assert {t.name for t in comms_tools} == {"slack_send_message", "email_send"}


class TestExplainResults:
    """Test result explanation functionality"""
    
    def test_explain_results_format(self, sample_catalog, temp_cache_dir):
        """Test explain_results generates readable explanation"""
        engine = ToolSearchEngine(cache_dir=temp_cache_dir)
        
        # Get some results (smart routing will return all with score 1.0)
        results = engine.search("receipt", sample_catalog, top_k=3)
        
        explanation = engine.explain_results("receipt processing", results)
        
        # Should contain query
        assert "receipt processing" in explanation
        
        # Should contain tool names
        for tool, score in results:
            assert tool.name in explanation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
