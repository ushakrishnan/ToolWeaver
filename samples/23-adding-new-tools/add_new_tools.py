"""
Example 23: Adding New Tools to Catalog (MCP and A2A)

End-to-end demonstration of:
1. Creating a custom MCP tool and registering it
2. Defining an A2A agent tool
3. Adding both to the unified catalog
4. Discovering and using them in workflows

This example shows:
- Tool definition with proper schemas
- MCP tool worker implementation
- Catalog registration
- Tool discovery and usage
- Both MCP (deterministic) and A2A (agent) tools in one catalog
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from orchestrator._internal.infra.a2a_client import A2AClient, AgentCapability
from orchestrator._internal.infra.mcp_client import MCPClientShim
from orchestrator.shared.models import (
    ToolCatalog,
    ToolDefinition,
    ToolExample,
    ToolParameter,
)
from orchestrator.tools.tool_discovery import discover_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# PART 1: Define Custom MCP Tools
# ============================================================================


def create_weather_mcp_tool() -> ToolDefinition:
    """
    Define a Weather MCP Tool

    This is a deterministic tool that fetches weather data.
    In production, this would connect to a real weather API via MCP server.

    Returns:
        ToolDefinition: Tool definition ready for catalog
    """
    return ToolDefinition(
        name="get_weather",
        type="mcp",
        description="Get current weather for a location using Weather API MCP server",
        parameters=[
            ToolParameter(
                name="city",
                type="string",
                description="City name (e.g., 'San Francisco', 'New York')",
                required=True,
            ),
            ToolParameter(
                name="units",
                type="string",
                description="Temperature units: 'celsius' or 'fahrenheit'",
                required=False,
                enum=["celsius", "fahrenheit"],
                default="fahrenheit",
            ),
        ],
        returns={
            "type": "object",
            "properties": {
                "temperature": {"type": "number", "description": "Current temperature"},
                "condition": {"type": "string", "description": "Weather condition (sunny, rainy, etc)"},
                "humidity": {"type": "integer", "description": "Humidity percentage (0-100)"},
                "wind_speed": {"type": "number", "description": "Wind speed in km/h"},
            },
        },
        examples=[
            ToolExample(
                scenario="Check current weather in San Francisco",
                input={"city": "San Francisco", "units": "celsius"},
                output={
                    "temperature": 18,
                    "condition": "partly cloudy",
                    "humidity": 65,
                    "wind_speed": 8,
                },
                notes="Results vary by time and season",
            ),
        ],
        domain="general",
        source="custom-mcp",
        version="1.0",
    )


def create_stock_price_mcp_tool() -> ToolDefinition:
    """
    Define a Stock Price MCP Tool

    This is another deterministic tool for financial data.
    """
    return ToolDefinition(
        name="get_stock_price",
        type="mcp",
        description="Get current stock price and market data for a ticker symbol",
        parameters=[
            ToolParameter(
                name="ticker",
                type="string",
                description="Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')",
                required=True,
            ),
            ToolParameter(
                name="include_history",
                type="boolean",
                description="Include 5-day price history",
                required=False,
                default=False,
            ),
        ],
        returns={
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "price": {"type": "number", "description": "Current price"},
                "currency": {"type": "string", "description": "Price currency (USD, EUR, etc)"},
                "timestamp": {"type": "string", "description": "Price timestamp in ISO 8601"},
                "change_percent": {"type": "number", "description": "Daily change percentage"},
            },
        },
        examples=[
            ToolExample(
                scenario="Check Apple stock price with history",
                input={"ticker": "AAPL", "include_history": True},
                output={
                    "ticker": "AAPL",
                    "price": 178.50,
                    "currency": "USD",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "change_percent": 2.5,
                },
                notes="Real-time data from market APIs",
            ),
        ],
        domain="general",
        source="custom-mcp",
        version="1.0",
    )


# ============================================================================
# PART 2: MCP Tool Worker Implementation
# ============================================================================


async def weather_tool_worker(payload: dict[str, Any]) -> dict[str, Any]:
    """
    MCP tool worker for weather service

    This worker is registered with MCPClientShim and called when
    get_weather tool is invoked.

    In production, this would call a real weather API.
    """
    city = payload.get("city", "Unknown")
    units = payload.get("units", "fahrenheit")

    logger.info(f"Fetching weather for {city} in {units}")

    # Simulate API call (in production, call real weather API)
    # Mock data based on city
    weather_data = {
        "San Francisco": {"temp": 18, "condition": "partly cloudy", "humidity": 65},
        "New York": {"temp": 8, "condition": "snowy", "humidity": 55},
        "London": {"temp": 5, "condition": "rainy", "humidity": 80},
        "Tokyo": {"temp": 12, "condition": "clear", "humidity": 50},
    }

    data = weather_data.get(city, {"temp": 20, "condition": "unknown", "humidity": 60})

    # Convert to Celsius if needed
    temp = data["temp"]
    if units == "celsius" and temp < 50:  # Assume temp is in Fahrenheit if > 50
        temp = (temp - 32) * 5 / 9

    result = {
        "temperature": round(temp, 1),
        "condition": data["condition"],
        "humidity": data["humidity"],
        "wind_speed": 5 + (hash(city) % 10),  # Pseudo-random based on city
    }

    logger.info(f"Weather result: {result}")
    return result


async def stock_price_tool_worker(payload: dict[str, Any]) -> dict[str, Any]:
    """
    MCP tool worker for stock price service

    Simulates fetching stock market data.
    """
    ticker = payload.get("ticker", "UNKNOWN").upper()
    include_history = payload.get("include_history", False)

    logger.info(f"Fetching stock price for {ticker}")

    # Mock stock prices
    prices = {
        "AAPL": 178.50,
        "MSFT": 380.20,
        "GOOGL": 140.75,
        "AMZN": 156.30,
        "TSLA": 238.10,
    }

    price = prices.get(ticker, 100.0)
    change = 2.5 if hash(ticker) % 2 == 0 else -1.5

    result = {
        "ticker": ticker,
        "price": round(price, 2),
        "currency": "USD",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "change_percent": change,
    }

    if include_history:
        # Add mock 5-day history
        result["history"] = [
            price - 5,
            price - 3,
            price - 1,
            price,
            price + 2,
        ]

    logger.info(f"Stock result: {result}")
    return result


# ============================================================================
# PART 3: Define A2A Agent Tools
# ============================================================================


def create_data_analyst_agent() -> AgentCapability:
    """
    Define a Data Analyst Agent for A2A

    This is an external agent that performs complex analysis.
    In production, this would be a running service with its own endpoint.
    """
    return AgentCapability(
        agent_id="data_analyst",
        name="Data Analyst",
        description="Analyzes data and provides insights, trends, and recommendations",
        endpoint="http://localhost:8001/agents/data_analyst",
    )


def create_report_generator_agent() -> AgentCapability:
    """
    Define a Report Generator Agent for A2A

    This agent creates formatted reports from analysis.
    """
    return AgentCapability(
        agent_id="report_generator",
        name="Report Generator",
        description="Generates professional reports and summaries from data and analysis",
        endpoint="http://localhost:8001/agents/report_generator",
    )


# ============================================================================
# PART 4: End-to-End Catalog Creation and Usage
# ============================================================================


async def setup_mcp_tools(mcp_client: MCPClientShim) -> ToolCatalog:
    """
    Step 1: Register MCP tools with MCPClientShim

    This demonstrates how to register custom MCP tool workers.
    """
    logger.info("=" * 70)
    logger.info("STEP 1: Registering Custom MCP Tools")
    logger.info("=" * 70)

    # Register tool workers
    mcp_client.tool_map["get_weather"] = weather_tool_worker
    mcp_client.tool_map["get_stock_price"] = stock_price_tool_worker

    logger.info(f"✓ Registered {len(mcp_client.tool_map)} MCP tool workers")
    logger.info(f"  Available tools: {list(mcp_client.tool_map.keys())}")

    # Create catalog with tool definitions
    catalog = ToolCatalog(source="custom-mcp", version="1.0")

    weather_tool = create_weather_mcp_tool()
    stock_tool = create_stock_price_mcp_tool()

    catalog.add_tool(weather_tool)
    catalog.add_tool(stock_tool)

    logger.info(f"✓ Created catalog with {len(catalog.tools)} tool definitions")
    logger.info(f"  Tools: {list(catalog.tools.keys())}")

    return catalog


async def setup_a2a_agents(a2a_client: A2AClient) -> None:
    """
    Step 2: Register A2A agents

    This demonstrates how to register agent capabilities.
    """
    logger.info("=" * 70)
    logger.info("STEP 2: Registering A2A Agents")
    logger.info("=" * 70)

    # Register agent capabilities
    agents = [
        create_data_analyst_agent(),
        create_report_generator_agent(),
    ]

    for agent in agents:
        a2a_client.register_agent(agent)
        logger.info(f"✓ Registered agent: {agent.agent_id} ({agent.name})")

    logger.info(f"✓ Total agents registered: {len(agents)}")


async def discover_all_tools(mcp_client: MCPClientShim, a2a_client: A2AClient) -> ToolCatalog:
    """
    Step 3: Unified discovery of all tools (MCP + A2A)

    This demonstrates how both MCP tools and A2A agents appear
    in a unified catalog.
    """
    logger.info("=" * 70)
    logger.info("STEP 3: Unified Tool Discovery (MCP + A2A)")
    logger.info("=" * 70)

    catalog = await discover_tools(
        mcp_client=mcp_client,
        a2a_client=a2a_client,
        use_cache=False,
    )

    logger.info(f"✓ Discovered {len(catalog.tools)} total tools")

    # Break down by type
    mcp_tools = catalog.get_by_type("mcp")
    agent_tools = catalog.get_by_type("agent")

    logger.info(f"  - MCP Tools: {len(mcp_tools)}")
    for tool in mcp_tools:
        logger.info(f"    • {tool.name}: {tool.description[:50]}...")

    logger.info(f"  - A2A Agents: {len(agent_tools)}")
    for tool in agent_tools:
        logger.info(f"    • {tool.name}: {tool.description[:50]}...")

    return catalog


async def demonstrate_tool_usage(
    mcp_client: MCPClientShim,
    catalog: ToolCatalog,
) -> dict[str, Any]:
    """
    Step 4: Demonstrate using tools from catalog

    Shows how to call MCP tools directly.
    """
    logger.info("=" * 70)
    logger.info("STEP 4: Using Tools from Catalog")
    logger.info("=" * 70)

    results = {}

    # Example 1: Call weather tool
    logger.info("\n📍 Calling get_weather tool...")
    weather_tool = catalog.get_tool("get_weather")

    if weather_tool:
        logger.info(f"Tool found: {weather_tool.name}")
        logger.info(f"Description: {weather_tool.description}")
        logger.info(f"Parameters: {[p.name for p in weather_tool.parameters]}")

        # Call the tool
        weather_payload = {"city": "San Francisco", "units": "celsius"}
        weather_result = await weather_tool_worker(weather_payload)
        results["weather"] = weather_result

        logger.info(f"✓ Result: {json.dumps(weather_result, indent=2)}")

    # Example 2: Call stock price tool
    logger.info("\n📊 Calling get_stock_price tool...")
    stock_tool = catalog.get_tool("get_stock_price")

    if stock_tool:
        logger.info(f"Tool found: {stock_tool.name}")
        logger.info(f"Description: {stock_tool.description}")

        stock_payload = {"ticker": "AAPL", "include_history": True}
        stock_result = await stock_price_tool_worker(stock_payload)
        results["stock"] = stock_result

        logger.info(f"✓ Result: {json.dumps(stock_result, indent=2)}")

    return results


async def demonstrate_tool_metadata(catalog: ToolCatalog) -> None:
    """
    Step 5: Show tool metadata and LLM-format conversion

    Demonstrates how tools are formatted for LLM consumption.
    """
    logger.info("=" * 70)
    logger.info("STEP 5: Tool Metadata and LLM Format")
    logger.info("=" * 70)

    # Show individual tool metadata
    for tool_name in ["get_weather", "get_stock_price"]:
        tool = catalog.get_tool(tool_name)
        if tool:
            logger.info(f"\n📋 Tool: {tool_name}")
            logger.info(f"   Type: {tool.type}")
            logger.info(f"   Domain: {tool.domain}")
            logger.info(f"   Source: {tool.source}")
            logger.info(f"   Parameters: {len(tool.parameters)}")
            logger.info(f"   Examples: {len(tool.examples)}")

            # Show LLM format
            llm_format = tool.to_llm_format(include_examples=False)
            logger.info(f"   LLM Format Keys: {list(llm_format.keys())}")

    # Show catalog-level stats
    logger.info("\n📊 Catalog Statistics:")
    logger.info(f"   Total tools: {len(catalog.tools)}")
    logger.info(f"   MCP tools: {len(catalog.get_by_type('mcp'))}")
    logger.info(f"   Agent tools: {len(catalog.get_by_type('agent'))}")
    logger.info(f"   Discovered at: {catalog.discovered_at}")
    logger.info(f"   Source: {catalog.source}")
    logger.info(f"   Version: {catalog.version}")


# ============================================================================
# PART 5: Main Workflow
# ============================================================================


async def main():
    """
    Complete end-to-end workflow for adding and using new tools
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 23: Adding New Tools to Catalog (MCP and A2A)".center(70))
    print("=" * 70 + "\n")

    # Initialize clients
    mcp_client = MCPClientShim()
    a2a_client = A2AClient(config_path=None)  # No config file needed for demo

    try:
        # Step 1: Register MCP tools
        mcp_catalog = await setup_mcp_tools(mcp_client)

        # Step 2: Register A2A agents
        await setup_a2a_agents(a2a_client)

        # Step 3: Unified discovery
        unified_catalog = await discover_all_tools(mcp_client, a2a_client)

        # Step 4: Demonstrate tool usage
        results = await demonstrate_tool_usage(mcp_client, unified_catalog)

        # Step 5: Show metadata and LLM format
        await demonstrate_tool_metadata(unified_catalog)

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("SUMMARY".center(70))
        logger.info("=" * 70)
        logger.info(f"✓ Successfully added {len(mcp_catalog.tools)} MCP tools")
        logger.info("✓ Successfully registered 2 A2A agents")
        logger.info(f"✓ Unified catalog contains {len(unified_catalog.tools)} total tools/agents")
        logger.info(f"✓ Called {len(results)} tools successfully")
        logger.info("\nAll tools are now ready for use in programmatic execution!")
        logger.info("=" * 70 + "\n")

        return unified_catalog

    except Exception as e:
        logger.error(f"Error in workflow: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    catalog = asyncio.run(main())
