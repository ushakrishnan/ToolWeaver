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
    return {"echo": message}
```

## List tools
```python
from orchestrator import get_available_tools
print(get_available_tools())
```

## Search by domain
```python
from orchestrator import search_tools
finance_tools = search_tools(query="", domain="finance")
print([t.name for t in finance_tools])
```

## Run a parallel dispatch (sample)
Use the ready-made sample to see parallel agents with limits:
```bash
python samples/25-parallel-agents/parallel_deep_dive.py
```
See [Parallel agents tutorial](../tutorials/parallel-agents.md) for expected output.
