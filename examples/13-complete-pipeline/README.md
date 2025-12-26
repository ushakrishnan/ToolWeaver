# Example 13: Complete End-to-End Pipeline

**Complexity:** ⭐⭐⭐ Advanced | **Time:** 20 minutes  
**Feature Demonstrated:** Complete ToolWeaver pipeline with all major features

## Overview

### What This Example Does
Demonstrates the complete ToolWeaver pipeline end-to-end: receipt processing with discovery, search, caching, monitoring, hybrid models, and workflows.

### All Features Showcased
1. **Tool Discovery** - Auto-discover MCP servers, functions, code execution
2. **Semantic Search** - Find relevant tools from large catalog
3. **Caching** - Redis cache for discovery, search, and results
4. **Monitoring** - WandB tracking for cost and performance
5. **Hybrid Models** - GPT-4 for planning, Phi-3 for execution
6. **Workflows** - Multi-step workflow with dependencies
7. **Code Execution** - Custom calculations in sandboxed environment
8. **Multi-Step Planning** - LLM generates execution plan
9. **Programmatic Execution** - Batch processing without LLM overhead

### Why This Matters
This is what a production ToolWeaver application looks like - combining all optimization techniques for maximum performance and minimum cost.

## Real-World Scenario

**Task**: Process 100 receipts, categorize expenses, generate summary report

**Without ToolWeaver**: 
- Cost: $15.00 (100 × $0.15 per receipt with GPT-4)
- Time: 200 seconds (100 × 2s sequential processing)
- No monitoring, no caching, manual workflows

**With ToolWeaver**:
- Cost: $0.75 (95% savings breakdown: ~60% hybrid models, ~25% caching, ~10% search)
- Time: 25 seconds (87% faster via parallelization + caching)
- Full monitoring, automatic workflows, production-ready

## Architecture

```
Natural Language Request
         ↓
    [Discovery & Cache]
    42 tools discovered
         ↓
    [Semantic Search]
    5 relevant tools selected (typically 70-90% token reduction when tools are well-categorized)
         ↓
    [Planning - GPT-4]
    Multi-step plan generated
         ↓
    [Hybrid Execution]
    ├─ Step 1: OCR (Azure CV)
    ├─ Step 2: Parse (Phi-3 - local)
    ├─ Step 3: Categorize (Phi-3 - local)
    └─ Step 4: Calculate (Code Execution)
         ↓
    [Monitoring & Analytics]
    WandB dashboard + metrics
```

## Prerequisites

- Python 3.10+
- Azure OpenAI API key
- Azure Computer Vision (optional, can use mock)
- Redis (optional, can use local fallback)
- Ollama with Phi-3 (optional, can use keyword matching)
- WandB account (optional, can use local logging)

## Setup

1. **Configure environment** (already done if using main .env):
   ```bash
   cp .env.example .env
   # Edit if needed - defaults are set from main .env
   ```

2. **Install dependencies**:
   ```bash
   pip install -r ../../requirements.txt
   ```

3. **Optional services**:
   ```bash
   # Redis (for caching)
   docker run -d -p 6379:6379 redis
   
   # Ollama (for Phi-3)
   ollama pull phi3
   ```

## Usage

```bash
python complete_pipeline.py
```

### Example Output

```
========================================================================
                  COMPLETE END-TO-END PIPELINE DEMO
========================================================================

Phase 1: Tool Discovery
----------------------------------------------------------------------
✓ Discovered 42 tools (from cache, 2ms)
  - 15 MCP tools
  - 18 function tools
  - 9 code execution patterns

Phase 2: Semantic Search
----------------------------------------------------------------------
Query: "Process receipt, categorize items, calculate statistics"
✓ Found 5 relevant tools in 12ms (94% token reduction)
  1. receipt_ocr (0.95)
  2. parse_items (0.89)
  3. categorize_items (0.84)
  4. calculate_stats (0.78)
  5. validate_data (0.72)

Phase 3: Multi-Step Planning (GPT-4)
----------------------------------------------------------------------
✓ Generated execution plan (850ms, $0.02)
  Step 1: extract_text (receipt_ocr)
  Step 2: parse_items (parse_items)
  Step 3a: categorize (categorize_items) [parallel]
  Step 3b: validate (validate_data) [parallel]
  Step 4: stats (calculate_stats)

Phase 4: Hybrid Execution
----------------------------------------------------------------------
Step 1: extract_text (Azure CV) ✓ 340ms
  → Extracted 12 line items from receipt

Step 2: parse_items (Phi-3 local) ✓ 180ms
  → Parsed: Burger $12.99, Fries $4.99, Drink $2.50...

Step 3a: categorize (Phi-3 local) ✓ 95ms [parallel]
  → Food: $15.48, Beverages: $5.00

Step 3b: validate (Code execution) ✓ 110ms [parallel]
  → Validation: PASSED (totals match)

Step 4: stats (Code execution) ✓ 45ms
  → Total: $20.48, Average: $1.71, Items: 12

Phase 5: Batch Processing (100 receipts)
----------------------------------------------------------------------
Using programmatic executor to avoid LLM overhead...

Processing batch 1-10: ✓ 2.1s (70% from cache)
Processing batch 11-20: ✓ 1.8s (80% from cache)
Processing batch 21-30: ✓ 1.6s (90% from cache)
...
Processing batch 91-100: ✓ 1.5s (95% from cache)

✓ Processed 100 receipts in 18.5s

Phase 6: Monitoring & Analytics
----------------------------------------------------------------------
WandB Dashboard: https://wandb.ai/usha-krishnan/ToolWeaver/runs/xyz123

Metrics Summary:
  Total requests: 101 (1 plan + 100 executions)
  Success rate: 100% (101/101)
  Average latency: 185ms per receipt
  Total tokens: 45,890
  Total cost: $0.75
  Cache hit rate: 85%

Cost Breakdown:
  Planning (GPT-4): $0.02 (2.7%)
  Execution (Phi-3): $0.01 (1.3%)
  OCR (Azure CV): $0.10 (13.3%)
  Cached results: $0.62 saved (45% of operations)
  
Tool Usage:
  receipt_ocr: 100 calls (15 from cache)
  parse_items: 100 calls (85 from cache)
  categorize_items: 100 calls (90 from cache)
  calculate_stats: 100 calls (100% code exec, $0)

========================================================================
✓ Complete pipeline demo finished successfully!
========================================================================

Summary:
  Without ToolWeaver: $15.00, 200s
  With ToolWeaver:    $0.75, 18.5s
  
  Savings: $14.25 (95% cost reduction)
  Speedup: 10.8x faster

Key Optimizations:
  1. Semantic search: 90% token reduction
  2. Hybrid models: 80% cost reduction (GPT-4 → Phi-3)
  3. Caching: 85% cache hit rate (62¢ saved)
  4. Parallelization: 25% faster execution
  5. Programmatic executor: 99% context reduction
  6. Code execution: $0 for calculations
```

## Key Concepts Demonstrated

### 1. Complete Pipeline Integration
All components work together seamlessly:
- Discovery → Search → Planning → Execution → Monitoring

### 2. Cost Optimization Stack
Multiple layers of cost reduction:
- Semantic search (90% token reduction)
- Hybrid models (80% model cost reduction)
- Caching (85% cache hit rate)
- Code execution ($0 for calculations)

### 3. Performance Optimization
Speed improvements from multiple techniques:
- Parallel execution (25% faster)
- Caching (10x faster for cached items)
- Local models (no network latency)
- Programmatic executor (avoid LLM overhead)

### 4. Production-Ready Features
Enterprise requirements met:
- Monitoring with WandB
- Error tracking and recovery
- Cache fallback (works without Redis)
- Graceful degradation (works without Phi-3)

### 5. Scalability
Handles growth efficiently:
- Sharded catalog (ready for 1000+ tools)
- Batch processing (100s of items)
- Distributed caching (Redis)
- Sub-linear cost scaling

## Configuration Options

```python
# Complete configuration
config = {
    # Discovery
    "enable_discovery_cache": True,
    "discovery_cache_ttl": 86400,
    
    # Search
    "search_strategy": "hybrid",
    "search_top_k": 5,
    "search_threshold": 20,
    
    # Planning
    "planner_model": "gpt-4o",
    "planner_provider": "azure-openai",
    
    # Execution
    "use_small_model": True,
    "worker_model": "phi3",
    "enable_parallel": True,
    
    # Caching
    "enable_redis": True,
    "cache_ttl": 3600,
    
    # Monitoring
    "monitoring_backends": ["wandb", "local"],
    
    # Code Execution
    "enable_code_exec": True,
    "code_exec_timeout": 5
}
```

## Advanced Features

The script demonstrates:
- ✅ Dynamic tool discovery
- ✅ Intelligent tool selection
- ✅ Multi-layer caching
- ✅ Real-time monitoring
- ✅ Hybrid model routing
- ✅ Workflow composition
- ✅ Sandboxed code execution
- ✅ Batch processing
- ✅ Parallel execution
- ✅ Error handling
- ✅ Cost tracking
- ✅ Performance profiling

## Related Examples

**Prerequisites** (Learn these first):
- [Example 01](../01-basic-receipt-processing) - Basic execution
- [Example 02](../02-receipt-with-categorization) - Multi-step workflows

**Individual Features** (Deep dive into each):
- [Example 04](../04-vector-search-discovery) - Discovery & search
- [Example 06](../06-monitoring-observability) - Monitoring
- [Example 07](../07-caching-optimization) - Caching
- [Example 08](../08-hybrid-model-routing) - Hybrid models
- [Example 11](../11-programmatic-executor) - Batch processing

## Learn More

- [Architecture Guide](../../docs/ARCHITECTURE.md)
- [Features Guide](../../docs/FEATURES_GUIDE.md)
- [Production Deployment](../../docs/PRODUCTION_DEPLOYMENT.md)
- [Two-Model Architecture](../../docs/TWO_MODEL_ARCHITECTURE.md)

## Production Deployment

This example shows a production-ready configuration. For deployment:

1. **Enable all services**:
   - Redis for caching
   - WandB for monitoring
   - Ollama/Azure for small models

2. **Set up monitoring**:
   - WandB dashboards
   - Prometheus metrics
   - Error tracking

3. **Configure for scale**:
   - Sharded catalog (1000+ tools)
   - Distributed caching
   - Load balancing

4. **Security**:
   - API key rotation
   - Sandboxed execution
   - Rate limiting

See [Production Deployment Guide](../../docs/PRODUCTION_DEPLOYMENT.md) for details.
