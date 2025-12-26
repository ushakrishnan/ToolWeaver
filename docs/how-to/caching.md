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
from orchestrator.tools.sub_agent_limits import DispatchResourceLimits

limits = DispatchResourceLimits(max_concurrent=5, max_total_cost_usd=10.0)

result = await dispatch_agents(
    template="do {{task}}",
    arguments=[{"task": "item_1"}, {"task": "item_2"}],
    agent_name="worker",
    model="haiku",
    limits=limits,
    aggregate_fn=lambda results: [r.output for r in results],
)
# Second call with same arguments reuses cached result
```

See deep dive: [samples/07-caching-optimization/caching_deep_dive.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/07-caching-optimization/caching_deep_dive.py)
