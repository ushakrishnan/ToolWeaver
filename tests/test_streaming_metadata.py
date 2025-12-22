"""Test streaming metadata surface in discovery and execution."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from orchestrator.shared.models import ToolDefinition, ToolParameter
from orchestrator.tools.agent_discovery import AgentDiscoverer
from orchestrator._internal.infra.a2a_client import A2AClient, AgentCapability


class TestStreamingMetadataSurface:
    """Test that streaming capabilities are properly surfaced in discovery."""

    def test_mcp_streaming_metadata_in_discovery(self):
        """Verify MCP tools indicate streaming support in metadata."""
        # Mock tool with streaming support
        tool = ToolDefinition(
            name="long_running_analysis",
            description="Analyze data over time",
            provider="mcp",
            type="tool",
            input_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "string"}
                },
                "required": ["data"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            },
            metadata={
                "supports_streaming": True,
                "stream_chunk_size": 1024,
                "execution_time_ms": 5000
            }
        )

        assert tool.metadata["supports_streaming"] is True
        assert tool.metadata["stream_chunk_size"] == 1024

    def test_a2a_agent_streaming_metadata(self):
        """Verify A2A agents expose streaming capabilities."""
        # Create agent with streaming capability
        agent = {
            "id": "analyzer",
            "name": "Data Analyzer",
            "description": "Analyze complex datasets",
            "input_schema": {
                "type": "object",
                "properties": {
                    "data": {"type": "array"}
                }
            },
            "capabilities": [
                AgentCapability(
                    name="stream_analysis",
                    description="Stream analysis results",
                    supports_streaming=True,
                    supports_http_streaming=True,
                    supports_sse=True,
                    supports_websocket=True
                )
            ]
        }

        capability = agent["capabilities"][0]
        assert capability.supports_streaming is True
        assert capability.supports_http_streaming is True
        assert capability.supports_sse is True
        assert capability.supports_websocket is True

    @pytest.mark.asyncio
    async def test_agent_discoverer_surfaces_streaming(self):
        """Verify AgentDiscoverer converts agent capabilities to tool metadata."""
        # Mock A2A client
        mock_a2a = AsyncMock(spec=A2AClient)
        mock_a2a.discover_agents.return_value = [
            {
                "id": "analyzer",
                "name": "Data Analyzer",
                "description": "Analyze data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "string"}
                    },
                    "required": ["data"]
                },
                "capabilities": [
                    AgentCapability(
                        name="streaming_analysis",
                        description="Stream results",
                        supports_streaming=True,
                        supports_http_streaming=True,
                        supports_sse=True
                    )
                ]
            }
        ]

        discoverer = AgentDiscoverer(mock_a2a)
        tools = await discoverer.discover()

        assert len(tools) == 1
        tool = list(tools.values())[0]
        
        # Verify streaming metadata is surfaced
        assert tool.type == "agent"
        assert tool.metadata.get("supports_streaming") is True
        assert tool.metadata.get("supports_http_streaming") is True
        assert tool.metadata.get("supports_sse") is True

    def test_tool_definition_streaming_schema(self):
        """Test ToolDefinition properly represents streaming metadata."""
        # Tool with comprehensive streaming info
        tool = ToolDefinition(
            name="generate_report",
            description="Generate analysis report",
            provider="a2a",
            type="agent",
            input_schema={
                "type": "object",
                "properties": {
                    "analysis_type": {"type": "string"},
                    "detail_level": {"type": "string"}
                },
                "required": ["analysis_type"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "report": {"type": "string"},
                    "metadata": {"type": "object"}
                }
            },
            metadata={
                "supports_streaming": True,
                "stream_format": "json-lines",  # or "text", "sse"
                "chunk_time_estimate_ms": 100,
                "estimated_total_time_ms": 5000,
                "cost_per_call_usd": 0.05,
                "execution_time_ms": 5000
            }
        )

        # Verify all streaming metadata is accessible
        metadata = tool.metadata
        assert metadata["supports_streaming"] is True
        assert metadata["stream_format"] == "json-lines"
        assert metadata["chunk_time_estimate_ms"] == 100
        assert metadata["estimated_total_time_ms"] == 5000

    @pytest.mark.asyncio
    async def test_streaming_metadata_in_discovery_response(self):
        """Test that discovered tools include complete streaming metadata."""
        # Create mock discovered tools
        tools = [
            ToolDefinition(
                name="mcp_tool",
                description="Fast deterministic tool",
                provider="mcp",
                type="tool",
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                metadata={
                    "supports_streaming": False,
                    "execution_time_ms": 100,
                    "cost_per_call_usd": 0.001
                }
            ),
            ToolDefinition(
                name="agent_tool",
                description="Agentic reasoning tool",
                provider="a2a",
                type="agent",
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                metadata={
                    "supports_streaming": True,
                    "supports_http_streaming": True,
                    "supports_sse": True,
                    "execution_time_ms": 3000,
                    "cost_per_call_usd": 0.05
                }
            )
        ]

        # Verify metadata is complete
        mcp_metadata = tools[0].metadata
        agent_metadata = tools[1].metadata

        assert "supports_streaming" in mcp_metadata
        assert "execution_time_ms" in mcp_metadata
        assert "cost_per_call_usd" in mcp_metadata

        assert "supports_streaming" in agent_metadata
        assert "supports_http_streaming" in agent_metadata
        assert "execution_time_ms" in agent_metadata
        assert "cost_per_call_usd" in agent_metadata

    def test_streaming_guidance_in_tool_metadata(self):
        """Test that metadata includes guidance for streaming decisions."""
        # Tool with decision guidance
        tool = ToolDefinition(
            name="process_large_file",
            description="Process a large data file",
            provider="mcp",
            type="tool",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            metadata={
                "supports_streaming": True,
                "supports_streaming_min_response_size_bytes": 1024 * 100,  # 100KB
                "supports_streaming_recommended": True,
                "stream_chunk_size_recommended": 4096,
                "execution_time_ms": 10000,
                "note": "Large files should use streaming to avoid memory issues"
            }
        )

        metadata = tool.metadata
        assert metadata["supports_streaming_recommended"] is True
        assert metadata["supports_streaming_min_response_size_bytes"] == 1024 * 100
        assert metadata["stream_chunk_size_recommended"] == 4096

    @pytest.mark.asyncio
    async def test_streaming_discovery_consistency(self):
        """Test that streaming metadata is consistent across discovery calls."""
        # Mock tools from two discovery sources
        mcp_tool = ToolDefinition(
            name="mcp_reader",
            description="Read file",
            provider="mcp",
            type="tool",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            metadata={
                "supports_streaming": True,
                "execution_time_ms": 500
            }
        )

        a2a_tool = ToolDefinition(
            name="agent_analyzer",
            description="Analyze with agent",
            provider="a2a",
            type="agent",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            metadata={
                "supports_streaming": True,
                "execution_time_ms": 3000,
                "supports_http_streaming": True
            }
        )

        # Both should have consistent structure
        for tool in [mcp_tool, a2a_tool]:
            assert "supports_streaming" in tool.metadata
            assert "execution_time_ms" in tool.metadata
            assert isinstance(tool.metadata["supports_streaming"], bool)
            assert isinstance(tool.metadata["execution_time_ms"], (int, float))

    def test_streaming_parameter_exposure(self):
        """Test that streaming parameters are exposed in tool definition."""
        tool = ToolDefinition(
            name="streaming_processor",
            description="Process with streaming",
            provider="custom",
            type="tool",
            input_schema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                    "enable_streaming": {
                        "type": "boolean",
                        "description": "Enable streaming output",
                        "default": True
                    },
                    "chunk_size": {
                        "type": "integer",
                        "description": "Size of each stream chunk",
                        "default": 4096
                    }
                }
            },
            output_schema={"type": "object"}
        )

        # Check that streaming parameters are documented
        props = tool.input_schema["properties"]
        assert "enable_streaming" in props
        assert "chunk_size" in props
        assert props["enable_streaming"]["description"] == "Enable streaming output"
        assert props["chunk_size"]["default"] == 4096


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
