# Tutorial: Caching Deep Dive

## Simple Explanation
Cache repeated work to save time and cost. When Redis is down, fallback kicks in automatically.

## Technical Explanation
Multi-layer caching: catalog, embeddings, and query results with TTLs and a circuit breaker for Redis. ToolCache APIs manage keys and expiration. Prompt caching at providers reduces token costs.

Explore Redis + file fallback, TTL, circuit breaker, and ToolCache API.

Run:
```bash
python samples/07-caching-optimization/caching_deep_dive.py
python samples/07-caching-optimization/caching_what_how_when.py
```

Prerequisites:
- Install from PyPI: `pip install toolweaver`

Highlights:
- Dual-layer cache with fallback when Redis is unavailable
- TTL expiration demonstration
- Circuit breaker protecting Redis outages
- ToolCache keys for catalog/search/embeddings

Files:
- [samples/07-caching-optimization/caching_deep_dive.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/07-caching-optimization/caching_deep_dive.py)
- [samples/07-caching-optimization/caching_what_how_when.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/07-caching-optimization/caching_what_how_when.py)
- [samples/07-caching-optimization/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/07-caching-optimization/README.md)
