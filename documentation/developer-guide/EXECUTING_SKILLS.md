# Executing Skills

Run saved code snippets or workflows from the Orchestrator.

## Quick Start

```python
from orchestrator import Orchestrator

orch = Orchestrator()

# Execute a saved skill by name
result = await orch.execute_skill("summarize_lengths", inputs={"items": ["hello", "world"]})
print(result)  # {'summarize_lengths': 10, ...}
```

## Under the Hood

1. Load skill from library (disk → Redis if available)
2. Validate syntax (AST parse)
3. Execute in sandbox with optional inputs
4. Log success/failure + latency via monitoring backend
5. Return scope (all non-private variables)

## Example Workflow

```python
# 1. Save a skill
from orchestrator.execution import skill_library as sl

code = """
def process(data):
    total = sum(len(x) for x in data)
    return total
"""

sl.save_skill(name="process_list", code=code, metadata={"tags": ["utility"]})

# 2. Execute it later
orch = Orchestrator()
result = await orch.execute_skill("process_list", inputs={"data": ["a", "bb", "ccc"]})
print(result["total"])  # 6
```

## Monitoring

Skill execution is logged as a tool call with:
- Name: `skill:{skill_name}`
- Success/failure flag
- Latency (milliseconds)
- Error message (if failed)

Access via monitoring backend (WandB, local file, etc.).

## Error Handling

```python
try:
    result = await orch.execute_skill("unknown_skill")
except KeyError:
    print("Skill not found")
except RuntimeError as e:
    print(f"Skill failed: {e}")
```

## Inputs and Outputs

- **Inputs**: Pass as `inputs` dict; variables are injected into skill scope
- **Outputs**: All non-private scope variables returned as dict

Example:

```python
code = """
result = x + y
debug_info = {"computed": True}
_internal = "hidden"
"""

result = await orch.execute_skill("math_skill", inputs={"x": 5, "y": 3})
# result = {"result": 8, "debug_info": {...}} (excludes _internal)
```

## Composing Skills

Combine multiple skills by passing outputs of one as inputs to another:

```python
r1 = await orch.execute_skill("fetch_data", inputs={"url": "..."})
r2 = await orch.execute_skill("analyze", inputs={"data": r1["output"]})
r3 = await orch.execute_skill("store", inputs={"result": r2["summary"]})
```

## Advanced: Skill Context

For complex workflows, save context-aware skills:

```python
code = """
# Assume 'context' is injected at runtime
user_id = context.get("user_id")
items = context.get("items", [])
result = f"Processing {len(items)} for user {user_id}"
"""

sl.save_skill(name="context_aware", code=code)

result = await orch.execute_skill(
    "context_aware",
    inputs={"context": {"user_id": 42, "items": [1, 2, 3]}}
)
```

## Performance Tips

- Use small skills for fast iteration and composition
- Cache hot skills via Redis if available
- Validate skills before production (`check_exec=True`)
- Monitor latency to identify slow skills
