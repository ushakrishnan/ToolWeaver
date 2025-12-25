# Programmatic Tool Calling - Code Walkthrough

A complete end-to-end code trace showing how a programmatic tool call happens.

---

## Complete Example: Adding & Using a New MCP Tool

### Scenario
You want to add a new MCP tool called `get_team_budget` that fetches budget information for a team.

---

## 1. IMPLEMENTATION PHASE

### Step 1A: Create the Worker Function

**File**: `orchestrator/dispatch/workers.py`

```python
# Add this worker function alongside existing workers

async def get_team_budget_worker(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP worker for fetching team budget information.
    
    Called by: MCPClientShim when user code calls the tool
    
    Args:
        payload: Dict with parameters
        {
            "team_id": "eng-team-1",
            "fiscal_year": 2024,
            "include_spent": True
        }
    
    Returns:
        Budget data
        {
            "team_id": "eng-team-1",
            "fiscal_year": 2024,
            "total_budget": 500000,
            "spent": 250000,
            "remaining": 250000,
            "details": [...]
        }
    """
    team_id = payload["team_id"]
    fiscal_year = payload.get("fiscal_year", datetime.now().year)
    include_spent = payload.get("include_spent", False)
    
    # Call your actual implementation
    # This could be an API call, database query, etc.
    budget_data = await get_budget_from_api(
        team_id=team_id,
        year=fiscal_year
    )
    
    if include_spent:
        spent_data = await get_spending_data(team_id, fiscal_year)
        budget_data["spent"] = spent_data["total"]
        budget_data["remaining"] = budget_data["total_budget"] - spent_data["total"]
    
    return budget_data
```

### Step 1B: Register in Tool Map

**File**: `orchestrator/infra/mcp_client.py`

```python
# BEFORE:
from ..dispatch.workers import (
    receipt_ocr_worker,
    line_item_parser_worker,
    expense_categorizer_worker,
    fetch_data_worker,
    store_data_worker,
)

_tool_map = {
    "receipt_ocr": receipt_ocr_worker,
    "line_item_parser": line_item_parser_worker,
    "expense_categorizer": expense_categorizer_worker,
    "fetch_data": fetch_data_worker,
    "store_data": store_data_worker,
}

# AFTER:
from ..dispatch.workers import (
    receipt_ocr_worker,
    line_item_parser_worker,
    expense_categorizer_worker,
    fetch_data_worker,
    store_data_worker,
    get_team_budget_worker,  # ← ADD THIS IMPORT
)

_tool_map = {
    "receipt_ocr": receipt_ocr_worker,
    "line_item_parser": line_item_parser_worker,
    "expense_categorizer": expense_categorizer_worker,
    "fetch_data": fetch_data_worker,
    "store_data": store_data_worker,
    "get_team_budget": get_team_budget_worker,  # ← ADD THIS MAPPING
}

# Now MCPClientShim can find it:
# self.tool_map["get_team_budget"]  ← Will work!
```

---

## 2. TOOL DEFINITION PHASE

### Define Tool in Catalog

**In your application code**:

```python
from orchestrator.shared.models import ToolCatalog, ToolDefinition, ToolParameter

# Create or get existing catalog
catalog = ToolCatalog(source="financial_app", version="1.0")

# Add the new tool definition
catalog.add_tool(ToolDefinition(
    name="get_team_budget",
    type="mcp",  # ← This is an MCP tool
    description="Retrieve budget information for a specific team",
    domain="finance",  # ← Groups with other finance tools
    parameters=[
        ToolParameter(
            name="team_id",
            type="string",
            description="Unique identifier for the team",
            required=True  # ← Must be provided
        ),
        ToolParameter(
            name="fiscal_year",
            type="integer",
            description="Fiscal year (e.g., 2024)",
            required=False,
            default=2024
        ),
        ToolParameter(
            name="include_spent",
            type="boolean",
            description="Include spent amount and remaining budget",
            required=False,
            default=False
        )
    ]
))

# catalog now has 1 tool: get_team_budget
print(f"Registered tools: {list(catalog.tools.keys())}")
# Output: Registered tools: ['get_team_budget']
```

---

## 3. STUB GENERATION PHASE

### Executor Initialization Triggers Stub Generation

```python
from orchestrator.execution.programmatic_executor import ProgrammaticToolExecutor
from pathlib import Path

# Create executor with stub generation enabled
executor = ProgrammaticToolExecutor(
    catalog,
    enable_stubs=True,  # ← Triggers stub generation
    stub_dir=Path("./stubs"),
    timeout=30
)

# Behind the scenes, ProgrammaticToolExecutor.__init__ does:
# 1. Calls _prepare_stub_environment()
# 2. StubGenerator groups tools by domain
# 3. For finance domain, generates:
#    - stubs/tools/finance/__init__.py
#    - stubs/tools/finance/get_team_budget.py  ← NEW STUB!
#    - stubs/tools/__init__.py
# 4. Creates importable Python modules
```

### Generated Stub File

**Auto-generated**: `stubs/tools/finance/get_team_budget.py`

```python
# AUTO-GENERATED - DO NOT EDIT
# Generated from ToolDefinition: get_team_budget

from pydantic import BaseModel
from typing import Optional

class GetTeamBudgetInput(BaseModel):
    """Input model for get_team_budget"""
    team_id: str
    fiscal_year: Optional[int] = 2024
    include_spent: Optional[bool] = False

async def get_team_budget(
    team_id: str,
    fiscal_year: Optional[int] = 2024,
    include_spent: Optional[bool] = False
) -> dict:
    """
    Retrieve budget information for a specific team
    
    Args:
        team_id (str): Unique identifier for the team
        fiscal_year (int, optional): Fiscal year (e.g., 2024). Defaults to 2024.
        include_spent (bool, optional): Include spent amount and remaining budget. 
                                       Defaults to False.
    
    Returns:
        dict: Budget data with fields like total_budget, spent, remaining
    
    Examples:
        budget = await get_team_budget("eng-team-1")
        budget = await get_team_budget("eng-team-1", 2024, include_spent=True)
    """
    
    # Import router
    from orchestrator.tools.tool_executor import call_tool
    
    # Pack parameters (only include non-None values)
    parameters = {
        "team_id": team_id,
    }
    if fiscal_year is not None:
        parameters["fiscal_year"] = fiscal_year
    if include_spent is not None:
        parameters["include_spent"] = include_spent
    
    # Route to tool executor
    # This will eventually call MCPClientShim.call_tool()
    result = await call_tool(
        server="finance",           # ← Domain/server
        tool_name="get_team_budget", # ← Tool name
        parameters=parameters,       # ← Packed parameters
        timeout=30
    )
    
    return result
```

### Generated Init File

**Auto-generated**: `stubs/tools/finance/__init__.py`

```python
# AUTO-GENERATED - DO NOT EDIT

from .get_team_budget import get_team_budget

__all__ = ["get_team_budget"]
```

---

## 4. CODE EXECUTION PHASE

### User/LLM Generates Code

The LLM (given the tool catalog) generates this orchestration code:

```python
code = """
from tools.finance import get_team_budget
import json

# Get budget for multiple teams
teams = ["eng-team-1", "sales-team-2", "product-team-3"]

budgets = []
for team_id in teams:
    budget = await get_team_budget(
        team_id=team_id,
        fiscal_year=2024,
        include_spent=True
    )
    budgets.append(budget)

# Process in Python (not in LLM context!)
total_budget = sum(b["total_budget"] for b in budgets)
total_spent = sum(b["spent"] for b in budgets)
total_remaining = total_budget - total_spent

summary = {
    "teams_queried": len(teams),
    "total_budget": total_budget,
    "total_spent": total_spent,
    "total_remaining": total_remaining,
    "teams": budgets
}

print(json.dumps(summary, indent=2))
"""

# Execute the code
result = await executor.execute(code)
```

---

## 5. EXECUTION FLOW - DETAILED TRACE

### Call #1: `await get_team_budget("eng-team-1", 2024, True)`

```
┌─────────────────────────────────────────────────────────────────────┐
│ TIME: T+0.100s                                                      │
│ CODE EXECUTION (in sandbox)                                         │
│                                                                     │
│ >>> from tools.finance import get_team_budget                       │
│     ✓ Imports auto-generated stub                                   │
│                                                                     │
│ >>> budget = await get_team_budget(                                 │
│                     team_id="eng-team-1",                           │
│                     fiscal_year=2024,                               │
│                     include_spent=True                              │
│                 )                                                   │
│                                                                     │
│ Execution enters stub function...                                   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ TIME: T+0.102s                                                      │
│ STUB EXECUTION (generated function)                                 │
│                                                                     │
│ async def get_team_budget(team_id, fiscal_year, include_spent):    │
│                                                                     │
│     # Import tool executor router                                   │
│     from orchestrator.tools.tool_executor import call_tool          │
│                                                                     │
│     # Pack parameters                                               │
│     parameters = {                                                  │
│         "team_id": "eng-team-1",                                    │
│         "fiscal_year": 2024,                                        │
│         "include_spent": True                                       │
│     }                                                               │
│                                                                     │
│     # Call router                                                   │
│     result = await call_tool(                                       │
│         server="finance",                                           │
│         tool_name="get_team_budget",                                │
│         parameters=parameters,                                      │
│         timeout=30                                                  │
│     )                                                               │
│                                                                     │
│ Jump to: call_tool() function...                                    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ TIME: T+0.103s                                                      │
│ TOOL EXECUTOR ROUTER (orchestrator/tools/tool_executor.py)         │
│                                                                     │
│ async def call_tool(server, tool_name, parameters, timeout):       │
│     # server="finance", tool_name="get_team_budget", ...            │
│                                                                     │
│     logger.info(f"Executing tool: finance/get_team_budget")         │
│     logger.debug(f"Parameters: {parameters}")                       │
│                                                                     │
│     # Route based on server type                                    │
│     if server == "default" or server == "function":                 │
│         → _execute_function(...)  # ← Not taken                     │
│     else:                                                           │
│         → result = await _execute_mcp_tool(                         │
│              server="finance",                                      │
│              tool_name="get_team_budget",                           │
│              parameters=parameters,                                 │
│              timeout=30                                             │
│          )                                                          │
│                                                                     │
│ Jump to: _execute_mcp_tool() function...                            │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ TIME: T+0.104s                                                      │
│ MCP TOOL EXECUTOR (orchestrator/tools/tool_executor.py)             │
│                                                                     │
│ async def _execute_mcp_tool(server, tool_name, parameters, timeout):
│     # server="finance", tool_name="get_team_budget", ...            │
│                                                                     │
│     # Create MCP client shim                                        │
│     from orchestrator.infra.mcp_client import MCPClientShim         │
│                                                                     │
│     client = MCPClientShim()                                        │
│     # client.tool_map has all registered tools:                     │
│     # {                                                              │
│     #   "receipt_ocr": worker_func,                                 │
│     #   "get_team_budget": get_team_budget_worker,  ← FOUND        │
│     #   ...                                                         │
│     # }                                                              │
│                                                                     │
│     # Call the tool via client                                      │
│     result = await asyncio.wait_for(                                │
│         client.call_tool(                                           │
│             tool_name="get_team_budget",                            │
│             payload=parameters                                      │
│         ),                                                          │
│         timeout=30                                                  │
│     )                                                               │
│                                                                     │
│ Jump to: MCPClientShim.call_tool()...                               │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ TIME: T+0.105s                                                      │
│ MCP CLIENT SHIM (orchestrator/infra/mcp_client.py)                  │
│                                                                     │
│ class MCPClientShim:                                                │
│                                                                     │
│     async def call_tool(self, tool_name, payload, ...):             │
│         # tool_name="get_team_budget", payload={...}                │
│                                                                     │
│         # Check idempotency cache                                   │
│         if idempotency_key:                                         │
│             cached = self._get_cached(idempotency_key)              │
│             if cached: return cached  ← Not in this example         │
│                                                                     │
│         # Check circuit breaker                                     │
│         if self._is_circuit_open():                                 │
│             raise RuntimeError("MCP circuit open")                  │
│                                                                     │
│         # Retry loop                                                │
│         last_exc = None                                             │
│         for attempt in range(self._max_retries + 1):                │
│             # Get worker function from tool_map                     │
│             coro = self.tool_map[tool_name](payload)                │
│             #              ↓                   ↓                     │
│             # self.tool_map["get_team_budget"]({                    │
│             #     "team_id": "eng-team-1",                          │
│             #     "fiscal_year": 2024,                              │
│             #     "include_spent": True                             │
│             # })                                                    │
│             #                                                       │
│             # This returns: coroutine of get_team_budget_worker()   │
│                                                                     │
│             try:                                                    │
│                 result = await asyncio.wait_for(coro, timeout=30)   │
│                 #                                                   │
│                 # If successful, reset circuit breaker              │
│                 self._reset_circuit()                               │
│                 #                                                   │
│                 # Cache result if idempotency key provided          │
│                 if idempotency_key:                                 │
│                     self._store(idempotency_key, result)            │
│                 #                                                   │
│                 # Emit metric                                       │
│                 self._emit("mcp.complete", {                        │
│                     "tool": tool_name,                              │
│                     "attempt": 1,                                   │
│                     "success": True                                 │
│                 })                                                  │
│                 #                                                   │
│                 # Return to caller                                  │
│                 return result  ← RETURNS HERE                       │
│                 #                                                   │
│             except asyncio.TimeoutError:                            │
│                 last_exc = RuntimeError(f"Tool timed out")          │
│             except Exception as e:                                  │
│                 last_exc = e                                        │
│                                                                     │
│ Jump to: get_team_budget_worker() coroutine execution...            │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ TIME: T+0.106s                                                      │
│ WORKER FUNCTION EXECUTION (orchestrator/dispatch/workers.py)        │
│                                                                     │
│ async def get_team_budget_worker(payload):                          │
│     # payload = {                                                   │
│     #     "team_id": "eng-team-1",                                  │
│     #     "fiscal_year": 2024,                                      │
│     #     "include_spent": True                                     │
│     # }                                                              │
│                                                                     │
│     team_id = payload["team_id"]                                    │
│     # team_id = "eng-team-1"                                        │
│                                                                     │
│     fiscal_year = payload.get("fiscal_year", 2024)                  │
│     # fiscal_year = 2024                                            │
│                                                                     │
│     include_spent = payload.get("include_spent", False)             │
│     # include_spent = True                                          │
│                                                                     │
│     # Call actual API / database                                    │
│     budget_data = await get_budget_from_api(                        │
│         team_id="eng-team-1",                                       │
│         year=2024                                                   │
│     )                                                               │
│     # Simulated result:                                              │
│     # budget_data = {                                               │
│     #     "team_id": "eng-team-1",                                  │
│     #     "fiscal_year": 2024,                                      │
│     #     "total_budget": 500000,                                   │
│     #     ...                                                        │
│     # }                                                              │
│                                                                     │
│     if include_spent:                                               │
│         spent_data = await get_spending_data("eng-team-1", 2024)    │
│         # spent_data = {"total": 250000, ...}                       │
│                                                                     │
│         budget_data["spent"] = 250000                               │
│         budget_data["remaining"] = 500000 - 250000 = 250000         │
│                                                                     │
│     return budget_data                                              │
│     # Returns: {                                                    │
│     #     "team_id": "eng-team-1",                                  │
│     #     "fiscal_year": 2024,                                      │
│     #     "total_budget": 500000,                                   │
│     #     "spent": 250000,                                          │
│     #     "remaining": 250000                                       │
│     # }                                                              │
│                                                                     │
│ Jump back to: MCPClientShim.call_tool()...                          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ TIME: T+0.350s (async operation completed)                          │
│ BACK IN MCP CLIENT SHIM                                             │
│                                                                     │
│ result = await asyncio.wait_for(coro, timeout=30)                   │
│ # ✓ Completed successfully                                          │
│ # result = {                                                         │
│ #     "team_id": "eng-team-1",                                      │
│ #     "fiscal_year": 2024,                                          │
│ #     "total_budget": 500000,                                       │
│ #     "spent": 250000,                                              │
│ #     "remaining": 250000                                           │
│ # }                                                                  │
│                                                                     │
│ self._reset_circuit()                                               │
│ self._emit("mcp.complete", {...})                                   │
│ return result  ← Back through call stack                            │
│                                                                     │
│ Jump back to: _execute_mcp_tool()...                                │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ TIME: T+0.351s                                                      │
│ BACK IN MCP TOOL EXECUTOR                                           │
│                                                                     │
│ result = await asyncio.wait_for(                                    │
│     client.call_tool(...),                                          │
│     timeout=30                                                      │
│ )                                                                   │
│ # ✓ Returned from client                                            │
│ # result = {...budget_data...}                                      │
│                                                                     │
│ logger.info(f"Tool get_team_budget executed successfully")          │
│ return result  ← Back to call_tool() router                         │
│                                                                     │
│ Jump back to: call_tool() router...                                 │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ TIME: T+0.352s                                                      │
│ BACK IN TOOL EXECUTOR ROUTER                                        │
│                                                                     │
│ result = await _execute_mcp_tool(...)                               │
│ # ✓ Returned from MCP tool executor                                 │
│ # result = {...budget_data...}                                      │
│                                                                     │
│ logger.info(f"Tool get_team_budget executed successfully")          │
│ return result  ← Back to stub                                       │
│                                                                     │
│ Jump back to: get_team_budget() stub...                             │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ TIME: T+0.353s                                                      │
│ BACK IN STUB                                                        │
│                                                                     │
│ result = await call_tool(...)                                       │
│ # ✓ Returned from call_tool()                                       │
│ # result = {...budget_data...}                                      │
│                                                                     │
│ return result  ← Back to user code                                  │
│                                                                     │
│ Jump back to: user code in sandbox...                               │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ TIME: T+0.353s                                                      │
│ BACK IN USER CODE (sandbox)                                         │
│                                                                     │
│ >>> budget = await get_team_budget(                                 │
│                     team_id="eng-team-1",                           │
│                     fiscal_year=2024,                               │
│                     include_spent=True                              │
│                 )                                                   │
│                                                                     │
│ # ✓ budget now contains:                                            │
│ budget = {                                                          │
│     "team_id": "eng-team-1",                                        │
│     "fiscal_year": 2024,                                            │
│     "total_budget": 500000,                                         │
│     "spent": 250000,                                                │
│     "remaining": 250000                                             │
│ }                                                                   │
│                                                                     │
│ budgets.append(budget)  ← Add to collection                         │
│                                                                     │
│ >>> Next iteration: budget for "sales-team-2"...                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. FULL EXECUTION RESULT

After all three teams' budgets are fetched:

```python
result = await executor.execute(code)

# result dictionary:
{
    "error": None,
    "execution_time": 0.850,  # Total time in sandbox
    "output": """{
  "teams_queried": 3,
  "total_budget": 1500000,
  "total_spent": 650000,
  "total_remaining": 850000,
  "teams": [
    {
      "team_id": "eng-team-1",
      "fiscal_year": 2024,
      "total_budget": 500000,
      "spent": 250000,
      "remaining": 250000
    },
    {
      "team_id": "sales-team-2",
      "fiscal_year": 2024,
      "total_budget": 600000,
      "spent": 300000,
      "remaining": 300000
    },
    {
      "team_id": "product-team-3",
      "fiscal_year": 2024,
      "total_budget": 400000,
      "spent": 100000,
      "remaining": 300000
    }
  ]
}""",
    "result": {...},
    "tool_calls": [
        {
            "tool": "get_team_budget",
            "type": "mcp",
            "parameters": {
                "team_id": "eng-team-1",
                "fiscal_year": 2024,
                "include_spent": True
            },
            "timestamp": 1702518000.100,
            "caller": {
                "type": "stub_import",
                "execution_id": "ptc_a1b2c3d4",
                "tool_id": "tool_call_1"
            },
            "completed_at": 1702518000.353,
            "duration": 0.253,
            "result_size": 2048,
            "error": None
        },
        {
            "tool": "get_team_budget",
            "type": "mcp",
            "parameters": {
                "team_id": "sales-team-2",
                "fiscal_year": 2024,
                "include_spent": True
            },
            "timestamp": 1702518000.354,
            "caller": {
                "type": "stub_import",
                "execution_id": "ptc_a1b2c3d4",
                "tool_id": "tool_call_2"
            },
            "completed_at": 1702518000.580,
            "duration": 0.226,
            "result_size": 2048,
            "error": None
        },
        {
            "tool": "get_team_budget",
            "type": "mcp",
            "parameters": {
                "team_id": "product-team-3",
                "fiscal_year": 2024,
                "include_spent": True
            },
            "timestamp": 1702518000.581,
            "caller": {
                "type": "stub_import",
                "execution_id": "ptc_a1b2c3d4",
                "tool_id": "tool_call_3"
            },
            "completed_at": 1702518000.850,
            "duration": 0.269,
            "result_size": 2048,
            "error": None
        }
    ],
    "execution_id": "ptc_a1b2c3d4"
}
```

---

## 7. Key Insights from This Trace

### What Happened

1. **1 LLM Inference**: LLM generated the complete orchestration code in 1 pass
2. **3 Tool Calls**: Made 3 API/DB calls to get_team_budget_worker
3. **~250ms per call**: Each async operation took ~250ms (realistic API latency)
4. **Sequential execution**: Calls happened one after another (could be parallel with asyncio.gather!)
5. **All tracking automatic**: Each call tracked with timing, parameters, errors
6. **Result aggregation in Python**: The loops and aggregation happened in sandbox code, NOT in LLM

### Comparison to Traditional

**Traditional approach** for same task:
- Inference 1: LLM generates "Call get_team_budget for team 1"
- Tool Call 1: ~250ms
- Inference 2: LLM generates "Call get_team_budget for team 2"
- Tool Call 2: ~250ms
- Inference 3: LLM generates "Call get_team_budget for team 3"
- Tool Call 3: ~250ms
- Inference 4: LLM analyzes results, generates summary
- **Total: 4 inferences + ~1 second = 3-5 seconds** (with LLM latency)

**Programmatic approach** (this example):
- Inference 1: LLM generates code
- Sandbox execution: 850ms (3 sequential calls)
- **Total: 1 inference + 850ms = 1-1.5 seconds** (50-70% faster!)

**With parallel execution** (asyncio.gather):
```python
budgets = await asyncio.gather(*[
    get_team_budget(team_id, 2024, True)
    for team_id in ["eng-team-1", "sales-team-2", "product-team-3"]
])
```
- All 3 calls run in parallel: ~250ms total (instead of 750ms!)
- **Final time: ~250ms (even faster!)**

---

## 8. Extensibility Example: Adding Another Tool

To add another MCP like `get_team_members`:

```python
# 1. Add worker
async def get_team_members_worker(payload):
    team_id = payload["team_id"]
    return await fetch_members_from_api(team_id)

# 2. Register
_tool_map["get_team_members"] = get_team_members_worker

# 3. Define tool
catalog.add_tool(ToolDefinition(
    name="get_team_members",
    type="mcp",
    domain="hr",  # Different domain!
    parameters=[...]
))

# 4. Stubs auto-generated to: stubs/tools/hr/get_team_members.py

# 5. Use in code
code = '''
from tools.finance import get_team_budget
from tools.hr import get_team_members

team = await get_team_members(team_id="eng-team-1")
budget = await get_team_budget(team_id="eng-team-1")
print(f"Team size: {len(team)}, Budget: ${budget['total_budget']}")
'''
```

**No executor changes needed!** The system automatically:
- ✓ Generates stubs
- ✓ Routes calls
- ✓ Tracks execution
- ✓ Manages retries & timeouts

This is the power of programmatic tool calling!

---

## 📚 Learn More

For **complete working code** that demonstrates this walkthrough:

- **[Example 23: Adding New Tools](../../../examples/23-adding-new-tools/)**
  - Full implementation of weather and stock price MCP tools
  - Complete A2A agent definitions
  - Demonstrates unified discovery of both MCP + A2A tools
  - Run: `cd examples/23-adding-new-tools && python add_new_tools.py`

- **[REFERENCE.md](REFERENCE.md)** - "Adding a New MCP Tool: Checklist"
  - Quick checklist version of this walkthrough

- **[EXPLAINED.md](EXPLAINED.md)** - Full architectural explanation
