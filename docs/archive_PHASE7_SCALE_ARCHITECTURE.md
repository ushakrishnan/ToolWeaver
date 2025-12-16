# Phase 7: Scale Optimization - Architecture Design

**Date:** December 16, 2025  
**Status:** In Progress  
**Goal:** Scale to 1000+ tools with sub-100ms search latency

---

## Executive Summary

Phase 7 scales ToolWeaver from 100-300 tools (Phase 3) to 1000+ tools while maintaining sub-100ms search latency. We'll replace in-memory search with vector databases, file caching with Redis, and add intelligent catalog sharding.

**Key Decisions:**
- **Vector DB**: Qdrant (open-source, fast, Python-native, Docker-deployable)
- **Cache**: Redis (industry standard, proven at scale)
- **Sharding Strategy**: Domain-based with automatic fallback
- **Embeddings**: Pre-computed batch processing with GPU support

---

## Current State Analysis (Phase 1-6)

### What Works Well ✅
- Hybrid BM25 + embeddings (excellent accuracy)
- Smart threshold routing (<20 tools skip search)
- Tool Search Tool (dynamic discovery)
- In-memory search adequate for 100-300 tools

### Limitations at Scale ⚠️
1. **Linear Search Time**: O(n) with tool count
   - 100 tools: ~50ms ✅
   - 500 tools: ~200ms ⚠️
   - 1000 tools: ~500ms ❌
   - 5000 tools: ~2500ms ❌

2. **Memory Footprint**: All embeddings in RAM
   - 384-dim embeddings × 1000 tools × 4 bytes = 1.5MB (manageable)
   - 384-dim embeddings × 10,000 tools × 4 bytes = 15MB (problematic for multiple instances)

3. **Cold Start Penalty**: 11-second model load on first search

4. **No Distributed Caching**: Each instance loads own embeddings

5. **No Search Optimization**: Searches entire catalog every time

---

## Architecture Design

### Component 1: Vector Database (Qdrant)

**Why Qdrant:**
- ✅ Open-source (Apache 2.0)
- ✅ Python-native client
- ✅ Sub-10ms query latency at 1M+ vectors
- ✅ Docker-deployable (easy local dev + production)
- ✅ Filtered search (domain sharding support)
- ✅ HNSW index (fast approximate nearest neighbor)
- ✅ Built-in persistence and replication

**Schema Design:**
```python
{
  "collection": "toolweaver_tools",
  "vectors": {
    "size": 384,  # all-MiniLM-L6-v2 dimension
    "distance": "Cosine"
  },
  "payload": {
    "tool_name": str,        # Unique identifier
    "tool_type": str,        # "mcp_worker", "function", "code_exec"
    "domain": str,           # "github", "slack", "aws", "general", etc.
    "description": str,      # Full description for BM25
    "parameters": dict,      # JSON Schema
    "version": str,          # Tool version
    "last_updated": timestamp
  }
}
```

**Operations:**
- **Upsert**: Add/update tool embeddings (batch mode for catalog initialization)
- **Search**: Cosine similarity with optional domain filter
- **Delete**: Remove deprecated tools
- **Bulk Load**: Import entire catalog at startup

**Performance Targets:**
- <10ms for single query (10 nearest neighbors)
- <50ms for filtered query (domain-specific)
- 10,000 tools indexed in <5 seconds

---

### Component 2: Distributed Caching (Redis)

**Why Redis:**
- ✅ Industry standard for distributed caching
- ✅ Sub-millisecond latency
- ✅ Automatic TTL management
- ✅ Cluster mode for high availability
- ✅ Python client (redis-py) is mature

**Cache Strategy:**

```python
# Cache Layers:
1. Tool Catalog Cache (24h TTL)
   Key: "catalog:v2:{catalog_hash}"
   Value: JSON serialized ToolCatalog
   Purpose: Avoid repeated tool discovery

2. Search Results Cache (1h TTL)
   Key: "search:{query_hash}:{catalog_version}:{top_k}"
   Value: Pickled List[Tuple[ToolDefinition, float]]
   Purpose: Repeated queries return instantly

3. Embedding Cache (7d TTL)
   Key: "embedding:{text_hash}:{model_name}"
   Value: Numpy array (binary)
   Purpose: Avoid re-computing embeddings for common queries

4. Tool Metadata Cache (24h TTL)
   Key: "tool:{tool_name}:v{version}"
   Value: JSON ToolDefinition
   Purpose: Fast tool lookup without DB query
```

**Redis Configuration:**
- Connection pooling (10-50 connections)
- Automatic reconnection with exponential backoff
- Circuit breaker pattern for Redis failures (fallback to local cache)
- Optional: Redis Cluster for production (3+ nodes)

---

### Component 3: Tool Catalog Sharding

**Domain-Based Sharding:**

Tools grouped by domain for focused searches:
- `github.*` - GitHub operations (PRs, issues, repos)
- `slack.*` - Slack messaging and channels
- `aws.*` - AWS operations (S3, EC2, Lambda)
- `azure.*` - Azure operations
- `database.*` - DB operations (queries, migrations)
- `general.*` - Utilities (file ops, parsing, formatting)

**Implementation:**
```python
class ShardedCatalog:
    def __init__(self):
        self.shards: Dict[str, ToolCatalog] = {}
        self.global_catalog: ToolCatalog = ToolCatalog()
    
    def add_tool(self, tool: ToolDefinition):
        domain = tool.domain or "general"
        if domain not in self.shards:
            self.shards[domain] = ToolCatalog()
        self.shards[domain].add_tool(tool)
        self.global_catalog.add_tool(tool)
    
    def search(self, query: str, domain_hint: Optional[str] = None):
        # Try domain-specific search first (10x smaller search space)
        if domain_hint and domain_hint in self.shards:
            results = search_engine.search(query, self.shards[domain_hint])
            if len(results) >= 3:  # Found enough good matches
                return results
        
        # Fallback to global search
        return search_engine.search(query, self.global_catalog)
```

**Domain Detection:**
- Keyword-based heuristics ("create PR" → github domain)
- LLM-based classification (optional, for ambiguous queries)
- User-provided hints (API parameter)

**Benefits:**
- 10x smaller search space (100 tools instead of 1000)
- Faster BM25 indexing
- Better relevance (domain-specific context)

---

### Component 4: Embedding Optimization

**GPU Acceleration:**
```python
# Detect GPU availability
device = "cuda" if torch.cuda.is_available() else "cpu"
embedding_model = SentenceTransformer(model_name, device=device)

# Batch processing (10x faster than sequential)
texts = [tool.description for tool in tools]
embeddings = embedding_model.encode(
    texts,
    batch_size=32,      # Process 32 at a time
    show_progress_bar=True,
    convert_to_numpy=True
)
```

**Pre-Computation Strategy:**
1. **Static Catalog**: Pre-compute all embeddings at app startup
2. **Store in Qdrant**: Avoids re-computation across restarts
3. **Incremental Updates**: Only embed new/changed tools
4. **Background Processing**: Queue-based embedding for dynamic tools

**Warm-Up Process:**
```python
async def warm_up_search_engine():
    """Run at application startup"""
    # 1. Load embedding model to GPU
    search_engine._init_embedding_model()
    
    # 2. Pre-compute catalog embeddings (if not in Qdrant)
    if not qdrant_client.collection_exists("toolweaver_tools"):
        await bulk_index_catalog(catalog)
    
    # 3. Prime Redis cache with common queries
    common_queries = ["github", "slack", "database", "file", "send"]
    for query in common_queries:
        search_engine.search(query, catalog)
    
    logger.info("Search engine warm-up complete")
```

---

## Performance Targets & Metrics

### Latency Goals
| Catalog Size | Phase 3 (Current) | Phase 7 (Target) | Improvement |
|--------------|-------------------|------------------|-------------|
| 100 tools    | 50ms              | 30ms             | 1.7x faster |
| 500 tools    | 200ms             | 60ms             | 3.3x faster |
| 1000 tools   | 500ms             | 80ms             | 6.3x faster |
| 5000 tools   | 2500ms            | 95ms             | 26x faster  |

### Memory Footprint
- **Phase 3**: 1.5MB per 1000 tools (all in RAM)
- **Phase 7**: 200KB per instance (only query embeddings), rest in Qdrant

### Cache Hit Rates
- Tool catalog cache: 95%+ (rarely changes)
- Search results cache: 60-70% (common queries)
- Embedding cache: 80%+ (limited query vocabulary)

### Cold Start
- **Phase 3**: 11 seconds (load embedding model + compute embeddings)
- **Phase 7**: 2 seconds (load model only, embeddings in Qdrant)

---

## Migration Strategy

### Phase 7a: Add Qdrant (Optional, Backward Compatible)
- Keep existing in-memory search
- Add QdrantToolSearchEngine as alternative
- Config flag: `USE_VECTOR_DB=true|false`
- Gradual rollout

### Phase 7b: Add Redis (Optional, Backward Compatible)
- Keep file-based cache as fallback
- Add RedisCache layer
- Config flag: `USE_REDIS=true|false`
- Graceful degradation if Redis unavailable

### Phase 7c: Enable Sharding (Always On)
- Add `domain` field to ToolDefinition (optional, defaults to "general")
- ShardedCatalog wraps existing ToolCatalog
- No breaking changes

### Phase 7d: GPU Embeddings (Auto-Detect)
- Detect CUDA availability at runtime
- Fall back to CPU if GPU unavailable
- No config needed

---

## Deployment Configurations

### Development (Local)
```yaml
# docker-compose.yml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_data:/qdrant/storage
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

```bash
# Start dependencies
docker-compose up -d

# Run ToolWeaver with scale optimization
python run_demo.py --use-vector-db --use-redis
```

### Production (Kubernetes)
- Qdrant: StatefulSet with persistent volumes
- Redis: Cluster mode (3 masters, 3 replicas)
- ToolWeaver: Deployment with horizontal scaling

---

## Risk Mitigation

### Risk 1: Qdrant Unavailable
**Mitigation**: Automatic fallback to in-memory search
```python
try:
    results = qdrant_search_engine.search(query, catalog)
except QdrantException:
    logger.warning("Qdrant unavailable, falling back to in-memory search")
    results = in_memory_search_engine.search(query, catalog)
```

### Risk 2: Redis Failure
**Mitigation**: Use file-based cache, continue operation
```python
try:
    cached = redis_client.get(cache_key)
except RedisError:
    cached = file_cache.get(cache_key)  # Fallback
```

### Risk 3: Embedding Model OOM (GPU)
**Mitigation**: Batch size adjustment, fall back to CPU
```python
try:
    embeddings = model.encode(texts, batch_size=32)
except torch.cuda.OutOfMemoryError:
    embeddings = model.encode(texts, batch_size=8)  # Smaller batches
```

### Risk 4: Network Latency (Qdrant/Redis)
**Mitigation**: Connection pooling, local cache layer
- Keep 100 most-used tools in local memory
- Query Qdrant only for rare tools

---

## Implementation Order

1. ✅ **Architecture Design** (this document)
2. ⏳ **Add Qdrant Integration** (orchestrator/vector_search.py)
3. ⏳ **Add Redis Caching** (orchestrator/redis_cache.py)
4. ⏳ **Implement Sharding** (orchestrator/sharded_catalog.py)
5. ⏳ **GPU Optimization** (update orchestrator/tool_search.py)
6. ⏳ **Performance Benchmarks** (tests/benchmark_scale.py)
7. ⏳ **Documentation** (README, configuration guide)

---

## Success Criteria

✅ **Phase 7 Complete When:**
- 1000-tool catalog search < 100ms (p95)
- 5000-tool catalog search < 150ms (p95)
- Cache hit rate > 80% for common queries
- Zero breaking changes to existing API
- Docker deployment works out-of-box
- All tests passing (Phase 1-6 + new benchmarks)

**Estimated Effort:** 4-5 days  
**Dependencies:** Docker, Qdrant, Redis

---

## Next Steps

Starting with **Component 1: Qdrant Integration** to unblock the critical path.
