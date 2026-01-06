# ToolWeaver

**Production-ready AI agent orchestrator with a two-model architecture and unified tool interface.**

Large models (GPT-4o, Claude) plan; small models (Phi-3, Llama) execute for 80–90% cost savings. A single interface powers three tool types—MCP workers (with Claude-style JSON config loader), structured function calls, and sandboxed code—plus adapters for Claude/Cline formats so your tools stay portable.

**New:** Claude-compatible MCP config loader (Sample 33) for hosted or local MCP servers, including env substitution and protocol auto-detect. See samples/33-mcp-json-config/ for a working GitHub MCP demo that pairs with Sample 34.

[![PyPI version](https://badge.fury.io/py/toolweaver.svg)](https://pypi.org/project/toolweaver/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/ushakrishnan/ToolWeaver/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/tests-964%20passing%20(98.5%25)-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-67.61%25-yellow.svg)]()
[![Analytics](https://img.shields.io/badge/analytics-3%20backends-blue.svg)](https://ushakrishnan.github.io/ToolWeaver/reference/deep-dives/analytics-guide/)

---

## 🚀 Quick Navigation

**Package users (start here):** [Quickstart](https://ushakrishnan.github.io/ToolWeaver/get-started/quickstart/) • [Registering tools](https://ushakrishnan.github.io/ToolWeaver/how-to/add-a-tool/) • [Discovering tools](https://ushakrishnan.github.io/ToolWeaver/reference/deep-dives/registry-discovery/) • [Extending via plugins](https://ushakrishnan.github.io/ToolWeaver/how-to/extend-with-plugins/) • [Sub-agent dispatch](https://ushakrishnan.github.io/ToolWeaver/reference/deep-dives/agent-delegation/)

**Contributors:** [Development guide](https://ushakrishnan.github.io/ToolWeaver/developer-guide/) • [Architecture](https://ushakrishnan.github.io/ToolWeaver/reference/deep-dives/workflow-architecture/) • [Plugins](https://ushakrishnan.github.io/ToolWeaver/reference/api-python/plugins/) • [Testing](https://ushakrishnan.github.io/ToolWeaver/samples/testing/) • [Security](https://ushakrishnan.github.io/ToolWeaver/product/security/)

**Documentation:** [How-to Guides](https://ushakrishnan.github.io/ToolWeaver/how-to/) • [Developer Guide](https://ushakrishnan.github.io/ToolWeaver/developer-guide/) • [Deployment](https://ushakrishnan.github.io/ToolWeaver/deployment/) • [Reference](https://ushakrishnan.github.io/ToolWeaver/reference/)

---

## Overview

### 🎯 What It Does

#### 💡 Simple Explanation
Imagine you have two teammates:
- **Smart Planner** (expensive consultant) - Figures out what needs to be done
- **Fast Worker** (efficient employee) - Actually does the work

You ask the Smart Planner: "Process these receipts and categorize items"

The Smart Planner thinks and says: "Okay, here's the plan:
1. Extract text from image
2. Find all items and prices
3. Put items into categories (food, beverage, etc.)"

Then the Fast Worker executes each step quickly and cheaply, only asking the Smart Planner if something goes wrong.

**Result:** You get smart planning + fast execution = better and cheaper than using the expensive consultant for everything!

#### 🔬 Technical Explanation
This is an **execution orchestrator** with a **two-model architecture** for agentic AI systems:

**Architecture:**
1. **Large Planner Model** (GPT-4o, Claude 3.5) - Converts natural language → JSON execution plans
2. **Small Worker Models** (Phi-3, Llama 3.2) - Executes specific tasks (parsing, classification)
3. **Hybrid Orchestrator** - DAG-based execution with three tool types

**Problem:** Using large models for everything is expensive and slow. Using small models for planning fails at complex reasoning.

**Solution:**
- **Large model**: Planning, complex reasoning (1 call per user request)
- **Small models**: Text extraction, classification, parsing (1000s of calls, local/cheap)
- **80-90% cost reduction** vs large-model-only approach

**Three Tool Types:**
- **MCP Workers** - Deterministic operations (OCR, APIs) with optional small model enhancement
- **Function Calls** - Structured APIs with Pydantic validation
- **Code Execution** - Sandboxed Python (multiprocessing, restricted builtins)

**Research Applications:**
- Multi-agent workflows with heterogeneous model requirements
- Cost-optimized ML pipelines (right model for each task)
- Hybrid symbolic-neural systems
- Privacy-preserving AI (sensitive data processed locally with small models)

Inspired by Anthropic's MCP, extended with function registries, sandboxed execution, and two-model optimization.

#### 🚀 For Developers
- **Automatic tool discovery** - Introspects MCP servers, Python functions, and code execution capabilities
- **Semantic tool search** - Finds relevant tools from 100+ catalog using hybrid BM25 + embedding search
- **Workflow composition** - Chains tools automatically with dependency resolution and parallel execution
- **Cost optimization** - Up to 80-90% reduction possible through two-model architecture and multi-layer caching (varies by workload)
- **Production-ready** - Monitoring, logging, security sandboxing, and distributed caching

### 💡 Simple Example

```
User: "Process receipt.jpg and send expenses over $50 to #finance"
                           ↓
System automatically:
1. Searches 100+ tools → finds receipt_ocr, slack_send
2. Plans execution → extract → filter → notify
3. Executes workflow → OCR (Azure) → filter (sandbox) → Slack (API)
4. Monitors & logs → 275ms, 3 tools, 100% success

Cost: $0.05 vs $0.45 (89% savings in this scenario—combines caching, search, and two-model architecture)
```

### 🏗️ Architecture

```
Natural Language → Large Model (Planning) → Tool Search → Workflow Execution
                   1 call, $0.03          Select 10/100   Parallel steps
                                           90% token       25% faster
                                           reduction       
                           ↓
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
   MCP Workers      Function Calls     Code Execution
   (OCR, APIs)      (Python funcs)     (Sandboxed)
        ↓                  ↓                  ↓
   Small Models (Phi-3/Llama) - 1000s of calls, $0.0001 each
```

**Key Innovation:** Right model for each task - GPT-4 for complex reasoning, Phi-3 for simple parsing/classification.

> **⚠️ Performance Disclaimer:** Cost and speedup claims are benchmarked with mock data. Real-world results vary based on:
> - Cache hit rates (examples assume 85%; actual range: 30-90%)
> - Tool catalog quality (search effectiveness: 70-90%)
> - Network latency and API availability
> - Error rates and retry overhead (examples assume 0%; real: 5-15% adds 10-15% overhead)
>
> See individual samples for scenario-specific details.

### 🧭 Why ToolWeaver (Crux)

- **Secure fan-out:** Parallel sub-agent dispatcher with guardrails for cost, concurrency, time, rate limits, and recursion depth.
- **Built-in safety:** PII/secrets redaction, template sanitization, and idempotency caching so large fan-outs do not leak or repeat work.
- **Useful outputs:** Aggregation/ranking (majority vote, best score, custom) to turn noisy parallel calls into a single decision.
- **When to use:** Divide-and-conquer workloads, ensemble scoring, self-consistency runs, or any planner that needs 100+ tool/model calls without runaway spend.
- **Why not DIY:** Removes boilerplate for limits, logging, and safety; integrates with A2A client and plugin registry with documented, typed APIs.

## Installation

### 👤 For Users (Install Package)

**Use this if you want to use ToolWeaver in your projects.**

```bash
# Basic installation
pip install toolweaver

# With optional features
pip install toolweaver[azure]       # Add Azure AI services
pip install toolweaver[openai]      # Add OpenAI
pip install toolweaver[anthropic]   # Add Anthropic/Claude
pip install toolweaver[monitoring]  # Add W&B monitoring
pip install toolweaver[redis]       # Add Redis caching
pip install toolweaver[vector-db]   # Add vector search
pip install toolweaver[all]         # Everything
```

Then explore ready-to-run samples:
- [Samples](https://ushakrishnan.github.io/ToolWeaver/samples/) - Standalone samples using the installed package
- Start with [Sample 01: Basic Receipt Processing](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/01-basic-receipt-processing)

### 👨‍💻 For Contributors (Development Setup)

**Use this if you want to modify ToolWeaver source code or contribute.**

```bash
git clone https://github.com/ushakrishnan/ToolWeaver.git
cd ToolWeaver
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -e .                # Editable install
# pip install -e ".[dev]"       # With dev tools
```

Then explore source samples:
- [Repository samples](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples) - Uses local source code with editable installs
- See [CONTRIBUTING.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/CONTRIBUTING.md) for contribution guidelines

## 🛠️ Support Matrix

### Python & Platform Support

| Python Version | Ubuntu | Windows | macOS | Status |
|---|---|---|---|---|
| **3.13** | ✅ | ✅ | ✅ | Fully Supported (Latest) |
| **3.12** | ✅ | ✅ | ✅ | Fully Supported |
| **3.11** | ✅ | ✅ | ✅ | Fully Supported |
| **3.10** | ✅ | ✅ | ✅ | Fully Supported (Minimum) |
| **3.9** | ❌ | ❌ | ❌ | Not Supported |

### Features by Platform

- **Windows**: Full support including sandboxed code execution
- **Linux**: Full support; recommended for production deployments
- **macOS**: Full support; may have slower sandbox performance on Apple Silicon (M1/M2/M3)

### Known Issues

- **Apple Silicon (M1/M2/M3)**: Sandbox timeouts may be slower due to virtualization overhead (~2x). Use native Python or Rosetta 2 translation.
- **Windows Defender**: May flag sandboxed code execution as suspicious; add ToolWeaver to exclusions if needed.
- **Network in Sandbox**: Code execution sandbox has no network access by design. Use tool callbacks for external APIs.

### Continuous Integration

All tests run on:
- **Python 3.10, 3.11, 3.12, 3.13**
- **Platforms: Ubuntu, Windows, macOS**
- **Test Results**: 964 passed, 15 failed (98.5% pass rate)
  - 7 Ollama tests (requires local Ollama installation)
  - 5 benchmark API tests (optional performance validation)
  - 3 feature tests (minor issues)
- **Test Coverage**: 67.61% overall (6,183 lines covered out of 9,145)
  - Security modules: 95%+ (pii_detector, secrets_redactor, template_sanitizer)
  - Core tools: 90%+ (sub_agent, composition, error_recovery, idempotency)
  - Infrastructure: 85%+ (rate_limiter, a2a_client, mcp_client)
- **Type Checking**: mypy strict mode on critical modules

**High-Coverage Modules (>90%):**
- `orchestrator/tools/` - Core tool management (85-97%)
- `orchestrator/security/` - Security features (96-100%)
- `orchestrator/_internal/infra/` - Infrastructure (67-100%)
- `orchestrator/shared/models.py` - Data models (100%)

**Failing Tests:**
- Optional service integrations (Ollama, Redis SaaS)
- Non-critical benchmark validations
- Edge case handling in specialized modules

See [.github/workflows/test-matrix.yml](https://github.com/ushakrishnan/ToolWeaver/blob/main/.github/workflows/test-matrix.yml) for CI details.

---

## Core Features

### 🤖 Tool Management
- **Automatic Discovery** - Introspects MCP servers, Python functions, and code execution at startup
- **Semantic Search** - Hybrid BM25 + embedding search finds relevant tools from 100+ catalog (90% token reduction)
- **Smart Routing** - Auto-activates search for large catalogs, bypasses for small ones
- **Tool Examples** - Include usage examples to improve LLM parameter accuracy from 72% to 90%+
- **Dynamic Discovery** - LLMs can search for tools mid-conversation via `tool_search_tool`

### ⚡ Workflow Engine
- **Automatic Chaining** - Composes multi-step workflows with dependency resolution
- **Parallel Execution** - Independent steps run concurrently (25% faster)
- **Variable Substitution** - Pass data between steps: `{{previous_step.result}}`
- **Pattern Learning** - Detects common tool sequences from usage logs
- **Workflow Library** - Pre-built and custom reusable workflow templates
- **Error Handling** - Retry logic with exponential backoff

### 💰 Cost Optimization
- **Two-Model Architecture** - GPT-4 for planning (1 call), Phi-3 for execution (1000s of calls)
- **Multi-Layer Caching** - Query cache (1h), embedding cache (24h), LLM prompt cache (5min)
- **Token Reduction** - Search selects 10/100 tools → 90% fewer tokens sent to LLM
- **Prompt Caching** - Anthropic 90% discount, OpenAI 50% discount on cached tool definitions
- **Result: 80-90% cost reduction** vs single large model approach

### � Production Monitoring
- **Zero-Configuration** - Automatic monitoring for all plan executions
- **Pluggable Backends** - Local (JSONL), Weights & Biases, Prometheus
- **Multi-Backend Support** - Log to multiple systems simultaneously via `MONITORING_BACKENDS`
- **Performance Metrics** - Latency, success/failure rates, tool usage patterns
- **Cost Tracking** - Monitor token usage and API costs in real-time
- **Production Ready** - W&B dashboards, Prometheus metrics endpoint (port 8000)

### 🔒 Security & Reliability
- **Sandboxed Execution** - AST validation, restricted builtins, timeout enforcement
- **Type Safety** - Full Pydantic validation on inputs/outputs
- **Auto-Retry** - Up to 3 retry attempts with JSON repair
- **Process Isolation** - Code runs in separate process with resource limits
- **Error Handling** - Comprehensive logging with stack traces

### 🎯 Multi-Provider Support
- **LLM Providers** - OpenAI, Azure OpenAI (API key or Azure AD), Anthropic, Google Gemini
- **Small Models** - Ollama (local), Azure OpenAI, OpenAI, or any OpenAI-compatible endpoint
- **MCP Servers** - Local and remote MCP servers, including GitHub MCP (36+ tools)
- **Caching** - Redis (distributed) or file-based (local development)
- **Vector Search** - Qdrant Cloud (free tier) or local deployment
- **Monitoring** - W&B (cloud), Prometheus (metrics), Local (JSONL)

## Quick Start

### \ud83c\udfaf For Users: Run a Sample

After installing via pip, try a ready-to-run sample:

```bash
# Install the package
pip install toolweaver

# Navigate to a sample
cd samples/01-basic-receipt-processing

# Install dependencies
pip install -r requirements.txt

# Configure (optional - add your API keys)
cp .env.example .env
# Edit .env with your Azure credentials

# Run it!
python process_receipt.py
```

**Browse all samples:** [samples/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/README.md)

### \ud83d\udee0\ufe0f For Developers: Try Samples

After cloning the repo and installing with `pip install -e .`:

```bash
# Basic OCR sample (\u2b50)
cd samples/01-basic-receipt-processing
python process_receipt.py

# Multi-step workflow (\u2b50\u2b50)
cd samples/02-receipt-with-categorization
python categorize_receipt.py

# Complete end-to-end demo (\u2b50\u2b50\u2b50)
cd samples/13-complete-pipeline
python complete_pipeline.py
```

**Browse all samples:** [samples/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/README.md)

### Option 3: Natural Language Planning (Requires LLM API Key)

```bash
# LLM providers already included in core install

# Configure provider in .env
# Edit .env and add:
#   For Azure OpenAI (with API Key):
#     PLANNER_PROVIDER=azure-openai
#     AZURE_OPENAI_API_KEY=...
#     AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
#   For Azure OpenAI (with Azure AD - Recommended):
#     PLANNER_PROVIDER=azure-openai
#     AZURE_OPENAI_USE_AD=true
#     AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
#     # Then run: az login
#   For OpenAI:
#     PLANNER_PROVIDER=openai
#     OPENAI_API_KEY=sk-...
#   For Anthropic:
#     PLANNER_PROVIDER=anthropic
#     ANTHROPIC_API_KEY=sk-ant-...

# Run planner demo
python run_planner_demo.py "Process this receipt and categorize items"
```

### Option 4: With Small Model Workers

**Option 4A: Ollama (Local - Free)**
```bash
# Install Ollama (https://ollama.ai)
ollama pull phi3

# Configure in .env
USE_SMALL_MODEL=true
SMALL_MODEL_BACKEND=ollama
WORKER_MODEL=phi3

# Run with Phi-3 for parsing/categorization
python run_demo.py
```

**Option 4B: Azure AI Foundry (Cloud - Managed)**
```bash
# Deploy Phi-3 in Azure AI Foundry (https://ai.azure.com)

# Configure in .env
USE_SMALL_MODEL=true
SMALL_MODEL_BACKEND=azure
AZURE_SMALL_MODEL_ENDPOINT=https://your-endpoint.inference.ml.azure.com/score
AZURE_SMALL_MODEL_KEY=...

# Run
python run_demo.py
```

## Tool Types

### MCP Workers
Deterministic, reliable operations with optional small model enhancement:
```json
{
  "tool": "receipt_ocr",
  "input": {"image_uri": "https://example.com/receipts/2024-12-receipt.jpg"}
}
```

**Small Model Integration:**
- `receipt_ocr` - Uses Azure Computer Vision (no small model needed)
- `line_item_parser` - Uses Phi-3 if `USE_SMALL_MODEL=true`, else keyword matching
- `expense_categorizer` - Uses Phi-3 if `USE_SMALL_MODEL=true`, else simple rules

**When to Enable Small Models:**
- ✅ Processing real-world receipts (diverse formats)
- ✅ Need intelligent categorization beyond keywords
- ✅ Want 80-90% cost reduction
- ❌ Simple testing with known formats (keyword matching sufficient)

### Function Calls
Type-safe, reusable functions with schema enforcement:
```json
{
  "tool": "function_call",
  "input": {
    "name": "compute_tax",
    "args": {"amount": 100.0, "tax_rate": 0.08}
  }
}
```

### Code Execution
Sandboxed Python for dynamic transformations:
```json
{
  "tool": "code_exec",
  "input": {
    "code": "output = {'total': sum(input['values'])}",
    "input_data": {"values": [10, 20, 30]}
  }
}
```

## Example Plan

```json
{
  "request_id": "req-001",
  "steps": [
    {
      "id": "step-1",
      "tool": "receipt_ocr",
      "input": {"image_uri": "https://example.com/receipts/2024-12-receipt.jpg"}
    },
    {
      "id": "step-2",
      "tool": "function_call",
      "input": {
        "name": "compute_tax",
        "args": {"amount": "step:step-1", "tax_rate": 0.08}
      },
      "depends_on": ["step-1"]
    }
  ],
  "final_synthesis": {
    "prompt_template": "Summary:\n{{steps}}"
  }
}
```

## Usage

```python
import asyncio
from orchestrator import execute_plan, final_synthesis

async def main():
    plan = {...}  # Your execution plan
    context = await execute_plan(plan)
    result = await final_synthesis(plan, context)
    print(result)

asyncio.run(main())
```

## Adding Custom Functions

```python
from orchestrator.hybrid_dispatcher import register_function

@register_function("my_function")
def my_function(arg1: str, arg2: int) -> dict:
    """Your custom logic here."""
    return {"result": arg1 * arg2}
```

## Built-in Functions

- `compute_tax` - Calculate tax amounts
- `merge_items` - Aggregate item statistics
- `apply_discount` - Apply percentage discounts
- `filter_items_by_category` - Filter items by category
- `compute_item_statistics` - Comprehensive item analytics

## Architecture

### Two-Model Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│ USER REQUEST                                                      │
│ "Process this receipt and categorize all items"                  │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ LARGE PLANNER MODEL (GPT-4o / Claude / Gemini)                   │
│ • Understands intent                                              │
│ • Generates JSON execution plan                                   │
│ • Cost: $0.002 per request                                        │
└─────────────────────────────┬────────────────────────────────────┘
                              │ JSON Plan
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ HYBRID ORCHESTRATOR                                               │
│ • Resolves dependencies (DAG)                                     │
│ • Parallel execution                                              │
│ • Routes to appropriate workers                                   │
└──────────┬───────────┬──────────┬─────────────────────────────────┘
           │           │          │
           ▼           ▼          ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │   MCP    │ │ Function │ │   Code   │
    │ Workers  │ │  Calls   │ │   Exec   │
    └────┬─────┘ └──────────┘ └──────────┘
         │
         ├─ receipt_ocr → Azure CV (deterministic)
         ├─ line_item_parser → ┐
         └─ expense_categorizer ┘
                    │
                    ▼
         ┌─────────────────────┐
         │  SMALL MODEL        │
         │  (Phi-3 / Llama)    │
         │                     │
         │  • Parse items      │
         │  • Categorize       │
         │  • Cost: FREE/cheap │
         │  • Fast: 2-3x       │
         └─────────────────────┘
```

### Execution Flow Example

```
1. User: "Process receipt and categorize"
   ↓
2. GPT-4o generates plan:
   - Step 1: receipt_ocr (Azure CV)
   - Step 2: line_item_parser (Phi-3 if enabled)
   - Step 3: expense_categorizer (Phi-3 if enabled)
   - Step 4: compute_item_statistics (function call)
   ↓
3. Orchestrator executes:
   - Step 1: Azure CV extracts text
   - Step 2: Phi-3 parses 15 items (2 seconds, local)
   - Step 3: Phi-3 categorizes items (1 second, local)
   - Step 4: Function computes stats (instant)
   ↓
4. Result: Structured data with categories
   Total cost: $0.002 (vs $0.15 with GPT-4o for everything)
```

## Usage Guide

### Tool Discovery & Management

**Automatic tool discovery** from multiple sources:

```python
from orchestrator.tool_discovery import ToolDiscoveryOrchestrator
from orchestrator.planner import LargePlanner

# Discover all available tools
orchestrator = ToolDiscoveryOrchestrator(
    enable_cache=True,  # 24-hour cache
    cache_ttl=86400
)

catalog = await orchestrator.discover_all()
# Sources: MCP workers, Python functions, code execution
# Performance: ~50ms first run, <1ms cached

# Use with planner
planner = LargePlanner(provider="azure-openai", tool_catalog=catalog)
plan = await planner.generate_plan("Process receipt...")
```

**Or manually define tools:**

```python
from orchestrator.models import ToolCatalog, ToolDefinition, ToolParameter

catalog = ToolCatalog()
catalog.add_tool(ToolDefinition(
    name="analyze_data",
    type="function",
    description="Analyze dataset and return insights",
    parameters=[
        ToolParameter(name="data", type="object", required=True),
        ToolParameter(name="format", type="string", enum=["json", "csv"])
    ]
))
```

### Semantic Tool Search

### Intelligent Tool Selection at Scale

When you have 30+ tools, ToolWeaver automatically uses **hybrid semantic search** to select the most relevant tools:

```python
from orchestrator.planner import LargePlanner

# Enable semantic search (default: auto-activates for 20+ tools)
planner = LargePlanner(
    provider="azure-openai",
    use_tool_search=True,      # Enable semantic search
    search_threshold=20         # Activate when tools > 20
)

# With 30 tools, planner automatically:
# 1. Runs hybrid BM25 + embedding search
# 2. Selects 10 most relevant tools
# 3. Passes only relevant tools to LLM
# 4. Logs: "30 tools → 10 relevant (~66.7% token reduction)"

plan = await planner.generate_plan("Process receipt and categorize items")
```

**Search Engine Architecture:**
- **Hybrid Scoring:** 30% BM25 (keyword matching) + 70% embeddings (semantic similarity)
- **Embedding Model:** `all-MiniLM-L6-v2` (384-dim, 80MB, fast inference)
- **Smart Routing:** Skips search for ≤20 tools (returns all with score 1.0)
- **Caching:** 
  - Embeddings: Persistent (MD5-hashed text → .npy files)
  - Query results: 1-hour TTL (pickled, includes catalog hash)

**Performance:**
- **Initial model load:** ~11 seconds (one-time, downloads 80MB model)
- **Search time:** 31-624ms (after model loaded)
- **Token reduction:** Selects top 10 from 30+ tools (logs actual reduction %)
- **Example:** 30 tools → 10 tools = 4,500 → 1,500 tokens sent to LLM

**Manual Search Usage:**
```python
from orchestrator.tool_search import ToolSearchEngine, search_tools

# Option 1: Explicit search
engine = ToolSearchEngine(
    bm25_weight=0.3,          # Keyword importance
    embedding_weight=0.7,      # Semantic importance
    cache_dir="~/.toolweaver/search_cache"
)

results = engine.search(
    query="process receipts and extract line items",
    catalog=catalog,
    top_k=10,
    min_score=0.3
)

# Returns: List[(ToolDefinition, score)]
for tool, score in results:
    print(f"{tool.name}: {score:.3f}")

# Option 2: Convenience function (returns tools only)
tools = search_tools(
    query="receipt processing",
    catalog=catalog,
    top_k=10
)

# Option 3: Explain results
explanation = engine.explain_results(results, query="receipt processing")
print(explanation)
# Output:
# Query: "receipt processing"
# 🔥 receipt_ocr (0.95) - High relevance
# ✓ line_item_parser (0.78) - Good match
# ~ expense_categorizer (0.45) - Partial match
```

**Configuration:**
```python
# Tune for your use case
engine = ToolSearchEngine(
    bm25_weight=0.5,           # More keyword matching
    embedding_weight=0.5,      # Less semantic
    embedding_model="all-MiniLM-L6-v2",  # Fast, small
    # Or: "all-mpnet-base-v2" (larger, more accurate)
    cache_dir="~/.toolweaver/search_cache"
)

# Clear cache
engine.clear_cache()
```

**When to Use:**
- ✅ Large tool catalogs (30+ tools)
- ✅ Reduce prompt token costs (66%+ reduction)
- ✅ Improve planner accuracy (less tool confusion)
- ✅ Dynamic tool selection based on query
- ❌ Small catalogs (≤20 tools, overhead not worth it)

### Programmatic Tool Calling

**Parallel execution with code orchestration:**

When you need to call multiple tools or process large datasets, ToolWeaver can **generate code that orchestrates tools in parallel**:

```python
from orchestrator.planner import LargePlanner

# Enable programmatic calling (default: enabled)
planner = LargePlanner(
    provider="azure-openai",
    use_programmatic_calling=True  # LLM can generate orchestration code
)

# Complex query that needs multiple tool calls
plan = await planner.generate_plan(
    "Get all engineering team members, fetch their Q3 expenses, "
    "and tell me who exceeded their travel budget"
)

# Planner generates code like:
# team = await get_team_members("engineering")
# expenses = await asyncio.gather(*[get_expenses(m["id"], "Q3") for m in team])
# exceeded = [m for m, exp in zip(team, expenses) if sum(e["amount"] for e in exp) > budget]

# Execute the plan
from orchestrator import execute_plan
result = await execute_plan(plan)
```

**How It Works:**

Traditional approach (BAD):
```
Step 1: get_team_members() → 20 members (5KB enters context)
Step 2: get_expenses(member1) → 50 items (10KB enters context)
Step 3-21: get_expenses(member2-20) → 190KB more!
Step 22: LLM manually processes 200KB+ of data

Total: 22 API calls, 200KB context, 5+ seconds
```

Programmatic approach (GOOD):
```python
# Step 1: LLM generates orchestration code
team = await get_team_members("engineering")
expenses = await asyncio.gather(*[get_expenses(m["id"], "Q3") for m in team])
exceeded = [m["name"] for m, exp in zip(team, expenses) 
            if sum(e["amount"] for e in exp) > 10000]
print(json.dumps(exceeded))  # Only 2KB result

Total: 1 inference pass, 2KB context, <1 second
```

**Benefits:**
- 🚀 **60-80% faster** - 1 inference pass vs 20+
- 💰 **37% token savings** - Intermediate data stays in sandbox (2KB vs 200KB)
- ⚡ **Parallel execution** - `asyncio.gather()` runs 20 calls simultaneously
- 🎯 **More reliable** - Explicit logic vs implicit LLM reasoning

**Direct Usage (Advanced):**
```python
from orchestrator.programmatic_executor import ProgrammaticToolExecutor

executor = ProgrammaticToolExecutor(tool_catalog)

code = """
# All tools are available as async functions
users = await get_users(department="sales")
reports = await asyncio.gather(*[generate_report(user_id=u["id"]) for u in users])

# Filter and aggregate in code (not in LLM context!)
summary = {
    "total_users": len(users),
    "reports_generated": len(reports),
    "top_performers": [r["name"] for r in reports if r["score"] > 90]
}
print(json.dumps(summary))
"""

result = await executor.execute(code)
print(result["output"])  # JSON summary
print(f"Called {len(result['tool_calls'])} tools in {result['execution_time']:.2f}s")
```

**Security:**
- AST-based validation (blocks dangerous imports, file I/O, subprocess)
- Safe builtins only (no `eval`, `exec`, `open`, `__import__`)
- Timeout protection (default: 30s)
- Tool call limits (default: 100 max calls)
- Execution sandboxing with restricted environment

**When to Use:**
- ✅ Multiple tool calls in a loop (iterate over collections)
- ✅ Parallel operations (independent tool calls)
- ✅ Large intermediate data (filter/aggregate before returning)
- ✅ Complex logic (conditionals, loops, transformations)
- ❌ Single tool call (use direct tool calling)
- ❌ LLM needs full intermediate results

### Programmatic Execution with Progressive Disclosure

**NEW:** Execute code that explores and imports tools on-demand instead of loading all tool definitions into context. Achieves **30-80% context reduction** while maintaining full functionality.

**Problem:** Loading 100+ tool definitions into LLM context consumes 800+ tokens. This doesn't scale.

**Solution:** Generate Python stubs AI can explore like a file tree, importing only needed tools:

```python
from orchestrator.programmatic_executor import ProgrammaticToolExecutor

# Create executor with stub generation enabled
executor = ProgrammaticToolExecutor(
    catalog=tool_catalog,
    enable_stubs=True  # Generate importable Python stubs
)

# AI explores tool directory (50 tokens instead of 800+)
tree = executor.get_tools_directory_tree()
# tools/
#   google_drive/
#     get_document.py
#     create_document.py
#   jira/
#     create_ticket.py
#   slack/
#     send_message.py

# AI searches for relevant tools
matches = executor.search_tools("document")  # ["get_document", "create_document"]

# AI generates code that imports only needed tools
code = '''
# Import specific tools with type safety
from tools.google_drive import get_document, GetDocumentInput

# Use Pydantic models for type-safe parameters
input_data = GetDocumentInput(doc_id="doc123", format="pdf")
result = await get_document(input_data)

# Process result
if result.success:
    print(f"Document: {result.result}")
else:
    print(f"Error: {result.error}")
'''

# Execute with full tool access
result = await executor.execute(code)
```

**Benefits:**
- 📉 **30-80% context reduction** - Load only needed tools, not entire catalog
- 📈 **Scales to 1000+ tools** - Exploration cost remains constant
- 🔒 **Type safety** - Pydantic models provide IDE support and validation
- 🎯 **On-demand loading** - AI discovers tools as needed
- 🐛 **Debuggable** - Generated stubs are readable Python code

**Architecture:**
```
ToolCatalog → StubGenerator → tools/ directory → ToolFileSystem → AI Code
                               (Python stubs)    (exploration API)
```

**See:** [Sample 14](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/14-programmatic-execution) for detailed demos and benchmarks.

### Tool Usage Examples

**Improve LLM parameter accuracy with examples:**

**Problem:** Schema-only tool definitions leave LLMs guessing about format conventions, optional parameters, and edge cases. Result: 72% parameter accuracy.

**Solution:** Add usage examples showing typical scenarios, input/output patterns, and format conventions. Result: **90%+ parameter accuracy**.

```python
from orchestrator.models import ToolDefinition, ToolParameter, ToolExample

# Create tool with examples
receipt_ocr_tool = ToolDefinition(
    name="receipt_ocr",
    type="mcp",
    description="Extract text from receipt images using Azure Computer Vision",
    parameters=[
        ToolParameter(name="image_url", type="string", description="URL or file path", required=True),
        ToolParameter(name="language", type="string", description="Language code", 
                     enum=["en", "es", "fr"], default="en"),
        ToolParameter(name="orientation", type="string", description="Image orientation",
                     enum=["auto", "0", "90", "180", "270"], default="auto")
    ],
    examples=[
        ToolExample(
            scenario="Process typical restaurant receipt from local file",
            input={
                "image_url": "./receipts/restaurant_2024_01_15.jpg",
                "language": "en",
                "orientation": "auto"
            },
            output={
                "text": "RESTAURANT XYZ\nDate: 2024-01-15\nBurger $12.99\nTotal: $16.98",
                "confidence": 0.95
            },
            notes="Use auto orientation for most receipts. Specify language if known."
        ),
        ToolExample(
            scenario="Process rotated receipt from URL",
            input={
                "image_url": "https://storage.example.com/img_001.jpg",
                "orientation": "90"
            },
            output={"text": "GROCERY STORE\nDate: 2024-02-01\nTotal: $8.49"},
            notes="Specify orientation (90/180/270) if consistently rotated."
        )
    ]
)

# Examples automatically included in LLM format
llm_format = receipt_ocr_tool.to_llm_format(include_examples=True)
# Description now includes examples with scenarios, showing format patterns!
```

**Benefits:**
- 📈 **72% → 90%+ accuracy** - Shows format conventions (dates YYYY-MM-DD, IDs USR-XXXXX)
- 🎯 **Clear optional params** - Examples show when to use/omit optional parameters
- 📚 **Edge case handling** - Multiple scenarios cover typical variations
- 🚫 **Less ambiguity** - Real inputs/outputs eliminate guesswork

### Performance Monitoring

**Automatic monitoring** is built-in and configured via `.env`:

```bash
# .env - Configure monitoring backends
MONITORING_BACKENDS=local,wandb  # Options: local, wandb, prometheus

# Weights & Biases (optional - pip install wandb)
WANDB_API_KEY=your-key-here
WANDB_PROJECT=ToolWeaver
WANDB_ENTITY=your-username

# Prometheus (optional - pip install prometheus-client)
PROMETHEUS_PORT=8000
```

**All plan executions are automatically logged** to enabled backends:

```python
from orchestrator import execute_plan

# Monitoring is automatic - no manual setup required
context = await execute_plan(plan)

# Metrics automatically logged:
# - Tool calls (success/failure)
# - Execution latency
# - Error details
# - Plan start/completion
```

**Manual logging (for standalone tool calls):**

```python
from orchestrator.monitoring import ToolUsageMonitor, print_metrics_report

# Create monitor with specific backends
monitor = ToolUsageMonitor(backends=["local", "wandb"])

# Log tool calls
monitor.log_tool_call("receipt_ocr", success=True, latency=0.045)

# Log search queries
monitor.log_search_query("process receipt", num_results=5, latency=0.1, cache_hit=True)

# View metrics
print_metrics_report(monitor)
```

**Output:**
```
================================================================================
TOOL USAGE MONITORING REPORT
================================================================================

📊 Overview:
   Total tool calls:    1,247
   Total errors:        18
   Overall error rate:  1.4%
   Unique tools used:   8
   Search queries:      523
   Cache hit rate:      82.3%

🔧 Top Tools:
   receipt_ocr                     453 calls  (p50: 45ms, errors: 0.2%)
   parse_line_items                312 calls  (p50: 12ms, errors: 0.9%)
   categorize_expenses             201 calls  (p50: 8ms, errors: 2.5%)

💰 Token Usage:
   Input tokens:       523,401
   Output tokens:       87,234
   Cached tokens:      2,104,523
   Cache savings:       80.1%

🚨 Recent Errors:
   No recent errors
```

### Prompt Caching (90% Cost Reduction)

Cache tool definitions for massive savings on repeated requests:

```python
# Anthropic format with caching
messages = [
    {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": "You are a helpful assistant.",
                "cache_control": {"type": "ephemeral"}  # Cache system prompt
            },
            {
                "type": "text",
                "text": json.dumps(catalog.to_llm_format(include_examples=True)),
                "cache_control": {"type": "ephemeral"}  # Cache tools + examples
            }
        ]
    },
    {"role": "user", "content": user_request}  # Only this changes
]

# First request: Full tokens × full price
# Next requests: Cached tokens × discounted price (90% Anthropic, 50% OpenAI)
# Significant savings on repeated requests with same tool catalog
```

**Cost Optimization Strategy:**
1. Semantic search: Select 10 relevant tools from 100+ catalog
2. Tool examples: Include examples for those 10 tools only
3. Prompt caching: Cache the 10 tools + examples (Anthropic 90% discount, OpenAI 50% discount)
4. **Result**: Improved accuracy + reduced token costs on repeated requests

### Production Deployment

See [Production Deployment](https://ushakrishnan.github.io/ToolWeaver/deployment/production-deployment/) for complete production guide covering:
- Security hardening (Azure AD, managed identity, sandboxing)
- Performance optimization (lazy loading, connection pooling, caching)
- Monitoring setup (health checks, Prometheus metrics)
- Scaling considerations (horizontal/vertical, cache sharing)
- Deployment patterns (Azure App Service, ACI, AKS)
- Troubleshooting common issues

**Production Checklist:**
- ✅ 234/234 tests passing
- ✅ Azure AD authentication
- ✅ Managed Identity configured
- ✅ Resource limits set
- ✅ Monitoring enabled
- ✅ Health checks working

### Workflow Composition

**Automatic multi-step workflows with dependency resolution:**

**Problem:** Complex tasks require multiple tools, but manually orchestrating dependencies is error-prone. LLMs repeat common tool sequences instead of learning patterns.

**Solution:** Workflow system automatically chains tools with dependency resolution, learns patterns from usage logs, and builds reusable workflow library.

```python
from orchestrator.workflow import WorkflowTemplate, WorkflowStep, WorkflowContext, WorkflowExecutor

# Define multi-step workflow with dependencies
deploy_workflow = WorkflowTemplate(
    name="ci_cd_pipeline",
    description="Build, test, and deploy application",
    steps=[
        WorkflowStep(
            step_id="build",
            tool_name="docker_build",
            parameters={"image": "{{image_name}}", "tag": "{{version}}"}
        ),
        WorkflowStep(
            step_id="test",
            tool_name="run_tests",
            parameters={"image": "{{build.image_id}}"},  # Use previous step result
            depends_on=["build"]  # Wait for build to complete
        ),
        WorkflowStep(
            step_id="push",
            tool_name="docker_push",
            parameters={"image": "{{build.image_id}}"},
            depends_on=["test"]  # Sequential execution
        )
    ]
)

# Execute with dependency resolution
executor = WorkflowExecutor(tool_registry=catalog)
context = WorkflowContext(initial_variables={"image_name": "myapp", "version": "1.2.3"})

# Automatic dependency resolution and parallel execution
result = await executor.execute(deploy_workflow, context)
```

### Pattern Recognition

**Learns common tool sequences from usage logs:**

```python
from orchestrator.workflow_library import PatternDetector, WorkflowLibrary
from orchestrator.monitoring import ToolUsageMonitor

# Monitor creates ToolCallMetric logs automatically
monitor = ToolUsageMonitor()

# Detect patterns from logs
detector = PatternDetector(min_frequency=3, min_success_rate=0.8)
patterns = detector.analyze_logs(monitor.tool_call_log, max_sequence_length=5)

# Top pattern: github_list_issues → github_create_pr → slack_send_message
# Frequency: 15 occurrences, Success rate: 93%

# Auto-generate workflow from pattern
workflow = detector.suggest_workflow(
    tools=patterns[0].tools,
    patterns=patterns
)
```

### Workflow Library

**Pre-built and custom workflow templates:**

```python
library = WorkflowLibrary()

# Search for relevant workflows
workflows = library.search(query="github pull request")

# Get workflow suggestions for specific tools
suggestions = library.suggest_for_tools(["github_list_issues", "github_create_pr"])

# Register custom workflows
library.register(custom_workflow)

# Persist to disk
library.save_to_disk("workflows/custom")
```

**Workflow System Benefits:**
- ✅ **25% faster** - Parallel execution of independent steps
- ✅ **Pattern learning** - Automatically detect common tool sequences
- ✅ **Reusable workflows** - Build library of proven patterns
- ✅ **Cross-step context** - Share data between steps with variable substitution
- ✅ **Error handling** - Retry logic with exponential backoff
- ✅ **52 tests** - Comprehensive test coverage for workflows and patterns

**See:** [Orchestrate with code](https://ushakrishnan.github.io/ToolWeaver/how-to/orchestrate-with-code/) | [Workflow architecture](https://ushakrishnan.github.io/ToolWeaver/reference/deep-dives/workflow-architecture/) | [Workflow library sample](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/05-workflow-library)

## End-to-End Example: Discovery → Search → Planning

```python
import asyncio
from orchestrator.tool_discovery import ToolDiscoveryOrchestrator
from orchestrator.planner import LargePlanner

async def main():
    # Step 1: Discover all available tools
    discovery = ToolDiscoveryOrchestrator(enable_cache=True)
    catalog = await discovery.discover_all()
    
    print(f"✅ Discovered {len(catalog.tools)} tools in {catalog.metadata['discovery_time_ms']:.2f}ms")
    
    # Step 2: Initialize planner with automatic semantic search
    planner = LargePlanner(
        provider="azure-openai",
        tool_catalog=catalog,
        use_tool_search=True,       # Auto-activates for 20+ tools
        search_threshold=20
    )
    
    # Step 3: Generate plan (semantic search happens automatically)
    plan = await planner.generate_plan(
        "Process this receipt: extract text, parse items, categorize as food/beverage/other"
    )
    
    # If catalog has 30 tools, logs:
    # "Semantic search: 30 tools → 10 relevant (~66.7% token reduction, ~3,000 tokens saved)"
    
    print(f"✅ Generated plan with {len(plan.steps)} steps")
    for step in plan.steps:
        print(f"  - Step {step.id}: {step.tool}")
    
    # Step 4: Execute plan (existing orchestrator code)
    from orchestrator import execute_plan, final_synthesis
    context = await execute_plan(plan)
    result = await final_synthesis(plan, context)
    
    print(f"✅ Result: {result}")

asyncio.run(main())
```

**Output:**
```
✅ Discovered 14 tools in 1.24ms (cached)
Semantic search: 30 tools → 10 relevant (~66.7% token reduction, ~3,000 tokens saved)
✅ Generated plan with 3 steps
  - Step step-1: receipt_ocr
  - Step step-2: line_item_parser
  - Step step-3: expense_categorizer
✅ Result: {"items": [...], "categories": {...}}
```

## Documentation

Full docs: https://ushakrishnan.github.io/ToolWeaver/

### Getting Started
- [Quickstart](https://ushakrishnan.github.io/ToolWeaver/get-started/quickstart/)
- [Installation](https://ushakrishnan.github.io/ToolWeaver/get-started/installation/)
- [Tutorials](https://ushakrishnan.github.io/ToolWeaver/tutorials/)

### How-to Guides
- [Add a Tool](https://ushakrishnan.github.io/ToolWeaver/how-to/add-a-tool/)
- [Parallel Dispatch](https://ushakrishnan.github.io/ToolWeaver/how-to/parallel-dispatch/)
- [Caching](https://ushakrishnan.github.io/ToolWeaver/how-to/caching/)
- [Extend with Plugins](https://ushakrishnan.github.io/ToolWeaver/how-to/extend-with-plugins/)
- [Monitor Performance](https://ushakrishnan.github.io/ToolWeaver/how-to/monitor-performance/)
- [Aggregate Agent Results](https://ushakrishnan.github.io/ToolWeaver/how-to/aggregate-agent-results/)

### Reference
- [Python API](https://ushakrishnan.github.io/ToolWeaver/reference/api-python/)
- [CLI Reference](https://ushakrishnan.github.io/ToolWeaver/reference/cli/)
- [Registry Discovery](https://ushakrishnan.github.io/ToolWeaver/reference/deep-dives/registry-discovery/)
- [Plugin Extension](https://ushakrishnan.github.io/ToolWeaver/reference/deep-dives/plugin-extension/)

### Architecture
- [Two-Model Architecture](https://ushakrishnan.github.io/ToolWeaver/reference/deep-dives/two-model-architecture/)
- [Workflow Architecture](https://ushakrishnan.github.io/ToolWeaver/reference/deep-dives/workflow-architecture/)
- [Agent Delegation](https://ushakrishnan.github.io/ToolWeaver/reference/deep-dives/agent-delegation/)
- [Control Flow Patterns](https://ushakrishnan.github.io/ToolWeaver/reference/deep-dives/control-flow-patterns/)

### Deployment
- [Production Deployment](https://ushakrishnan.github.io/ToolWeaver/deployment/production-deployment/)
- [Azure Setup](https://ushakrishnan.github.io/ToolWeaver/deployment/azure-setup/)
- [Redis Setup](https://ushakrishnan.github.io/ToolWeaver/deployment/redis-setup/)
- [Qdrant Setup](https://ushakrishnan.github.io/ToolWeaver/deployment/qdrant-setup/)
- [SQLite + Grafana](https://ushakrishnan.github.io/ToolWeaver/deployment/sqlite-grafana-setup/)

### Samples
- [Samples Index](https://ushakrishnan.github.io/ToolWeaver/samples/)
- [Samples Testing](https://ushakrishnan.github.io/ToolWeaver/samples/testing/)

## Provider Support

### Large Model Planner
| Provider | Models | Configuration |
|----------|--------|---------------|
| **Azure OpenAI** | gpt-4o, gpt-4-turbo | `PLANNER_PROVIDER=azure-openai` |
| **OpenAI** | gpt-4o, gpt-4-turbo | `PLANNER_PROVIDER=openai` |
| **Anthropic** | claude-3.5-sonnet | `PLANNER_PROVIDER=anthropic` |
| **Google** | gemini-1.5-pro | `PLANNER_PROVIDER=gemini` |

### Small Model Workers
| Backend | Models | Configuration |
|---------|--------|---------------|
| **Ollama** (Local) | phi3, llama3.2, mistral | `SMALL_MODEL_BACKEND=ollama` |
| **Azure AI Foundry** | Phi-3, Llama 3.2 | `SMALL_MODEL_BACKEND=azure` |
| **Transformers** (Local) | Any HuggingFace model | `SMALL_MODEL_BACKEND=transformers` |

## Samples

The `samples/` directory ships with 30+ runnable demos that match the PyPI package layout. Start with a few quick wins:

- Receipt basics: [Sample 01](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/01-basic-receipt-processing)
- Multi-step categorization: [Sample 02](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/02-receipt-with-categorization)
- Workflow library: [Sample 05](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/05-workflow-library)
- Code execution sandbox: [Sample 09](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/09-code-execution)
- Parallel agents with limits: [Sample 25](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/25-parallel-agents)

See the full catalog in the [samples README](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/README.md).

## Project Structure

```
ToolWeaver/
├── orchestrator/                    # Core package (public API)
│   ├── __init__.py                 # Public exports (@mcp_tool, search_tools, etc.)
│   ├── config.py                   # Configuration management
│   ├── plugins/                    # Plugin system
│   ├── selection/                  # Tool selection & cost optimization
│   ├── shared/                     # Shared models (ToolDefinition, etc.)
│   ├── skills/                     # Skill management
│   ├── tools/                      # Tool utilities (decorators, discovery, etc.)
│   │   ├── decorators.py          # @mcp_tool, @tool, @a2a_agent
│   │   ├── discovery_api.py       # search_tools(), get_available_tools()
│   │   ├── sub_agent.py           # dispatch_agents()
│   │   └── error_recovery.py      # Error handling
│   └── _internal/                  # Internal implementation (not public API)
│       ├── execution/              # Programmatic execution engine
│       ├── infra/                  # Infrastructure (MCP client, A2A client)
│       ├── workflows/              # Workflow execution
│       └── ...
├── tests/                           # Test suite (971/985 passing, 98.6%)
│   ├── test_tool_*.py
│   ├── test_*_integration.py
│   └── conftest.py
├── docs/                            # Documentation (published via MkDocs)
│   ├── get-started/               # Quick start
│   ├── tutorials/                 # Hands-on walkthroughs
│   ├── how-to/                    # Task-focused guides
│   ├── reference/                 # API and deep dives
│   └── deployment/                # Production deployment
├── samples/                        # Runnable samples that ship with the package
│   ├── 01-basic-receipt-processing/
│   ├── 02-receipt-with-categorization/
│   ├── 05-workflow-library/
│   ├── 09-code-execution/
│   └── ... (25+ more)
├── scripts/                         # Helper scripts
├── pyproject.toml                  # Package configuration
├── requirements.txt                # Dependencies
├── conftest.py                     # Pytest configuration
└── README.md                       # This file
```

## Requirements

- Python 3.8+
- pydantic
- asyncio (built-in)
- **Optional**: Azure Computer Vision for real OCR (see [setup guide](https://ushakrishnan.github.io/ToolWeaver/deployment/azure-setup/))

## Benefits

| Feature | Description |
|---------|-------------|
| **Safety** | Validated functions, sandboxed code execution |
| **Flexibility** | Dynamic transformations via code execution |
| **Reliability** | Deterministic tools for predictable operations |
| **Extensibility** | Easy to add new tools without core changes |
| **MCP-Compatible** | Mirrors Anthropic's Model Context Protocol design |

## Development Setup

### Prerequisites
- Python 3.8+
- Git
- (Optional) Docker for Redis/Qdrant

### Clone and Setup

```bash
git clone https://github.com/ushakrishnan/ToolWeaver.git
cd ToolWeaver

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# Install in editable mode
pip install -e .

# Or with all features
pip install -e ".[all]"
```

### Configure Environment

```bash
# Copy example environment
cp .env.example .env

# Edit .env with your credentials
# See https://ushakrishnan.github.io/ToolWeaver/reference/api-python/configuration/ for details
```

### Run Tests

```bash
pytest                           # Run all tests
pytest tests/test_tool_search.py # Specific test
```

### Project vs Package Usage

| Aspect | **Repo (editable)** | **PyPI install** |
|--------|---------------------|------------------|
| **Purpose** | Development/Contributing | Learning/Using |
| **Installation** | `pip install -e .` | `pip install toolweaver` |
| **Imports** | Local source code | Installed package |
| **Use When** | Modifying ToolWeaver | Building with ToolWeaver |
| **sys.path** | Modified | Not modified |

## Contributing

Contributions are welcome! 

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes in `samples/` or `orchestrator/`
4. Add tests for new functionality
5. Run `pytest` to ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

See [CONTRIBUTING.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/CONTRIBUTING.md) for detailed guidelines.

## License

Apache License 2.0 - See [LICENSE](https://github.com/ushakrishnan/ToolWeaver/blob/main/LICENSE) for details.

This package is open source and free to use. Apache 2.0 provides explicit patent protection and trademark rights.

## Acknowledgments

Inspired by [Anthropic's Model Context Protocol](https://modelcontextprotocol.io/)
