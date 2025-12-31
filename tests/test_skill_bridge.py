"""Tests for skill bridge integration between tools and skill library."""

from pathlib import Path

import pytest

from orchestrator import (
    FunctionToolTemplate,
    get_skill_backed_tools,
    get_tool_skill,
    load_tool_from_skill,
    save_tool_as_skill,
    sync_tool_with_skill,
    tool,
)
from orchestrator._internal.execution.skill_library import (
    save_skill,
    update_skill,
)


@pytest.fixture(autouse=True)
def clean_skills(tmp_path, monkeypatch):
    """Use a temporary skill directory for tests."""
    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Windows
    yield skill_dir


def test_save_tool_as_skill():
    """Test saving a tool's implementation as a skill."""
    # Create a tool with decorator
    @tool(
        name="calculate_total",
        description="Calculate order total",
        type="function",
        parameters=[
            {"name": "items", "type": "array", "required": True, "description": "List of items"},
            {"name": "tax_rate", "type": "number", "required": False, "description": "Tax rate"}
        ]
    )
    def calculate_total(items: list, tax_rate: float = 0.1) -> dict:
        subtotal = sum(item.get("price", 0) for item in items)
        tax = subtotal * tax_rate
        total = subtotal + tax
        return {"subtotal": subtotal, "tax": tax, "total": total}

    # Get tool definition
    from orchestrator.tools.discovery_api import get_tool_info
    tool_def = get_tool_info("calculate_total")

    assert tool_def is not None

    # Save as skill
    skill = save_tool_as_skill(tool_def, calculate_total, tags=["finance", "calculation"])

    assert skill.name == "calculate_total"
    assert skill.description == "Calculate order total"
    assert "finance" in skill.tags
    assert "calculation" in skill.tags
    # Version might be 0.1.0 (new) or 0.1.1+ (update if skill already exists)
    assert skill.version.startswith("0.1")
    assert skill.metadata["tool_name"] == "calculate_total"

    # Verify skill code was saved
    skill_path = Path(skill.code_path)
    assert skill_path.exists()
    code = skill_path.read_text()
    assert "calculate_total" in code
    assert "subtotal" in code


def test_load_tool_from_skill():
    """Test creating a tool from an existing skill."""
    # First create a skill directly
    code = """
def process_invoice(invoice_data):
    invoice_number = invoice_data.get("invoice_number", "unknown")
    items = invoice_data.get("items", [])
    total = sum(item.get("amount", 0) for item in items)
    return {
        "invoice_number": invoice_number,
        "total": total,
        "status": "processed"
    }
"""

    save_skill(
        "process_invoice",
        code,
        description="Process invoice and calculate total",
        tags=["invoice", "accounting"]
    )

    # Load as tool
    tool_def, func = load_tool_from_skill("process_invoice")

    assert tool_def.name == "process_invoice"
    assert tool_def.description == "Process invoice and calculate total"
    assert tool_def.type == "function"
    assert tool_def.provider == "skill"
    assert tool_def.metadata["skill_reference"] == "process_invoice"
    assert tool_def.metadata["loaded_from_skill"] is True

    # Test execution
    result = func({"invoice_number": "INV-001", "items": [{"amount": 100}, {"amount": 200}]})
    assert result["invoice_number"] == "INV-001"
    assert result["total"] == 300
    assert result["status"] == "processed"


def test_template_save_as_skill():
    """Test template's save_as_skill method."""
    # Create a template with function
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

    # Save as skill
    skill = template.save_as_skill(tags=["math"])

    assert skill.name == "add_numbers"
    assert skill.description == "Add two numbers"
    assert "math" in skill.tags
    assert skill.version.startswith("0.1")  # Might be updated version


def test_template_load_from_skill():
    """Test template's load_from_skill class method."""
    # Create a skill
    code = """
def multiply(x, y):
    return x * y
"""
    save_skill("multiply", code, description="Multiply two numbers", tags=["math"])

    # Load as template
    template, func = FunctionToolTemplate.load_from_skill("multiply")

    assert template.name == "multiply"
    assert template.description == "Multiply two numbers"
    assert template.type == "function"

    # Test execution
    result = func(x=5, y=3)
    assert result == 15


def test_get_tool_skill():
    """Test getting the skill backing a tool."""
    # Create a skill
    code = "def test_func(): return 'test'"
    save_skill("test_skill", code, description="Test skill")

    # Get skill
    skill = get_tool_skill("test_skill")

    assert skill is not None
    assert skill.name == "test_skill"
    assert skill.description == "Test skill"


def test_sync_tool_with_skill():
    """Test syncing a tool with latest skill version."""
    # Create initial skill
    code_v1 = """
def get_discount(price):
    return price * 0.1  # 10% discount
"""
    save_skill("get_discount", code_v1, description="Calculate discount")

    # Update skill to new version
    code_v2 = """
def get_discount(price):
    return price * 0.15  # 15% discount
"""
    update_skill("get_discount", code_v2, bump_type="minor")

    # Sync tool
    tool_def, func = sync_tool_with_skill("get_discount")

    assert tool_def is not None
    assert tool_def.name == "get_discount"

    # Verify it uses new version
    result = func(price=100)
    assert result == 15.0  # 15% not 10%


def test_get_skill_backed_tools():
    """Test getting list of tools backed by skills."""
    # Create some skills with tool metadata
    save_skill(
        "tool1",
        "def tool1(): pass",
        metadata={"tool_name": "tool1"}
    )
    save_skill(
        "tool2",
        "def tool2(): pass",
        metadata={"tool_name": "tool2"}
    )
    save_skill(
        "not_a_tool",
        "def not_a_tool(): pass",
        metadata={}  # No tool_name
    )

    backed_tools = get_skill_backed_tools()

    assert "tool1" in backed_tools
    assert "tool2" in backed_tools
    assert "not_a_tool" not in backed_tools


def test_skill_versioning():
    """Test that skill versions are properly managed."""
    # Create function template
    def version_test(x: int) -> int:
        return x * 2

    # Use timestamp in name to ensure uniqueness across test runs
    import time
    unique_name = f"version_test_{int(time.time() * 1000)}"

    template = FunctionToolTemplate(
        name=unique_name,
        description="Test versioning",
        function=version_test
    )

    # First save creates initial version
    skill_v1 = template.save_as_skill()
    v1 = skill_v1.version

    # Patch bump should increment
    skill_v2 = template.save_as_skill(bump_type="patch")
    v2 = skill_v2.version
    assert v2 != v1, f"Patch bump should change version: {v1} -> {v2}"

    # Minor bump should increment
    skill_v3 = template.save_as_skill(bump_type="minor")
    v3 = skill_v3.version
    assert v3 != v2, f"Minor bump should change version: {v2} -> {v3}"


def test_nested_schema_preservation():
    """Test that nested schemas are preserved when saving/loading skills."""
    # Create tool with nested schema
    @tool(
        name="nested_tool",
        description="Tool with nested schema",
        type="function",
        parameters=[{"name": "data", "type": "object", "required": True, "description": "Input data"}],
        input_schema={
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "properties": {
                        "user": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"}
                            }
                        },
                        "items": {
                            "type": "array",
                            "items": {"type": "object"}
                        }
                    }
                }
            }
        }
    )
    def nested_tool(data: dict) -> dict:
        return {"processed": data}

    # Get tool def and save as skill
    from orchestrator.tools.discovery_api import get_tool_info
    tool_def = get_tool_info("nested_tool")
    skill = save_tool_as_skill(tool_def, nested_tool)

    # Verify nested schema is in metadata
    assert skill.metadata["input_schema"] is not None
    assert skill.metadata["input_schema"]["properties"]["data"]["properties"]["user"]["properties"]["name"]["type"] == "string"

    # Load back and verify schema preserved
    loaded_tool_def, _ = load_tool_from_skill("nested_tool")
    assert loaded_tool_def.input_schema is not None
    assert loaded_tool_def.input_schema["properties"]["data"]["properties"]["user"]["properties"]["name"]["type"] == "string"


def test_error_no_function():
    """Test error when template has no function to save."""
    template = FunctionToolTemplate(
        name="no_function",
        description="Template without function"
    )
    # Don't set _function

    with pytest.raises(NotImplementedError, match="does not have a callable function"):
        template.save_as_skill()


def test_error_skill_not_found():
    """Test error when loading non-existent skill."""
    with pytest.raises(KeyError, match="not found"):
        load_tool_from_skill("nonexistent_skill")


def test_error_invalid_skill_code():
    """Test error when skill code cannot be executed."""
    # Create skill with syntax error
    save_skill("bad_skill", "def bad_func(: invalid syntax", description="Bad skill")

    with pytest.raises(ValueError, match="Cannot execute skill code"):
        load_tool_from_skill("bad_skill")
