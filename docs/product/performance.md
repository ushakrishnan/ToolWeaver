# Performance & Cost

## Caching strategy
- Dual-layer: Redis + file fallback
- TTL per data type (catalog, search, embeddings, idempotency)
- Circuit breaker to handle Redis outages gracefully

## Idempotency
- Automatic deduplication of identical requests
- Dramatic speedups for retries (instant hits)

## Demonstrations
- Parallel agents speedup (1.7x for 50 items)
- Caching deep dive with TTL and fallback

See:
- [Tutorial: Caching Deep Dive](../tutorials/caching-deep-dive.md)
- [Tutorial: Parallel Agents](../tutorials/parallel-agents.md)
