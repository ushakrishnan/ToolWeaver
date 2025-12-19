# Semantic Search for Tool Discovery (Phase 1.7)

ToolWeaver now supports **semantic search** for finding relevant tools using vector embeddings. This enables discovering tools by meaning and intent, not just keywords.

## Quick Start

### Enable Semantic Search

```python
from orchestrator import semantic_search_tools

# Search semantically (using vector embeddings)
results = semantic_search_tools(
    "create github pull request",
    top_k=3
)

for tool, score in results:
    print(f"{tool.name}: {score:.2f}")
    # Output:
    # github_create_pr: 0.95
    # github_list_issues: 0.72
    # github_add_comment: 0.68
```

### Or Use via `search_tools()`

```python
from orchestrator import search_tools

# Same semantic search via unified API
tools = search_tools(
    "create pull request",
    use_semantic=True,
    top_k=3
)
```

### CLI Support

```bash
# Substring search (default)
toolweaver search "github pull request"

# Semantic search
toolweaver search "create code review" --semantic

# With top-k limit
toolweaver search "notify team" --semantic --top-k 5
```

## How It Works

Semantic search converts your query and all tools into dense vectors using a sentence embedding model (`all-MiniLM-L6-v2`), then computes cosine similarity to find the most relevant tools.

**Benefits:**
- ✅ Find tools by meaning, not keywords
- ✅ Works for conceptually similar queries ("notify team" → "send message")
- ✅ Better results with large tool catalogs (100+ tools)
- ✅ Sub-100ms latency with Qdrant vector database

**Trade-offs:**
- Requires optional dependencies: `qdrant-client`, `sentence-transformers`
- Falls back to substring search if Qdrant unavailable
- First query may be slower (embedding generation)

## Setup

### Option 1: Docker (Recommended for Development)

```bash
# Start Qdrant in Docker
docker run -p 6333:6333 qdrant/qdrant

# ToolWeaver will auto-detect and use it
python your_script.py
```

### Option 2: Qdrant Cloud (Recommended for Production)

1. Sign up at https://cloud.qdrant.io (free tier available)
2. Create a cluster
3. Set environment variable:

```bash
export QDRANT_URL=https://your-cluster.qdrant.io:6333
```

### Option 3: Disable Vector Search

If you don't want semantic search, just don't set `QDRANT_URL`. The system will fall back to fast substring search.

## API Reference

### `semantic_search_tools(query, *, top_k=5, domain=None, min_score=0.3, fallback_to_substring=True)`

Search for tools using vector embeddings.

**Parameters:**
- `query`: Natural language query (e.g., "create github PR")
- `top_k`: Number of results to return (default: 5)
- `domain`: Optional domain filter (e.g., "github", "slack")
- `min_score`: Minimum similarity score 0-1 (default: 0.3)
- `fallback_to_substring`: Fall back to substring search if Qdrant unavailable (default: True)

**Returns:**
- List of `(ToolDefinition, score)` tuples sorted by relevance

**Example:**

```python
from orchestrator import semantic_search_tools

# Find all communication tools (conceptually)
results = semantic_search_tools(
    "send notification",
    top_k=5,
    domain="slack",
    min_score=0.2
)

for tool, score in results:
    print(f"- {tool.name:30} (relevance: {score:.2%})")
```

### `search_tools(..., use_semantic=False, ...)`

Unified search API that supports both substring and semantic modes.

**Parameters:**
- `query`: Search query
- `domain`: Optional domain filter
- `type_filter`: Optional type filter
- `use_semantic`: Use semantic search (default: False)
- `top_k`: Number of results (default: 10)
- `min_score`: Minimum score for semantic search (default: 0.3)

**Example:**

```python
from orchestrator import search_tools

# Semantic search
results = search_tools(
    query="process data",
    use_semantic=True,
    top_k=3
)

# Substring search (fast, no dependencies)
results = search_tools(
    query="process data",
    use_semantic=False
)
```

## Advanced Usage

### Batch Indexing

Pre-compute embeddings for faster first-time search:

```python
from orchestrator.tools.vector_search import VectorToolSearchEngine
from orchestrator.tools.discovery_api import get_available_tools

# Get all tools
tools = get_available_tools()
catalog = {t.name: t for t in tools}

# Initialize search engine
engine = VectorToolSearchEngine(
    qdrant_url="http://localhost:6333",
    fallback_to_memory=True
)

# Index all tools (pre-compute embeddings)
engine.index_catalog(catalog, batch_size=32)

# Now searches will be fast
```

### Semantic + Substring Hybrid

Combine both approaches:

```python
from orchestrator import search_tools, semantic_search_tools

def find_tools(query: str):
    # Try semantic first
    semantic_results = semantic_search_tools(query, top_k=3, min_score=0.5)
    if semantic_results:
        return semantic_results
    
    # Fall back to substring
    substring_results = search_tools(query, use_semantic=False)
    return [(t, 1.0) for t in substring_results[:3]]
```

### Domain-Specific Search

Search within a specific domain:

```python
from orchestrator import semantic_search_tools

# Find only GitHub tools semantically
results = semantic_search_tools(
    "create and manage repositories",
    domain="github",
    top_k=5
)
```

## Performance

Typical latencies (with Qdrant):

| Scenario | Latency | Notes |
|----------|---------|-------|
| First query | 100-200ms | Includes embedding generation |
| Subsequent queries | 10-50ms | Uses embedding cache |
| Substring search | 1-5ms | No dependencies needed |
| Catalog indexing | 2-10s | For 100 tools |

## Troubleshooting

### "Vector search dependencies not available"

Install optional dependencies:

```bash
pip install qdrant-client sentence-transformers
```

### "Failed to connect to Qdrant"

Check if Qdrant is running:

```bash
# Docker
docker ps | grep qdrant

# Or test connection
python -c "from qdrant_client import QdrantClient; QdrantClient(url='http://localhost:6333').get_collections()"
```

### Slow first query

First query pre-computes embeddings. Subsequent queries are 5-10x faster.

### High memory usage

Embeddings are cached. Clear cache if needed:

```bash
rm -rf ~/.toolweaver/search_cache
```

## Environment Variables

- `QDRANT_URL`: Qdrant server URL (e.g., "http://localhost:6333")
- `QDRANT_COLLECTION`: Qdrant collection name (default: "toolweaver_tools")

Example:

```bash
export QDRANT_URL=http://localhost:6333
export QDRANT_COLLECTION=my_tools
python your_script.py
```

## Examples

### Example 1: Smart Tool Discovery

```python
import asyncio
from orchestrator import semantic_search_tools, get_available_tools

async def discover_capability():
    """Find tools for a capability description"""
    queries = [
        "extract text from images",
        "validate email addresses",
        "send notifications to teams",
        "parse financial data"
    ]
    
    for query in queries:
        results = semantic_search_tools(query, top_k=2)
        print(f"\nQuery: {query}")
        for tool, score in results:
            print(f"  ✓ {tool.name:30} ({score:.0%} match)")
```

### Example 2: Progressive Discovery

```python
from orchestrator import search_tools

# Start with fast substring search
quick_results = search_tools("github", use_semantic=False)
print(f"Quick results: {len(quick_results)} tools")

# If too many, refine with semantic search
if len(quick_results) > 10:
    precise_results = search_tools(
        "create pull request with code review",
        use_semantic=True,
        top_k=3
    )
    print(f"Refined to: {len(precise_results)} tools")
```

### Example 3: CLI Integration

```bash
#!/bin/bash

# Search for tools interactively
echo "What would you like to do?"
read -r task

# Try semantic search first
echo "Searching semantically..."
toolweaver search "$task" --semantic --top-k 3

# If no results, try substring
if [ $? -ne 0 ]; then
    echo "Searching by keyword..."
    toolweaver search "$task" --top-k 5
fi
```

## Migration from Substring Search

Existing code continues to work unchanged:

```python
# Old code (still works)
from orchestrator import search_tools
results = search_tools(query="github")  # Uses substring search

# New code (with semantic search)
results = search_tools(query="github", use_semantic=True)  # Uses embeddings
```

## Architecture

The semantic search system consists of:

1. **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions, 80MB)
2. **Vector Database**: Qdrant (optional, with in-memory fallback)
3. **Search Engine**: `VectorToolSearchEngine` with fallback logic
4. **Discovery API**: Unified `search_tools()` function

When Qdrant is unavailable:
- Embeddings are cached in-memory
- Cosine similarity computed locally
- Same accuracy, slightly slower for large catalogs

## Cost Considerations

With Qdrant, semantic search reduces LLM token usage:

- **Before**: Send all 100 tools (50,000 tokens)
- **After**: Send top 5 tools (2,500 tokens) = **95% reduction**

Qdrant Cloud free tier includes:
- Up to 1GB storage
- Free tier never expires
- Paid plans for larger catalogs

## Next Steps

1. Install dependencies: `pip install qdrant-client sentence-transformers`
2. Start Qdrant (Docker or Cloud)
3. Replace `use_semantic=False` with `use_semantic=True` in your code
4. Monitor latencies with `--verbose` CLI flag

For more on tool discovery, see [discovery-api.md](./discovery-api.md).
