"""
Example 05: YAML Workflows

Demonstrates:
- Define tools in YAML configuration
- Load tools from YAML files
- Reusable workflow definitions
- Configuration-driven tool registration

Use Case:
Manage tools through configuration files for easy version control and deployment
"""

import asyncio
from pathlib import Path

import yaml

from orchestrator import get_available_tools, mcp_tool

# ============================================================
# Create a sample YAML workflow file
# ============================================================

SAMPLE_WORKFLOW_YAML = """
tools:
  - name: fetch_weather
    description: Get current weather for a city
    type: mcp
    domain: weather
    parameters:
      - name: city
        description: City name
        type: string
        required: true
      - name: units
        description: Temperature units (C or F)
        type: string
        required: false
        default: C
  
  - name: format_report
    description: Format data into a report
    type: mcp
    domain: reporting
    parameters:
      - name: data
        description: Data to format
        type: object
        required: true
      - name: format
        description: Output format (json, csv, html)
        type: string
        required: true
  
  - name: send_notification
    description: Send notification via email or Slack
    type: mcp
    domain: communication
    parameters:
      - name: message
        description: Message to send
        type: string
        required: true
      - name: channel
        description: Destination (email, slack, sms)
        type: string
        required: true
"""


# ============================================================
# Demonstrate YAML Loading
# ============================================================

async def demo_yaml_loading():
    """Show how to load tools from YAML."""
    print("\n" + "="*70)
    print("DEMO: Loading Tools from YAML")
    print("="*70)
    print()

    # Create temp YAML file
    yaml_path = Path(__file__).parent / "tools_config.yaml"

    try:
        # Write sample YAML
        yaml_path.write_text(SAMPLE_WORKFLOW_YAML)
        print(f"Created YAML config: {yaml_path.name}")
        print()

        # Load tools from YAML (note: this loads definitions, not actual implementations)
        print("Loading tools from YAML...")
        # Note: load_tools_from_yaml loads tool definitions but requires actual
        # implementations or workers to be registered separately

        print("Sample YAML content:")
        print("-" * 70)
        print(SAMPLE_WORKFLOW_YAML[:300] + "...")
        print("-" * 70)
        print()

        print("Tools defined in YAML:")
        yaml_data = yaml.safe_load(SAMPLE_WORKFLOW_YAML)
        for tool in yaml_data.get('tools', []):
            print(f"  • {tool['name']:25} | {tool['description']}")
        print()

    finally:
        # Cleanup
        if yaml_path.exists():
            yaml_path.unlink()


# ============================================================
# Hybrid Approach: Mix YAML + Code Registration
# ============================================================

async def demo_hybrid_approach():
    """Show mixing YAML definitions with code registration."""
    print("\n" + "="*70)
    print("DEMO: Hybrid Approach (YAML + Code)")
    print("="*70)
    print()

    print("Step 1: Define tools in code")

    @mcp_tool(domain="weather", description="Get current temperature")
    async def get_temperature(city: str) -> dict:
        """Get temperature for a city."""
        temps = {"London": 8, "Paris": 7, "New York": -2, "Tokyo": 5}
        return {"city": city, "temperature": temps.get(city, "Unknown"), "unit": "C"}

    @mcp_tool(domain="weather", description="Get weather forecast")
    async def get_forecast(city: str, days: int = 3) -> dict:
        """Get weather forecast."""
        return {
            "city": city,
            "forecast_days": days,
            "conditions": ["Sunny", "Cloudy", "Rainy"][:days]
        }

    @mcp_tool(domain="reporting", description="Generate summary report")
    async def generate_report(title: str, data: dict) -> dict:
        """Generate a report from data."""
        return {
            "title": title,
            "sections": len(data),
            "format": "markdown",
            "content": f"# {title}\n\nData summary: {len(str(data))} chars"
        }

    print("   Registered 3 tools")
    print()

    print("Step 2: Use tools dynamically")

    # Get temperature
    print("   Fetching weather...")
    temp_result = await get_temperature({"city": "London"})
    print(f"   -> {temp_result['city']}: {temp_result['temperature']}°{temp_result['unit']}")

    # Get forecast
    forecast_result = await get_forecast({"city": "London", "days": 3})
    print(f"   -> Forecast: {', '.join(forecast_result['conditions'])}")

    # Generate report
    report_result = await generate_report({
        "title": "Weather Report",
        "data": temp_result
    })
    print(f"   -> Generated: {report_result['title']}")
    print()


# ============================================================
# Show Tool Organization by Domain
# ============================================================

async def demo_tool_organization():
    """Show how tools organize by domain."""
    print("\n" + "="*70)
    print("DEMO: Tool Organization")
    print("="*70)
    print()

    all_tools = get_available_tools()

    # Group by domain
    domains = {}
    for tool in all_tools:
        domain = getattr(tool, 'domain', 'general')
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(tool)

    print(f"Total registered tools: {len(all_tools)}")
    print()
    print("Tools by domain:")
    for domain in sorted(domains.keys()):
        tools = domains[domain]
        print(f"  {domain}:")
        for tool in tools[:3]:  # Show first 3
            print(f"    - {tool.name}")
        if len(tools) > 3:
            print(f"    ... and {len(tools)-3} more")
    print()


# ============================================================
# Main
# ============================================================

async def main():
    """Run workflow library demonstrations."""
    print("\n" + "="*70)
    print("EXAMPLE 05: YAML Workflows")
    print("="*70)
    print()
    print("This example shows how to define and manage tools using YAML")
    print("configurations and code registration patterns.")
    print()

    await demo_yaml_loading()
    await demo_hybrid_approach()
    await demo_tool_organization()

    print("="*70)
    print("Complete! You can now:")
    print("  1. Define tools in YAML for configuration management")
    print("  2. Register tools in code using @mcp_tool decorator")
    print("  3. Mix both approaches for flexibility")
    print("="*70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
