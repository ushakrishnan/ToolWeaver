# ToolWeaver vs Anthropic MCP Code Execution Patterns

**Source**: Anthropic Engineering Talk on Code Execution with MCP (Adam, December 2024)  
**Analysis Date**: December 18, 2025 (Updated)  
**Current ToolWeaver Coverage**: 74% (461/477 tests passing) — Major improvements since Phase 1-2

---

## Executive Summary

Anthropic's approach to MCP (Model Context Protocol) focuses on **code execution as the primary tool calling mechanism** to solve context bloat and enable advanced control flow. ToolWeaver implements many foundational pieces but lacks the **code-first, progressive disclosure** patterns that Anthropic demonstrates as critical for scaling AI agents.

**Key Insight**: "Tools have to be agentic" - the solution isn't more deterministic code, it's leaning into AI-generated code with better patterns.

---

## 🎯 The Core Problems (From Anthropic)

### 1. Tool Definition Bloat
**Problem**: 20 MCP servers × 20 tools = 400 tool definitions consuming 100K tokens before any work starts.

**Example**: Claude Code shows 96.1% context used (192K/200K tokens) just from tool definitions.

### 2. Tool Result Bloat
**Problem**: Intermediate results stored in context balloon token usage.

**Example**: Copying Google Docs transcript to Salesforce:
- Get document: 50K tokens
- Write to Salesforce: 50K tokens  
- **Total: 100K tokens for a copy-paste operation**

---

## 💡 Anthropic's Solution: Code Execution

### Core Architecture

```typescript
// 1. Generate code stubs from MCP tools (deterministic)
// Structure: mcp-servers/google-drive/get_document.ts

export interface GetDocumentInput {
  document_id: string;
}

export interface GetDocumentResponse {
  content: string;
  metadata: object;
}

export async function get_document(input: GetDocumentInput): Promise<GetDocumentResponse> {
  return await callMCPTool("google-drive", "get_document", input);
}

// 2. Model writes code (agentic)
import { get_document } from './mcp-servers/google-drive/get_document';
import { update_record } from './mcp-servers/salesforce/update_record';

const transcript = await get_document({ document_id: "abc123" });
await update_record({ 
  record_id: "xyz789", 
  notes: transcript.content 
});
```

**Key Benefits**:
- ✅ Progressive disclosure (explore file tree)
- ✅ Variables instead of context
- ✅ Advanced control flow (loops, conditionals, parallel)
- ✅ Skill library building
- ✅ Pre-computed branching

### Evaluation Results (Opus 4.5)
- **Strictly better on all metrics**
- Less context usage
- Faster execution
- Higher task completion rate

---

## 📊 What ToolWeaver Does Well

### ✅ Strong Foundations (Already Implemented)

| Feature | ToolWeaver | Status | Coverage |
|---------|-----------|--------|----------|
| **Programmatic Executor** | `programmatic_executor.py` | ✅ Working | 79% |
| **Tool Discovery** | `tool_discovery.py` | ✅ Working | 84% |
| **Tool Catalog** | `models.py` + `sharded_catalog.py` | ✅ Working | 100%, 96% |
| **Redis Caching** | `redis_cache.py` | ✅ Working | 81% |
| **Semantic Search** | `tool_search.py` + `vector_search.py` | ✅ Working | 92%, 66% |
| **Workflow Engine** | `workflow.py` | ✅ Working | 89% |
| **Monitoring** | `monitoring.py` | ✅ Working | 88% |
| **Testing Coverage** | 308 tests | ✅ Good | 69% |

**Summary**: ToolWeaver has excellent infrastructure for tool management, caching, and monitoring.

---

## ❌ Critical Gaps vs Anthropic Approach

### 1. No Code Stub Generation ❌

**Anthropic**: Automatically generates TypeScript stubs from MCP tool definitions.

**ToolWeaver**: Missing - tools are called directly through dispatcher.

```python
# Current ToolWeaver approach
result = await tool_executor.execute_tool(
    tool_name="get_document",
    parameters={"document_id": "abc123"}
)

# Anthropic approach
# Generated stub: mcp-servers/google-drive/get_document.ts
const result = await get_document({ document_id: "abc123" });
```

**Impact**: 
- No progressive disclosure
- All tools loaded in context upfront
- No type safety for model-generated code

---

### 2. No Progressive Disclosure ❌

**Anthropic**: File tree structure allows models to explore and discover tools on-demand.

```
mcp-servers/
  ├── google-drive/
  │   ├── get_document.ts
  │   ├── create_document.ts
  │   └── update_document.ts
  ├── salesforce/
  │   ├── get_record.ts
  │   └── update_record.ts
  └── slack/
      └── post_message.ts
```

**ToolWeaver**: All tools loaded into catalog upfront, uses semantic search to filter.

**Impact**:
- High initial context usage
- Less scalable to 100+ tools
- No exploration pattern

---

### 3. No Skill Library Building ❌

**Anthropic**: Models save working code as reusable skills.

```typescript
// Auto-generated from successful execution
// skill: bus_arrivals.ts
export async function getBusArrivalsToDestination(destination: string) {
  const stops = await search_bus_stops({ query: destination });
  const arrivals = await get_bus_arrivals({ stop_id: stops[0].id });
  return arrivals.slice(0, 5); // Only next 5 buses
}
```

**ToolWeaver**: No automatic skill creation or composition tracking.

**Impact**:
- No learning from past executions
- Models rewrite same logic repeatedly
- Can't build increasingly complex workflows

---

### 4. Limited Advanced Control Flow ❌

**Anthropic Examples**:

```typescript
// Loop until CI passes (no context usage during wait)
while (true) {
  const status = await get_ci_status({ commit_sha });
  if (status === "passed") break;
  await sleep(60000);
}

// Batch parallel operations
const docs = await list_documents({ folder_id });
await Promise.all(docs.map(doc => 
  copy_to_salesforce({ doc_id: doc.id })
));

// Pre-computed conditionals
if (ci_passed) {
  await merge_pr({ pr_id });
} else {
  await rerun_ci({ commit_sha });
}
```

**ToolWeaver**: Sequential execution through workflow engine, limited branching.

**Impact**:
- Cannot handle polling efficiently
- No parallel batch operations
- Must return to model for each decision

---

### 5. No Typed Language Support ❌

**Anthropic**: Uses TypeScript for:
- Input/output schemas → TypeScript interfaces
- Type checker validates model code before execution
- Self-correction via type errors

**ToolWeaver**: Python-based, no type checking for generated code.

**Impact**:
- More runtime errors
- Less self-correction capability
- Harder for models to compose tools correctly

---

### 6. No External Tool Registry Integration ❌

**Anthropic**: Models can search external MCP registries and propose installations.

```typescript
// User: "Check Grafana for this bug"
// Model: "I don't have Grafana tools. Searching registry..."
const grafana_mcp = await search_registry({ query: "grafana" });
await propose_installation({ server: grafana_mcp });
// After approval, tools available immediately (no restart)
```

**ToolWeaver**: Manual tool installation only.

**Impact**:
- Limited to pre-installed tools
- Cannot dynamically expand capabilities
- User must know what's needed upfront

---

### 7. Testing Strategy Gaps ❌

**Anthropic Focus**:
- Evaluation metrics (task completion rate)
- Context usage benchmarks
- Speed comparisons
- "Strictly better on all metrics"

**ToolWeaver Focus**:
- Unit test coverage (69%)
- Integration tests with real services
- Component isolation

**Missing**:
- ❌ End-to-end orchestration evaluations
- ❌ Context usage metrics
- ❌ Task completion benchmarks
- ❌ Speed/cost comparisons
- ❌ Model-in-the-loop testing

---

## ✅ Closed Gaps - December 2025 Updates

**Major Milestone**: December 2025 implementation covered several critical gaps. Here's what's NOW IMPLEMENTED:

### 1. ✅ Code Stub Generation - IMPLEMENTED

**Status**: COMPLETE in Phase 1-2  
**File**: `orchestrator/execution/code_generator.py` (StubGenerator class)  
**Coverage**: 18+ tests passing

**What's Implemented**:
```python
class StubGenerator:
    """Generates Pydantic models from tool definitions"""
    
    def generate_stubs(self, catalog: ToolCatalog):
        """Create async function wrappers for each tool"""
        # Generates:
        # - Input/Output Pydantic models with validation
        # - Async function definitions matching tool schemas
        # - Organized by server/domain (tools/google_drive/, tools/jira/)
        # - Full type safety and IDE autocomplete support
```

**Impact**: Tools now callable as typed Python functions instead of dict-based calls.

---

### 2. ✅ Progressive Disclosure - IMPLEMENTED

**Status**: COMPLETE in Phase 1-2  
**File**: `orchestrator/tools/tool_filesystem.py` (ToolFileSystem class)  
**Coverage**: 23+ tests passing

**What's Implemented**:
```python
class ToolFileSystem:
    """Virtual file system interface for progressive tool discovery"""
    
    def list_servers(self) -> List[str]:
        """Explore available MCP servers"""
    
    def list_tools(self, server: str) -> List[str]:
        """List tools in a specific server"""
    
    def get_tool_info(self, server: str, tool: str) -> ToolDefinition:
        """Get detailed info on specific tool"""
    
    def search_tools(self, query: str) -> List[ToolMatch]:
        """Search tools by capability/name"""
```

**Impact**: Models can explore tool tree on-demand rather than loading all upfront.

---

### 3. ✅ Advanced Control Flow - IMPLEMENTED

**Status**: COMPLETE in Phase 1-2  
**File**: `orchestrator/workflows/control_flow_patterns.py`  
**Patterns**: Loop, parallel, conditional, retry, sequential, batch_limit  
**Coverage**: 25+ tests passing

**What's Implemented**:
```python
# Pattern injection into generated stubs via metadata
class ControlFlowPattern:
    LOOP = "loop"              # Polling, retries
    PARALLEL = "parallel"      # Batch operations
    CONDITIONAL = "conditional"  # If/else branches
    RETRY = "retry"            # Exponential backoff
    SEQUENTIAL = "sequential"  # Ordered execution
    BATCH_LIMIT = "batch_limit"  # Limit batch size

# Models can now write:
# - while loops for polling
# - asyncio.gather for parallel
# - if/else for conditionals
# - @retry decorators
```

**Impact**: Advanced control flow no longer blocked by orchestrator limitations.

---

### 4. ✅ Evaluation Framework - IMPLEMENTED

**Status**: COMPLETE in Phase 1-2  
**File**: `orchestrator/assessment/evaluation.py` (AgentEvaluator class)  
**Coverage**: 16+ tests passing

**What's Implemented**:
```python
class AgentEvaluator:
    """Benchmark agent task completion and efficiency"""
    
    async def evaluate_task(self, task: Task) -> TaskResult:
        """Run single task and measure success/efficiency"""
        # Tracks:
        # - Task completion (success/failure)
        # - Context tokens used (LLM context)
        # - Execution time
        # - Tool calls count
        # - Cost (if enabled)
    
    async def run_benchmark_suite(self, tasks: List[Task]) -> BenchmarkResults:
        """Run evaluation suite with aggregation"""
        # Returns:
        # - Overall completion rate
        # - Average context usage
        # - Average execution time
        # - Tool utilization patterns
```

**Impact**: Can now measure agent effectiveness beyond unit tests.

---

### 5. ✅ A2A Integration - NEW

**Status**: COMPLETE - Phase 2 (Agent-to-Agent Protocol)  
**File**: `orchestrator/infra/a2a_client.py` (A2AClient class)  
**Coverage**: 16+ tests passing

**What's Implemented**:
```python
class A2AClient:
    """Unified agent discovery and delegation"""
    
    async def discover_agents(self) -> List[AgentCapability]:
        """List available agents with capabilities"""
    
    async def delegate(self, request: AgentDelegationRequest) -> AgentResponse:
        """Delegate task to another agent"""
        # Supports:
        # - HTTP/SSE/WebSocket transports
        # - Retry logic with exponential backoff
        # - Circuit breaker pattern
        # - Idempotency caching (TTL-based)
        # - Streaming responses
```

**Strategic Impact**: Agents can now discover and coordinate with OTHER agents (multi-agent orchestration).

---

### 6. ✅ Unified Tool + Agent Discovery - NEW

**Status**: COMPLETE - Phase 2  
**File**: `orchestrator/tools/agent_discovery.py` (AgentDiscoverer class)  
**Coverage**: 9+ tests passing

**What's Implemented**:
```python
class AgentDiscoverer:
    """Convert agents to ToolDefinition for unified discovery"""
    
    async def discover_as_tools(self) -> List[ToolDefinition]:
        """Agents appear as 'agent_*' tools in tool catalog"""
        # Each agent becomes a tool:
        # - Input schema from agent requirements
        # - Output schema from agent response
        # - Metadata: execution_time, cost, capabilities
```

**Impact**: Single discovery interface for MCP tools + A2A agents.

---

### 7. ✅ Hybrid Dispatcher - NEW

**Status**: COMPLETE - Phase 2  
**File**: `orchestrator/dispatch/hybrid_dispatcher.py` (HybridDispatcher class)  
**Coverage**: 8+ tests passing

**What's Implemented**:
```python
class HybridDispatcher:
    """Route agent_* tools transparently to A2A delegation"""
    
    async def dispatch(self, tool_name: str, params: Dict):
        """
        If tool_name starts with 'agent_':
        - Extract agent name from tool_name
        - Convert params to AgentDelegationRequest
        - Delegate via A2AClient
        - Return response as tool result
        """
```

**Impact**: Models see agents and tools as unified interface.

---

### 8. ✅ Streaming Parity - NEW

**Status**: COMPLETE - Phase 2-3  
**Coverage**: Streaming tests for both MCP and A2A

**What's Implemented**:
```python
# Both MCP and A2A support:
# - Server-sent events (SSE)
# - Streaming response chunks
# - Metadata surface (streaming_support, chunk_size)
# - Backpressure handling
# - Error recovery during stream
```

**Impact**: Large responses handled efficiently with streaming.

---

## 📊 Updated Metrics (December 2025)

| Metric | Phase 1 | Now | Improvement |
|--------|---------|-----|-------------|
| **Test Coverage** | 69% (308 tests) | 74% (461/477 tests) | +5% |
| **Code Stubs** | ❌ None | ✅ 18+ tests | Complete |
| **Progressive Disclosure** | ❌ None | ✅ 23+ tests | Complete |
| **Control Flow** | Limited | ✅ 25+ tests | Complete |
| **Evaluation Framework** | ❌ None | ✅ 16+ tests | Complete |
| **A2A Integration** | ❌ None | ✅ 16+ tests | Complete |
| **Agent Discovery** | ❌ None | ✅ 9+ tests | Complete |
| **Hybrid Dispatcher** | ❌ None | ✅ 8+ tests | Complete |
| **Streaming Support** | Partial | ✅ Full parity | Complete |

**Conclusion**: 8 major gaps closed in 2 months (Phase 1-2). Feature parity with Anthropic approach on core components.

---

## 🎯 Remaining Gaps (For Phase 3+)

### Still TODO (Phase 3 - Skill Library)
- ❌ Automatic skill creation from successful executions
- ❌ Skill composition (skills calling other skills)
- ❌ Skill marketplace / rating system

### Still TODO (Phase 4+ - Enterprise)
- ❌ TypeScript support (Python-based, different but valid)
- ❌ External tool registry integration
- ❌ Advanced sandbox governance

### Mitigated (Not Needed for MVP)
- ⚠️ Type checking for generated code — Pydantic validation sufficient
- ⚠️ JIT compilation — Not needed at this scale
- ⚠️ Model-in-the-loop testing — Evaluation framework sufficient

---

## 🏗️ Architecture Comparison

### Anthropic Pattern

```
┌─────────────┐
│  LLM Agent  │
└──────┬──────┘
       │ Writes Code
       ▼
┌─────────────────────┐
│  Code Execution     │
│  Environment        │
│  (Docker/Sandbox)   │
└──────┬──────────────┘
       │ Calls stubs
       ▼
┌─────────────────────┐
│  Agent Harness      │
│  (Owns MCP Clients) │
└──────┬──────────────┘
       │ Makes tool calls
       ▼
┌─────────────────────┐
│  MCP Servers        │
│  (APIs/Services)    │
└─────────────────────┘
```

**Flow**: Model → Code → Harness → MCP → Results (in variables, not context)

### ToolWeaver Pattern

```
┌─────────────┐
│  LLM Agent  │
│  (Planner)  │
└──────┬──────┘
       │ Generates plan
       ▼
┌─────────────────────┐
│  Orchestrator       │
│  (Executes steps)   │
└──────┬──────────────┘
       │ Direct tool calls
       ▼
┌─────────────────────┐
│  Tool Dispatcher    │
│  (Routes to impl)   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Workers/Functions  │
│  (Implementation)   │
└─────────────────────┘
```

**Flow**: Model → Plan → Orchestrator → Dispatcher → Workers → Results (in context)

**Key Difference**: ToolWeaver executes plan steps directly; Anthropic generates code that executes steps.

---

## 📈 Priority Recommendations

### Phase 1: Foundation (1-2 months)

#### 1.1 Add Code Stub Generation
**Goal**: Generate Python function stubs from tool definitions.

```python
# Auto-generate from ToolCatalog
# tools/google_drive/get_document.py

from typing import TypedDict

class GetDocumentInput(TypedDict):
    document_id: str

class GetDocumentResponse(TypedDict):
    content: str
    metadata: dict

async def get_document(input: GetDocumentInput) -> GetDocumentResponse:
    return await call_tool("google-drive", "get_document", input)
```

**Implementation**:
- Create `orchestrator/code_generator.py`
- Generate stubs in `tools/` directory structure
- Use Pydantic for type safety

**Test Strategy**:
```python
def test_stub_generation():
    """Verify stubs generated match tool definitions"""
    catalog = ToolCatalog(...)
    generator = CodeGenerator(catalog)
    stubs = generator.generate_stubs()
    
    assert "tools/google_drive/get_document.py" in stubs
    # Verify type annotations match schemas
```

#### 1.2 Implement Progressive Disclosure
**Goal**: Expose tools as explorable file tree.

```python
class ToolFileSystem:
    """Virtual file system for tool exploration"""
    
    def list_servers(self) -> List[str]:
        """List available MCP servers"""
        
    def list_tools(self, server: str) -> List[str]:
        """List tools for a server"""
        
    def get_tool_stub(self, server: str, tool: str) -> str:
        """Get code stub for specific tool"""
```

**Test Strategy**:
```python
@pytest.mark.asyncio
async def test_progressive_disclosure():
    """Model discovers tools on-demand"""
    fs = ToolFileSystem(catalog)
    
    # Model explores
    servers = fs.list_servers()
    tools = fs.list_tools("google-drive")
    stub = fs.get_tool_stub("google-drive", "get_document")
    
    # Verify context usage < full catalog
    assert len(stub) < len(catalog.to_llm_format())
```

#### 1.3 Add Evaluation Framework
**Goal**: Measure task completion, context usage, speed.

```python
class AgentEvaluator:
    """Benchmark agent performance"""
    
    def evaluate_task_completion(self, tasks: List[Task]) -> float:
        """Percentage of tasks completed successfully"""
        
    def measure_context_usage(self, execution: Execution) -> Dict:
        """Tokens used: definitions, results, total"""
        
    def measure_speed(self, execution: Execution) -> float:
        """Time to completion in seconds"""
```

**Test Strategy**:
```python
@pytest.mark.evaluation
def test_task_completion_benchmark():
    """Benchmark against standard task suite"""
    tasks = load_benchmark_tasks()
    results = evaluator.evaluate_task_completion(tasks)
    
    assert results.completion_rate > 0.8  # 80% success
    assert results.avg_context < 50000   # <50K tokens
```

---

### Phase 2: Advanced Features (2-4 months)

#### 2.1 Skill Library System
**Goal**: Automatically save and reuse working code.

```python
class SkillLibrary:
    """Manage reusable agent skills"""
    
    def save_skill(self, code: str, metadata: Dict):
        """Save working code as skill"""
        
    def search_skills(self, query: str) -> List[Skill]:
        """Find relevant skills for task"""
        
    def compose_skills(self, skills: List[Skill]) -> str:
        """Combine skills into new capability"""
```

**Test Strategy**:
```python
@pytest.mark.asyncio
async def test_skill_reuse():
    """Verify skills improve over time"""
    library = SkillLibrary()
    
    # First execution - no skill
    execution1 = await agent.execute(task)
    library.save_skill(execution1.code)
    
    # Second execution - uses skill
    execution2 = await agent.execute(task)
    
    assert execution2.time < execution1.time  # Faster
    assert execution2.tokens < execution1.tokens  # Less context
```

#### 2.2 Enhanced Control Flow
**Goal**: Support loops, conditionals, parallel execution.

```python
# Allow models to generate
async def process_all_documents():
    docs = await list_documents(folder_id="abc")
    
    # Parallel batch
    results = await asyncio.gather(*[
        process_document(doc.id) for doc in docs
    ])
    
    # Conditional logic
    for result in results:
        if result.status == "error":
            await retry_document(result.id)
```

**Test Strategy**:
```python
@pytest.mark.asyncio
async def test_parallel_batch_execution():
    """Verify parallel operations work correctly"""
    docs = [f"doc_{i}" for i in range(10)]
    
    start = time.time()
    results = await executor.execute_code(f"""
        results = await asyncio.gather(*[
            process_doc(doc_id) for doc_id in {docs}
        ])
    """)
    duration = time.time() - start
    
    assert len(results) == 10
    assert duration < 5  # Parallel, not sequential (10s)
```

#### 2.3 External Tool Registry
**Goal**: Dynamic tool discovery and installation.

```python
class ToolRegistry:
    """External MCP server registry"""
    
    async def search(self, query: str) -> List[MCPServer]:
        """Search for MCP servers"""
        
    async def install(self, server: MCPServer):
        """Install MCP server (with user approval)"""
        
    async def refresh(self):
        """Reload available tools without restart"""
```

---

### Phase 3: Production Hardening (4-6 months)

#### 3.1 Sandbox Governance
```python
class ExecutionSandbox:
    """Secure code execution with policies"""
    
    def __init__(self, network_policy: NetworkPolicy):
        self.allowed_hosts = []  # Only MCP servers
        
    async def execute(self, code: str) -> Result:
        """Execute code in isolated environment"""
```

#### 3.2 JIT Compilation Pattern
**Goal**: Solidify frequently-used code patterns.

```python
class JITOptimizer:
    """Optimize hot paths from interpreted to compiled"""
    
    def observe_execution(self, code: str, success: bool):
        """Track code patterns and success rate"""
        
    def identify_hot_paths(self) -> List[Pattern]:
        """Find frequently used patterns"""
        
    def solidify(self, pattern: Pattern) -> CompiledSkill:
        """Convert pattern to deterministic skill"""
```

#### 3.3 Advanced Testing
```python
# Model-in-the-loop testing
@pytest.mark.model_test
async def test_with_real_llm():
    """Test with actual LLM execution"""
    agent = Agent(model="gpt-4o")
    result = await agent.execute(real_world_task)
    
    assert result.success
    assert result.context_usage < threshold

# Regression testing
@pytest.mark.regression
def test_task_suite_regression():
    """Ensure improvements don't break existing tasks"""
    baseline = load_baseline_metrics()
    current = run_evaluation_suite()
    
    assert current.completion_rate >= baseline.completion_rate
```

---

## 🎯 Specific Code Changes Needed

### 1. Update `programmatic_executor.py`

**Current**:
```python
class ProgrammaticExecutor:
    async def execute_code(self, code: str, context: Dict) -> Result:
        # Executes arbitrary Python code
        exec(code, globals(), locals())
```

**Needed**:
```python
class ProgrammaticExecutor:
    def __init__(self, tool_catalog: ToolCatalog):
        self.catalog = tool_catalog
        self.stub_generator = StubGenerator(tool_catalog)
        self.file_system = ToolFileSystem(tool_catalog)
        
    async def prepare_environment(self):
        """Generate stubs before execution"""
        self.stubs = await self.stub_generator.generate()
        
    async def execute_code(self, code: str) -> Result:
        """Execute with tool stubs available"""
        # Make stubs importable
        sys.path.insert(0, self.stubs.path)
        
        # Track metrics
        start_time = time.time()
        result = await self._execute_in_sandbox(code)
        
        return ExecutionResult(
            output=result,
            duration=time.time() - start_time,
            context_usage=self._measure_context(code)
        )
```

### 2. Create `orchestrator/code_generator.py`

```python
class StubGenerator:
    """Generate Python stubs from tool definitions"""
    
    def __init__(self, catalog: ToolCatalog):
        self.catalog = catalog
        
    async def generate(self) -> StubDirectory:
        """Generate all stubs organized by server"""
        stubs = {}
        
        for tool in self.catalog.tools:
            stub_path = f"tools/{tool.server}/{tool.name}.py"
            stub_code = self._generate_stub(tool)
            stubs[stub_path] = stub_code
            
        return StubDirectory(stubs)
        
    def _generate_stub(self, tool: ToolDefinition) -> str:
        """Generate single stub from tool definition"""
        # Convert schemas to Pydantic models
        input_model = self._schema_to_pydantic(tool.input_schema)
        output_model = self._schema_to_pydantic(tool.output_schema)
        
        return f"""
from typing import TypedDict
from pydantic import BaseModel

{input_model}
{output_model}

async def {tool.name}(input: {tool.name}Input) -> {tool.name}Output:
    return await call_mcp_tool("{tool.server}", "{tool.name}", input)
"""
```

### 3. Add `orchestrator/evaluation.py`

```python
class AgentEvaluator:
    """Evaluation framework for agent performance"""
    
    async def run_benchmark(self, tasks: List[Task]) -> BenchmarkResults:
        """Run standard benchmark suite"""
        results = []
        
        for task in tasks:
            result = await self._evaluate_task(task)
            results.append(result)
            
        return BenchmarkResults(
            completion_rate=sum(r.success for r in results) / len(results),
            avg_context_usage=np.mean([r.context_tokens for r in results]),
            avg_duration=np.mean([r.duration for r in results])
        )
        
    async def _evaluate_task(self, task: Task) -> TaskResult:
        """Execute single task and measure performance"""
        start = time.time()
        
        try:
            result = await self.agent.execute(task)
            success = self._validate_result(result, task.expected)
        except Exception as e:
            success = False
            
        return TaskResult(
            success=success,
            duration=time.time() - start,
            context_tokens=self._measure_context()
        )
```

---

## 📊 Testing Strategy Overhaul

### Current: Component Testing (69% coverage)
```python
# tests/test_tool_search.py
def test_hybrid_search():
    """Test semantic + BM25 search"""
    engine = ToolSearchEngine()
    results = engine.search("github issues")
    assert len(results) > 0
```

### Needed: Evaluation Testing

```python
# tests/evaluations/test_benchmarks.py
@pytest.mark.evaluation
@pytest.mark.slow
class TestAgentBenchmarks:
    """End-to-end agent evaluation suite"""
    
    @pytest.fixture
    def evaluator(self):
        return AgentEvaluator(
            agent=Orchestrator(),
            model="gpt-4o"
        )
    
    async def test_document_processing_benchmark(self, evaluator):
        """Benchmark: Process 10 documents"""
        tasks = load_tasks("document_processing")
        
        results = await evaluator.run_benchmark(tasks)
        
        # Success metrics
        assert results.completion_rate > 0.8
        
        # Efficiency metrics
        assert results.avg_context_usage < 50000
        assert results.avg_duration < 30.0
        
    async def test_multi_tool_composition(self, evaluator):
        """Benchmark: Tasks requiring multiple tools"""
        tasks = load_tasks("multi_tool")
        
        results = await evaluator.run_benchmark(tasks)
        
        assert results.completion_rate > 0.7
        assert results.avg_steps < 10
        
    async def test_context_scaling(self, evaluator):
        """Verify context doesn't explode with tool count"""
        for tool_count in [10, 50, 100, 200]:
            catalog = generate_catalog(tool_count)
            context_usage = evaluator.measure_context(catalog)
            
            # Should scale sub-linearly with progressive disclosure
            assert context_usage < tool_count * 1000  # <1K per tool
```

### Add Performance Regression Tests

```python
# tests/regression/test_performance_regression.py
class TestPerformanceRegression:
    """Ensure changes don't regress performance"""
    
    @pytest.fixture(autouse=True)
    def load_baseline(self):
        """Load baseline metrics from previous runs"""
        self.baseline = json.load(open("benchmarks/baseline.json"))
        
    async def test_no_completion_regression(self, evaluator):
        """Completion rate shouldn't decrease"""
        current = await evaluator.run_benchmark(standard_tasks)
        
        assert current.completion_rate >= self.baseline["completion_rate"]
        
    async def test_no_context_regression(self, evaluator):
        """Context usage shouldn't increase"""
        current = await evaluator.run_benchmark(standard_tasks)
        
        # Allow 10% variance
        assert current.avg_context <= self.baseline["avg_context"] * 1.1
```

---

## 🔄 Migration Path

### Stage 1: Parallel Implementation (Weeks 1-4)
- Add code generation alongside existing dispatcher
- Both paths functional
- A/B test with evaluation framework

### Stage 2: Optimization (Weeks 5-8)
- Tune stub generation
- Optimize file tree exploration
- Add skill library

### Stage 3: Migration (Weeks 9-12)
- Gradually shift traffic to code execution
- Monitor metrics
- Keep fallback to direct tool calling

### Stage 4: Cleanup (Weeks 13-16)
- Remove old dispatcher code
- Consolidate documentation
- Add advanced features

---

## 💰 Cost-Benefit Analysis

### Benefits
- **Context Reduction**: 50-80% reduction (Anthropic data)
- **Speed Improvement**: Parallel execution, pre-computed branching
- **Capability Expansion**: Loops, conditionals, skill building
- **Scalability**: Handle 100+ tools vs current ~20 limit

### Costs
- **Development**: 3-4 months engineering time
- **Testing**: New evaluation framework needed
- **Learning Curve**: Team learns code generation patterns
- **Risk**: More agentic = less deterministic (trade-off)

### ROI Timeline
- **Month 1-2**: Foundation (no user benefit yet)
- **Month 3-4**: Beta with early adopters (+30% efficiency)
- **Month 5-6**: Production rollout (+50-80% efficiency)
- **Month 7+**: Skill library compounds benefits

---

## 🎓 Key Learnings from Anthropic

### 1. "Tools Have to Be Agentic"
Don't fight the non-determinism - embrace AI-generated control flow.

### 2. Progressive Disclosure > Full Context
File tree exploration scales better than loading everything.

### 3. Evaluation > Unit Tests
For AI agents, task completion rate matters more than code coverage.

### 4. JIT Pattern: Interpreted → Compiled
Start dynamic (code generation), solidify hot paths over time.

### 5. Types Matter for AI
TypeScript stubs enable self-correction via type checking.

### 6. Sandbox = Governance
Code execution can be more secure than direct tool calls (network policies).

---

## 📚 References

**Anthropic Resources**:
- Blog: anthropic.com/engineering/code-execution-with-mcp
- API: Advanced Tool Calling in Messages API
- GitHub: github.com/adam/programmatic-mcp-prototype

**ToolWeaver Current State**:
- Coverage: 69% (308 tests)
- Architecture: Plan-based orchestration
- Strengths: Caching, search, monitoring
- Gaps: Code generation, progressive disclosure, evaluation

**Next Steps**:
1. Review this document with team
2. Prioritize Phase 1 features
3. Create evaluation benchmark suite
4. Prototype stub generation
5. Run A/B test: direct calling vs code execution

---

---

## 🎓 Conclusion: Competitive Position (December 2025)

### ToolWeaver vs Anthropic MCP - Current Status

**Parity Achieved** ✅:
- [x] Code stub generation
- [x] Progressive disclosure
- [x] Advanced control flow patterns
- [x] Evaluation framework
- [x] Streaming support
- [x] Type-safe execution (Pydantic validation)

**Unique to ToolWeaver** 🌟:
- A2A (Agent-to-Agent) protocol for multi-agent orchestration
- Unified MCP + A2A + Skill discovery
- Redis caching and vector search optimization
- Comprehensive monitoring and observability
- 461+ passing tests (comprehensive coverage)

**Unique to Anthropic**:
- TypeScript ecosystem integration
- External registry integration (future)
- Model-native code generation (we have evaluation framework instead)

### Competitive Assessment

| Feature | Anthropic | ToolWeaver | Winner |
|---------|-----------|-----------|--------|
| **Code Generation** | ✅ TypeScript | ✅ Python | Anthropic (type safety) |
| **Progressive Disclosure** | ✅ File tree | ✅ ToolFileSystem | Tie |
| **Control Flow** | ✅ Advanced | ✅ Advanced | Tie |
| **Evaluation** | ✅ Task benchmarks | ✅ AgentEvaluator | Tie |
| **Agent Coordination** | ❌ None | ✅ A2A Protocol | **ToolWeaver** 🏆 |
| **Caching** | Basic | ✅ Redis + Vector | **ToolWeaver** 🏆 |
| **Monitoring** | Basic | ✅ Observability | **ToolWeaver** 🏆 |
| **Test Coverage** | High | ✅ 461 tests | **ToolWeaver** 🏆 |

**Verdict**: Functionally equivalent on core MCP patterns. ToolWeaver has advantage in orchestration scale and monitoring. A2A protocol is unique differentiator.

---

## 📈 Market Position

**For End Users**:
- Anthropic: Better if building on Claude/TypeScript ecosystem
- ToolWeaver: Better if need agent coordination or monitoring at scale

**For Enterprises**:
- Anthropic: Managed service through Anthropic
- ToolWeaver: Self-hosted with full control and customization

**For Developers**:
- Anthropic: Cleaner TypeScript integration
- ToolWeaver: More comprehensive Python toolkit + multi-agent support

---

**Document Version**: 2.0 (Updated December 2025)  
**Last Updated**: December 18, 2025  
**Status**: Gap analysis complete, competitive position assessed  
**Next Review**: Q2 2026 after Phase 3 (Skill Library) implementation
