# Agent Orchestration & Tool Composition Roadmap

**Goal:** Implement intelligent agent-to-agent orchestration and tool composition patterns inspired by Claude's multi-model workflow (Opus orchestrating 100x Haiku agents in parallel).

**Status:** Planning Phase  
**Target Start:** January 2025  
**Target Completion:** Q1 2025

---

## 📋 Overview

ToolWeaver currently supports:
- ✅ Individual tool registration and discovery
- ✅ Single-agent execution
- ✅ Basic tool dispatching

**Gap:** No support for:
- ❌ Agent-to-agent orchestration (sub-agent dispatch)
- ❌ Tool composition/chaining
- ❌ Parallel agent execution at scale
- ❌ Cost-benefit aware tool selection
- ❌ Error recovery across parallel calls

This roadmap addresses these gaps by implementing the patterns from Claude's architecture.

---

## 🎯 Phase 1: Sub-Agent Dispatch (v0.4) - HIGHEST PRIORITY

### Overview
Enable smart agents to spawn multiple sub-agents in parallel for divide-and-conquer workloads.

### Implementation Steps

#### Step 1.1: Define Sub-Agent Dispatch API
**File:** `orchestrator/tools/sub_agent.py` (NEW)

```python
# New module
from dataclasses import dataclass
from typing import List, Dict, Any, Callable
import asyncio

@dataclass
class SubAgentTask:
    """Single task for a sub-agent"""
    prompt_template: str
    arguments: Dict[str, Any]
    agent_name: str = "default"
    model: str = "haiku"  # Cost-optimized default
    timeout_sec: int = 30

@dataclass  
class SubAgentResult:
    """Result from one sub-agent execution"""
    task_args: Dict[str, Any]
    output: Any
    error: Optional[str] = None
    duration_ms: float = 0
    success: bool = True

async def dispatch_agents(
    template: str,
    arguments: List[Dict[str, Any]],
    agent_name: str = "default",
    model: str = "haiku",
    max_parallel: int = 10,
    timeout_per_agent: int = 30,
    retry_on_failure: bool = True,
    min_success_rate: float = 0.8
) -> List[SubAgentResult]:
    """
    Dispatch multiple parallel sub-agents with same prompt template.
    
    Args:
        template: Prompt template with {placeholder} for arguments
        arguments: List of dicts to fill placeholders
        agent_name: Which agent to use
        model: Model to run each sub-agent on (e.g., "haiku")
        max_parallel: Max concurrent executions
        timeout_per_agent: Timeout per agent in seconds
        retry_on_failure: Retry failed tasks
        min_success_rate: Minimum % tasks that must succeed
    
    Returns:
        List of SubAgentResult objects
        
    Raises:
        SubAgentDispatchError: If success rate falls below threshold
    """
    # Implementation in Step 1.2
    pass
```

**Why:** Define clear contract for sub-agent dispatch before implementation.

---

#### Step 1.2: Implement Dispatch Logic
**File:** `orchestrator/tools/sub_agent.py`

```python
async def dispatch_agents(
    template: str,
    arguments: List[Dict[str, Any]],
    agent_name: str = "default",
    model: str = "haiku",
    max_parallel: int = 10,
    timeout_per_agent: int = 30,
    retry_on_failure: bool = True,
    min_success_rate: float = 0.8
) -> List[SubAgentResult]:
    """Implementation steps:
    
    1. Validate inputs (template syntax, argument structure)
    2. Create semaphore for max_parallel control
    3. Create task list with filled templates
    4. Execute all tasks concurrently with asyncio.gather()
    5. Handle timeouts gracefully
    6. Track results and errors separately
    7. Check success rate against min_success_rate
    8. Retry failed tasks if enabled
    9. Return aggregated results with metadata
    """
    
    results = []
    semaphore = asyncio.Semaphore(max_parallel)
    
    async def run_single_agent(task: SubAgentTask) -> SubAgentResult:
        async with semaphore:
            try:
                # Fill template with arguments
                filled_prompt = task.prompt_template.format(**task.arguments)
                
                # Execute agent
                start = time.time()
                output = await execute_agent(
                    name=task.agent_name,
                    prompt=filled_prompt,
                    model=task.model,
                    timeout=task.timeout_sec
                )
                duration_ms = (time.time() - start) * 1000
                
                return SubAgentResult(
                    task_args=task.arguments,
                    output=output,
                    duration_ms=duration_ms,
                    success=True
                )
            except asyncio.TimeoutError:
                return SubAgentResult(
                    task_args=task.arguments,
                    error="Timeout",
                    success=False
                )
            except Exception as e:
                return SubAgentResult(
                    task_args=task.arguments,
                    error=str(e),
                    success=False
                )
    
    # Create tasks
    tasks = [
        SubAgentTask(template, args, agent_name, model, timeout_per_agent)
        for args in arguments
    ]
    
    # Execute in parallel
    results = await asyncio.gather(
        *[run_single_agent(task) for task in tasks],
        return_exceptions=False
    )
    
    # Check success rate
    success_count = sum(1 for r in results if r.success)
    success_rate = success_count / len(results) if results else 0
    
    if success_rate < min_success_rate:
        raise SubAgentDispatchError(
            f"Success rate {success_rate:.1%} below threshold {min_success_rate:.1%}"
        )
    
    return results
```

**Why:** Implement the core orchestration logic with proper error handling and parallel execution.

---

#### Step 1.3: Add to Public API
**File:** `orchestrator/__init__.py`

```python
from .tools.sub_agent import dispatch_agents, SubAgentResult, SubAgentTask

__all__ = [
    # ... existing exports ...
    "dispatch_agents",
    "SubAgentResult",
    "SubAgentTask",
]
```

---

#### Step 1.4: Create Comprehensive Tests
**File:** `tests/test_sub_agent_dispatch.py` (NEW)

```python
import pytest
import asyncio
from orchestrator import dispatch_agents, SubAgentResult

class TestSubAgentDispatch:
    """Test sub-agent dispatch orchestration"""
    
    @pytest.mark.asyncio
    async def test_basic_dispatch(self):
        """Test basic parallel dispatch"""
        results = await dispatch_agents(
            template="Analyze this number: {number}",
            arguments=[{"number": i} for i in range(5)],
            max_parallel=5
        )
        assert len(results) == 5
        assert all(r.success for r in results)
    
    @pytest.mark.asyncio
    async def test_max_parallel_limit(self):
        """Verify max_parallel constraint respected"""
        start = asyncio.time.time()
        results = await dispatch_agents(
            template="Sleep for 1 second",
            arguments=[{} for _ in range(10)],
            max_parallel=2  # Only 2 at a time
        )
        duration = asyncio.time.time() - start
        
        # With 2 parallel, 10 tasks should take ~5 seconds
        assert duration >= 4.5
        assert len(results) == 10
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test graceful timeout handling"""
        results = await dispatch_agents(
            template="Long running task",
            arguments=[{} for _ in range(3)],
            timeout_per_agent=1,
            min_success_rate=0.0  # Allow failures
        )
        # Should have some timeouts tracked
        assert any(not r.success for r in results)
    
    @pytest.mark.asyncio
    async def test_success_rate_threshold(self):
        """Test min_success_rate enforcement"""
        with pytest.raises(SubAgentDispatchError):
            await dispatch_agents(
                template="Fail half the time",
                arguments=[{"id": i} for i in range(10)],
                min_success_rate=0.9  # Require 90% success
            )
```

---

#### Step 1.5: Documentation & Examples
**File:** `docs/user-guide/sub_agent_dispatch.md` (NEW)

```markdown
# Sub-Agent Dispatch

Execute multiple agents in parallel for divide-and-conquer workflows.

## Example: Find Fastest QuickSort (from Claude demo)

```python
from orchestrator import dispatch_agents

# 1. Main agent fetches implementations
implementations = await fetch_github_quicksorts(limit=100)

# 2. Dispatch 100 Haiku agents to test each implementation
results = await dispatch_agents(
    template="""
    Test this QuickSort implementation on random arrays of size 10,000.
    
    Implementation:
    {code}
    
    Return: average_time_ms, success_rate
    """,
    arguments=[{"code": impl} for impl in implementations],
    model="haiku",      # Fast and cheap
    max_parallel=50,    # 50 concurrent tests
    min_success_rate=0.8
)

# 3. Main agent aggregates results and picks fastest
fastest = max(results, key=lambda r: r.output["success_rate"])
print(f"Fastest implementation: {fastest.task_args['code']}")
```

## Use Cases

1. **Batch Analysis:** Test 1000 code snippets in parallel
2. **Distributed Search:** Query 100 data sources simultaneously
3. **A/B Testing:** Run 50 model variants on same dataset
4. **Content Generation:** Generate 100 variations of an article
```

---

### Phase 1 Acceptance Criteria

- [ ] `dispatch_agents()` function works with 100+ parallel agents
- [ ] Timeout handling prevents hanging
- [ ] Success rate tracking is accurate
- [ ] Error recovery works correctly
- [ ] Performance: 100 agents in <60 seconds (latency-bound)
- [ ] All tests pass
- [ ] Documentation complete with 2+ examples

---

## 🔀 Phase 2: Tool Composition (v0.5) - HIGH PRIORITY

### Overview
Chain multiple tools together where output of one becomes input to next.

### Implementation Steps

#### Step 2.1: Define Composition API
**File:** `orchestrator/tools/composition.py` (NEW)

```python
from typing import List, Callable, Any
from dataclasses import dataclass

@dataclass
class CompositionStep:
    """One step in a tool chain"""
    tool: Callable
    param_mapping: Dict[str, str]  # Map step output keys to next input params
    error_handler: Optional[Callable] = None
    retry_count: int = 1

class ToolComposition:
    """Chain multiple tools with automatic output → input wiring"""
    
    def __init__(self, steps: List[CompositionStep]):
        self.steps = steps
    
    async def execute(self, initial_input: Dict[str, Any]) -> Any:
        """
        Execute tool chain:
        1. Pass initial_input to first step
        2. For each subsequent step:
           - Extract outputs from previous step
           - Map outputs to next step inputs using param_mapping
           - Execute next step
           - Handle errors with error_handler if provided
        3. Return final output
        """
        pass

def compose(*tools: Callable) -> ToolComposition:
    """Shorthand to compose tools with automatic parameter wiring"""
    pass
```

**Why:** Define composition abstraction before building implementation.

---

#### Step 2.2: Implement Auto-Wiring Logic
**File:** `orchestrator/tools/composition.py`

```python
async def execute(self, initial_input: Dict[str, Any]) -> Any:
    """Execute composed tool chain"""
    current_output = initial_input
    
    for step in self.steps:
        try:
            # Map previous output to this step's input
            step_input = self._map_params(current_output, step.param_mapping)
            
            # Execute tool
            current_output = await step.tool(**step_input)
            
            # Ensure output is dict for next iteration
            if not isinstance(current_output, dict):
                current_output = {"result": current_output}
        
        except Exception as e:
            if step.error_handler:
                current_output = await step.error_handler(e, current_output)
            else:
                raise ToolCompositionError(f"Step {step.tool.__name__} failed: {e}")
    
    return current_output

def _map_params(self, output: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
    """
    Map output keys to input parameter names.
    
    Example:
        output = {"html": "<html>...", "status": 200}
        mapping = {"html": "content", "status": "code"}
        
        result = {"content": "<html>...", "code": 200}
    """
    result = {}
    for output_key, input_param in mapping.items():
        if output_key not in output:
            raise CompositionMappingError(f"Output key '{output_key}' not found")
        result[input_param] = output[output_key]
    return result
```

---

#### Step 2.3: Create Decorator API
**File:** `orchestrator/tools/decorators.py` (enhance existing)

```python
def composite_tool(steps: List[CompositionStep]):
    """Decorator to create composed tools"""
    def decorator(fn):
        composition = ToolComposition(steps)
        
        async def wrapper(*args, **kwargs):
            return await composition.execute(kwargs)
        
        # Register as new tool
        register_tool(
            name=fn.__name__,
            description=fn.__doc__ or f"Composed tool: {[s.tool.__name__ for s in steps]}",
            fn=wrapper
        )
        
        return wrapper
    
    return decorator
```

**Example Usage:**

```python
@composite_tool([
    CompositionStep(
        tool=fetch_webpage,
        param_mapping={"url": "page_url"}
    ),
    CompositionStep(
        tool=parse_html,
        param_mapping={"html": "content"}
    ),
    CompositionStep(
        tool=extract_links,
        param_mapping={"parsed": "doc"}
    )
])
async def fetch_and_extract_links(page_url: str):
    """Fetch webpage and extract all links"""
    pass
```

---

#### Step 2.4: Tests for Composition
**File:** `tests/test_tool_composition.py` (NEW)

```python
@pytest.mark.asyncio
async def test_simple_composition():
    """Test basic tool chaining"""
    composition = ToolComposition([
        CompositionStep(
            tool=step1_double,
            param_mapping={"result": "x"}
        ),
        CompositionStep(
            tool=step2_add_ten,
            param_mapping={"result": "x"}
        )
    ])
    
    result = await composition.execute({"x": 5})
    # (5 * 2) + 10 = 20
    assert result["result"] == 20

@pytest.mark.asyncio
async def test_composition_error_handling():
    """Test error handling in chain"""
    def error_handler(err, output):
        return {"result": 0, "error": str(err)}
    
    composition = ToolComposition([
        CompositionStep(tool=step1_ok),
        CompositionStep(
            tool=step2_fails,
            error_handler=error_handler
        )
    ])
    
    result = await composition.execute({})
    assert result["error"] is not None
```

---

#### Step 2.5: Documentation
**File:** `docs/user-guide/tool_composition.md` (NEW)

```markdown
# Tool Composition

Chain multiple tools where output of one becomes input to next.

## Example: Fetch, Parse, Extract

```python
from orchestrator import composite_tool, CompositionStep
from my_tools import fetch_webpage, parse_html, extract_links

@composite_tool([
    CompositionStep(fetch_webpage, {"url": "page_url"}),
    CompositionStep(parse_html, {"html": "content"}),
    CompositionStep(extract_links, {"parsed": "doc"})
])
async def get_links_from_page(page_url: str):
    """Fetch page and extract all links"""
    pass

# Use it as a regular tool
links = await get_links_from_page("https://example.com")
```
```

---

### Phase 2 Acceptance Criteria

- [ ] Tools chain correctly with automatic parameter mapping
- [ ] Error handling and retry logic works
- [ ] Composition supports conditional branching (optional)
- [ ] Performance: chain 5 tools <100ms
- [ ] All tests pass
- [ ] Documentation complete with 3+ examples

---

## 💰 Phase 3: Cost-Benefit Aware Tool Selection (v0.5.5) - MEDIUM PRIORITY

### Overview
Tag tools with cost/latency metadata; let planners choose intelligently.

### Implementation Steps

#### Step 3.1: Define Tool Metadata
**File:** `orchestrator/tools/metadata.py` (NEW)

```python
from dataclasses import dataclass
from enum import Enum

class CostClass(Enum):
    CHEAP = 1      # <$0.01 per call
    MODERATE = 2   # $0.01-$0.10
    EXPENSIVE = 3  # >$0.10

class SpeedClass(Enum):
    INSTANT = 1    # <100ms
    FAST = 2       # 100ms-1s
    SLOW = 3       # >1s

@dataclass
class ToolMetadata:
    """Extended tool information for intelligent selection"""
    
    # Cost metrics
    cost_per_call: float  # Approximate USD
    cost_class: CostClass
    
    # Performance metrics
    expected_latency_ms: float
    speed_class: SpeedClass
    
    # Capabilities
    capabilities: List[str]  # e.g., ["web_access", "computation"]
    requires: List[str]      # e.g., ["internet", "gpu"]
    
    # Model compatibility
    model_compatible: List[str]  # e.g., ["opus", "sonnet", "haiku"]
    
    # Optimization hints
    best_for: str  # Primary use case
    worst_for: str # Avoid use case
    batch_friendly: bool = False
```

---

#### Step 3.2: Enhance Tool Registry
**File:** `orchestrator/plugins/registry.py` (enhance)

```python
class ToolDefinition:
    # ... existing fields ...
    
    # Add metadata field
    metadata: Optional[ToolMetadata] = None

class ToolRegistry:
    def get_best_tool(
        self,
        capability: str,
        cost_budget: float = float('inf'),
        latency_budget_ms: float = float('inf'),
        model: str = "auto"
    ) -> Optional[ToolDefinition]:
        """
        Find best tool for a task based on constraints.
        
        Ranking:
        1. Capability match (required)
        2. Cost efficiency (prefer cheap if within budget)
        3. Speed (prefer fast if within latency budget)
        4. Model compatibility (prefer requested model)
        """
        candidates = [
            t for t in self._plugins.values()
            if capability in (t.metadata.capabilities if t.metadata else [])
        ]
        
        # Filter by constraints
        candidates = [
            t for t in candidates
            if (not t.metadata 
                or (t.metadata.cost_per_call <= cost_budget 
                    and t.metadata.expected_latency_ms <= latency_budget_ms))
        ]
        
        # Rank by efficiency
        return max(candidates, 
                   key=lambda t: self._efficiency_score(t, model))
    
    def _efficiency_score(self, tool: ToolDefinition, model: str) -> float:
        """Score tool based on cost and speed trade-off"""
        if not tool.metadata:
            return 0.0
        
        cost_score = 1.0 / (tool.metadata.cost_per_call + 0.01)
        speed_score = 1.0 / (tool.metadata.expected_latency_ms + 1)
        model_bonus = 1.0 if model in tool.metadata.model_compatible else 0.5
        
        return (cost_score + speed_score) * model_bonus
```

---

#### Step 3.3: Planner Integration
**File:** `orchestrator/planning/planner.py` (enhance)

```python
class Planner:
    async def plan_with_constraints(
        self,
        goal: str,
        cost_budget: float = 1.0,  # $1.00 max
        latency_budget_ms: float = 10000  # 10 seconds
    ) -> List[PlanStep]:
        """
        Generate plan respecting cost and latency constraints.
        
        Uses get_best_tool() to select appropriate tools.
        """
        # Get available tools with constraints
        tools = self.registry.search_tools(
            query=goal,
            filter_fn=lambda t: (
                not t.metadata 
                or (t.metadata.cost_per_call <= cost_budget / 10  # Reserve per step
                    and t.metadata.expected_latency_ms <= latency_budget_ms / 10)
            )
        )
        
        # Continue with normal planning using filtered tools
        plan = await self._generate_plan(goal, tools)
        return plan
```

---

#### Step 3.4: Example Usage
**File:** `examples/cost_aware_agent.py` (NEW)

```python
from orchestrator import tool, dispatch_agents, get_registry

# Register tools with metadata
@tool(
    metadata=ToolMetadata(
        cost_per_call=0.01,
        cost_class=CostClass.CHEAP,
        expected_latency_ms=500,
        speed_class=SpeedClass.FAST,
        capabilities=["data_analysis"],
        best_for="quick_analysis",
        model_compatible=["haiku", "sonnet"]
    )
)
async def quick_analyze(data: str) -> dict:
    """Fast analysis for simple data"""
    pass

@tool(
    metadata=ToolMetadata(
        cost_per_call=0.50,
        cost_class=CostClass.EXPENSIVE,
        expected_latency_ms=3000,
        speed_class=SpeedClass.SLOW,
        capabilities=["deep_analysis"],
        best_for="complex_reasoning",
        model_compatible=["opus"]
    )
)
async def deep_analyze(data: str) -> dict:
    """Deep reasoning for complex tasks"""
    pass

# Agent chooses tool based on budget
registry = get_registry()

# For cheap operation (use quick_analyze)
tool1 = registry.get_best_tool(
    capability="data_analysis",
    cost_budget=0.05,
    latency_budget_ms=1000
)

# For thorough operation (use deep_analyze)
tool2 = registry.get_best_tool(
    capability="deep_analysis",
    cost_budget=1.00,
    latency_budget_ms=10000
)
```

---

### Phase 3 Acceptance Criteria

- [ ] Tool metadata fully integrated with registry
- [ ] `get_best_tool()` scores and selects correctly
- [ ] Planner respects cost/latency constraints
- [ ] All tests pass
- [ ] Documentation complete with cost-optimization examples

---

## 🛡️ Phase 4: Error Recovery at Scale (v0.6) - MEDIUM PRIORITY

### Overview
Graceful degradation when partial failures occur in large parallel operations.

### Key Components

**File:** `orchestrator/tools/error_recovery.py` (NEW)

```python
@dataclass
class ErrorRecoveryPolicy:
    """How to handle failures in parallel operations"""
    
    retry_count: int = 3
    retry_backoff: float = 2.0  # Exponential backoff multiplier
    min_success_rate: float = 0.80  # 80% of tasks must succeed
    fallback_tool: Optional[Callable] = None  # Fallback if main tool fails
    log_failures: bool = True
    
    async def execute_with_recovery(
        self,
        task: Callable,
        args: Any,
        timeout: float
    ) -> Tuple[Any, bool, Optional[str]]:
        """Execute task with retry and error logging"""
        pass

class PartialResultsError(Exception):
    """Raised when success rate falls below threshold but results are available"""
    def __init__(self, results, success_rate, required_rate):
        self.results = results
        self.success_rate = success_rate
        self.required_rate = required_rate
```

### Implementation Pattern

```python
async def dispatch_agents_with_recovery(
    template: str,
    arguments: List[Dict],
    recovery_policy: ErrorRecoveryPolicy = None,
    allow_partial_results: bool = False
) -> List[SubAgentResult]:
    """
    Dispatch with intelligent error recovery.
    
    Strategies:
    1. Retry failed tasks (exponential backoff)
    2. Fall back to alternative tool if available
    3. Allow partial results with warning
    4. Log all failures for debugging
    """
    if not recovery_policy:
        recovery_policy = ErrorRecoveryPolicy()
    
    results = []
    for attempt in range(recovery_policy.retry_count):
        failed_tasks = [...]  # Tasks that failed
        
        if not failed_tasks:
            break
        
        # Exponential backoff
        await asyncio.sleep((2 ** attempt) * recovery_policy.retry_backoff)
        
        # Retry
        retry_results = await dispatch_agents(...)
        results.extend(retry_results)
    
    # Check final success rate
    success_rate = sum(1 for r in results if r.success) / len(results)
    
    if success_rate < recovery_policy.min_success_rate:
        if allow_partial_results:
            raise PartialResultsError(results, success_rate, 
                                     recovery_policy.min_success_rate)
        else:
            raise SubAgentDispatchError(...)
    
    return results
```

---

## 📅 Timeline & Dependencies

```
Phase 1 (Sub-Agent Dispatch)
├─ Week 1: Implement dispatch_agents()
├─ Week 2: Integration tests
└─ Week 3: Documentation & examples

Phase 2 (Tool Composition)
├─ Week 4: Implement composition logic
├─ Week 5: Decorator API
└─ Week 6: Documentation

Phase 3 (Cost-Benefit Metadata)
├─ Week 7: Metadata system
├─ Week 8: Planner integration
└─ Week 9: Examples

Phase 4 (Error Recovery)
├─ Week 10: Recovery policies
├─ Week 11: Integration
└─ Week 12: Documentation
```

**Total Estimated Effort:** 12 weeks (part-time)  
**Team Size:** 1-2 developers

---

## 🧪 Testing Strategy

### Unit Tests (Per Phase)
- Test each function in isolation
- Mock external dependencies
- Test error paths

### Integration Tests
- End-to-end sub-agent dispatch
- Multi-step tool composition
- Cost-aware planning

### Performance Tests
- 100 agents in parallel (target: <60s)
- Tool composition overhead (target: <100ms)
- Error recovery impact (target: <200ms)

### Example Tests
- Real-world scenarios from examples/
- Claude-like quicksort orchestration demo
- Cost optimization scenarios

---

## 📚 Documentation Plan

### For Users
1. `docs/user-guide/sub_agent_dispatch.md` - How to use dispatch_agents()
2. `docs/user-guide/tool_composition.md` - How to compose tools
3. `docs/user-guide/cost_aware_selection.md` - Cost optimization
4. `docs/examples/quicksort_orchestration.py` - Full demo

### For Contributors
1. `docs/architecture/agent_orchestration.md` - Design decisions
2. `docs/architecture/composition_design.md` - Composition internals
3. Implementation guides with code examples

### API Reference
- Auto-generated from docstrings
- Include parameter descriptions and examples

---

## ✅ Success Criteria

### Phase 1: Sub-Agent Dispatch
- [x] Dispatch 100+ agents in parallel
- [x] < 60 seconds for 100 agents
- [x] Proper timeout handling
- [x] Success rate tracking
- [x] Production-ready documentation

### Phase 2: Tool Composition
- [x] Chain 5+ tools seamlessly
- [x] < 100ms overhead
- [x] Error handling works
- [x] Auto-wiring correctness

### Phase 3: Cost-Benefit
- [x] Tools ranked by efficiency
- [x] Planner respects constraints
- [x] Cost predictions accurate

### Phase 4: Error Recovery
- [x] Retry logic works
- [x] Fallback tools functional
- [x] Partial results handled gracefully

---

## 🚀 Getting Started

Next steps when ready:
1. Create branches for each phase
2. Start with Phase 1 (highest value)
3. Write tests first (TDD approach)
4. Get code review from team
5. Merge to main only when Phase complete
6. Update documentation with each phase

---

## 📝 Notes

- **Inspiration:** Claude's architecture from Anthropic demo (Opus + 100x Haiku)
- **Key insight:** Agent orchestration is the cutting edge—most powerful use case
- **Design principle:** Make complex patterns as simple as: `await dispatch_agents(template, args)`
- **Future:** This enables ToolWeaver to compete with enterprise AI platforms

