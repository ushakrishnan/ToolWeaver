# Programmatic Execution with Progressive Disclosure

This folder demonstrates programmatic tool execution - a pattern where AI models generate orchestration code that explores and imports tools on-demand rather than loading all tool definitions into context. This achieves 30-50% context reduction while maintaining full functionality.

## Overview

Instead of traditional tool calling where each tool use requires an LLM round-trip, programmatic execution lets models write code that orchestrates multiple tool calls, uses control flow (loops, conditionals), and only loads the specific tools needed.

## Components Demonstrated

### 1. Stub Generation
**File**: `demo_stub_generator.py`

Demonstrates the `StubGenerator` that converts `ToolCatalog` definitions into executable Python stubs with:
- Pydantic input/output models
- Async function wrappers
- Type hints and docstrings
- Server-based organization

**Run**:
```bash
python examples/phase1-code-execution/demo_stub_generator.py
```

**Output**:
- Generated stub file structure
- Sample stub code
- Context reduction metrics
- Usage examples

### 2. Baseline Benchmark
**File**: `run_baseline_benchmark.py`

Establishes baseline performance metrics before implementing progressive disclosure:
- Task completion rate
- Average context token usage
- Execution steps
- Error rates

**Run**:
```bash
python examples/phase1-code-execution/run_baseline_benchmark.py
```

**Current Baseline**:
- Completion: 40.9%
- Avg tokens: 804
- Avg steps: 1.2

### 3. Progressive Discovery Demo
**File**: `demo_progressive_discovery.py`

End-to-end demonstration showing:
- AI model exploring tool file tree
- On-demand stub loading
- 30-50% context reduction
- Comparison with baseline

## Architecture

```
┌─────────────────┐
│  ToolCatalog    │  ← Existing tool definitions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ StubGenerator   │  ← Converts to Python stubs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  tools/         │  ← Generated stub directory
│  ├── google_drive/
│  │   ├── get_document.py
│  │   └── create_document.py
│  ├── jira/
│  │   └── create_ticket.py
│  └── slack/
│      └── send_message.py
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ToolFileSystem  │  ← Progressive discovery interface
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AI Model Code   │  ← Explores & imports on-demand
└─────────────────┘
```

## Key Benefits

1. **Context Reduction**: 30-50% fewer tokens in context
   - Full catalog: ~800 tokens
   - File tree: ~50 tokens
   - Single tool import: ~200 tokens

2. **Scalability**: Handles 100+ tools efficiently
   - Exploration cost remains constant
   - Only load what's needed

3. **Type Safety**: Pydantic models provide
   - IDE autocomplete
   - Runtime validation
   - Clear error messages

4. **Maintainability**: Generated code is
   - Readable and debuggable
   - Version controlled
   - Can be manually edited if needed

## Testing

Tests are located in `tests/`:
- `test_code_generator.py` - Stub generation (18 tests)
- `test_tool_filesystem.py` - Progressive discovery (23 tests)  
- `test_programmatic_executor.py` - Code execution integration

Run all tests:
```bash
python -m pytest tests/test_code_generator.py tests/test_tool_filesystem.py tests/test_programmatic_executor.py -v
```

## Production Usage

```python
from orchestrator.programmatic_executor import ProgrammaticToolExecutor
from orchestrator.models import ToolCatalog

# Create executor with stub generation enabled
executor = ProgrammaticToolExecutor(
    catalog=your_tool_catalog,
    enable_stubs=True
)

# Get tool directory for AI to explore
tree = executor.get_tools_directory_tree()

# AI generates code that imports and uses tools
code = '''
from tools.google_drive import get_document, GetDocumentInput
result = await get_document(GetDocumentInput(doc_id="123"))
'''

# Execute
result = await executor.execute(code)
```

## References

- Implementation Details: `docs/internal/CODE_EXECUTION_IMPLEMENTATION_PLAN.md`
- Storage Architecture: `docs/architecture/skill-storage-decision.md`
- Pattern Comparison: `docs/internal/ANTHROPIC_MCP_COMPARISON.md`
