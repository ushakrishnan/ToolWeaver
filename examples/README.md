# ToolWeaver Examples

Real-world examples demonstrating ToolWeaver capabilities with increasing complexity.

## 📚 Structured Examples (Start Here!)

### [01-basic-receipt-processing](01-basic-receipt-processing/)
**Complexity:** ⭐ Basic  
**Time:** 5 minutes

Simple OCR extraction from receipt images using Azure Computer Vision.

**What You'll Learn:**
- Basic execution plans
- MCP workers
- Orchestrator execution

### [02-receipt-with-categorization](02-receipt-with-categorization/)
**Complexity:** ⭐⭐ Intermediate  
**Time:** 10 minutes

End-to-end receipt processing: OCR → Parse → Categorize → Statistics.

**What You'll Learn:**
- Multi-step workflows
- Step dependencies
- Small model workers (Phi-3)
- Function calls
- Cost optimization (98% savings vs GPT-4o)

### [03-github-operations](03-github-operations/)
**Complexity:** ⭐⭐⭐ Advanced  
**Time:** 15 minutes

GitHub operations using remote MCP server: list files, create issues, PRs, search code.

**What You'll Learn:**
- Remote MCP servers
- GitHub integration
- SSE protocol
- Token authentication
- 36+ GitHub tools

## 🚀 Quick Start

Each example is self-contained with:
- **README.md** - What it does, setup, run instructions
- **.env** - Minimal configuration (only what's needed)
- **Python script** - Working code with comments

```bash
# Navigate to any example
cd 01-basic-receipt-processing

# Follow the README
cat README.md

# Run
python process_receipt.py
```

## 📖 Learning Path

1. Start with **01-basic** to understand execution plans
2. Move to **02-receipt-with-categorization** for multi-step workflows
3. Try **03-github-operations** for external integrations

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
