# Registry Discovery

How ToolWeaver builds and queries the tool catalog.

Sources
- MCP servers (remote/local)
- Python decorators/templates
- YAML loaders

Indexing
- Normalizes name/domain/description/parameters.
- Stores examples to improve planner grounding.

Discovery paths
- `get_available_tools` for full listings
- `search_tools` for filtered sets (domain/keywords)
- `semantic_search_tools` for NL queries (BM25 + embeddings)

Best practices
- Keep descriptions concise and specific.
- Provide examples for better planner parameter filling.
- Use domains to scope planner search and reduce tokens.
