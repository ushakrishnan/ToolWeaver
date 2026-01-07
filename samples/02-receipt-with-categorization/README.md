# Example 2: Receipt with Categorization

## What This Does

Demonstrates the **execution phase** of ToolWeaver's two-model orchestration:

- **Tool Registration**: Multiple tools with `@mcp_tool` decorator
- **Workflow Composition**: Chaining tools with data flow (OCR → Parser → Categorizer → Stats)
- **Execution Context**: Each tool passes results to the next
- **Practical Example**: Real-world receipt processing workflow

**Key Insight**: This is the **second half** of the two-model architecture (the execution part).
The first half (planning with LargePlanner) converts natural language to execution plans.
This sample shows what happens when the orchestrator **executes** those plans.

**Complexity:** ⭐⭐ Intermediate  
**Concepts:** Tool chaining, orchestration, multi-step workflows, execution context  
**Time:** 10 minutes

## What You'll Learn

- How to build multi-step workflows with `@mcp_tool`
- Tool chaining and data passing between steps
- Orchestrator execution model (what happens after LargePlanner generates plans)
- Building realistic business processes from modular tools

## The ToolWeaver Two-Model Architecture

ToolWeaver separates **planning** from **execution** to reduce costs 80-90%:

```
USER REQUEST
    ↓
[1] LARGE MODEL PLANNER (GPT-4o/Claude)
    • Understands intent
    • Discovers available tools
    • Generates execution plan (DAG)
    • Cost: ~$0.002 per request
    ↓
EXECUTION PLAN (JSON with steps and dependencies)
    ↓
[2] ORCHESTRATOR (ToolWeaver)
    • Executes each step ← (THIS IS SAMPLE 02)
    • Handles dependencies & parallelization
    • Routes to appropriate workers
    • Caches results
    ↓
[3] SMALL WORKERS (Phi-3, APIs, deterministic tools)
    • Parse items, classify, validate
    • Cost: ~$0.001 per tool call
    • Many calls, very cheap
```

### Why This Matters

**Without ToolWeaver** (all large model):
```
✗ 1 LLM call to plan: $0.002
✗ 1 LLM call per tool: $0.02 × 4 = $0.08
✗ Total: $0.10 per receipt
✗ Large model sees all intermediate data (bloat)
```

**With ToolWeaver** (this sample):
```
✓ 1 LLM call to plan: $0.002
✓ 4 deterministic tool calls: $0.001 × 4 = $0.004
✓ Total: $0.006 per receipt
✓ 94% cheaper per request
✓ Large model never sees intermediate receipts
```

**This sample focuses on step [2] above** - the orchestrator executing tools.

## How This Connects to Planning & LargePlanner

**The Planning Phase** (generates execution plans from natural language):
```python
# What LargePlanner does - converts user request to execution plan
from orchestrator import LargePlanner

planner = LargePlanner(provider="azure-openai", model="gpt-4o")
plan = await planner.generate_plan(
  "Process receipt, extract items, categorize, compute stats"
)
# Returns a JSON plan with steps, dependencies, tool references, etc.
# Cost: ~$0.002 (one large model call)
```

**The Execution Phase** (THIS IS THIS SAMPLE):
```python
# What the Orchestrator does - executes the plan efficiently
from orchestrator import execute_plan

context = await execute_plan(plan)
# • Executes steps in dependency order
# • Can parallelize independent steps
# • Passes data between steps automatically
# • Handles errors and retries
# • Caches results
```

**In this sample**, we demonstrate the **execution** part directly by calling tools in sequence.
In production, you'd:
1. Use `LargePlanner` to generate plans from user requests (1 call, expensive)
2. Use `execute_plan()` to run those plans (many calls, cheap)
3. ToolWeaver orchestrates everything automatically

**The Cost Benefit**: Large model plans once ($0.002), small tools execute many times ($0.001 each) = **94% cheaper**

## Prerequisites

- Python 3.10+
- This sample (planning + orchestration + W&B monitoring) ⇒ install the monitoring extra

## Setup

**🎯 Package First Approach** (always from PyPI, in `.venv`):

```bash
# Full install for this sample: Azure + monitoring backends (wandb)
pip install toolweaver[azure,monitoring]

# If you only want mock OCR and local logging:
pip install toolweaver
```

**Verify Installation:**
```bash
# Confirm you're using the installed package (not local dev code)
python -c "import orchestrator; print('✅ Version:', orchestrator.__version__); print('📦 Location:', orchestrator.__file__)"
```

Expected output should show `site-packages`:
```
✅ Version: 0.13.6
📦 Location: /path/to/site-packages/orchestrator/__init__.py
```

**Configuration:**

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

The `.env` file controls OCR mode (defaults to mock):
```bash
# ✅ Default: Use mock OCR (no credentials needed, instant testing)
USE_MOCK_OCR=true

# 🔄 To switch to real Azure Computer Vision OCR when ready:
USE_MOCK_OCR=false
AZURE_CV_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_CV_KEY=your-api-key

# For large model planning (fill with your credentials; do not commit secrets)
PLANNER_PROVIDER=azure-openai
PLANNER_MODEL=gpt-4o
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
```

## Run

This sample includes **3 progressive demos** showing different orchestration patterns:

### 1. Basic Multi-Step Orchestration

```bash
cd samples/02-receipt-with-categorization
python categorize_receipt.py
```

**What it does:**
- Registers 4 tools with `@mcp_tool` decorator
- Chains them sequentially: OCR → Parser → Categorizer → Statistics
- Best for learning tool composition and data flow

**Output:** Console display of results

**Time:** ~1 second with mock OCR

---

### 2. Pre-Generated Plan Execution

```bash
python categorize_receipt_orchestrated.py
```

**What it does:**
- Executes a **static DAG** (no large model planning)
- Shows the orchestrator + execution engine in action
- Monitors each tool with W&B (Weights & Biases)
- All results saved to `execution_outputs/` folder

**Output:**
- Console + W&B tracking dashboard
- Files in `execution_outputs/`:
  - `results_TIMESTAMP.json` - Execution results and metrics

**Time:** ~1 second with mock OCR

---

### 3. End-to-End with Large Model Planning ⭐ (Recommended)

```bash
python categorize_receipt_end_to_end.py
```

**The Complete Pipeline:**

```
┌─────────────────────────────────────────────────────────┐
│ PHASE 1: PLANNING (Large Model Design)                 │
│ ┌──────────────────────────────────────────────────┐   │
│ │ GPT-4o reads: "Process grocery store receipt"   │   │
│ │ GPT-4o generates: 4-step execution plan (DAG)   │   │
│ │ Plan saved → plan_TIMESTAMP.json                │   │
│ │ Cost: $0.002                                     │   │
│ └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 2: EXECUTION (Sandbox + Orchestrator)            │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Sandbox created: max 30s, 512MB memory           │   │
│ │ Step 1: receipt_ocr (extract text)              │   │
│ │ Step 2: line_item_parser (parse items)          │   │
│ │ Step 3: expense_categorizer (categorize)        │   │
│ │ Step 4: compute_statistics (calculate totals)   │   │
│ │ W&B tracks: latency, success, errors            │   │
│ │ Total: ~175ms end-to-end                        │   │
│ │ Cost: $0.00 (tools are deterministic)           │   │
│ └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 3: STORAGE (Audit Trail + Results)               │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Artifacts saved to execution_outputs/            │   │
│ │ • plan_TIMESTAMP.json (1.2 KB)                  │   │
│ │ • results_TIMESTAMP.json (3 KB)                 │   │
│ │ • items_TIMESTAMP.json (for downstream)         │   │
│ │ • manifest.json (execution history)             │   │
│ │ Cost: $0.002 total                              │   │
│ └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**How to run with all credentials:**

```bash
# Ensure .env has planner credentials:
PLANNER_PROVIDER=azure-openai
PLANNER_MODEL=gpt-4o
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...

python categorize_receipt_end_to_end.py
```

**Output Files in `execution_outputs/`:**

```
execution_outputs/
├── example_plan.json              # Reference template
├── plan_20260107_154037.json      # Generated plan (GPT-4o design)
├── results_20260107_154037.json   # Execution results + context
├── items_20260107_154037.json     # Detailed item breakdown
└── manifest.json                  # Execution history across all runs
```

**Sample manifest.json:**
```json
{
  "20260107_154037": {
    "timestamp": "2026-01-07T15:40:37",
    "success": true,
    "plan_file": "plan_20260107_154037.json",
    "results_file": "results_20260107_154037.json",
    "items_file": "items_20260107_154037.json",
    "statistics": {
      "total_amount": 47.42,
      "item_count": 7,
      "avg_amount": 6.77,
      "categories": {
        "food": {"total": 30.43, "percentage": 64.2, "count": 5},
        "household": {"total": 13.48, "percentage": 28.4, "count": 2}
      }
    }
  }
}
```

**W&B Monitoring:**
```
Tracking run: production-run-1
├── receipt_ocr: 0ms
├── line_item_parser: 114ms
├── expense_categorizer: 60ms
└── compute_statistics: 0.3ms
Total: 175ms | Success: 100%
```

**Time:** ~3 seconds (includes large model planning call)

## Key Features Demonstrated

### 1. Mock OCR by Default
All demos start with **mock OCR** (no credentials needed):
```python
use_mock = os.getenv("USE_MOCK_OCR", "true").lower() == "true"
```

**Easy switch when ready:**
```env
USE_MOCK_OCR=false
AZURE_CV_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_CV_KEY=your-api-key
```

No code changes needed—the same demos automatically use real OCR.

### 2. Execution Artifacts & Audit Trail
Every run generates timestamped files:
- `plan_YYYYMMDD_HHMMSS.json` - What GPT-4o decided to do
- `results_YYYYMMDD_HHMMSS.json` - What actually happened + all intermediate data
- `items_YYYYMMDD_HHMMSS.json` - Detailed item breakdown for BI/reporting
- `manifest.json` - Cumulative execution log (gets appended on each run)

**Why this matters:**
- **Reproducibility:** Every execution is logged with exact plan + results
- **Debugging:** See exactly what the large model planned vs. what actually executed
- **Batch Processing:** Run multiple receipts, check manifest for status
- **Compliance:** Full audit trail for financial/processing applications

### 3. Sandbox Execution with Resource Limits
The end-to-end demo creates an isolated sandbox:
```python
limits = ResourceLimits(
    max_duration=30.0,      # 30 second timeout (prevent infinite loops)
    max_memory_mb=512,      # 512 MB limit
    allow_network=True,     # Allow MCP calls
    allow_file_io=False     # No file I/O
)
```

**Security guarantees:**
- No `eval()` or `exec()` access
- No file system access
- No direct network access (only via tools)
- Timeout enforcement prevents hangs

### 4. W&B Monitoring Integration
End-to-end demo automatically tracks with Weights & Biases:
- Tool execution latency
- Success/error rates
- Execution step history
- Cost tracking
- All visible in W&B dashboard

### 5. Large Model Planning (Phase 1)
End-to-end demo calls GPT-4o to:
- **Parse natural language** request
- **Discover available tools** automatically
- **Design optimal DAG** with dependencies
- **Save plan as JSON** for audit trail

Example plan generated by GPT-4o:
```json
{
  "request_id": "unique-id-123",
  "steps": [
    {"id": "step-1", "tool": "receipt_ocr", "depends_on": []},
    {"id": "step-2", "tool": "line_item_parser", "depends_on": ["step-1"]},
    {"id": "step-3", "tool": "expense_categorizer", "depends_on": ["step-2"]},
    {"id": "step-4", "tool": "compute_statistics", "depends_on": ["step-3"]}
  ]
}
```

## Architecture Comparison

| Aspect | Traditional LLM | ToolWeaver (This Sample) |
|--------|-----------------|------------------------|
| **Planning** | Manual hardcoding | Large model designs DAG |
| **Execution** | Sequential, blocking | Orchestrator + sandbox |
| **Isolation** | None | Sandbox with resource limits |
| **Monitoring** | Manual logging | W&B integration |
| **Audit Trail** | Minimal | Full plan + results on disk |
| **Cost per receipt** | ~$0.10 | ~$0.002 (98% savings!) |
| **Latency** | 5-8 seconds | 175ms (end-to-end) |
| **Scale** | 1 receipt/call | Parallel-ready |

## Code Walkthrough

### Register Multiple Tools
```python
from orchestrator import mcp_tool

@mcp_tool(domain="receipts", description="Extract text from receipt images")
async def receipt_ocr(image_uri: str) -> dict:
    """Extract text from receipt image (mock by default, real OCR when configured)."""
    use_mock = os.getenv("USE_MOCK_OCR", "true").lower() == "true"
    
    if not use_mock:
        # Use real Azure Computer Vision OCR
        try:
            from orchestrator.dispatch.workers import receipt_ocr_worker
            result = await receipt_ocr_worker({"image_uri": image_uri})
            return {"text": result["text"], "confidence": result.get("confidence", 0.95)}
        except Exception as e:
            print(f"⚠️  Real OCR failed: {e}. Falling back to mock mode.")
    
    # Mock mode - returns realistic test data
    return {
        "text": "GROCERY MART\nMilk 2% $3.99\n...",
        "confidence": 0.96
    }
```

### Create Sandbox for Safe Execution
```python
from orchestrator import SandboxEnvironment, ResourceLimits

limits = ResourceLimits(
    max_duration=30.0,      # 30 second timeout
    max_memory_mb=512,      # 512 MB memory limit
    allow_network=True,     # Allow MCP calls to tools
    allow_file_io=False     # No file I/O
)

sandbox = SandboxEnvironment(limits=limits)
# Sandbox validates code safety before execution
# Enforces resource limits with timeouts
# Captures stdout/stderr
```

### Execute with Large Model Planning
```python
from orchestrator import LargePlanner, execute_plan

# Phase 1: Large model designs plan
planner = LargePlanner(provider="azure-openai", model="gpt-4o")
plan = await planner.generate_plan(
    user_request="Process a receipt from a grocery store",
    available_tools=tools[:10]
)

# Phase 2: Orchestrator executes plan
context = await execute_plan(plan)

# Phase 3: Save artifacts
with open(f"results_{timestamp}.json", "w") as f:
    json.dump({"plan": plan, "context": context}, f, indent=2)
```

### Data Flow Through Steps
```
Step 1 Output ──→ Step 2 Input (via "step:step-1" reference)
                        ↓
Step 2 Output ──→ Step 3 Input (via "step:step-2" reference)
                        ↓
Step 3 Output ──→ Step 4 Input (via "step:step-3" reference)
                        ↓
Step 4 Output ──→ Final Results (saved to JSON)
```

## Configuration Reference

### Environment Variables
| Variable | Default | Purpose |
|----------|---------|---------|
| `USE_MOCK_OCR` | `true` | Use mock data (true) or Azure CV (false) |
| `AZURE_CV_ENDPOINT` | - | Azure Computer Vision endpoint URL |
| `AZURE_CV_KEY` | - | Azure Computer Vision API key |
| `AZURE_USE_AD` | `false` | Use Azure AD authentication instead of API key |
| `OCR_MODE` | `azure` | OCR provider ('mock' or 'azure') |

## Troubleshooting

### ❌ ImportError: No module named 'orchestrator'
```bash
# Install the package first
pip install toolweaver
```

### ❌ Using local dev code instead of package
```bash
# Uninstall editable install, reinstall from PyPI
pip uninstall -y toolweaver
pip install toolweaver
```

### ❌ "Planning failed" or planner errors
This usually means Azure OpenAI credentials are not set. For demos 1-2, this is OK—they work without planner.

For demo 3 (end-to-end), you need:
```bash
PLANNER_PROVIDER=azure-openai
PLANNER_MODEL=gpt-4o
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

If not set, demo 3 falls back to a hardcoded plan automatically.

### ❌ W&B login issues
```bash
# Offline mode if W&B API is unavailable
wandb offline

# Or skip W&B monitoring by removing from .env
# (unset WANDB_* variables)
```

### ❌ Tools not registering
- Verify imports: `from orchestrator import mcp_tool`
- Check logs for "Tool registered: {name}" messages
- Ensure async function signatures: `async def tool_name(param: type) -> dict`
- All tool parameters must be JSON-serializable (dict, list, str, int, float, bool)

### ❌ Sandbox timeout (execution > 30s)
- Default sandbox timeout: 30 seconds
- To change: edit `ResourceLimits(max_duration=60.0)` in the script
- Mock mode should be <200ms; real OCR may need longer timeout

### ❌ Results not saving
- Check that `execution_outputs/` folder exists
- Ensure write permissions in the sample directory
- Check disk space
- Verify `.gitkeep` file is present (preserves folder structure)

## Understanding the Output Folder

All execution artifacts go to `execution_outputs/`:

```
execution_outputs/
├── .gitkeep                    # Preserves empty folder in git
├── README.md                   # This documentation
├── example_plan.json           # Reference template (do not modify)
├── manifest.json               # ← Execution log (gets updated each run)
├── plan_20260107_154037.json   # Generated by LargePlanner
├── results_20260107_154037.json  # Full execution results + context
└── items_20260107_154037.json  # Item-level details
```

### File Descriptions

**`manifest.json`** - Your execution history:
```json
{
  "20260107_154037": {
    "timestamp": "2026-01-07T15:40:37",
    "success": true,
    "plan_file": "plan_20260107_154037.json",
    "results_file": "results_20260107_154037.json",
    "items_file": "items_20260107_154037.json",
    "statistics": {
      "total_amount": 47.42,
      "item_count": 7,
      "categories": {"food": {...}, "household": {...}}
    }
  },
  "20260107_160000": {
    "timestamp": "2026-01-07T16:00:00",
    "success": true,
    ...next run...
  }
}
```

**`plan_TIMESTAMP.json`** - What GPT-4o designed:
```json
{
  "request_id": "unique-id",
  "steps": [
    {"id": "step-1", "tool": "receipt_ocr", "depends_on": []},
    {"id": "step-2", "tool": "line_item_parser", "depends_on": ["step-1"]},
    ...
  ]
}
```

**`results_TIMESTAMP.json`** - Complete execution record:
```json
{
  "execution_id": "20260107_154037",
  "execution_success": true,
  "plan": {...plan content...},
  "context": {
    "step-1": {"text": "...", "confidence": 0.96},
    "step-2": {"items": [...], "item_count": 7},
    "step-3": {"items": [...], "category_totals": {...}},
    "step-4": {"total_amount": 47.42, "categories": {...}}
  }
}
```

**`items_TIMESTAMP.json`** - Item-level details for BI/reporting:
```json
{
  "execution_id": "20260107_154037",
  "items": [
    {"name": "Milk 2%", "price": 3.99, "category": "food"},
    {"name": "Eggs Large 12ct", "price": 4.50, "category": "food"},
    ...
  ]
}
```

### Use Cases

1. **Batch Processing:** Run 100 receipts, check manifest for all execution IDs
2. **Debugging:** Compare planned steps vs. actual results side-by-side
3. **Reporting:** Use items JSON for business intelligence dashboards
4. **Compliance:** Audit trail shows exact plan + execution for each receipt
5. **Cost Tracking:** Manifest aggregates execution metrics

## Performance Metrics (Real Run)

```
Mock OCR Mode (Demo 1 & 2):
├── receipt_ocr:        0ms (instant mock data)
├── line_item_parser:   114ms (regex parsing 7 items)
├── expense_categorizer: 60ms (keyword matching)
└── compute_statistics: 0.3ms (pure arithmetic)
   Total: ~175ms end-to-end
   Cost: $0.00 (deterministic tools)

End-to-End with Planner (Demo 3):
├── GPT-4o planning:    ~3 seconds ($0.002)
├── Plan normalization: <1 second (tool name mapping)
├── Sandbox execution:  ~175ms ($0.00)
└── Results storage:    <1 second ($0.00)
   Total: ~4-5 seconds
   Total Cost: ~$0.002 per receipt
   
Compare to all-LLM approach:
   1 planner call + 4 tool calls with LLM = $0.10
   ToolWeaver = $0.002
   Savings: 98% ✅
```
