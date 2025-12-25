# How to Use Caching

ToolWeaver caches tool catalogs, searches, embeddings, and idempotent agent calls.

## Enable Redis (optional)
- Set `REDIS_URL` (TLS supported). If absent, file cache is used automatically.

## Cache a tool catalog
```python
from orchestrator import search_tools

# First call populates cache
print(search_tools(query="", domain="finance"))

# Subsequent calls are fast and cheap (from cache)
print(search_tools(query="", domain="finance"))
```

## Idempotency for agent runs
```python
from orchestrator.tools.sub_agent import dispatch_agents

result = await dispatch_agents(
    agent_configs=[{"name": "a", "template": "do {{x}}", "arguments": {"x": "task"}}],
    aggregation="collect_all",
    idempotency_ttl_seconds=3600,
)
# Second call reuses cached result
```

See deep dive: [samples/07-caching-optimization/caching_deep_dive.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/07-caching-optimization/caching_deep_dive.py)
