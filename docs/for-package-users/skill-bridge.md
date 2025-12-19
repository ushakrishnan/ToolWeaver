# Skill Bridge: Connecting Tools and Skills

The skill bridge provides bidirectional integration between tool registration and skill library versioning.

## Overview

- **Tools → Skills**: Save tool implementations as versioned skills for reuse
- **Skills → Tools**: Load tools from existing skills
- **Sync**: Update tools to match latest skill versions

## Quick Start

### Save Tool as Skill

```python
from orchestrator import tool, save_tool_as_skill, get_tool_info

# Register a tool
@tool(
    name="process_invoice",
    description="Process invoice and calculate total",
    type="function",
    parameters=[
        {"name": "invoice_data", "type": "object", "required": True, "description": "Invoice data"}
    ]
)
def process_invoice(invoice_data: dict) -> dict:
    items = invoice_data.get("items", [])
    total = sum(item.get("amount", 0) for item in items)
    return {"total": total, "status": "processed"}

# Save as skill
tool_def = get_tool_info("process_invoice")
skill = save_tool_as_skill(tool_def, process_invoice, tags=["finance", "invoice"])

print(f"Saved as skill: {skill.name} v{skill.version}")
```

### Load Tool from Skill

```python
from orchestrator import load_tool_from_skill

# Load tool from existing skill
tool_def, func = load_tool_from_skill("process_invoice")

# Use the tool
result = func({"invoice_number": "INV-001", "items": [{"amount": 100}]})
print(result)  # {"total": 100, "status": "processed"}
```

### Template Integration

Templates have built-in skill bridge methods:

```python
from orchestrator import FunctionToolTemplate

# Create template with function
def add_numbers(a: int, b: int) -> int:
    return a + b

template = FunctionToolTemplate(
    name="add_numbers",
    description="Add two numbers",
    function=add_numbers,
    parameters=[
        {"name": "a", "type": "integer", "required": True, "description": "First number"},
        {"name": "b", "type": "integer", "required": True, "description": "Second number"}
    ]
)

# Save as skill directly from template
skill = template.save_as_skill(tags=["math"])

# Load template from skill
loaded_template, func = FunctionToolTemplate.load_from_skill("add_numbers")
result = func(a=5, b=3)
print(result)  # 8
```

### Skill Versioning

Skills are automatically versioned when saved:

```python
from orchestrator import save_tool_as_skill, get_tool_info

# Initial save creates version 0.1.0
@tool(name="calculate_discount", description="Calculate discount")
def calculate_discount(price: float) -> float:
    return price * 0.1

tool_def = get_tool_info("calculate_discount")
skill_v1 = save_tool_as_skill(tool_def, calculate_discount)
print(skill_v1.version)  # 0.1.0

# Update with patch bump (bug fix)
skill_v2 = save_tool_as_skill(tool_def, calculate_discount, bump_type="patch")
print(skill_v2.version)  # 0.1.1

# Update with minor bump (new feature)
skill_v3 = save_tool_as_skill(tool_def, calculate_discount, bump_type="minor")
print(skill_v3.version)  # 0.2.0

# Update with major bump (breaking change)
skill_v4 = save_tool_as_skill(tool_def, calculate_discount, bump_type="major")
print(skill_v4.version)  # 1.0.0
```

### Sync Tool with Latest Skill

```python
from orchestrator import sync_tool_with_skill

# Update tool to use latest skill version
tool_def, func = sync_tool_with_skill("calculate_discount")
print(f"Using skill version: {tool_def.metadata['skill_version']}")
```

## API Reference

### Functions

#### `save_tool_as_skill(tool_def, function, *, tags=None, bump_type="patch")`

Save a tool's implementation as a skill.

**Parameters:**
- `tool_def` (ToolDefinition): Tool definition to save
- `function` (Callable): The actual function implementation
- `tags` (list[str], optional): Tags for categorization
- `bump_type` (str): Version bump type: "major", "minor", or "patch"

**Returns:** `Skill` object

**Example:**
```python
tool_def = get_tool_info("my_tool")
skill = save_tool_as_skill(tool_def, my_tool_func, tags=["data"])
```

---

#### `load_tool_from_skill(skill_name, *, version=None, tool_type="function", provider="skill")`

Load a tool from a skill.

**Parameters:**
- `skill_name` (str): Name of the skill
- `version` (str, optional): Specific version (defaults to latest)
- `tool_type` (str): Type of tool to create
- `provider` (str): Provider name

**Returns:** Tuple of `(ToolDefinition, callable)`

**Raises:**
- `KeyError`: If skill not found
- `ValueError`: If skill code cannot be executed

**Example:**
```python
tool_def, func = load_tool_from_skill("process_data", version="1.0.0")
result = func({"input": "test"})
```

---

#### `get_tool_skill(tool_name)`

Get the skill backing a tool (if any).

**Returns:** `Skill` object or `None`

---

#### `sync_tool_with_skill(tool_name)`

Sync a tool with the latest version of its backing skill.

**Returns:** Tuple of `(ToolDefinition, callable)` or `None`

---

#### `get_skill_backed_tools()`

Get list of all tools that are backed by skills.

**Returns:** List of tool names

### Template Methods

All template classes inherit these methods:

#### `template.save_as_skill(*, tags=None, bump_type="patch")`

Save this template's implementation as a skill.

**Example:**
```python
template = FunctionToolTemplate(name="my_tool", function=my_func)
skill = template.save_as_skill(tags=["utility"])
```

---

#### `Template.load_from_skill(skill_name, *, version=None, **template_kwargs)`

Class method to create a template from a skill.

**Example:**
```python
template, func = FunctionToolTemplate.load_from_skill("my_skill")
```

## Use Cases

### 1. Version Control

Save tool implementations with semantic versioning for rollback and auditing.

### 2. Reusability

Share tool logic across projects by storing in skill library.

### 3. Hot Reload

Update tool behavior by syncing with latest skill version without redeployment.

### 4. Collaborative Development

Team members can publish tools as skills for others to use.

## Best Practices

1. **Tag Appropriately**: Use tags for easy discovery (`finance`, `data`, `ml`)
2. **Semantic Versioning**: Use `major` for breaking changes, `minor` for new features, `patch` for bug fixes
3. **Document Functions**: Add docstrings - they become skill descriptions
4. **Test Before Saving**: Verify tool works before saving as skill
5. **Use Unique Names**: Avoid name conflicts in skill library

## Limitations

- Decorated functions are unwrapped (decorators not preserved in skills)
- Only function source code is saved (no closure variables)
- Skills must be pure Python (no external file dependencies)

## See Also

- [Skill Library Reference](../reference/SKILL_LIBRARY.md)
- [Skill Versioning Guide](../developer-guide/SKILL_VERSIONING.md)
- [Registering Tools](registering-tools.md)
