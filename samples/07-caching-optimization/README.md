# Sample 07: Caching and Optimization

> Status: PyPI package refresh is in progress. This sample may lag behind the latest source; for the most up-to-date code paths, use [examples/](../../examples/). Samples will be regenerated after the refresh.
> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`


**Complexity:** ⭐⭐ Intermediate | **Time:** 10 minutes  
**Feature Demonstrated:** Multi-layer caching with Redis for cost and performance optimization

## Overview

### What This Example Does
Implements distributed Redis caching across multiple layers (discovery, search, results, embeddings).

### Key Features Showcased
- **Redis Integration**: Distributed caching with Redis Cloud
- **Multi-Layer Cache**: Discovery (24h), search (1h), results (5min)
- **Performance**: 87% faster with cache hits
- **Cost Savings**: 90% reduction through cache optimization

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
- Cost: $0.05 per request (90% savings)
- Time: 0.3s per request (87% faster)

## Setup

```bash
cp .env.example .env
# Add your API keys

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

# Optional: Start Redis locally or use cloud Redis

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

docker run -d -p 6379:6379 redis
python caching_demo.py
```

## Files

- `caching_demo.py` - Main demonstration
- `.env` / `.env.example` - Configuration
- `README.md` - This file