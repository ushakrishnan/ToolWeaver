
# Example 23: Adding New Tools to Catalog (MCP and A2A)

**Complexity:** ⭐⭐⭐ Advanced | **Time:** 15 minutes

A complete end-to-end demonstration of how to add new custom tools to the ToolWeaver catalog, including both MCP tools and A2A agents.

## What This Example Shows

This example demonstrates the complete lifecycle of adding and using new tools:

1. **Creating MCP Tools** - Define deterministic tools with proper schemas
2. **Implementing Tool Workers** - Write execution logic for your tools
3. **Registering Tools** - Add tools to MCPClientShim
4. **Defining A2A Agents** - Configure external agent capabilities
5. **Unified Discovery** - Discover all tools (MCP + A2A) in one catalog
6. **Tool Metadata** - Understand tool format and LLM integration

## Key Files

- **`add_new_tools.py`** - Main example showing complete end-to-end workflow
- **`agents.yaml`** - Optional agent configuration for A2A tools
- **`test_example.py`** - Smoke tests for the example

## How It Works

### Part 1: Define MCP Tools

Tools are defined as `ToolDefinition` objects with:
- Name and description
- Parameter schema (for validation)
- Return type schema
- Examples (for LLM context)

```python
from orchestrator.shared.models import ToolDefinition, ToolParameter

weather_tool = ToolDefinition(
    name="get_weather",
    type="mcp",
    description="Get current weather for a location",
    parameters=[
        ToolParameter(
            name="city",
            type="string",
            description="City name",
            required=True,
        ),
    ],
    # ... more fields
)
```

See [Tool Definition Deep Dive](#tool-definition-deep-dive) below.

### Part 2: Implement Tool Workers

Each MCP tool needs a worker function that handles execution:

```python
async def weather_tool_worker(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Worker function for weather tool execution"""
    city = payload.get("city")
    
    # Fetch from API, database, or service
    result = fetch_weather_api(city)
    
    return result
```

### Part 3: Register Tools with MCPClientShim

Register your tool workers with the MCP client:

```python
mcp_client = MCPClientShim()
mcp_client.tool_map["get_weather"] = weather_tool_worker
mcp_client.tool_map["get_stock_price"] = stock_price_tool_worker
```

### Part 4: Add to Catalog

Create a catalog and add your tools:

```python
catalog = ToolCatalog(source="custom-mcp")
catalog.add_tool(weather_tool)
catalog.add_tool(stock_tool)
```

### Part 5: Unified Discovery

Discover all tools (MCP + A2A agents):

```python
from orchestrator.tools.tool_discovery import discover_tools

unified_catalog = await discover_tools(
    mcp_client=mcp_client,
    a2a_client=a2a_client,
    use_cache=False,
)

# Now includes both:
# - MCP tools (deterministic)
# - A2A agents (intelligent)
```

## Running the Example

### Quick Start

```bash
cd examples/23-adding-new-tools

# Run the example
python add_new_tools.py
```

### With Optional Logging

```bash
# Verbose output
LOGLEVEL=DEBUG python add_new_tools.py

# JSON output for parsing
python add_new_tools.py 2>&1 | grep "✓"
```

### Running Tests

```bash
# Run smoke tests
pytest test_example.py -v

# Run with coverage
pytest test_example.py --cov=orchestrator
```

## Sample Output

```
======================================================================
EXAMPLE 23: Adding New Tools to Catalog (MCP and A2A)
======================================================================

======================================================================
STEP 1: Registering Custom MCP Tools
======================================================================
✓ Registered 2 MCP tool workers
  Available tools: ['get_weather', 'get_stock_price']
✓ Created catalog with 2 tool definitions
  Tools: ['get_weather', 'get_stock_price']

======================================================================
STEP 2: Registering A2A Agents
======================================================================
✓ Registered agent: data_analyst (Data Analyst)
✓ Registered agent: report_generator (Report Generator)
✓ Total agents registered: 2

======================================================================
STEP 3: Unified Tool Discovery (MCP + A2A)
======================================================================
✓ Discovered 4 total tools
  - MCP Tools: 2
    • get_weather: Get current weather for a location...
    • get_stock_price: Get current stock price and market...
  - A2A Agents: 2
    • data_analyst: Analyzes data and provides insights...
    • report_generator: Generates professional reports...

======================================================================
STEP 4: Using Tools from Catalog
======================================================================

📍 Calling get_weather tool...
Tool found: get_weather
Description: Get current weather for a location using Weather API...
Parameters: ['city', 'units']
✓ Result:
{
  "temperature": 18.0,
  "condition": "partly cloudy",
  "humidity": 65,
  "wind_speed": 8
}

📊 Calling get_stock_price tool...
Tool found: get_stock_price
Description: Get current stock price and market data for a ticker...
✓ Result:
{
  "ticker": "AAPL",
  "price": 178.5,
  "currency": "USD",
  "timestamp": "2024-01-15T10:30:00Z",
  "change_percent": 2.5,
  "history": [173.5, 175.5, 177.5, 178.5, 180.5]
}

======================================================================
STEP 5: Tool Metadata and LLM Format
======================================================================

📋 Tool: get_weather
   Type: mcp
   Domain: general
   Source: custom-mcp
   Parameters: 2
   Examples: 1
   LLM Format Keys: ['name', 'description', 'parameters']

📋 Tool: get_stock_price
   Type: mcp
   Domain: general
   Source: custom-mcp
   Parameters: 2
   Examples: 1
   LLM Format Keys: ['name', 'description', 'parameters']

📊 Catalog Statistics:
   Total tools: 4
   MCP tools: 2
   Agent tools: 2
   Discovered at: 2024-01-15T10:30:00.000000+00:00
   Source: discover_tools
   Version: 1.0

======================================================================
SUMMARY
======================================================================
✓ Successfully added 2 MCP tools
✓ Successfully registered 2 A2A agents
✓ Unified catalog contains 4 total tools/agents
✓ Called 2 tools successfully

All tools are now ready for use in programmatic execution!
======================================================================
```

## Tool Definition Deep Dive

### Required Fields

Every tool must have:

| Field | Type | Purpose |
|-------|------|---------|
| `name` | string | Unique identifier (snake_case recommended) |
| `type` | string | One of: `mcp`, `function`, `code_exec`, `agent` |
| `description` | string | Human-readable description (LLM sees this) |
| `parameters` | List[ToolParameter] | Input schema |

### Optional but Recommended Fields

| Field | Type | Purpose |
|-------|------|---------|
| `returns` | Dict | Output schema (JSON Schema) |
| `examples` | List[ToolExample] | Usage examples (improves LLM accuracy) |
| `domain` | string | Tool domain: `github`, `slack`, `aws`, `database`, `general` |
| `source` | string | Where tool comes from (for tracking) |
| `version` | string | Tool version for compatibility tracking |

### Example: Complete Weather Tool Definition

```python
from orchestrator.shared.models import ToolDefinition, ToolParameter, ToolExample

weather_tool = ToolDefinition(
    name="get_weather",
    type="mcp",
    description="Get current weather for a location using Weather API MCP server",
    
    parameters=[
        ToolParameter(
            name="city",
            type="string",
            description="City name (e.g., 'San Francisco')",
            required=True,
        ),
        ToolParameter(
            name="units",
            type="string",
            description="Temperature units",
            required=False,
            enum=["celsius", "fahrenheit"],
            default="fahrenheit",
        ),
    ],
    
    returns={
        "type": "object",
        "properties": {
            "temperature": {"type": "number"},
            "condition": {"type": "string"},
            "humidity": {"type": "integer"},
        },
    },
    
    examples=[
        ToolExample(
            scenario="Check weather in San Francisco",
            input={"city": "San Francisco", "units": "celsius"},
            output={
                "temperature": 18,
                "condition": "partly cloudy",
                "humidity": 65,
            },
        ),
    ],
    
    domain="general",
    source="custom-mcp",
    version="1.0",
)
```

## Catalog Structure

Tools are organized hierarchically:

```
Catalog (unified view)
├── MCP Tools (deterministic)
│   ├── get_weather
│   ├── get_stock_price
│   └── ... (other MCP tools)
└── A2A Agents (intelligent)
    ├── data_analyst
    ├── report_generator
    └── ... (other agents)
```

### Accessing Tools

```python
# Get specific tool
tool = catalog.get_tool("get_weather")

# Get all tools of a type
mcp_tools = catalog.get_by_type("mcp")
agents = catalog.get_by_type("agent")

# Convert to LLM format
llm_tools = catalog.to_llm_format()
```

## Integration with Programmatic Execution

Once tools are in the catalog, they're ready for use with programmatic execution:

```python
from orchestrator.execution.programmatic_executor import ProgrammaticToolExecutor

executor = ProgrammaticToolExecutor(catalog=unified_catalog)

# LLM generates code that imports and uses tools
user_code = """
import asyncio
from toolweaver import get_weather, get_stock_price

# Get weather and stock price in parallel
weather = await get_weather(city="San Francisco")
stock = await get_stock_price(ticker="AAPL")

# LLM-generated orchestration
result = {
    "weather": weather,
    "stock": stock,
    "decision": "Buy if sunny and stock up 5%"
}
"""

# Execute safely in sandbox
result = await executor.execute(user_code)
```

For more details, see [Programmatic Tool Calling Explained](../../docs/how-it-works/programmatic-tool-calling/EXPLAINED.md).

## MCP vs A2A: When to Use What

### Use MCP Tools When You Need:
- ✓ Fast, deterministic operations (<1 second)
- ✓ API calls, database queries, calculations
- ✓ Low cost, no external service delays
- ✓ Strict input/output schemas

### Use A2A Agents When You Need:
- ✓ Complex reasoning and analysis
- ✓ Flexible, conversational responses
- ✓ Ability to call multiple tools themselves
- ✓ Intelligent decision-making

### Example: Hybrid Workflow

```python
# Step 1: Use MCP tool for data fetch (fast, cheap)
weather = await get_weather(city="San Francisco")
stock = await get_stock_price(ticker="AAPL")

# Step 2: Use A2A agent for analysis (intelligent)
analysis = await delegate_to_agent(
    agent_id="data_analyst",
    task="Analyze this weather and stock data",
    context={"weather": weather, "stock": stock}
)

# Step 3: Use MCP tool to store results (fast, deterministic)
await store_results(data=analysis)
```

## Common Patterns

### Pattern 1: Custom Function Tool

```python
from orchestrator.shared.models import ToolDefinition, ToolParameter

def add_numbers(payload):
    """Local function tool worker"""
    a = payload.get("a", 0)
    b = payload.get("b", 0)
    return {"result": a + b}

tool = ToolDefinition(
    name="add_numbers",
    type="function",
    description="Add two numbers",
    parameters=[
        ToolParameter(name="a", type="integer", required=True),
        ToolParameter(name="b", type="integer", required=True),
    ],
)

# Register
mcp_client.tool_map["add_numbers"] = add_numbers
catalog.add_tool(tool)
```

### Pattern 2: API Wrapper Tool

```python
async def fetch_user_data(payload):
    """Wrapper around external API"""
    user_id = payload.get("user_id")
    
    # Call external API
    response = await http_client.get(f"/api/users/{user_id}")
    return response.json()

tool = ToolDefinition(
    name="fetch_user",
    type="mcp",
    description="Fetch user data from API",
    parameters=[
        ToolParameter(name="user_id", type="string", required=True),
    ],
)

mcp_client.tool_map["fetch_user"] = fetch_user_data
catalog.add_tool(tool)
```

### Pattern 3: Database Query Tool

```python
async def query_database(payload):
    """Execute database queries safely"""
    sql = payload.get("sql")
    params = payload.get("params", {})
    
    # Validate SQL (prevent injection)
    if not is_safe_query(sql):
        raise ValueError("Unsafe SQL detected")
    
    # Execute with connection pooling
    result = await db.execute(sql, params)
    return {"rows": result}
```

## Checklist: Adding a New Tool

Use this checklist when adding a new tool to your system:

- [ ] **Define the Tool**
  - [ ] Tool name (snake_case)
  - [ ] Description (clear, LLM-friendly)
  - [ ] Parameters with types and descriptions
  - [ ] Return type schema
  - [ ] At least one usage example
  - [ ] Domain assignment (github/slack/aws/database/general)

- [ ] **Implement Worker**
  - [ ] Async function with `async def`
  - [ ] Accepts `payload: Dict[str, Any]`
  - [ ] Returns `Dict[str, Any]`
  - [ ] Proper error handling
  - [ ] Input validation

- [ ] **Register Tool**
  - [ ] Add to `mcp_client.tool_map` (MCP tools)
  - [ ] Or register with `a2a_client.register_agent()` (A2A agents)
  - [ ] Add `ToolDefinition` to catalog

- [ ] **Test**
  - [ ] Unit test for worker function
  - [ ] Integration test with catalog
  - [ ] Test with invalid inputs
  - [ ] Test error scenarios

- [ ] **Document**
  - [ ] Add docstring to worker
  - [ ] Update tool examples
  - [ ] Document parameters and return types
  - [ ] Add usage examples

## Troubleshooting

### Tool Not Appearing in Discovery

```python
# Problem: Tool registered in tool_map but not in catalog

# Solution: Add ToolDefinition to catalog
catalog.add_tool(tool_definition)

# Verify
discovered = await discover_tools(mcp_client=mcp_client)
assert "my_tool" in [t.name for t in discovered.tools.values()]
```

### Worker Function Not Called

```python
# Problem: Tool worker not being invoked

# Solution: Ensure correct registration
mcp_client.tool_map["my_tool"] = my_worker_function

# Verify function is callable
assert callable(mcp_client.tool_map["my_tool"])
```

### Type Validation Errors

```python
# Problem: "Invalid parameter type"

# Solution: Use correct type strings
VALID_TYPES = ["string", "integer", "number", "boolean", "object", "array"]

ToolParameter(
    name="count",
    type="integer",  # Not "int"
    required=True,
)
```

## What's Next

1. **Programmatic Execution**: See [Example 14](../14-programmatic-execution/) to learn how tools are used in AI-generated code
2. **Workflow Composition**: See [Example 5](../05-workflow-library/) for composing tools into reusable workflows
3. **Tool Search**: See [Example 4](../04-vector-search-discovery/) for semantic search across large tool catalogs
4. **Production Deployment**: See [docs/deployment/](../../docs/deployment/) for production considerations

## Related Documentation

### In This Repository

- [Programmatic Tool Calling Explained](../../docs/how-it-works/programmatic-tool-calling/EXPLAINED.md) - Deep dive into how tools are called programmatically
- [Programmatic Tool Calling Walkthrough](../../docs/how-it-works/programmatic-tool-calling/WALKTHROUGH.md) - Step-by-step execution trace
- [MCP Setup Guide](../../docs/user-guide/MCP_SETUP_GUIDE.md) - Configuring MCP servers and tools
- [A2A Setup Guide](../../docs/user-guide/A2A_SETUP_GUIDE.md) - Setting up agent-to-agent communication

### Quick Reference

- **Tool Definition**: `orchestrator.shared.models.ToolDefinition`
- **Tool Catalog**: `orchestrator.shared.models.ToolCatalog`
- **Discovery**: `orchestrator.tools.tool_discovery.discover_tools()`
- **MCP Client**: `orchestrator.infra.mcp_client.MCPClientShim`
- **A2A Client**: `orchestrator.infra.a2a_client.A2AClient`

## Example Directory Structure

```
23-adding-new-tools/
├── README.md                      ← This file
├── add_new_tools.py              ← Main example (600+ lines)
├── agents.yaml                    ← A2A agent configuration (optional)
├── test_example.py               ← Smoke tests
└── .env.example                  ← Environment template (if needed)
```

## Performance Notes

- **MCP Tool Discovery**: ~50-100ms (cached after first call)
- **A2A Agent Discovery**: ~100-200ms (registry lookup)
- **Unified Discovery**: ~150-300ms (first call), ~1ms (cached)
- **Tool Execution**: Depends on backend (MCP: <1s typically, A2A: 1-30s)

## References

| Resource | Link |
|----------|------|
| Tool Models | [orchestrator/shared/models.py](../../orchestrator/shared/models.py#L12-L100) |
| Tool Catalog | [orchestrator/shared/models.py](../../orchestrator/shared/models.py#L130-L165) |
| Discovery Logic | [orchestrator/tools/tool_discovery.py](../../orchestrator/tools/tool_discovery.py) |
| MCP Client | [orchestrator/infra/mcp_client.py](../../orchestrator/infra/mcp_client.py) |
| A2A Client | [orchestrator/infra/a2a_client.py](../../orchestrator/infra/a2a_client.py) |
