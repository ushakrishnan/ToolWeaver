# Tutorial: Caching Deep Dive

## Simple Explanation
Cache repeated work to save time and cost. Toggle `USE_REDIS=true` to use real Redis, or `false` for file-based cache. Automatic fallback ensures zero downtime.

## Technical Explanation
Multi-layer caching: catalog, embeddings, and query results with TTLs and automatic fallback. Works with real Redis (production) or file cache (development/CI). Circuit breaker protects against Redis failures. ToolCache APIs manage keys and expiration. Prompt caching at providers reduces token costs.

Explore Redis + file fallback, TTL, circuit breaker, and ToolCache API with configurable backends.

Run:
```bash
# With file cache (no Redis required)
USE_REDIS=false python samples/07-caching-optimization/caching_deep_dive.py
USE_REDIS=false python samples/07-caching-optimization/caching_what_how_when.py

# With real Redis (shows production latencies)
USE_REDIS=true python samples/07-caching-optimization/caching_deep_dive.py
USE_REDIS=true python samples/07-caching-optimization/caching_what_how_when.py
```

Prerequisites:
- Install from PyPI: `pip install toolweaver`
- Optional for Redis mode: `pip install redis`

Highlights:
- Toggle between Redis and file cache via `USE_REDIS` environment variable
- Dual-layer cache with automatic fallback when Redis is unavailable
- TTL expiration demonstration (24h for catalogs, 7d for embeddings, 1h for searches)
- Circuit breaker protecting Redis outages
- ToolCache keys for catalog/search/embeddings
- Same code demonstrates both production and development patterns

Files:
- [samples/07-caching-optimization/caching_demo.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/07-caching-optimization/caching_demo.py) - In-memory basics
- [samples/07-caching-optimization/caching_deep_dive.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/07-caching-optimization/caching_deep_dive.py) - Multi-layer with toggle
- [samples/07-caching-optimization/caching_what_how_when.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/07-caching-optimization/caching_what_how_when.py) - Complete WHAT/HOW/WHEN guide
- [samples/07-caching-optimization/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/07-caching-optimization/README.md) - Full documentation
