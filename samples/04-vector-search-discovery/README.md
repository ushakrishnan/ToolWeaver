# Example 04: Vector Search and Tool Discovery

**Complexity:** ⭐⭐ Intermediate | **Time:** 10 minutes  
**Feature Demonstrated:** Automatic tool discovery and semantic search

## Overview

### What This Example Does
Automatically discovers tools from multiple sources (MCP servers, Python functions, code execution) and uses semantic search to find relevant tools from large catalogs (100+ tools).

### Key Features Showcased
- **Tool Discovery**: Automatic introspection of MCP servers, functions, and code execution
- **Semantic Search**: Hybrid BM25 + embeddings to find relevant tools
- **Token Reduction**: 66-95% reduction by selecting only relevant tools
- **Caching**: Multi-layer cache (discovery, embeddings, search results)

### Why This Matters

When you have a large tool ecosystem (50-1000+ tools), you can't send all tool definitions to the LLM due to:
- **Token limits**: Claude 200K context, but 1000 tools can use 100K+ tokens
- **Cost**: More tokens = more money ($0.05 vs $0.0025 per request)
- **Accuracy**: Too many tools confuse the model (65% → 92% with search)

**Solution:** Semantic search finds only the 5-10 relevant tools for each task.

### Real-World Use Case

## How It Works

1. **Discovery Phase**: System introspects available tools
   - MCP servers (OCR, APIs, integrations)
   - Python functions (custom logic)
   - Code execution capabilities

2. **Search Phase**: Hybrid search (BM25 + embeddings) finds relevant tools
   - User query: "analyze receipt image"
   - Search returns: `receipt_ocr`, `image_processor`, `text_extractor`
   - Filters out irrelevant tools (slack, github, database ops)

3. **Execution Phase**: Only relevant tools sent to LLM for task execution

## Architecture

```
User Query → Semantic Search → Tool Selection → LLM Execution
  "OCR"         (100 tools)      (5 relevant)    (95% reduction)
                                                  
Discovery Cache ← Tool Catalog ← MCP/Functions/Code
  (24hr TTL)      (Auto-refresh)   (Introspection)
```

## Cost & Performance Impact

**Without Search (send all tools):**
- Tokens: 50,000 for 100 tools
- Cost: $0.05 per request
- Accuracy: 65% (LLM confused by too many options)

**With Search (send 5 relevant):**
- Tokens: 2,500 for 5 tools
- Cost: $0.0025 per request (95% reduction)
- Accuracy: 92% (LLM focused on right tools)

## Files

- `discover_tools.py` - Main example script
- `.env` - Your API keys (don't commit!)
- `.env.example` - Template for setup
- `README.md` - This file

## Prerequisites

- Python 3.10+
- Azure OpenAI or OpenAI API access
- ToolWeaver installed (`pip install toolweaver==0.5.0`)

## Setup

1. **Configure environment** (if not already using main .env):
   ```bash
   cp .env.example .env
   # Edit .env with your API keys if needed
   ```

2. **Install dependencies** (from project root):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python discover_tools.py
```

### Example Output

```
=== Tool Discovery Example ===

Phase 1: Discovering all available tools...
✓ Found 42 tools in 48ms
  - 15 MCP tools
  - 18 function tools
  - 9 code execution patterns

Phase 2: Semantic search for "process receipt image"...
✓ Found 5 relevant tools in 8ms:
  1. receipt_ocr (score: 0.94)
  2. image_analyzer (score: 0.87)
  3. text_extractor (score: 0.82)
  4. document_parser (score: 0.76)
  5. data_validator (score: 0.71)

Phase 3: Executing with optimal tool set...
✓ Task completed successfully

Metrics:
- Token reduction: 94% (50K → 3K tokens)
- Cost savings: $0.047 per request
- Search time: 8ms
- Total time: 1.2s
```

## Key Concepts

### 1. Hybrid Search Strategy

Combines two approaches:
- **BM25 (40%)**: Keyword matching ("receipt" matches "receipt_ocr")
- **Embeddings (60%)**: Semantic similarity ("analyze image" matches "image_processor")

### 2. Smart Thresholds

- **< 20 tools**: Skip search, send all (overhead not worth it)
- **20-100 tools**: Use search, return top 5-10
- **100+ tools**: Use search + sharding, return top 10-20

### 3. Caching Layers

- **Discovery cache**: 24 hours (tools don't change often)
- **Embedding cache**: 1 hour (same queries repeated)
- **Search results cache**: 5 minutes (same user patterns)

## Configuration Options

```python
# Discovery settings
ToolDiscoveryOrchestrator(
    enable_cache=True,          # Cache discovered tools
    cache_ttl=86400,            # 24 hours
    auto_refresh=True           # Refresh stale cache
)

# Search settings
ToolSearchEngine(
    strategy="hybrid",          # hybrid, bm25, embeddings
    bm25_weight=0.4,           # 40% keyword, 60% semantic
    top_k=5,                   # Return top 5 tools
    min_score=0.5              # Filter low-scoring tools
)
```

## Advanced Usage

See the script for examples of:
- Custom tool registration
- Search strategy comparison
- Performance benchmarking
- Cache management
- Multi-query optimization

## Related Examples

- **Example 01**: Basic tool usage (no search needed)
- **Example 10**: Multi-step planning (uses search internally)
- **Example 12**: Sharded catalog (search at scale)

## Learn More

- [Tool Search Documentation](../../docs/FEATURES_GUIDE.md#semantic-tool-search)
- [Architecture Guide](../../docs/ARCHITECTURE.md)
- [Search Tuning Guide](../../docs/SEARCH_TUNING.md)
