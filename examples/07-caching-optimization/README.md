# Example 07: Caching and Optimization

**Capability Demonstrated:** Multi-layer caching with Redis for cost and performance optimization

## What This Shows

- Redis-based distributed caching
- Multiple cache layers (discovery, search, results, embeddings)
- Cache invalidation strategies
- Performance benchmarks with/without caching
- Cost savings through cache hit optimization

## Real-World Impact

**Without Caching:**
- Every request: Full tool discovery + search + execution
- Cost: $0.50 per request
- Time: 2.5s per request

**With Caching:**
- Discovery cached: 24 hours
- Search results cached: 1 hour
- Execution results cached: 5 minutes
- Cost: $0.05 per request (90% savings)
- Time: 0.3s per request (87% faster)

## Setup

```bash
cp .env.example .env
# Add your API keys
# Optional: Start Redis locally or use cloud Redis
docker run -d -p 6379:6379 redis
python caching_demo.py
```

## Files

- `caching_demo.py` - Main demonstration
- `.env` / `.env.example` - Configuration
- `README.md` - This file