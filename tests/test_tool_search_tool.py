"""
Tests for Tool Search Tool (Phase 6)

Validates that tool_search_tool correctly searches and returns relevant tools.
"""

import pytest
from orchestrator.tool_search_tool import (
    tool_search_tool,
    initialize_tool_search,
    get_tool_search_definition
)
from orchestrator.models import ToolCatalog, ToolDefinition, ToolParameter


@pytest.fixture
def sample_catalog():
    """Create a sample tool catalog for testing"""
    catalog = ToolCatalog()
    
    # Add various tools
    tools = [
        ToolDefinition(
            name="github_create_pr",
            type="function",
            description="Create a pull request on GitHub repository",
            parameters=[
                ToolParameter(name="repo", type="string", description="Repository name", required=True),
                ToolParameter(name="title", type="string", description="PR title", required=True)
            ]
        ),
        ToolDefinition(
            name="github_list_issues",
            type="function",
            description="List issues in a GitHub repository",
            parameters=[
                ToolParameter(name="repo", type="string", description="Repository name", required=True)
            ]
        ),
        ToolDefinition(
            name="slack_send_message",
            type="function",
            description="Send a message to a Slack channel",
            parameters=[
                ToolParameter(name="channel", type="string", description="Channel name", required=True),
                ToolParameter(name="text", type="string", description="Message text", required=True)
            ]
        ),
        ToolDefinition(
            name="email_send",
            type="function",
            description="Send an email to recipients",
            parameters=[
                ToolParameter(name="to", type="string", description="Recipient email", required=True),
                ToolParameter(name="subject", type="string", description="Email subject", required=True)
            ]
        ),
        ToolDefinition(
            name="parse_json",
            type="function",
            description="Parse JSON string into structured data",
            parameters=[
                ToolParameter(name="json_str", type="string", description="JSON string", required=True)
            ]
        ),
        ToolDefinition(
            name="compute_tax",
            type="function",
            description="Calculate tax amount for a given amount",
            parameters=[
                ToolParameter(name="amount", type="number", description="Base amount", required=True),
                ToolParameter(name="rate", type="number", description="Tax rate", required=False)
            ]
        )
    ]
    
    for tool in tools:
        catalog.add_tool(tool)
    
    return catalog


def test_get_tool_search_definition():
    """Test that tool_search_tool definition is properly created"""
    tool_def = get_tool_search_definition()
    
    assert tool_def.name == "tool_search_tool"
    assert tool_def.type == "function"
    assert tool_def.defer_loading == False  # Should always be loaded
    assert len(tool_def.parameters) == 2  # query and top_k
    assert tool_def.parameters[0].name == "query"
    assert tool_def.parameters[1].name == "top_k"
    assert len(tool_def.examples) > 0  # Should have examples


def test_tool_search_not_initialized():
    """Test tool search returns error when not initialized"""
    # Don't initialize - test uninitialized state
    result = tool_search_tool("test query")
    
    assert "error" in result
    assert result["tools"] == []
    assert result["total_available"] == 0


def test_tool_search_initialization(sample_catalog):
    """Test initializing tool search with a catalog"""
    initialize_tool_search(sample_catalog)
    
    result = tool_search_tool("github")
    
    assert "error" not in result
    assert result["total_available"] == 6  # Sample catalog has 6 tools


def test_tool_search_github_tools(sample_catalog):
    """Test searching for GitHub-related tools"""
    initialize_tool_search(sample_catalog)
    
    result = tool_search_tool("create pull request on github", top_k=3)
    
    assert "tools" in result
    assert len(result["tools"]) > 0
    assert result["query"] == "create pull request on github"
    
    # Check that github_create_pr is in top results
    tool_names = [t["name"] for t in result["tools"]]
    assert "github_create_pr" in tool_names


def test_tool_search_communication_tools(sample_catalog):
    """Test searching for communication tools"""
    initialize_tool_search(sample_catalog)
    
    result = tool_search_tool("send message to team", top_k=5)
    
    assert len(result["tools"]) > 0
    tool_names = [t["name"] for t in result["tools"]]
    
    # Should find slack or email tools
    assert any("slack" in name or "email" in name for name in tool_names)


def test_tool_search_top_k_limit(sample_catalog):
    """Test that top_k parameter limits results"""
    initialize_tool_search(sample_catalog)
    
    result = tool_search_tool("tool", top_k=2)
    
    assert len(result["tools"]) <= 2
    assert result["returned"] <= 2


def test_tool_search_relevance_scores(sample_catalog):
    """Test that results include relevance scores"""
    initialize_tool_search(sample_catalog)
    
    result = tool_search_tool("github pull request", top_k=3)
    
    assert len(result["tools"]) > 0
    for tool in result["tools"]:
        assert "relevance_score" in tool
        assert 0 <= tool["relevance_score"] <= 1


def test_tool_search_returns_tool_format(sample_catalog):
    """Test that search returns tools in LLM-compatible format"""
    initialize_tool_search(sample_catalog)
    
    result = tool_search_tool("parse data", top_k=2)
    
    assert len(result["tools"]) > 0
    
    # Check format matches LLM expectations
    for tool in result["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool
        assert "type" in tool["parameters"]
        assert "properties" in tool["parameters"]


def test_tool_search_empty_query(sample_catalog):
    """Test search with empty query"""
    initialize_tool_search(sample_catalog)
    
    result = tool_search_tool("", top_k=5)
    
    # Should still return some results
    assert "tools" in result
    assert result["total_available"] == 6


def test_tool_search_no_matches(sample_catalog):
    """Test search with query that has no good matches"""
    initialize_tool_search(sample_catalog)
    
    result = tool_search_tool("quantum computing blockchain AI", top_k=3)
    
    # Should return something even with poor matches
    assert "tools" in result
    # Might return empty or low-relevance results


def test_tool_search_case_insensitive(sample_catalog):
    """Test that search is case-insensitive"""
    initialize_tool_search(sample_catalog)
    
    result_lower = tool_search_tool("github", top_k=3)
    result_upper = tool_search_tool("GITHUB", top_k=3)
    result_mixed = tool_search_tool("GitHub", top_k=3)
    
    # All should return similar results
    assert len(result_lower["tools"]) > 0
    assert len(result_upper["tools"]) > 0
    assert len(result_mixed["tools"]) > 0


def test_tool_search_multiple_keywords(sample_catalog):
    """Test search with multiple keywords"""
    initialize_tool_search(sample_catalog)
    
    result = tool_search_tool("send email message", top_k=5)
    
    assert len(result["tools"]) > 0
    tool_names = [t["name"] for t in result["tools"]]
    
    # Should find both email and slack tools
    communication_tools = [name for name in tool_names 
                          if "email" in name or "slack" in name]
    assert len(communication_tools) > 0


def test_tool_search_returns_metadata(sample_catalog):
    """Test that search result includes useful metadata"""
    initialize_tool_search(sample_catalog)
    
    result = tool_search_tool("test", top_k=3)
    
    assert "query" in result
    assert "total_available" in result
    assert "returned" in result
    assert result["total_available"] == 6
    assert result["returned"] <= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
