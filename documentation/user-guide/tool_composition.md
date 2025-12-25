# Tool Composition

Chain tools where output from one becomes input to the next.

## What it does
- Registers sequences of tools as reusable workflows (`CompositionChain`).
- Auto-wires step outputs to inputs with validation and type checks.
- Supports error handling per-step (retry, continue, or short-circuit).
- Optional timeouts and per-step retry policies (aligned with Phase 4 later).

## API

### CompositionStep
```python
@dataclass
class CompositionStep:
    name: str                      # Unique name in the chain
    tool_ref: str                  # Reference to tool (name or callable)
    input_schema: dict = {}        # Expected input fields
    output_mapping: dict = {}      # {target_field: source_field} mapping
    timeout_sec: int = 30
    retry_count: int = 0
    on_error: str = "raise"        # "raise" | "continue" | "fallback"
```

### CompositionChain
```python
@dataclass
class CompositionChain:
    name: str
    steps: list[CompositionStep]
    description: str = ""
    is_linear: bool = True         # Linear for now; DAG support later

    def add_step(step: CompositionStep) -> Self  # Chainable
    def validate() -> list[str]                   # Returns warnings/errors
```

### @composite_tool decorator
Register a chain for reuse:
```python
@composite_tool(name="fetch_parse_extract", description="...")
def my_chain():
    return (
        CompositionChain(name="fetch_parse_extract")
        .add_step(CompositionStep(name="fetch", tool_ref="http_get", ...))
        .add_step(CompositionStep(name="parse", tool_ref="parse_html", ...))
        .add_step(CompositionStep(name="extract", tool_ref="regex_extract", ...))
    )
```

### Parameter mapping
Auto-wire outputs → inputs:
```python
from orchestrator.tools.composition import build_parameter_mapping

# Explicit mapping: {target_field: source_field}
mapped = build_parameter_mapping(
    source_output=step1_result,
    target_input_schema={"url": ..., "data": ...},
    explicit_mapping={"url": "source_url"},
)
```

## Simple example
```python
from orchestrator.tools.composition import (
    CompositionChain,
    CompositionStep,
    composite_tool,
)

@composite_tool(name="extract_from_html")
def extract_chain():
    return (
        CompositionChain(name="extract_from_html")
        .add_step(
            CompositionStep(
                name="fetch",
                tool_ref="http_get",
                input_schema={"url": str},
                output_mapping={"html": "body"},
            )
        )
        .add_step(
            CompositionStep(
                name="parse",
                tool_ref="parse_html",
                input_schema={"html": str},
                output_mapping={"title": "title", "text": "body_text"},
            )
        )
    )

# Run via orchestrator.execute_composition(extract_chain(), {"url": "..."})
```

## When to use
- Multi-step workflows (fetch → parse → classify → notify).
- Sequential tool pipelines with data passing between steps.
- Reusable chains registered once, invoked many times.

## Error handling
- `on_error="raise"` — fail chain (default).
- `on_error="continue"` — skip step, use None or passthrough for next.
- `on_error="fallback"` — (later) use alternate tool if primary fails.

## Notes
- Linear chains only for now; DAG support in Phase 2 extension.
- Retries and per-step policies aligned with Phase 4 (error recovery).
- Integration with dispatch for parallel sub-chains (Phase 2+ extension).
