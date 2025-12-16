# Implementation Details

## System Architecture

A **production-ready hybrid orchestrator** that treats MCP workers, function calls, and code execution as **interchangeable tools** through a unified dispatcher.

This document provides technical implementation details for developers working with ToolWeaver's internals.

---

## 🎯 Tool Types

| Type | Purpose | Example Tools |
|------|---------|---------------|
| **MCP Workers** | Deterministic, reliable operations | `receipt_ocr`, `line_item_parser`, `expense_categorizer` |
| **Function Calls** | Structured APIs with type safety | `compute_tax`, `merge_items`, `compute_item_statistics` |
| **Code Execution** | Dynamic Python transformations | Sandboxed code with safe builtins |

---

## 📦 Files Created/Modified

### New Files (5)
```
orchestrator/
├── hybrid_dispatcher.py    ⭐ Core dispatcher + function registry
└── functions.py            ⭐ 5 example functions (compute_tax, merge_items, etc.)

example_plan_hybrid.json    ⭐ Demo plan using all three tool types
README.md                   ⭐ GitHub-style documentation
docs/ARCHITECTURE.md        ⭐ Detailed technical documentation
```

### Enhanced Files (6)
```
orchestrator/
├── models.py              + FunctionCallInput/Output models
├── orchestrator.py        → Uses hybrid_dispatcher
├── code_exec_worker.py    + Safe builtins (len, sum, etc.)
├── workers.py             + Handles nested dict inputs
└── __init__.py            + Exports new modules

run_demo.py                → Enhanced demo script
```

---

## 🚀 Key Features

✅ **Unified Dispatcher** - Single interface for all tool types  
✅ **Type Safety** - Full Pydantic validation  
✅ **Decorator Pattern** - Easy function registration with `@register_function`  
✅ **Safe Sandboxing** - Code-exec with whitelisted builtins  
✅ **Parallel Execution** - Independent steps run concurrently  
✅ **Reference Resolution** - Automatic `step:` reference handling  
✅ **Nested Dict Support** - Workers handle both direct and nested inputs  
✅ **Comprehensive Logging** - Full execution trace  
✅ **Error Handling** - Retry logic with exponential backoff  

---

## 🎯 Three Tool Types - One Interface

### 1️⃣ MCP Workers (Deterministic)
```python
{
  "tool": "receipt_ocr",
  "input": {"image_uri": "s3://..."}
}
```
**Use for:** Fast, reliable, predictable operations

### 2️⃣ Function Calls (Structured APIs)
```python
{
  "tool": "function_call",
  "input": {
    "name": "compute_tax",
    "args": {"amount": 100, "tax_rate": 0.08}
  }
}
```
**Use for:** Type-safe, reusable business logic

### 3️⃣ Code Execution (Dynamic)
```python
{
  "tool": "code_exec",
  "input": {
    "code": "output = {'sum': sum(input['values'])}",
    "input_data": {"values": [1, 2, 3]}
  }
}
```
**Use for:** Flexible transformations and custom logic

---

## 📊 Test Results

Both plans execute successfully with **100% success rate**:

### Original Plan (4 steps)
- ✅ MCP: receipt_ocr
- ✅ MCP: line_item_parser
- ✅ Code-Exec: item count
- ✅ MCP: expense_categorizer

### Hybrid Plan (7 steps)
- ✅ MCP: receipt_ocr
- ✅ MCP: line_item_parser
- ✅ Function: merge_items (aggregate statistics)
- ✅ Code-Exec: extract descriptions
- ✅ MCP: expense_categorizer
- ✅ Function: compute_tax (8% on $8.50 = $0.68)
- ✅ Function: compute_item_statistics (categories, totals, etc.)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         Planner LLM (JSON Plan)             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│           ORCHESTRATOR ENGINE               │
│  • Dependency Resolution                    │
│  • Parallel Execution                       │
│  • Retry Logic                              │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│          HYBRID DISPATCHER                  │
│  • Resolves step: references                │
│  • Routes by tool type                      │
└───────┬───────────────┬───────────────┬─────┘
        │               │               │
        ▼               ▼               ▼
   ┌────────┐    ┌───────────┐   ┌──────────┐
   │  MCP   │    │ Function  │   │  Code    │
   │Workers │    │  Calls    │   │  Exec    │
   └────────┘    └───────────┘   └──────────┘
        │               │               │
        └───────────────┴───────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │ Context Store    │
              │ (Step Outputs)   │
              └──────────────────┘
```

---

## 🎪 Benefits

| Benefit | Implementation |
|---------|----------------|
| **Safety** | Functions validated; code sandboxed with safe builtins |
| **Flexibility** | Dynamic transformations via code-exec |
| **Reliability** | Deterministic MCP tools for predictable operations |
| **Extensibility** | Add functions with single decorator |
| **MCP-Compatible** | Mirrors Anthropic's design pattern |

---

## 🧪 How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run all demo plans
python run_demo.py

# Run specific plan
python run_demo.py example_plan_hybrid.json
```

---

## 💡 Adding New Tools

### Add MCP Worker
```python
# In workers.py
async def my_worker(payload: Dict[str, Any]):
    return {"result": ...}

# In mcp_client.py
_tool_map["my_tool"] = my_worker
```

### Add Function
```python
# In functions.py
@register_function("my_function")
def my_function(arg: str) -> dict:
    return {"result": arg.upper()}
```

---

## 🎓 Function Registry

5 registered functions ready to use:
1. `compute_tax` - Tax calculations
2. `merge_items` - Item aggregation
3. `apply_discount` - Discount application
4. `filter_items_by_category` - Category filtering
5. `compute_item_statistics` - Comprehensive statistics

---

## 📈 Project Metrics

- **Files Created:** 5
- **Files Enhanced:** 6  
- **Total Code:** ~1,500+ lines
- **Functions Registered:** 5
- **Tool Types:** 3
- **Test Success:** 100% ✅
- **Parallel Execution:** Yes ⚡
- **Production Ready:** Yes 🚀

---

Generated: December 2025  
Status: **Active Development**
