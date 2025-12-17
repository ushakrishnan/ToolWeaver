# ToolWeaver Examples

Complete showcase of ToolWeaver capabilities through real-world examples.

## 📚 Example Index

### Getting Started (Basic Usage)

#### [01-basic-receipt-processing](01-basic-receipt-processing/)
**Complexity:** ⭐ Basic | **Time:** 5 minutes  
**Demonstrates:** Basic tool execution, MCP workers, Azure Computer Vision

Simple OCR extraction from receipt images.

#### [02-receipt-with-categorization](02-receipt-with-categorization/)
**Complexity:** ⭐⭐ Intermediate | **Time:** 10 minutes  
**Demonstrates:** Multi-step workflows, small model workers, cost optimization

End-to-end receipt processing with categorization (98% cost savings).

#### [03-github-operations](03-github-operations/)
**Complexity:** ⭐⭐⭐ Advanced | **Time:** 15 minutes  
**Demonstrates:** Remote MCP servers, GitHub integration, 36+ tools

GitHub operations: list files, create issues/PRs, search code.

---

### Core Capabilities

#### [04-vector-search-discovery](04-vector-search-discovery/)
**Complexity:** ⭐⭐ Intermediate | **Time:** 10 minutes  
**Demonstrates:** Tool discovery, semantic search, token reduction (66-95%)

Automatically discover tools and use hybrid search to find relevant ones from large catalogs.

#### [05-workflow-library](05-workflow-library/)
**Complexity:** ⭐⭐ Intermediate | **Time:** 15 minutes  
**Demonstrates:** Workflow composition, dependency resolution, parallel execution

Create reusable workflow templates with automatic parallelization (25-40% speedup).

#### [06-monitoring-observability](06-monitoring-observability/)
**Complexity:** ⭐⭐ Intermediate | **Time:** 10 minutes  
**Demonstrates:** WandB integration, Prometheus metrics, cost tracking, error monitoring

Production-grade observability with real-time dashboards.

---

### Optimization Techniques

#### [07-caching-optimization](07-caching-optimization/)
**Complexity:** ⭐⭐ Intermediate | **Time:** 10 minutes  
**Demonstrates:** Redis caching, multi-layer cache strategies, 90% cost savings

Distributed caching for discovery, search, and results (87% faster, 90% cheaper).

#### [08-hybrid-model-routing](08-hybrid-model-routing/)
**Complexity:** ⭐⭐⭐ Advanced | **Time:** 15 minutes  
**Demonstrates:** Two-model architecture, 80-90% cost reduction, intelligent routing

GPT-4 for planning, Phi-3 for execution (98.7% cost savings at scale).

#### [09-code-execution](09-code-execution/)
**Complexity:** ⭐⭐ Intermediate | **Time:** 10 minutes  
**Demonstrates:** Sandboxed Python execution, security features, dynamic operations

Safe code execution for custom logic without predefined tools.

---

### Advanced Orchestration

#### [10-multi-step-planning](10-multi-step-planning/)
**Complexity:** ⭐⭐⭐ Advanced | **Time:** 15 minutes  
**Demonstrates:** LLM-generated plans, DAG construction, conditional execution

Natural language → executable plans with automatic parallelization.

#### [11-programmatic-executor](11-programmatic-executor/)
**Complexity:** ⭐⭐⭐ Advanced | **Time:** 15 minutes  
**Demonstrates:** Programmatic workflows, context management, batch processing

Keep intermediate results out of LLM context for large-scale processing.

#### [12-sharded-catalog](12-sharded-catalog/)
**Complexity:** ⭐⭐⭐ Advanced | **Time:** 15 minutes  
**Demonstrates:** Sharded catalogs, sub-linear scaling, 1000+ tools

Scale to thousands of tools with constant search performance.

## 🚀 Quick Start

Each example is self-contained with:
- **README.md** - What it does, setup, run instructions
- **.env** / **.env.example** - Configuration templates
- **Python script** - Working code with detailed comments

```bash
# Navigate to any example
cd 01-basic-receipt-processing

# Setup
cp .env.example .env
# Edit .env with your API keys

# Run
python process_receipt.py
```

## 📖 Recommended Learning Paths

### Path 1: Quick Start (30 minutes)
For those who want to see basic functionality:
1. **01-basic-receipt-processing** - Understand basic execution
2. **02-receipt-with-categorization** - Learn multi-step workflows
3. **04-vector-search-discovery** - See tool discovery in action

### Path 2: Production Ready (1-2 hours)
For those building production systems:
1. **01, 02, 03** - Master the basics
2. **06-monitoring-observability** - Set up monitoring
3. **07-caching-optimization** - Reduce costs
4. **08-hybrid-model-routing** - Optimize model selection

### Path 3: Advanced Orchestration (2-3 hours)
For complex workflow scenarios:
1. **05-workflow-library** - Reusable patterns
2. **10-multi-step-planning** - Auto-generated plans
3. **11-programmatic-executor** - Large-scale processing
4. **12-sharded-catalog** - Scale to 1000+ tools

### Path 4: Full Tour (4+ hours)
Complete understanding of all capabilities:
- Do all 12 examples in order
- Each builds on previous concepts
- Covers all ToolWeaver features

## 🎯 Use Case Examples

**Need to...**
- Process images? → Start with **01** or **02**
- Integrate with GitHub? → See **03**
- Scale to many tools? → Try **04** and **12**
- Reduce costs? → Check **07** and **08**
- Monitor production? → Use **06**
- Build complex workflows? → Explore **05**, **10**, **11**
- Execute custom code? → Look at **09**

---

## Legacy Demo Applications (Unstructured)

### run_demo.py
**Complete orchestrator demo** - Execute predefined execution plans

**Usage**:
```bash
python examples/run_demo.py
```

**What it shows**:
- Hybrid orchestration (MCP workers + function calls + code execution)
- DAG-based execution with dependencies
- Receipt OCR → parsing → tax calculation workflow
- Uses `example_plan.json` and `example_plan_hybrid.json`

### run_planner_demo.py
**Two-model architecture demo** - Generate and execute plans from natural language

**Usage**:
```bash
python examples/run_planner_demo.py "Calculate tax on grocery receipt"
```

**What it shows**:
- Large model (GPT-4o/Claude) generates execution plans
- Small models (Phi-3/Llama) execute specific tasks
- Hybrid orchestrator manages DAG execution
- Full natural language → plan → execution pipeline

---

## Example Data Files

### example_plan.json
Sample execution plan for receipt processing workflow:
1. OCR image
2. Parse line items
3. Calculate tax

### example_plan_hybrid.json
Advanced execution plan demonstrating:
- Parallel execution
- Function calls (compute_tax)
- Code execution (filter operations)
- Complex dependencies

---

## Quick Start Examples

### Basic Usage
- **usage_examples.py** - Simple examples of tool registration and execution

### Discovery & Search
- **test_discovery.py** - Tool discovery validation (discovers 14 tools)
- **test_search.py** - Semantic search demo (6 queries with relevance scores)
- **demo_auto_discover.py** - Automatic tool discovery integration

### Advanced Features
- **demo_integrated.py** - Full pipeline: discovery → search → planning (30 tools)
- **demo_tool_examples.py** - Tool usage examples showing 72% → 90%+ accuracy improvement

### Testing Connection
- **test_azure_connection.py** - Verify Azure OpenAI connection and credentials

## Running Examples

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Run any example
python examples/demo_integrated.py
python examples/test_discovery.py
python examples/demo_tool_examples.py
```

## What Each Example Demonstrates

| Example | Features | Output |
|---------|----------|--------|
| **run_demo.py** | Hybrid orchestration, DAG execution | Full receipt workflow |
| **run_planner_demo.py** | Two-model architecture, NL → plan | Complete pipeline demo |
| **usage_examples.py** | Basic tool registration, function decorators | Tool catalog operations |
| **test_discovery.py** | Automatic tool discovery, caching | 14 tools discovered in 1ms |
| **test_search.py** | Semantic search, relevance scoring | Top 10 tools for 6 queries |
| **demo_auto_discover.py** | Full discovery orchestration | Complete tool catalog |
| **demo_integrated.py** | Discovery + search + planning | 3-step receipt processing |
| **demo_tool_examples.py** | Tool examples, parameter accuracy | Cost-benefit analysis |
| **test_azure_connection.py** | Azure AD authentication | Connection validation |

## Requirements

All examples require:
- Python 3.11+
- Virtual environment activated
- Environment variables configured (see `.env.example`)
- Azure OpenAI credentials (for planning examples)

Optional for semantic search examples:
- sentence-transformers
- rank-bm25
- torch
- scikit-learn

See main [requirements.txt](../requirements.txt) for complete dependencies.
