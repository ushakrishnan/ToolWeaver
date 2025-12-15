# Hybrid Orchestrator with Two-Model Architecture

A production-ready orchestrator for AI agent workflows featuring a **two-model architecture**: large models (GPT-4o, Claude) for planning and small models (Phi-3, Llama) for efficient execution. Supports **three types of tools** through a unified interface: MCP workers, structured function calls, and sandboxed code execution.

## What Does This Do?

### 🎓 Simple Explanation
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

### 🔬 Technical Explanation
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

## Features

### Two-Model Architecture
- **🧠 Large Model Planner** - GPT-4o or Claude generates execution plans from natural language
- **🤖 Small Model Workers** - Phi-3/Llama for parsing, classification (local or cloud)
- **💰 Cost Optimization** - 80-90% cost reduction vs large-model-only
- **⚡ Speed** - Small models run 2-3x faster for routine tasks

### Dynamic Tool Discovery (Phase 1 - Complete ✅)
- **📦 ToolCatalog** - Centralized tool definition management with JSON Schema validation
- **🔄 Backward Compatible** - Existing code works without changes
- **🎯 Multi-Provider Support** - OpenAI, Azure OpenAI (with Azure AD), Anthropic, Gemini
- **🔍 Semantic Search Ready** - `available_tools` parameter for Phase 3 tool filtering
- **🔧 Flexible Tool Injection** - Custom catalogs, default catalog, or search results

### Orchestration Engine
- **🎯 Hybrid Tool Dispatch** - Seamlessly route between MCP, function calls, and code execution
- **🔒 Type Safety** - Full Pydantic validation for all inputs and outputs
- **⚡ Parallel Execution** - Automatic dependency resolution and concurrent step execution
- **🔄 Retry Logic** - Configurable retry policies with exponential backoff
- **🔐 Sandboxed Code** - Isolated process execution with safe builtins
- **📝 Function Registry** - Easy function registration via decorators
- **🔑 Idempotency** - Built-in idempotency key support

## Quick Start

### Option 1: Pre-Defined Plans (No LLM Required)

```bash
# Clone and setup
git clone <your-repo-url>
cd CodeExec
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# Install core dependencies
pip install -r requirements.txt

# Run demo with existing plans
python run_demo.py
```

### Option 2: Natural Language Planning (Requires LLM API Key)

```bash
# Install LLM dependencies
pip install openai anthropic

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

### Option 3: With Small Model Workers

**Option 3A: Ollama (Local - Free)**
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

**Option 3B: Azure AI Foundry (Cloud - Managed)**
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

## Phase 1: Dynamic Tool Discovery (✅ Complete)

### ToolCatalog Architecture

The planner now uses a **ToolCatalog** system for flexible tool management:

```python
from orchestrator.models import ToolCatalog, ToolDefinition, ToolParameter
from orchestrator.planner import LargePlanner

# Option 1: Use default catalog (backward compatible)
planner = LargePlanner(provider="azure-openai")
plan = await planner.generate_plan("Process receipt...")

# Option 2: Custom catalog
catalog = ToolCatalog(source="my_tools", version="1.0")
catalog.add_tool(ToolDefinition(
    name="custom_analyzer",
    type="mcp",
    description="Analyze custom data",
    parameters=[
        ToolParameter(name="data", type="object", description="Input data", required=True)
    ]
))

planner = LargePlanner(provider="azure-openai", tool_catalog=catalog)
plan = await planner.generate_plan("Analyze this data...")

# Option 3: With semantic search (Phase 3 - Coming Soon)
search_results = tool_search.search("receipt processing", top_k=10)
plan = await planner.generate_plan("Process receipt...", available_tools=search_results)
```

**Key Features:**
- **Backward Compatible** - Existing code works without changes
- **Type Safe** - Full Pydantic validation with JSON Schema support
- **Multi-Provider** - Converts to OpenAI/Anthropic/Gemini formats automatically
- **Search Ready** - `available_tools` parameter for dynamic tool filtering (Phase 3)

See [MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) for upgrading existing code.

## Documentation

- **[Configuration Guide](docs/CONFIGURATION.md)** - Complete setup for all providers (Azure OpenAI, OpenAI, Claude, Gemini, Ollama, Azure AI Foundry)
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - Upgrade to Phase 1 ToolCatalog architecture
- **[Two-Model Architecture](docs/TWO_MODEL_ARCHITECTURE.md)** - Why two models? Cost comparison, use cases
- **[Dynamic Tool Discovery Implementation](docs/DYNAMIC_TOOL_DISCOVERY_IMPLEMENTATION.md)** - Phase 1-5 implementation plan
- [Architecture Details](docs/ARCHITECTURE.md) - Technical deep dive into orchestrator design
- [Implementation Summary](docs/IMPLEMENTATION.md) - Development details and metrics
- [Azure Computer Vision Setup](docs/AZURE_SETUP.md) - Configure real OCR with Azure CV

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

## Examples

Run the demo with example plans:

```bash
# Run all examples
python run_demo.py

# Run specific plan
python run_demo.py example_plan.json
python run_demo.py example_plan_hybrid.json
```

## Project Structure

```
CodeExec/
├── orchestrator/           # Core orchestration engine
│   ├── orchestrator.py    # Main execution engine
│   ├── hybrid_dispatcher.py  # Tool routing
│   ├── functions.py       # Registered functions
│   ├── workers.py         # MCP workers
│   ├── code_exec_worker.py   # Code execution
│   ├── mcp_client.py      # MCP client
│   └── models.py          # Pydantic models
├── docs/                  # Documentation
├── example_plan.json      # Example: MCP + code-exec
├── example_plan_hybrid.json  # Example: All tool types
└── run_demo.py           # Demo script
```

## Requirements

- Python 3.8+
- pydantic
- asyncio (built-in)
- **Optional**: Azure Computer Vision for real OCR (see [setup guide](docs/AZURE_SETUP.md))

## Benefits

| Feature | Description |
|---------|-------------|
| **Safety** | Validated functions, sandboxed code execution |
| **Flexibility** | Dynamic transformations via code execution |
| **Reliability** | Deterministic tools for predictable operations |
| **Extensibility** | Easy to add new tools without core changes |
| **MCP-Compatible** | Mirrors Anthropic's Model Context Protocol design |

## Contributing

Contributions are welcome! Please see the documentation for architecture details and coding guidelines.

## License

[Your License Here]

## Acknowledgments

Inspired by [Anthropic's Model Context Protocol](https://modelcontextprotocol.io/)
