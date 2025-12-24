# Next Steps: Systematic Example Fixes

## Progress So Far ✅

- Example 01: ✅ DONE (basic @mcp_tool)
- Example 02: ✅ DONE (tool chaining)
- Example 04: ✅ DONE (tool discovery/search)

## Priority Queue (Recommended Order)

### TIER 1: Core Concepts (Required for basic learning)
- Example 03: GitHub operations (verify or light update)
- Example 05: YAML workflows (load_tools_from_yaml)
- Example 09: Programmatic executor

### TIER 2: Advanced Patterns (Show off capabilities)
- Example 06: Monitoring with logging
- Example 07: Tool composition patterns
- Example 08: Model routing
- Example 10-12: More programmatic executor patterns
- Example 16-18: Agent delegation (A2AClient)
- Example 25: Parallel agents (dispatch_agents)

### TIER 3: Specialized (Nice to have)
- Example 13-15: Control flow patterns
- Example 19-24: Test/utility examples
- Example 27-28: Optimization examples

### NOT NEEDED (Can be archived)
- Examples with "non-existent module" errors
- Examples that duplicate functionality

## Strategy for Efficient Completion

### For Each Example:

1. **Read** the current code/README
2. **Identify** what it should demonstrate (from FEATURES_MAPPING.md)
3. **Rewrite** to use correct API (template-based or quick refactor)
4. **Test** (python script_name.py - must pass silently or show correct output)
5. **Update README** (clear learning objectives + actual output)
6. **Commit** (one example per commit for clarity)

## Estimated Time

- Tier 1 (examples 03, 05, 09): 30-45 min
- Tier 2 (examples 06-08, 10-12, 16-18, 25): 1.5-2 hours
- Tier 3 (13-15, 19-24, 27-28): 1-1.5 hours
- Total: 3-4 hours for complete systematic fix

## Success Criteria

All 29 examples should:
1. ✅ Run without errors (exit code 0)
2. ✅ Produce meaningful output demonstrating the feature
3. ✅ Have a clear README explaining what they do
4. ✅ Show actual feature usage (not mocks/stubs)
5. ✅ Work with just `python script.py` (no complex setup)

## Template for Tier 2+ Fixes

```python
# For programmatic executor (examples 09-12):
from orchestrator._internal.execution.programmatic_executor import ProgrammaticExecutor

# For A2A client (examples 16-18):
from orchestrator import A2AClient

# For dispatch agents (example 25):
from orchestrator.tools.sub_agent import dispatch_agents, DispatchResourceLimits
```

---

Recommendation: Fix Tier 1 first (highest ROI), then assess remaining time for Tier 2+.
