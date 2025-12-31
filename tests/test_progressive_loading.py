"""
Tests for progressive tool loading with detail levels.

Ensures browse_tools(), search_tools(), and get_tool_info() support
progressive disclosure with detail_level parameter.
"""

from typing import Any

import pytest

from orchestrator import (
    browse_tools,
    get_tool_info,
    search_tools,
    tool,
)
from orchestrator.plugins.registry import get_registry
from orchestrator.shared.models import ToolParameter


@pytest.fixture(autouse=True)
def setup_tools():
    """Create sample tools for testing."""
    registry = get_registry()
    registry.clear()

    @tool(
        description="Create a GitHub pull request",
        parameters=[
            ToolParameter(name="title", type="string", description="PR title", required=True),
            ToolParameter(name="body", type="string", description="PR body", required=False),
            ToolParameter(name="base", type="string", description="Base branch", required=True),
        ],
    )
    def create_pr(params: dict[str, Any]) -> dict[str, Any]:
        return {"pr_number": 123}

    @tool(
        description="Send Slack message",
        parameters=[
            ToolParameter(name="channel", type="string", description="Channel ID", required=True),
            ToolParameter(name="text", type="string", description="Message text", required=True),
        ],
    )
    def send_message(params: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True}

    @tool(
        description="Process invoice",
        parameters=[
            ToolParameter(name="invoice_id", type="string", description="Invoice ID", required=True),
        ],
    )
    def process_invoice(params: dict[str, Any]) -> dict[str, Any]:
        return {"status": "processed"}

    yield
    registry.clear()


def test_browse_tools_name_level():
    """Test browse_tools with detail_level='name'."""
    results = browse_tools(detail_level="name", limit=10)

    assert len(results) == 3
    for item in results:
        assert isinstance(item, dict)
        assert "name" in item
        assert "type" in item
        assert "domain" in item
        # Should NOT have description or parameters at name level
        assert "description" not in item
        assert "parameters" not in item


def test_browse_tools_summary_level():
    """Test browse_tools with detail_level='summary'."""
    results = browse_tools(detail_level="summary", limit=10)

    assert len(results) == 3
    for item in results:
        assert isinstance(item, dict)
        assert "name" in item
        assert "description" in item
        assert "parameter_count" in item
        # Should have summary but NOT full parameter schema
        assert "parameters" not in item


def test_browse_tools_full_level():
    """Test browse_tools with detail_level='full'."""
    results = browse_tools(detail_level="full", limit=10)

    assert len(results) == 3
    for item in results:
        # Full level returns ToolDefinition objects
        assert hasattr(item, "name")
        assert hasattr(item, "description")
        assert hasattr(item, "parameters")


def test_browse_tools_pagination():
    """Test browse_tools pagination with offset/limit."""
    # Get first page
    page1 = browse_tools(detail_level="name", offset=0, limit=2)
    assert len(page1) == 2

    # Get second page
    page2 = browse_tools(detail_level="name", offset=2, limit=2)
    assert len(page2) == 1

    # Ensure no overlap
    names1 = {item["name"] for item in page1}
    names2 = {item["name"] for item in page2}
    assert len(names1 & names2) == 0


def test_browse_tools_with_domain_filter():
    """Test browse_tools with domain filter."""
    # All tools have domain="general" by default
    general_tools = browse_tools(domain="general", detail_level="summary")
    assert len(general_tools) >= 1


def test_browse_tools_with_type_filter():
    """Test browse_tools with type filter."""
    function_tools = browse_tools(type_filter="function", detail_level="summary")
    assert len(function_tools) == 3
    assert all(t["type"] == "function" for t in function_tools)


def test_search_tools_with_detail_level_name():
    """Test search_tools with detail_level='name'."""
    results = search_tools(query="github", detail_level="name")

    assert len(results) >= 1
    for item in results:
        assert isinstance(item, dict)
        assert "name" in item
        assert "description" not in item


def test_search_tools_with_detail_level_summary():
    """Test search_tools with detail_level='summary'."""
    results = search_tools(query="slack", detail_level="summary")

    assert len(results) >= 1
    for item in results:
        assert isinstance(item, dict)
        assert "name" in item
        assert "description" in item
        assert "parameter_count" in item
        assert "parameters" not in item


def test_search_tools_with_detail_level_full():
    """Test search_tools with detail_level='full'."""
    results = search_tools(query="invoice", detail_level="full")

    assert len(results) >= 1
    for item in results:
        assert hasattr(item, "name")
        assert hasattr(item, "parameters")


def test_search_tools_without_detail_level():
    """Test search_tools defaults to full ToolDefinition objects."""
    results = search_tools(query="message")

    assert len(results) >= 1
    for item in results:
        # Without detail_level, should return full ToolDefinition
        assert hasattr(item, "name")
        assert hasattr(item, "parameters")


def test_get_tool_info_name_level():
    """Test get_tool_info with detail_level='name'."""
    info = get_tool_info("create_pr", detail_level="name")

    assert isinstance(info, dict)
    assert info["name"] == "create_pr"
    assert "description" not in info


def test_get_tool_info_summary_level():
    """Test get_tool_info with detail_level='summary'."""
    info = get_tool_info("send_message", detail_level="summary")

    assert isinstance(info, dict)
    assert info["name"] == "send_message"
    assert info["description"] == "Send Slack message"
    assert info["parameter_count"] == 2
    assert "parameters" not in info


def test_get_tool_info_full_level():
    """Test get_tool_info with detail_level='full' (default)."""
    info = get_tool_info("process_invoice")

    # Full level returns ToolDefinition
    assert hasattr(info, "name")
    assert info.name == "process_invoice"
    assert hasattr(info, "parameters")
    assert len(info.parameters) == 1


def test_get_tool_info_with_examples():
    """Test get_tool_info with include_examples parameter."""
    # Tools created with @tool don't have examples, but test the parameter works
    info = get_tool_info("create_pr", detail_level="summary", include_examples=True)

    assert isinstance(info, dict)
    # Should have example_count field showing 0
    assert "example_count" in info


def test_get_tool_info_without_examples():
    """Test get_tool_info excludes examples by default at summary level."""
    info = get_tool_info("create_pr", detail_level="summary", include_examples=False)

    assert isinstance(info, dict)
    assert "examples" not in info


def test_browse_tools_invalid_detail_level():
    """Test browse_tools raises on invalid detail_level."""
    with pytest.raises(ValueError, match="detail_level must be one of"):
        browse_tools(detail_level="invalid")


def test_browse_tools_negative_offset():
    """Test browse_tools raises on negative offset."""
    with pytest.raises(ValueError, match="offset and limit must be non-negative"):
        browse_tools(offset=-1)


def test_browse_tools_negative_limit():
    """Test browse_tools raises on negative limit."""
    with pytest.raises(ValueError, match="offset and limit must be non-negative"):
        browse_tools(limit=-1)


def test_progressive_workflow():
    """Test realistic progressive disclosure workflow."""
    # 1. Browse names to see what's available
    names = browse_tools(detail_level="name", limit=100)
    assert len(names) >= 3

    # 2. Search for specific capability with summary
    summaries = search_tools(query="github", detail_level="summary")
    assert len(summaries) >= 1
    tool = summaries[0]
    assert "parameter_count" in tool
    assert tool["parameter_count"] == 3

    # 3. Get full details for selected tool
    full_info = get_tool_info(tool["name"], detail_level="full")
    assert hasattr(full_info, "parameters")
    assert len(full_info.parameters) == 3


def test_detail_levels_token_reduction():
    """Verify detail levels reduce token usage."""
    # Full tools have all parameters
    full_tools = browse_tools(detail_level="full")

    # Summary tools omit parameter schemas
    summary_tools = browse_tools(detail_level="summary")

    # Name-only tools minimal
    name_tools = browse_tools(detail_level="name")

    # Rough token estimate: full > summary > name
    # Each level should be progressively smaller
    full_size = sum(len(str(t)) for t in full_tools)
    summary_size = sum(len(str(t)) for t in summary_tools)
    name_size = sum(len(str(t)) for t in name_tools)

    assert name_size < summary_size < full_size


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
