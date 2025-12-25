# MCP Tools Setup Guide

This guide walks you through setting up and using Model Context Protocol (MCP) tools in ToolWeaver.

## Table of Contents

1. [What is MCP?](#what-is-mcp)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Discovery](#discovery)
5. [Calling Tools](#calling-tools)
6. [Streaming Tools](#streaming-tools)
7. [Error Handling](#error-handling)
8. [Monitoring](#monitoring)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Comparison: MCP vs A2A](#comparison-mcp-vs-a2a)

## What is MCP?

**Model Context Protocol (MCP)** is a standard for defining and calling deterministic tools with structured schemas. MCP servers expose tools that:

- Have strict, JSON-schema-based inputs and outputs
- Execute quickly (typically <1 second)
- Are cost-efficient to call
- May support streaming for long-running operations

**Use MCP for:**
- API calls with known inputs/outputs
- Data transformations
- Calculations
- Web scraping
- Code execution
- Any deterministic operation

## Quick Start

### 1. Set Up MCP Client

```python
from orchestrator.mcp_client import MCPClient
from orchestrator.tool_search import discover_tools

# Initialize MCP client from environment
mcp = MCPClient(env_file=".env")

# Discover all tools from MCP servers
tools = await discover_tools(mcp_client=mcp, use_cache=True)
print(f"Found {len(tools)} tools")
```

### 2. Call a Tool

```python
from orchestrator.orchestrator import Orchestrator

# Create orchestrator with catalog
orchestrator = Orchestrator(catalog, monitoring=monitor)

# Execute a tool
result = await orchestrator.run_step({
    "tool_name": "extract_text",
    "inputs": {
        "image_url": "https://example.com/image.jpg",
        "enhance": True
    }
})

print(result)  # {"text": "Extracted content..."}
```

### 3. Search for Tools

```python
from orchestrator.tools.tool_search_tool import tool_search_tool

# Search for a tool
search_result = await tool_search_tool(
    tool_search_tool.call,
    {
        "query": "extract text from image",
        "limit": 5
    },
    catalog
)

for tool in search_result:
    print(f"- {tool['name']}: {tool['description']}")
```

## Configuration

### Environment Variables

MCP servers are configured via environment variables. Example `.env`:

```env
# Claude Desktop integrations
CLAUDE_SERVERS_FILE=~/.claude/config.json

# Or individual MCP server configs
MCP_SERVER_WEATHER=https://weather-server.example.com
MCP_SERVER_API_DOCS=https://api-docs-server.example.com
```

### Configuration Options

```python
from orchestrator.mcp_client import MCPClient

mcp = MCPClient(
    env_file=".env",                    # Load from file
    verify_ssl=True,                     # SSL verification
    timeout=30,                          # Request timeout
    max_retries=2                        # Retry failed requests
)
```

### Tool Categories

MCP tools in ToolWeaver are organized by:

- **Built-in**: Functions in orchestrator.functions
- **Code Execution**: Code execution with package management
- **External**: MCP servers (Claude, custom implementations)

## Discovery

### One-Time Discovery

```python
from orchestrator.tool_search import discover_tools

# Full discovery (no caching)
all_tools = await discover_tools(mcp_client=mcp, use_cache=False)
print(f"Discovered {len(all_tools)} tools")
```

### Cached Discovery

```python
# With caching (24-hour TTL by default)
tools = await discover_tools(mcp_client=mcp, use_cache=True)
# First call: ~50-100ms (introspects MCP servers)
# Subsequent calls: ~1ms (from cache)
```

### Search for Specific Tools

```python
from orchestrator.tool_search import find_relevant_tools

# Semantic search across tools
relevant = await find_relevant_tools(
    query="extract structured data from PDF",
    catalog=catalog,
    limit=5
)

for tool in relevant:
    print(f"\n{tool.name} (confidence: {tool.search_score:.2f})")
    print(f"  {tool.description}")
    print(f"  Input: {tool.input_schema}")
    print(f"  Output: {tool.output_schema}")
```

### Tool Metadata

Each discovered tool includes:

```python
{
    "name": "extract_text",
    "description": "Extract text content from images",
    "provider": "mcp",                    # Source
    "type": "tool",                       # Not "agent"
    "input_schema": {                     # JSON Schema
        "type": "object",
        "properties": {
            "image_url": {"type": "string"},
            "enhance": {"type": "boolean", "default": False}
        },
        "required": ["image_url"]
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "confidence": {"type": "number"}
        }
    },
    "examples": [                         # Tool usage examples
        {
            "input": {"image_url": "...", "enhance": True},
            "output": {"text": "...", "confidence": 0.95}
        }
    ],
    "metadata": {
        "supports_streaming": False,       # Or True for async-gen tools
        "execution_time_ms": 250,
        "cost_per_call_usd": 0.01
    }
}
```

## Calling Tools

### Basic Tool Call

```python
from orchestrator.orchestrator import Orchestrator

orchestrator = Orchestrator(catalog, monitoring=monitor)

result = await orchestrator.run_step({
    "tool_name": "extract_text",
    "inputs": {
        "image_url": "https://example.com/image.jpg"
    }
})

print(result)
```

### With Error Handling

```python
result = await orchestrator.run_step({
    "tool_name": "extract_text",
    "inputs": {"image_url": url},
    "max_retries": 2,
    "timeout": 30
})

if result.get("error"):
    print(f"Tool failed: {result['error']}")
else:
    print(f"Success: {result['text']}")
```

### With Context Passing

```python
# First tool call
step1 = await orchestrator.run_step({
    "tool_name": "fetch_api_data",
    "inputs": {"endpoint": "/api/users"}
})

# Second tool uses first result
step2 = await orchestrator.run_step({
    "tool_name": "transform_data",
    "inputs": {"data": step1["users"]},
    "context": {"source_call": "fetch_api_data"}  # Optional metadata
})
```

### Tool Chaining

```python
# Manual chaining
result1 = await orchestrator.run_step({
    "tool_name": "tool_a",
    "inputs": {...}
})

result2 = await orchestrator.run_step({
    "tool_name": "tool_b",
    "inputs": {..., "data": result1["output"]}
})

# Or use Workflow for automatic chaining
from orchestrator.workflow import WorkflowTemplate, WorkflowExecutor

template = WorkflowTemplate(
    name="data_pipeline",
    steps=[
        WorkflowStep(step_id="fetch", tool_name="fetch_api_data"),
        WorkflowStep(step_id="transform", tool_name="transform_data",
                    depends_on=["fetch"]),
        WorkflowStep(step_id="store", tool_name="store_in_db",
                    depends_on=["transform"])
    ]
)

executor = WorkflowExecutor(catalog, monitoring=monitor)
result = await executor.execute(template)
```

## Streaming Tools

Some MCP tools support streaming (for long-running operations):

### Detecting Streaming Support

```python
# Tool metadata indicates streaming
tools = await discover_tools(mcp_client=mcp, use_cache=True)
streaming_tools = [t for t in tools if t.metadata.get("supports_streaming")]

for tool in streaming_tools:
    print(f"{tool.name} supports streaming")
```

### Calling Streaming Tools

```python
# Request streaming output
result = await orchestrator.run_step({
    "tool_name": "long_running_analysis",
    "inputs": {"data": data},
    "stream": True  # Enable streaming
})

# Result is list of chunks
if isinstance(result.get("chunks"), list):
    for chunk in result["chunks"]:
        print(f"Received chunk: {chunk}")
```

### Consuming Streaming Responses

```python
response = await orchestrator.run_step({
    "tool_name": "generate_report",
    "inputs": {"data": data},
    "stream": True
})

# Chunks are already buffered
report = ""
for chunk in response["chunks"]:
    report += chunk  # Aggregate as needed
    print(f"Received: {len(chunk)} bytes")

print(f"Final report length: {len(report)}")
```

## Error Handling

### Common Errors

```python
try:
    result = await orchestrator.run_step({
        "tool_name": "api_call",
        "inputs": {"url": "https://api.example.com"}
    })
except ValueError as e:
    # Invalid inputs
    print(f"Input validation failed: {e}")
except TimeoutError as e:
    # Tool took too long
    print(f"Tool timeout: {e}")
except Exception as e:
    # Other errors
    print(f"Tool execution failed: {e}")
```

### Retries

```python
# Automatic retries with exponential backoff
result = await orchestrator.run_step({
    "tool_name": "api_call",
    "inputs": {...},
    "max_retries": 3,          # Retry up to 3 times
    "retry_delay": 1.0,        # Start with 1s delay
    "retry_backoff": 2.0       # Double each time
})
```

### Fallback Patterns

```python
# Try primary tool, fallback to alternative
try:
    result = await orchestrator.run_step({
        "tool_name": "primary_extractor",
        "inputs": {"document": doc}
    })
except Exception:
    # Fallback
    result = await orchestrator.run_step({
        "tool_name": "fallback_extractor",
        "inputs": {"document": doc}
    })
```

## Monitoring

### Tool Execution Metrics

```python
from orchestrator.monitoring import MonitoringBackend

monitor = MonitoringBackend(backend="wandb")
orchestrator = Orchestrator(catalog, monitoring=monitor)

# Metrics are automatically logged
result = await orchestrator.run_step({
    "tool_name": "api_call",
    "inputs": {...}
})

# Logged metrics include:
# - tool_name: str
# - success: bool
# - latency_ms: float
# - input_tokens: int (if applicable)
# - output_tokens: int (if applicable)
# - error: str (if failed)
```

### Custom Monitoring

```python
import time
from orchestrator.monitoring import MonitoringObserver

class CustomObserver(MonitoringObserver):
    def on_tool_call_start(self, tool_name, inputs):
        print(f"Starting {tool_name}")
    
    def on_tool_call_complete(self, tool_name, success, latency_ms):
        print(f"Completed {tool_name} in {latency_ms}ms")

monitor = MonitoringBackend(observer=CustomObserver())
```

## Best Practices

### 1. Use Semantic Search for Tool Discovery

```python
# Good: Find relevant tools dynamically
relevant_tools = await find_relevant_tools(
    query="extract structured data from documents",
    catalog=catalog,
    limit=5
)

# Avoid: Hardcoding tool names
# result = await orchestrator.run_step({"tool_name": "random_tool_name"})
```

### 2. Handle Tool Errors Gracefully

```python
# Good: Check for errors and handle
result = await orchestrator.run_step({
    "tool_name": "external_api",
    "inputs": {...}
})

if result.get("error"):
    # Handle error
    logger.warning(f"Tool failed: {result['error']}")
    # Use fallback or retry
else:
    # Process result
```

### 3. Cache Tool Discovery Results

```python
# Good: Use cached discovery
tools = await discover_tools(mcp_client=mcp, use_cache=True)
# (24-hour TTL, ~1ms lookup)

# Avoid: Calling without cache
# tools = await discover_tools(mcp_client=mcp, use_cache=False)
# (~50-100ms, slower)
```

### 4. Monitor Tool Costs

```python
# Log cost information
for tool in tools:
    cost = tool.metadata.get("cost_per_call_usd", 0)
    latency = tool.metadata.get("execution_time_ms", 0)
    print(f"{tool.name}: ${cost:.4f} per call, {latency}ms")
```

### 5. Chain Tools with Workflows

```python
# Good: Use Workflow for complex chains
workflow = WorkflowTemplate(
    name="multi_step_process",
    steps=[
        WorkflowStep(step_id="step1", tool_name="tool_a"),
        WorkflowStep(step_id="step2", tool_name="tool_b", depends_on=["step1"]),
        WorkflowStep(step_id="step3", tool_name="tool_c", depends_on=["step2"])
    ]
)

# Avoid: Manual step sequencing
# result1 = await run_step(...)
# result2 = await run_step(...)
# result3 = await run_step(...)
```

### 6. Document Tool Usage

```python
# Include tool examples in discovery
tool_examples = [
    ToolExample(
        scenario="Extract receipt from image",
        input={"image_url": "https://...", "enhance": True},
        expected_output="Receipt text with line items",
        notes="Use enhance=True for low-quality images"
    )
]
```

## Troubleshooting

### Tool Not Found

```python
# Ensure MCP client is initialized
mcp = MCPClient(env_file=".env")
tools = await discover_tools(mcp_client=mcp)

# Check available tools
print(f"Available tools: {[t.name for t in tools]}")

# Search for similar tools
relevant = await find_relevant_tools(
    query="your tool description",
    catalog=catalog
)
```

### Tool Call Timeout

```python
# Increase timeout for long-running tools
result = await orchestrator.run_step({
    "tool_name": "long_running_tool",
    "inputs": {...},
    "timeout": 120  # 2 minute timeout
})
```

### Streaming Issues

```python
# Check if tool supports streaming
tool = next(t for t in tools if t.name == "your_tool")
supports_streaming = tool.metadata.get("supports_streaming", False)

if supports_streaming:
    result = await orchestrator.run_step({
        "tool_name": "your_tool",
        "inputs": {...},
        "stream": True
    })
else:
    print("This tool does not support streaming")
```

## Comparison: MCP vs A2A

| Aspect | MCP Tools | A2A Agents |
|--------|-----------|-----------|
| **Purpose** | Deterministic operations | Complex reasoning |
| **Speed** | <1s typically | 1-30s |
| **Cost** | Cheap | Varies |
| **Input/Output** | Strict schema | Flexible JSON |
| **Streaming** | async-generator | HTTP/SSE/WebSocket |
| **Error Handling** | Structured exceptions | Error fields in response |
| **When to use** | API calls, calculations | Analysis, validation |
| **Discovery** | Via MCP servers | Via agent registry |
| **Unified Interface** | Yes (via discover_tools) | Yes (via discover_tools) |

### Example: Choosing Between MCP and A2A

```python
# MCP: Fast deterministic task
mcp_result = await orchestrator.run_step({
    "tool_name": "parse_json",  # MCP tool
    "inputs": {"json_str": data}
})

# A2A: Complex analysis
a2a_result = await orchestrator.run_step({
    "type": "agent",
    "agent_id": "analyzer",  # A2A agent
    "inputs": {"data": mcp_result}
})

# Hybrid: Tools + Agents
final = await orchestrator.run_step({
    "tool_name": "format_report",  # MCP tool
    "inputs": {"analysis": a2a_result}
})
```

## Next Steps

- [Features Guide](FEATURES_GUIDE.md) - Complete feature reference
- [A2A Agents Guide](A2A_SETUP_GUIDE.md) - Set up Agent-to-Agent delegation
- [Workflow Usage Guide](WORKFLOW_USAGE_GUIDE.md) - Build complex workflows
- [Quick Reference](QUICK_REFERENCE.md) - Common patterns and commands
