# Quickstart

Get ToolWeaver running in minutes.

## Install
```bash
pip install toolweaver
```

## Define a tool
```python
from orchestrator import mcp_tool

@mcp_tool(domain="demo", description="Echo a message")
async def echo(message: str) -> dict:
    """
    Echo back the provided message.
    
    Args:
        message: The message to echo back
        
    Returns:
        dict: A dictionary with the echoed message
    """
    return {"echo": message}
```

## List tools
```python
from orchestrator import mcp_tool, get_available_tools

# Define a tool first
@mcp_tool(domain="demo", description="Echo a message")
async def echo(message: str) -> dict:
    """Echo back the provided message."""
    return {"echo": message}

# List all registered tools
print(get_available_tools())
```

## Search by domain
```python
from orchestrator import mcp_tool, get_available_tools, search_tools

# Define a tool so the decorator registers it
@mcp_tool(domain="demo", description="Echo a message")
async def echo(message: str) -> dict:
    """Echo back the provided message."""
    return {"echo": message}

# Verify all tools are registered
print(f"All tools: {[t.name for t in get_available_tools()]}")

# Search by domain
demo_tools = search_tools(query="", domain="demo")
print(f"Demo domain: {[t.name for t in demo_tools]}")
```

## Run a parallel dispatch (sample)
Use the ready-made sample to see parallel agents with limits:
```bash
python samples/25-parallel-agents/parallel_deep_dive.py
```
See [Parallel agents tutorial](../tutorials/parallel-agents.md) for expected output.
