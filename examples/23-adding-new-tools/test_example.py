"""
Test Example 23: Adding New Tools

Smoke tests for the add_new_tools example.
"""

import pytest

from orchestrator import A2AClient
from orchestrator._internal.infra.mcp_client import MCPClientShim
from orchestrator.shared.models import ToolCatalog


class TestToolDefinition:
    """Test tool definition creation"""

    def test_weather_tool_definition(self):
        """Test weather tool definition structure"""
        from add_new_tools import create_weather_mcp_tool

        tool = create_weather_mcp_tool()

        assert tool.name == "get_weather"
        assert tool.type == "mcp"
        assert len(tool.parameters) == 2
        assert tool.parameters[0].name == "city"
        assert tool.parameters[1].name == "units"
        assert len(tool.examples) >= 1

    def test_stock_tool_definition(self):
        """Test stock price tool definition"""
        from add_new_tools import create_stock_price_mcp_tool

        tool = create_stock_price_mcp_tool()

        assert tool.name == "get_stock_price"
        assert tool.type == "mcp"
        assert len(tool.parameters) == 2
        assert tool.parameters[0].name == "ticker"
        assert tool.parameters[1].name == "include_history"

    def test_tool_to_llm_format(self):
        """Test conversion to LLM function calling format"""
        from add_new_tools import create_weather_mcp_tool

        tool = create_weather_mcp_tool()
        llm_format = tool.to_llm_format(include_examples=False)

        assert "name" in llm_format
        assert "description" in llm_format
        assert "parameters" in llm_format
        assert llm_format["name"] == "get_weather"
        assert llm_format["parameters"]["type"] == "object"
        assert "properties" in llm_format["parameters"]


class TestToolWorkers:
    """Test tool worker functions"""

    @pytest.mark.asyncio
    async def test_weather_tool_worker(self):
        """Test weather tool worker execution"""
        from add_new_tools import weather_tool_worker

        result = await weather_tool_worker({"city": "San Francisco", "units": "celsius"})

        assert "temperature" in result
        assert "condition" in result
        assert "humidity" in result
        assert "wind_speed" in result
        assert isinstance(result["temperature"], (int, float))
        assert 0 <= result["humidity"] <= 100

    @pytest.mark.asyncio
    async def test_stock_price_tool_worker(self):
        """Test stock price tool worker execution"""
        from add_new_tools import stock_price_tool_worker

        result = await stock_price_tool_worker({"ticker": "AAPL", "include_history": True})

        assert result["ticker"] == "AAPL"
        assert "price" in result
        assert "currency" in result
        assert result["currency"] == "USD"
        assert "timestamp" in result
        assert "change_percent" in result
        assert "history" in result
        assert len(result["history"]) == 5

    @pytest.mark.asyncio
    async def test_worker_with_invalid_input(self):
        """Test worker handles missing parameters gracefully"""
        from add_new_tools import weather_tool_worker

        # Missing required city parameter
        result = await weather_tool_worker({})

        # Should still return result (with default city)
        assert "temperature" in result


class TestCatalogRegistration:
    """Test tool catalog operations"""

    @pytest.mark.asyncio
    async def test_register_mcp_tools(self):
        """Test MCP tool registration"""
        from add_new_tools import setup_mcp_tools

        mcp_client = MCPClientShim()
        catalog = await setup_mcp_tools(mcp_client)

        assert len(mcp_client.tool_map) == 2
        assert "get_weather" in mcp_client.tool_map
        assert "get_stock_price" in mcp_client.tool_map
        assert len(catalog.tools) == 2

    def test_catalog_get_tool(self):
        """Test retrieving tool from catalog"""
        from add_new_tools import create_weather_mcp_tool

        catalog = ToolCatalog()
        tool = create_weather_mcp_tool()
        catalog.add_tool(tool)

        retrieved = catalog.get_tool("get_weather")
        assert retrieved is not None
        assert retrieved.name == "get_weather"

    def test_catalog_get_by_type(self):
        """Test filtering tools by type"""
        from add_new_tools import create_stock_price_mcp_tool, create_weather_mcp_tool

        catalog = ToolCatalog()
        catalog.add_tool(create_weather_mcp_tool())
        catalog.add_tool(create_stock_price_mcp_tool())

        mcp_tools = catalog.get_by_type("mcp")
        assert len(mcp_tools) == 2
        assert all(t.type == "mcp" for t in mcp_tools)

    def test_catalog_to_llm_format(self):
        """Test converting catalog to LLM format"""
        from add_new_tools import create_weather_mcp_tool

        catalog = ToolCatalog()
        catalog.add_tool(create_weather_mcp_tool())

        llm_format = catalog.to_llm_format()
        assert len(llm_format) == 1
        assert llm_format[0]["name"] == "get_weather"


class TestAgentDefinition:
    """Test A2A agent definitions"""

    def test_data_analyst_agent(self):
        """Test data analyst agent definition"""
        from add_new_tools import create_data_analyst_agent

        agent = create_data_analyst_agent()

        assert agent.agent_id == "data_analyst"
        assert agent.name == "Data Analyst"
        assert "analysis" in agent.description.lower() or "insight" in agent.description.lower()

    def test_report_generator_agent(self):
        """Test report generator agent definition"""
        from add_new_tools import create_report_generator_agent

        agent = create_report_generator_agent()

        assert agent.agent_id == "report_generator"
        assert agent.name == "Report Generator"
        assert "report" in agent.description.lower()


class TestDiscovery:
    """Test tool discovery"""

    @pytest.mark.asyncio
    async def test_unified_discovery(self):
        """Test unified discovery of MCP tools and A2A agents"""
        from add_new_tools import setup_mcp_tools

        mcp_client = MCPClientShim()
        A2AClient(config_path=None)

        # Setup MCP tools
        catalog = await setup_mcp_tools(mcp_client)

        # Verify tools are in catalog
        assert len(catalog.tools) == 2
        assert "get_weather" in catalog.tools
        assert "get_stock_price" in catalog.tools


class TestWorkflow:
    """Test complete workflow"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete workflow from definition to execution"""
        from add_new_tools import (
            demonstrate_tool_usage,
            discover_all_tools,
            setup_a2a_agents,
            setup_mcp_tools,
        )

        mcp_client = MCPClientShim()
        a2a_client = A2AClient(config_path=None)

        # Step 1: Setup MCP tools
        mcp_catalog = await setup_mcp_tools(mcp_client)
        assert len(mcp_catalog.tools) == 2

        # Step 2: Setup A2A agents
        await setup_a2a_agents(a2a_client)
        # Verify agents are registered
        assert len(a2a_client.agents) >= 2

        # Step 3: Unified discovery
        unified_catalog = await discover_all_tools(mcp_client, a2a_client)
        # Should have at least MCP tools
        assert len(unified_catalog.tools) >= 2

        # Step 4: Demonstrate usage
        results = await demonstrate_tool_usage(mcp_client, unified_catalog)
        assert "weather" in results
        assert "stock" in results

        # Verify results
        assert "temperature" in results["weather"]
        assert "ticker" in results["stock"]


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests with mocking"""

    @pytest.mark.asyncio
    async def test_tool_call_with_catalog(self):
        """Test calling tool from catalog"""
        from add_new_tools import create_weather_mcp_tool, weather_tool_worker

        catalog = ToolCatalog()
        tool = create_weather_mcp_tool()
        catalog.add_tool(tool)

        # Verify tool exists in catalog
        assert catalog.get_tool("get_weather") is not None

        # Call tool worker
        result = await weather_tool_worker({"city": "London"})
        assert result is not None
        assert "temperature" in result

    @pytest.mark.asyncio
    async def test_parameter_validation(self):
        """Test parameter schema validation"""
        from add_new_tools import create_weather_mcp_tool

        tool = create_weather_mcp_tool()

        # Verify required parameters
        required_params = [p for p in tool.parameters if p.required]
        assert len(required_params) >= 1
        assert required_params[0].name == "city"

        # Verify optional parameters
        optional_params = [p for p in tool.parameters if not p.required]
        assert len(optional_params) >= 1

    def test_tool_domain_assignment(self):
        """Test tools are assigned to correct domain"""
        from add_new_tools import create_weather_mcp_tool

        tool = create_weather_mcp_tool()
        assert tool.domain in ["github", "slack", "aws", "database", "general"]

    def test_tool_source_tracking(self):
        """Test tool source is tracked"""
        from add_new_tools import create_weather_mcp_tool

        tool = create_weather_mcp_tool()
        assert tool.source == "custom-mcp"
        assert tool.version == "1.0"


# ============================================================================
# Run Tests
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
