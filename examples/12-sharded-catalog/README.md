# Example 12: Sharded Catalog

**Complexity:** ⭐⭐⭐ Advanced | **Time:** 15 minutes  
**Feature Demonstrated:** Sharded catalogs for scaling to 1000+ tools

## Overview

### What This Example Does
Partitions tools across shards and searches only relevant shards, enabling sub-linear scaling.

### Key Features Showcased
- **Sharding Strategy**: Domain-based, provider-based, or frequency-based
- **Smart Routing**: Search 2-3 shards instead of all 20
- **Sub-Linear Scaling**: Constant search time as catalog grows
- **Performance**: 10x faster search, 95% token reduction

### Why This Matters

- Partition tools across multiple shards
- Route queries to relevant shards only
- Reduce search space from 1000 to 50-100 tools
- Maintain sub-linear scaling

## The Scaling Problem

**Naive approach:**
- 1000 tools × 200 tokens/tool = 200K tokens
- Search time: 500ms+
- Context: At token limit
- Cost: $0.02 per search

**Sharded approach:**
- 1000 tools across 20 shards (50 tools each)
- Search 2-3 relevant shards only (100-150 tools)
- Search time: 50ms
- Cost: $0.002 per search

## Sharding Strategies

### 1. Domain-Based
```
Shard 1: Image processing tools
Shard 2: Database operations
Shard 3: Communication tools
Shard 4: File operations
...
```

### 2. Provider-Based
```
Shard 1: Azure tools
Shard 2: AWS tools
Shard 3: Google Cloud tools
Shard 4: Custom tools
...
```

### 3. Frequency-Based
```
Shard 1: Hot (90% of requests)
Shard 2: Warm (9% of requests)
Shard 3-20: Cold (1% of requests)
```

## Setup

```bash
cp .env.example .env
python sharded_catalog_demo.py
```

## Files

- `sharded_catalog_demo.py` - Main demonstration
- `.env` / `.env.example` - Configuration
- `README.md` - This file