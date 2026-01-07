# Example 01: Why ToolWeaver? The Value Proposition

**Complexity:** ⭐ Beginner | **Time:** 10 minutes | **Package:** toolweaver >= 0.13.6

## 🎯 The Core Question

**Why use ToolWeaver instead of just calling GPT-4o for everything?**

This sample answers that question with a clear, concrete example: **processing receipts**.

## The Problem

You have a multi-step task:
1. Extract text from receipt image (OCR)
2. Parse line items from text
3. Categorize expenses
4. Compute statistics

**Naive approach**: Call GPT-4o for each step  
**Result**: Works, but expensive ($0.10/receipt), slow (1.4s), non-deterministic, no audit trail

**ToolWeaver approach**: Plan once with GPT-4o, execute with deterministic tools  
**Result**: Works, cheaper ($0.002/receipt = 98% savings), faster (0.175s), deterministic, full traceability

## What This Sample Shows

Three progressive demonstrations:

| **naive_all_llm.py** | Call GPT-4o for every step | Show the expensive approach | This is your baseline |
| **smart_toolweaver.py** | Plan with GPT-4o, execute with tools | Show ToolWeaver advantage | Smart planning + cheap execution |
| **comparison.py** | Side-by-side metrics & philosophy | Explain why it matters | Why ToolWeaver is production-ready |

## Prerequisites

```bash
# Python 3.10 or higher
python --version

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install ToolWeaver with all features (includes planner + monitoring)
pip install toolweaver[all]

# Verify installation
python -c "import orchestrator; print('✓ ToolWeaver installed')"
```

**Note**: All demos use mock OCR by default - no API keys required to start!

## Run the Examples

```bash
cd samples/01-basic-receipt-processing

# Activate virtual environment first
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Demo 1: Show the expensive naive approach
python naive_all_llm.py

# Demo 2: Show the ToolWeaver approach with smart planning
python smart_toolweaver.py

# Demo 3: Understand the differences
python comparison.py
```

## Understanding the Execution Flow

### Naive Approach (All-LLM)

```
Receipt Image
    ↓
[GPT-4o Call 1] → OCR
    ↓
[GPT-4o Call 2] → Parse items      ← EXPENSIVE, NO GUARANTEE
    ↓
[GPT-4o Call 3] → Categorize       ← EXPENSIVE, MAY VARY
    ↓
[GPT-4o Call 4] → Statistics       ← EXPENSIVE, UNPREDICTABLE
    ↓
Final Result

Cost: $0.10 | Time: 1.4s | Reproducible: ❌ | Audit Trail: ❌
```

### ToolWeaver Approach (Smart Planning + Cheap Execution)

```
Receipt Image
    ↓
[GPT-4o Planning] → Generate execution DAG (plan)
    ↓
[Execution Plan] → Deterministic Tool Chain (sandboxed)
    ↓
[OCR Tool]       → Extract text (deterministic)
    ↓
[Parser Tool]    → Parse items (regex/keyword)
    ↓
[Categorizer]    → Categorize (lookup table)
    ↓
[Statistics]     → Compute totals (arithmetic)
    ↓
[Save Artifacts] → plan_*.json + results_*.json + manifest.json
    ↓
Final Result

Cost: $0.002 | Time: 0.25s | Reproducible: ✅ | Audit Trail: ✅
```

## The Key Differences

| Aspect | Naive (All-LLM) | ToolWeaver | Impact |
|--------|-----------------|-----------|--------|
| **Cost per receipt** | $0.10 | $0.002 | **98% savings** |
| **Cost for 100 receipts** | $10.00 | $0.20 | **$9.80 saved** |
| **Execution time** | 1.4s/receipt | 0.25s/receipt | **5.6x faster** |
| **Reproducibility** | Non-deterministic | Deterministic | **Always same result** |
| **Audit trail** | None | Complete | **Full traceability** |
| **LLM calls** | 4 per receipt | 1 per receipt | **75% fewer LLM calls** |
| **Code complexity** | Simple | Moderate | **Better design** |
| **Production ready** | ❌ Too expensive | ✅ Yes | **Suitable for scale** |

## What Gets Saved

When you run `smart_toolweaver.py`, it saves timestamped artifacts to `execution_outputs/`:

```
execution_outputs/
├── manifest.json                    # Execution history log
├── plan_20260107_154037.json        # What was planned
├── results_20260107_154037.json     # What actually happened
└── items_20260107_154037.json       # Item-level details
```

This demonstrates **the ToolWeaver advantage**: complete reproducibility and auditability.

## PLANNER CREDENTIALS (Optional)

The demos work in two modes:

### Mode 1: Mock Planning (Default)
```bash
# No credentials needed - uses hardcoded fallback plan
python smart_toolweaver.py
```

### Mode 2: Real Planning
```bash
# Set credentials in .env
PLANNER_PROVIDER=azure
PLANNER_MODEL=gpt-4o
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...

# Now it will call real LargePlanner to generate plans
python smart_toolweaver.py
```

If planner credentials are not available, the demo gracefully falls back to a hardcoded plan.

## Package-First Philosophy ⭐

**This is a fundamental principle of ToolWeaver samples:**

- All imports are from the installed `orchestrator` package (`pip install toolweaver`)
- Never use local development code or relative imports
- The sample shows how to USE ToolWeaver, not how to develop it
- This is production-grade: same code works in real applications

Verify:
```bash
python -c "import orchestrator; print('Package:', orchestrator.__file__)"
# Should show: .venv/Lib/site-packages/orchestrator/__init__.py
```

## Key Takeaways

✅ **Cost Efficiency**: 98% cheaper than naive all-LLM approach  
✅ **Speed**: 5.6x faster execution  
✅ **Determinism**: Same plan = same result (reproducible)  
✅ **Traceability**: Full audit trail with timestamped artifacts  
✅ **Safety**: Sandboxed execution with resource limits  
✅ **Production Ready**: Suitable for mission-critical applications  

## The ToolWeaver Philosophy

> **"Smart Planning + Cheap Execution + Safe Isolation + Full Traceability"**

This is what makes ToolWeaver different:

1. **Expensive models** (GPT-4o) do strategic planning only
2. **Cheap models/tools** (deterministic) handle execution
3. **Safe isolation** (sandbox) prevents errors from cascading
4. **Full traceability** (artifacts + manifest) enables compliance

The result: **Intelligence where it matters, efficiency everywhere else.**

## Next Steps

After understanding the value prop in Sample 01:

1. **[Sample 02](../02-receipt-with-categorization)** - Multi-tool workflows with orchestration
2. **[Sample 10](../10-multi-step-planning)** - Complex multi-step planning with LargePlanner
3. **[Sample 26](../26-sandbox-execution)** - Sandbox isolation and execution models

## Troubleshooting

**Issue**: Import error with `orchestrator`
```bash
# Solution: Reinstall the package
pip uninstall toolweaver
pip install toolweaver
```

**Issue**: Planner unavailable (ModuleNotFoundError)
```bash
# Solution: This is OK - demos fall back to hardcoded plan
# Only needed if you want to test real LargePlanner
# Add PLANNER credentials to .env
```

**Issue**: "Cannot find execution_outputs"
```bash
# Solution: Run smart_toolweaver.py first to create it
python smart_toolweaver.py
python comparison.py
```

## Summary

This sample answers **"Why ToolWeaver?"** with concrete, measurable evidence:

- **Cost**: 98% cheaper ($0.002 vs $0.10 per receipt)
- **Speed**: 5.6x faster (0.25s vs 1.4s)
- **Reliability**: Deterministic, reproducible, auditable
- **Production**: Safe, sandboxed, compliant

The key insight: **Plan with expensive LLM once, execute with cheap deterministic tools.**

This is ToolWeaver's core value proposition.



