# ToolWeaver Samples (PyPI)

> **\ud83d\udc64 New User?** See [samples/](../samples/) for ready-to-run examples using the installed package.  
> **\ud83d\udccc Current status:** PyPI package refresh is in progress; treat `examples/` as the canonical, up-to-date source. We'll regenerate `samples/` after the package is finalized.
> **\ud83d\udee0\ufe0f For Developers:** Use `examples/` to work against local source.  
> **\ud83d\udc64 End Users:** These samples run against the published package `toolweaver==0.5.0`.  
> **\ud83d\udccc Status:** Samples mirror `examples/` and import the installed package (no local path hacks).

Complete showcase of ToolWeaver capabilities through real-world scenarios using the installed package.
➡️ **Status:** Mirrored from `examples/`; see [EXAMPLES_TESTING_REPORT.md](../docs/internal/EXAMPLES_TESTING_REPORT.md) for validated runs.

## \ud83d\udd04 Examples vs Samples

| Feature | **examples/** (Here) | **[samples/](../samples/)** |
|---------|---------------------|---------------------------|
| **For** | Contributors & Developers | End Users |
| **Requires** | `git clone` + `pip install -e .` | `pip install toolweaver==0.5.0` |
| **Imports** | From local source | From installed package |
| **Modify** | Yes - edit source directly | No - use as reference |
| **Use When** | Contributing to ToolWeaver | Building with ToolWeaver |

## \ud83d\ude80 Quick Start

**New to ToolWeaver?** Start with [Example 13: Complete End-to-End Pipeline](13-complete-pipeline/) for a full demonstration of all features in action.

### Setup

```bash
# Clone and install the published package (pinned to the deployed release)
git clone https://github.com/ushakrishnan/ToolWeaver.git
cd ToolWeaver
pip install toolweaver==0.5.0

# Navigate to a sample
cd samples/01-basic-receipt-processing

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run
python process_receipt.py
```

## 📚 Example Index

### ⭐ Featured: Complete End-to-End

#### [13-complete-pipeline](13-complete-pipeline/)
**Complexity:** ⭐⭐⭐ Advanced | **Time:** 20 minutes  
**Demonstrates:** ALL ToolWeaver features in production-ready pipeline

Complete demonstration: discovery, search, caching, monitoring, hybrid models, workflows, code execution, and batch processing. Shows 95% cost reduction and 10x speedup.

---

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

### New Advanced Scenarios

#### [19-fetch-analyze-store](19-fetch-analyze-store/)
**Complexity:** ⭐⭐ Intermediate | **Time:** 10 minutes  
**Demonstrates:** Tool → agent → tool hybrid flow with streaming analysis and cost logging.

#### [20-approval-workflow](20-approval-workflow/)
**Complexity:** ⭐⭐⭐ Advanced | **Time:** 10 minutes  
**Demonstrates:** Multi-agent draft/validate, human approval gate, deterministic finalize.

#### [21-error-recovery](21-error-recovery/)
**Complexity:** ⭐⭐⭐ Advanced | **Time:** 10 minutes  
**Demonstrates:** Self-healing flow: fail → diagnose agent → remediate → retry.

#### [22-end-to-end-showcase](22-end-to-end-showcase/)
**Complexity:** ⭐⭐⭐ Advanced | **Time:** 10 minutes  
**Demonstrates:** Complete pipeline combining tools, agents, and skill library reuse.

#### [23-adding-new-tools](23-adding-new-tools/) ⭐ NEW
**Complexity:** ⭐⭐⭐ Advanced | **Time:** 15 minutes  
**Demonstrates:** End-to-end guide for adding new custom tools (MCP and A2A) to the catalog and discovering them.

Complete demonstration of:
- Creating custom MCP tools with proper schemas
- Implementing tool workers (weather, stock price)
- Registering tools with MCPClientShim
- Defining A2A agent capabilities
- Unified discovery (MCP tools + A2A agents in one catalog)
- Tool metadata and LLM format conversion

See [docs/how-it-works/programmatic-tool-calling/](../docs/how-it-works/programmatic-tool-calling/) for deep dive on how tools work programmatically.

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

### Path 0: Overview (20 minutes) ⭐ NEW
Want to see everything at once?
1. **13-complete-pipeline** - All features in one demo

### Path 1: Quick Start (30 minutes)
For those who want to see basic functionality:
1. **01-basic-receipt-processing** - Understand basic execution
2. **02-receipt-with-categorization** - Learn multi-step workflows
3. **04-vector-search-discovery** - See tool discovery in action

### Path 2: Production Ready (1-2 hours)
For those building production systems:
1. **13-complete-pipeline** - See the full picture first
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
- Start with **13-complete-pipeline** to understand the big picture
- Then do examples 01-12 for deep dives into each feature
- Each builds on previous concepts

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

## Legacy Demo Applications

Located in [`legacy-demos/`](legacy-demos/) folder for backward compatibility.

### Main Demos

**`run_demo.py`** - Complete orchestrator demo
- Execute predefined execution plans
- Hybrid orchestration (MCP workers + function calls + code execution)
- Uses `example_plan.json` and `example_plan_hybrid.json`

**`run_planner_demo.py`** - Two-model architecture demo
- Natural language → plan → execution pipeline
- Large model (GPT-4o) generates plans, small models (Phi-3) execute

### Testing & Discovery

**`test_discovery.py`** - Tool discovery validation  
**`test_search.py`** - Semantic search demo  
**`test_azure_connection.py`** - Azure CV connection test  
**`test_github_mcp.py`** - GitHub MCP server test  
**`test_monitoring_integration.py`** - Monitoring backends test  

### Additional Demos

**`demo_auto_discover.py`** - Automatic tool discovery  
**`demo_integrated.py`** - Integrated orchestrator example  
**`demo_monitoring_backends.py`** - Monitoring backends showcase  
**`demo_tool_examples.py`** - Tool registration examples  
**`demo_workflow.py`** - Workflow execution examples  
**`usage_examples.py`** - Basic usage patterns  

### Usage

```bash
# Run from examples directory
cd examples/legacy-demos
python run_demo.py
python run_planner_demo.py "Calculate tax on grocery receipt"
```

---

## Additional Resources
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
python examples/legacy-demos/demo_integrated.py
python examples/legacy-demos/test_discovery.py
python examples/legacy-demos/demo_tool_examples.py
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

## Testing Examples

Run the comprehensive test suite to validate all examples:

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/Mac

# Run validation
cd examples
python test_all_examples.py
```

See [EXAMPLES_TESTING_REPORT.md](../docs/internal/EXAMPLES_TESTING_REPORT.md) for detailed test results.

## Requirements

All samples require:
- Python 3.10+
- Virtual environment activated
- Core dependencies: `pip install toolweaver==0.5.0`
- Environment variables configured (see each example's `.env.example`)

Optional dependencies for advanced features (if available for this version):
- WandB, Redis, Qdrant: `pip install "toolweaver[all]==0.5.0"`

See main [requirements.txt](../requirements.txt) for complete dependencies.
