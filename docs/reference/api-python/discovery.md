# Discovery & Search

Why: Find and browse tools programmatically for planners, APIs, and UIs.
Jump to symbols: [API Exports Index](exports/index.md)

Exports: `get_available_tools`, `search_tools`, `get_tool_info`, `list_tools_by_domain`, `semantic_search_tools`, `browse_tools`

## `get_available_tools()`
What: Return all registered tools.
When: Bootstrap catalogs for planners or adapters.
```python
from orchestrator import get_available_tools
tools = get_available_tools()
print("Total tools:", len(tools))
```

## `search_tools(...)`
What: Filter tools by domain/keywords/provider.
When: User-driven discovery or planner narrowing.
```python
from orchestrator import search_tools

# Search by domain (no query required)
finance_tools = search_tools(query="", domain="finance")
print([t.name for t in finance_tools])

# Search with query + domain filter
tools = search_tools(query="send message", domain="comms")
```

## `get_tool_info(name)`
What: Detailed definition for a tool by name.
When: Render schemas in UIs or validate parameters.
```python
from orchestrator import get_tool_info
print(get_tool_info("receipt_ocr"))
```

## `list_tools_by_domain(domain)`
What: List tools within a given domain.
When: Build domain-focused menus or filters.
```python
from orchestrator import list_tools_by_domain
print(list_tools_by_domain("finance"))
```

## `semantic_search_tools(query)`
What: Semantic matching against tool descriptions.
When: Natural language discovery flows.
```python
from orchestrator import semantic_search_tools
print(semantic_search_tools(query="process receipts"))
```

## `browse_tools(query)`
What: Progressive detail browsing for CLI/UX.
When: Guided exploration flows.
```python
from orchestrator import browse_tools
print(browse_tools(query="github"))
```

Related:
