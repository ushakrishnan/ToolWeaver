# Example 07: Caching and Optimization

**Complexity:** ⭐⭐ Intermediate | **Time:** 10 minutes  
**Feature Demonstrated:** Multi-layer caching with Redis for cost and performance optimization

## Overview

### What This Example Does
Implements distributed Redis caching across multiple layers (discovery, search, results, embeddings).

### Key Features Showcased
- **Redis Integration**: Distributed caching with Redis Cloud
- **Multi-Layer Cache**: Discovery (24h), search (1h), results (5min)
- **Performance**: Up to 87% faster with cache hits (varies 30-90% by hit rate)
- **Cost Savings**: Up to 90% reduction through cache optimization (assumes 85% hit rate)

### Why This Matters

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
- Cost: $0.05 per request (90% savings with 85% cache hit rate)
- Time: 0.3s per request (87% faster with cache hits)

> **Note:** Performance numbers assume 85% cache hit rate on repeated patterns. Real-world hit rates vary 30-90% depending on query diversity and workload repetition.

## Setup

```bash
cp .env.example .env
# Add your API keys
# Optional: Start Redis locally or use cloud Redis
docker run -d -p 6379:6379 redis
python caching_demo.py
```

## Files

- `caching_demo.py` - Basic caching demonstration
- `caching_deep_dive.py` - Detailed architecture walkthrough (multi-layer cache, circuit breaker, TTL strategies)
- `.env` / `.env.example` - Configuration
- `README.md` - This file

## Run the Samples

```bash
# Basic demo (simple in-memory cache)
python caching_demo.py

# Deep dive (RedisCache + ToolCache architecture)
python caching_deep_dive.py
```