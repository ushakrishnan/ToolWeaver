# Discovering Tools

Discovery APIs are available:
- `get_available_tools(plugin=None, type_filter=None, domain=None)`
- `search_tools(query=None, domain=None, type_filter=None)`
- `get_tool_info(name)`
- `list_tools_by_domain(domain)`

## Examples
```python
from orchestrator import (
	get_available_tools,
	search_tools,
	get_tool_info,
	list_tools_by_domain,
)

# List everything
all_tools = get_available_tools()
print([t.name for t in all_tools])

# Search by keyword
echo_tools = search_tools(query="echo")

# Get full info
info = get_tool_info("echo")
print(info.input_schema)

# Filter by domain
general = list_tools_by_domain("general")
```

Notes:
- Discovery normalizes plugin outputs to `ToolDefinition`, including nested `input_schema`/`output_schema`.
- Semantic search will be added later; current search is substring-based.
