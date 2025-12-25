# Concepts Overview

Core ideas that shape ToolWeaver:

## Simple Explanation
ToolWeaver helps you define tools, organize them into a catalog, and lets agents find and run them safely and efficiently. Sandboxed execution isolates tool code, parallel agents scale out work, and caching speeds up common operations. Skills and plugins make sharing and extension easy.

## Technical Explanation
Concepts map to system components: registration and discovery form a searchable catalog (including semantic search), sandbox enforces isolation and timeouts, parallel dispatch manages concurrency with quotas and idempotency caching, and a multi-tier cache (Redis + file) backs catalogs, embeddings, and execution guardrails. Skills package tools for reuse; plugins extend registries and runtimes.

- **Tools**: Functions or external actions registered via `@mcp_tool`, `@tool`, or templates.
- **Discovery**: Catalog and search tools by domain, keywords, or semantics.
- **Sandboxed execution**: Isolated code paths with restricted builtins and timeouts.
- **Parallel agents**: Fan out tasks with semaphores, quotas, and idempotency caching.
- **Caching**: Multi-tier cache (Redis + file fallback) for tool catalogs, search, embeddings, idempotency.
- **Skills and plugins**: Share tools as skills; extend via plugin registry.

Key references:
- Sandbox implementation: [orchestrator/_internal/execution/sandbox.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/orchestrator/_internal/execution/sandbox.py)
- Parallel dispatch: [orchestrator/tools/sub_agent.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/orchestrator/tools/sub_agent.py)
- Caching: [orchestrator/_internal/infra/redis_cache.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/orchestrator/_internal/infra/redis_cache.py)
- Public API surface: [reference/api.md](../reference/api.md)
