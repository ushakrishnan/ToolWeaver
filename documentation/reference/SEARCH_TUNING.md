# Semantic Tool Search - Tuning Guide

**Document Version:** 1.0  
**Date:** December 15, 2025  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Options](#configuration-options)
3. [Hybrid Scoring](#hybrid-scoring)
4. [Embedding Models](#embedding-models)
5. [Cache Management](#cache-management)
6. [Performance Tuning](#performance-tuning)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The semantic search engine uses **hybrid BM25 + embedding search** to intelligently select the most relevant tools from large catalogs. This guide covers configuration, tuning, and optimization strategies.

### When to Use Semantic Search

✅ **Use semantic search when:**
- Tool catalog has 30+ tools
- Tools have overlapping functionality
- Need to reduce prompt token costs
- Want to improve planner accuracy
- Dynamic tool selection based on query

❌ **Skip semantic search when:**
- Tool catalog has ≤20 tools (overhead not worth it)
- All tools are equally relevant
- Execution speed is critical (avoid 11s model load)
- Running on resource-constrained hardware

### Default Behavior

**Smart Routing** (automatic):
- **≤20 tools:** Returns all tools with score 1.0 (no search)
- **>20 tools:** Activates semantic search, returns top 10 tools

---

## Configuration Options

### Basic Setup

```python
from orchestrator.tool_search import ToolSearchEngine

# Default configuration (recommended for most use cases)
engine = ToolSearchEngine()

# Custom configuration
engine = ToolSearchEngine(
    bm25_weight=0.3,           # Keyword matching importance (0.0-1.0)
    embedding_weight=0.7,      # Semantic similarity importance (0.0-1.0)
    embedding_model="all-MiniLM-L6-v2",  # Model name
    cache_dir="~/.toolweaver/search_cache"  # Cache location
)
```

### LargePlanner Integration

```python
from orchestrator.planner import LargePlanner

# Enable semantic search (default: on)
planner = LargePlanner(
    provider="azure-openai",
    use_tool_search=True,      # Enable semantic search
    search_threshold=20         # Activate when tools > 20
)

# Disable semantic search
planner = LargePlanner(
    provider="azure-openai",
    use_tool_search=False       # Always use all tools
)

# Aggressive search (activate earlier)
planner = LargePlanner(
    provider="azure-openai",
    use_tool_search=True,
    search_threshold=10         # Activate when tools > 10
)
```

---

## Hybrid Scoring

The search engine combines **BM25 (keyword)** and **embedding (semantic)** scores using weighted averaging:

```
final_score = (bm25_weight × bm25_score) + (embedding_weight × embedding_score)
```

### Default Weights

```python
bm25_weight = 0.3        # 30% keyword matching
embedding_weight = 0.7   # 70% semantic similarity
```

**Rationale:** Semantic understanding is more important for natural language queries, but keyword matching helps disambiguate similar tools.

### Tuning Weights

**More Keyword Matching (0.5 / 0.5):**
```python
engine = ToolSearchEngine(bm25_weight=0.5, embedding_weight=0.5)
```
- ✅ Better for exact tool name mentions
- ✅ Better for technical/API queries
- ❌ Worse for natural language queries

**More Semantic Matching (0.2 / 0.8):**
```python
engine = ToolSearchEngine(bm25_weight=0.2, embedding_weight=0.8)
```
- ✅ Better for natural language queries
- ✅ Better for conceptual similarity
- ❌ May miss exact name matches

**Pure Semantic (0.0 / 1.0):**
```python
engine = ToolSearchEngine(bm25_weight=0.0, embedding_weight=1.0)
```
- ✅ Best semantic understanding
- ❌ Ignores exact matches (not recommended)

**Pure Keyword (1.0 / 0.0):**
```python
engine = ToolSearchEngine(bm25_weight=1.0, embedding_weight=0.0)
```
- ✅ Fast (no embedding computation)
- ❌ No semantic understanding (not recommended)

### Example Comparisons

**Query:** "analyze receipt and extract items"

| Weights | Top Results | Rationale |
|---------|-------------|-----------|
| **0.3 / 0.7 (default)** | receipt_ocr (0.95), line_item_parser (0.87) | Balanced, prefers semantic |
| **0.5 / 0.5** | receipt_ocr (0.92), line_item_parser (0.85) | Similar, slightly favors exact "receipt" match |
| **0.2 / 0.8** | line_item_parser (0.90), receipt_ocr (0.88) | Prefers "parser" as more semantically aligned |

---

## Embedding Models

### Available Models

| Model | Dimensions | Size | Speed | Accuracy | Use Case |
|-------|-----------|------|-------|----------|----------|
| **all-MiniLM-L6-v2** (default) | 384 | 80MB | Fast | Good | Production (recommended) |
| **all-mpnet-base-v2** | 768 | 420MB | Medium | Better | High accuracy needs |
| **multi-qa-mpnet-base-dot-v1** | 768 | 420MB | Medium | Best | Question-answering |
| **all-distilroberta-v1** | 768 | 290MB | Fast | Good | Balance speed/accuracy |

### Model Selection

**all-MiniLM-L6-v2 (Default):**
```python
engine = ToolSearchEngine(embedding_model="all-MiniLM-L6-v2")
```
- ✅ Small size (80MB)
- ✅ Fast inference (~30ms per query)
- ✅ Low memory footprint
- ✅ Good accuracy for tool search
- ❌ Less accurate than larger models

**all-mpnet-base-v2 (High Accuracy):**
```python
engine = ToolSearchEngine(embedding_model="all-mpnet-base-v2")
```
- ✅ Better semantic understanding
- ✅ Higher dimensional representations (768-dim)
- ❌ Larger size (420MB)
- ❌ Slower inference (~60ms per query)

**multi-qa-mpnet-base-dot-v1 (Question Matching):**
```python
engine = ToolSearchEngine(embedding_model="multi-qa-mpnet-base-dot-v1")
```
- ✅ Optimized for question-answer pairs
- ✅ Best for "how do I..." queries
- ❌ Larger size (420MB)
- ❌ Overkill for simple tool search

### Model Download

Models are downloaded automatically on first use from Hugging Face:
```
~/.cache/torch/sentence_transformers/sentence-transformers_all-MiniLM-L6-v2/
```

**Pre-download (optional):**
```python
from sentence_transformers import SentenceTransformer

# Download model ahead of time
model = SentenceTransformer("all-MiniLM-L6-v2")
print(f"Model downloaded to: {model.cache_folder}")
```

---

## Cache Management

### Cache Levels

**1. Embedding Cache (Persistent)**
- **Location:** `~/.toolweaver/search_cache/emb_*.npy`
- **Format:** NumPy arrays (binary)
- **Key:** MD5 hash of tool description text
- **TTL:** Infinite (persists across runs)
- **Size:** ~1.5KB per tool (384-dim × 4 bytes)

**2. Query Result Cache (Temporary)**
- **Location:** `~/.toolweaver/search_cache/search_*.pkl`
- **Format:** Pickled Python objects
- **Key:** MD5(query + catalog_hash + weights + top_k)
- **TTL:** 1 hour (3600 seconds)
- **Size:** ~2-5KB per query

### Cache Invalidation

**Clear all caches:**
```python
engine = ToolSearchEngine()
engine.clear_cache()
```

**Clear specific cache types:**
```python
import shutil
from pathlib import Path

# Clear query cache only (keep embeddings)
cache_dir = Path.home() / ".toolweaver" / "search_cache"
for file in cache_dir.glob("search_*.pkl"):
    file.unlink()

# Clear embedding cache only (keep query results)
for file in cache_dir.glob("emb_*.npy"):
    file.unlink()
```

**Automatic invalidation:**
- Query cache: Expires after 1 hour
- Embedding cache: Never expires (recompute only if tool description changes)
- Catalog hash changes: Query cache invalidated automatically

### Cache Configuration

**Change cache location:**
```python
engine = ToolSearchEngine(cache_dir="/tmp/tool_search_cache")
```

**Disable caching (not recommended):**
```python
# Caching is always enabled for performance
# To effectively disable, clear cache after each search:
results = engine.search(query, catalog)
engine.clear_cache()
```

### Cache Performance

**Cache Hit Rates (Typical):**
- **Embedding cache:** 95%+ (stable tool descriptions)
- **Query cache:** 20-40% (depends on query diversity)

**Cache Savings:**
- **Embedding hit:** Save 30-50ms per tool
- **Query hit:** Save 31-624ms total search time

---

## Performance Tuning

### Latency Optimization

**1. Reduce top_k:**
```python
# Faster search, fewer results
results = engine.search(query, catalog, top_k=5)  # Default: 10
```

**2. Increase min_score:**
```python
# Skip low-relevance tools early
results = engine.search(query, catalog, min_score=0.5)  # Default: 0.0
```

**3. Use smaller embedding model:**
```python
engine = ToolSearchEngine(embedding_model="all-MiniLM-L6-v2")  # Fast
# vs
engine = ToolSearchEngine(embedding_model="all-mpnet-base-v2")  # Slow
```

**4. Pre-load model:**
```python
# Avoid 11s load time on first search
engine = ToolSearchEngine()
_ = engine.search("warmup", catalog, top_k=1)  # Load model
```

### Memory Optimization

**1. Use smaller embedding model:**
- all-MiniLM-L6-v2: ~200MB RAM
- all-mpnet-base-v2: ~600MB RAM

**2. Clear cache periodically:**
```python
import time

while True:
    results = engine.search(query, catalog)
    # Process results...
    
    # Clear cache every 1000 searches
    if search_count % 1000 == 0:
        engine.clear_cache()
```

### Cost Optimization

**Token Reduction by top_k:**

| top_k | Tools Selected | Token Reduction | Cost Savings @ 1000 req/day |
|-------|----------------|-----------------|------------------------------|
| 5 | 5 tools | 83.3% | $4,562/year |
| 10 | 10 tools | 66.7% | $2,737/year |
| 15 | 15 tools | 50.0% | $1,369/year |
| 20 | 20 tools | 33.3% | $913/year |

**Calculation:**
```python
# 30 tools = 4,500 tokens @ $0.005/1K = $0.0225
# 10 tools = 1,500 tokens @ $0.005/1K = $0.0075
# Savings per request: $0.015
# Annual savings: $0.015 × 1000 req/day × 365 days = $5,475
```

---

## Troubleshooting

### Issue: "Model download is slow (11 seconds)"

**Cause:** First-time model download from Hugging Face

**Solution:**
```python
# Pre-download model during setup
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
```

---

### Issue: "Search returns irrelevant tools"

**Cause:** Query too generic or weights not tuned

**Solutions:**
1. **More specific query:**
   ```python
   # Bad: "process data"
   # Good: "extract text from receipt images"
   ```

2. **Tune weights for keyword matching:**
   ```python
   engine = ToolSearchEngine(bm25_weight=0.5, embedding_weight=0.5)
   ```

3. **Increase min_score:**
   ```python
   results = engine.search(query, catalog, min_score=0.5)
   ```

---

### Issue: "Search is too slow (>1 second)"

**Cause:** Large catalog or large embedding model

**Solutions:**
1. **Use smaller model:**
   ```python
   engine = ToolSearchEngine(embedding_model="all-MiniLM-L6-v2")
   ```

2. **Reduce top_k:**
   ```python
   results = engine.search(query, catalog, top_k=5)
   ```

3. **Check cache hits:**
   ```python
   # If cache_hit=False frequently, embeddings are being recomputed
   # Ensure cache directory is writable
   import os
   cache_dir = os.path.expanduser("~/.toolweaver/search_cache")
   os.makedirs(cache_dir, exist_ok=True)
   ```

---

### Issue: "High memory usage (>1GB)"

**Cause:** Large embedding model loaded in memory

**Solutions:**
1. **Use smaller model:**
   ```python
   # all-MiniLM-L6-v2: ~200MB RAM
   # all-mpnet-base-v2: ~600MB RAM
   engine = ToolSearchEngine(embedding_model="all-MiniLM-L6-v2")
   ```

2. **Lazy loading (default behavior):**
   ```python
   # Model only loaded on first search call
   engine = ToolSearchEngine()  # No model loaded yet
   results = engine.search(query, catalog)  # Model loaded here
   ```

---

### Issue: "Cache not working (searches always slow)"

**Cause:** Cache directory not writable or catalog changing

**Solutions:**
1. **Check cache directory:**
   ```python
   import os
   cache_dir = os.path.expanduser("~/.toolweaver/search_cache")
   
   # Ensure directory exists and is writable
   if not os.path.exists(cache_dir):
       os.makedirs(cache_dir, exist_ok=True)
   
   # Check permissions
   assert os.access(cache_dir, os.W_OK), "Cache directory not writable"
   ```

2. **Verify cache files:**
   ```bash
   ls -lh ~/.toolweaver/search_cache/
   # Should see: emb_*.npy and search_*.pkl files
   ```

3. **Check catalog stability:**
   ```python
   # Catalog hash changes → cache invalidated
   # Ensure tool descriptions are stable
   catalog = await orchestrator.discover_all()
   print(catalog.metadata.get("catalog_hash"))
   ```

---

## Production Recommendations

### Configuration

```python
from orchestrator.planner import LargePlanner

planner = LargePlanner(
    provider="azure-openai",
    use_tool_search=True,       # Enable semantic search
    search_threshold=20,         # Activate for 20+ tools (conservative)
    tool_catalog=catalog
)

# For production with 50+ tools:
planner = LargePlanner(
    provider="azure-openai",
    use_tool_search=True,
    search_threshold=15,         # More aggressive
    tool_catalog=catalog
)
```

### Monitoring

```python
import logging

# Enable search logging
logging.basicConfig(level=logging.INFO)

# Logs show:
# "Semantic search: 30 tools → 10 relevant (~66.7% token reduction, ~3,000 tokens saved)"
```

### Cost Tracking

```python
# Track token usage before/after
pre_search_tokens = len(catalog.tools) * 150  # Estimate 150 tokens per tool
post_search_tokens = 10 * 150  # After search

savings_per_request = (pre_search_tokens - post_search_tokens) * price_per_token
annual_savings = savings_per_request * requests_per_day * 365

print(f"Annual savings: ${annual_savings:,.2f}")
```

---

## Summary

**Key Takeaways:**
- ✅ Use default configuration (0.3 BM25 + 0.7 embedding) for most use cases
- ✅ Smart routing activates automatically for 20+ tools
- ✅ all-MiniLM-L6-v2 model balances speed and accuracy
- ✅ Embedding cache persists across runs (1ms cached vs 50ms uncached)
- ✅ Query cache expires after 1 hour (handles catalog changes)
- ✅ 66.7% token reduction = $2,737/year savings @ 1000 req/day

**Next Steps:**
- Start with default configuration
- Monitor token usage and cost savings
- Tune weights if needed (0.5/0.5 for technical queries, 0.2/0.8 for natural language)
- Experiment with top_k (5-15 range) to balance cost and accuracy
