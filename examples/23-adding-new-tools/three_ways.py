"""
Example 23: Three Ways to Add Tools to ToolWeaver

Demonstrates all three tool registration methods side-by-side:
1. Template classes (programmatic, verbose, most control)
2. Decorators (fast, automatic parameter extraction)
3. YAML configuration (config-driven, DevOps-friendly)

All three approaches produce identical tools and can be used together.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Any

from orchestrator import (
    mcp_tool,
    a2a_agent,
    FunctionToolTemplate,
    register_template,
    load_tools_from_yaml,
    get_available_tools,
    search_tools,
)
from orchestrator.shared.models import ToolParameter


# ============================================================================
# METHOD 1: Template Classes (Phase 1)
# Verbose but gives maximum control over tool definition
# ============================================================================

class ExpensesFunctionTool(FunctionToolTemplate):
    """Example tool using template class approach."""
    
    def __init__(self):
        super().__init__(
            name="get_expenses_via_template",
            description="Fetch employee expenses (template approach)",
            function=self.worker,
            parameters=[
                ToolParameter(
                    name="employee_id",
                    type="string",
                    description="Employee ID",
                    required=True,
                ),
                ToolParameter(
                    name="year",
                    type="integer",
                    description="Fiscal year",
                    required=False,
                    default=2025,
                ),
            ],
        )
    
    @staticmethod
    def worker(employee_id: str, year: int = 2025) -> Dict[str, Any]:
        """Template worker implementation."""
        return {
            "employee_id": employee_id,
            "year": year,
            "expenses": [
                {"date": "2025-01-15", "amount": 125.50, "category": "travel"},
                {"date": "2025-01-18", "amount": 45.00, "category": "meals"},
            ],
        }


# ============================================================================
# METHOD 2: Decorators (Phase 2)
# Fast and simple - auto-extracts parameters from type hints
# ============================================================================

@mcp_tool(domain="finance", description="Fetch employee expenses (decorator approach)")
async def get_expenses_via_decorator(employee_id: str, year: int = 2025) -> Dict[str, Any]:
    """
    Fetch employee expenses using the decorator approach.
    
    The @mcp_tool decorator automatically:
    - Extracts parameters from type hints (employee_id: required, year: optional with default)
    - Uses the function name as the tool name
    - Registers the tool at import time (no manual registration needed)
    - Supports both sync and async functions
    
    Args:
        employee_id: Employee ID to fetch expenses for
        year: Fiscal year (default: 2025)
    
    Returns:
        Dictionary with employee expenses and metadata
    """
    # Simulate async operation (e.g., API call)
    await asyncio.sleep(0.01)
    
    return {
        "employee_id": employee_id,
        "year": year,
        "expenses": [
            {"date": "2025-01-15", "amount": 125.50, "category": "travel"},
            {"date": "2025-01-18", "amount": 45.00, "category": "meals"},
        ],
    }


@a2a_agent(domain="finance")
def route_expense_approval(employee_id: str, amount: float, reason: str = "") -> Dict[str, Any]:
    """
    Route expense for approval (agent decorator).
    
    Agent decorators work identically to mcp_tool but indicate
    this tool is agent-to-agent communication.
    """
    return {
        "status": "routed",
        "employee_id": employee_id,
        "amount": amount,
        "reason": reason or "No reason provided",
        "approver": "finance-team",
    }


# ============================================================================
# METHOD 3: YAML Configuration (Phase 3)
# Config-driven - ideal for DevOps and configuration management
# ============================================================================

# Example YAML that would be loaded from file:
YAML_TOOLS_CONFIG = """
tools:
  - name: get_expenses_via_yaml
    type: function
    domain: finance
    description: "Fetch employee expenses (YAML approach)"
    worker: __main__:yaml_worker_get_expenses
    parameters:
      - name: employee_id
        type: string
        description: "Employee ID"
        required: true
      - name: year
        type: integer
        description: "Fiscal year"
        required: false
        default: 2025
    metadata:
      version: "1.0"
      source: yaml
"""


def yaml_worker_get_expenses(employee_id: str, year: int = 2025) -> Dict[str, Any]:
    """Worker function for YAML-defined tool."""
    return {
        "employee_id": employee_id,
        "year": year,
        "expenses": [
            {"date": "2025-01-15", "amount": 125.50, "category": "travel"},
            {"date": "2025-01-18", "amount": 45.00, "category": "meals"},
        ],
    }


# ============================================================================
# Demo: Show All Three Approaches
# ============================================================================

async def demo_all_three_methods():
    """Demonstrate registering tools via all three methods."""
    
    print("\n" + "="*80)
    # Register template explicitly (not auto-registered like decorators)
    register_template(template_tool)
    template_def = template_tool.build_definition()
    print(f"   Tool: {template_def.name}")
    print(f"   Description: {template_def.description}")
    print(f"   Parameters: {[p.name for p in template_def.parameters]}")
    print("   ✓ Registered via register_template() call"))")
    print("-" * 80)
    template_tool = ExpensesFunctionTool()
    template_def = template_tool.build_definition()
    print(f"   Tool: {template_def.name}")
    print(f"   Description: {template_def.description}")
    print(f"   Parameters: {[p.name for p in template_def.parameters]}")
    # Note: Template auto-registration happens in decorator
    
    # Decorators already registered during import, let's verify
    print("\n2. DECORATOR APPROACH (Fast, automatic parameter extraction)")
    print("-" * 80)
    
    # METHOD 2 & 3: Already registered via decorators during import
    available = get_available_tools()
    decorator_tools = [t for t in available if "decorator" in t.name.lower()]
    agent_tools = [t for t in available if "route" in t.name.lower()]
    
    for tool in decorator_tools:
        print(f"   Tool: {tool.name}")
        print(f"   Description: {tool.description}")
        print(f"   Parameters: {[p.name for p in tool.parameters]}")
        
        # Test search
        result = search_tools(query="expenses", use_semantic=False)
        print(f"   Search found: {len(result)} tools\n")
    
    for tool in agent_tools:
        print(f"   Tool: {tool.name}")
        print(f"   Description: {tool.description}")
        print(f"   Type: {tool.type}")
    
    # METHOD 3: Load YAML tools
    print("\n3. YAML APPROACH (Config-driven, DevOps-friendly)")
    print("-" * 80)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(YAML_TOOLS_CONFIG)
        yaml_file = Path(f.name)
    
    try:
        count = load_tools_from_yaml(yaml_file)
        print(f"   Loaded {count} tools from YAML")
        
        yaml_tools = [t for t in get_available_tools() if "yaml" in t.name.lower()]
        for tool in yaml_tools:
            print(f"   Tool: {tool.name}")
            print(f"   Description: {tool.description}")
            print(f"   Domain: {tool.domain}")
    finally:
        yaml_file.unlink(missing_ok=True)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY: All Three Methods Produce Compatible Tools")
    print("="*80)
    print("""
    ✓ Templates:  Programmatic, maximum control, verbose
    ✓ Decorators: Fast registration, automatic parameter extraction, clean
    ✓ YAML:       Config-driven, DevOps-friendly, version-controllable
    
    All three approaches:
    - Produce identical ToolDefinition objects
    - Work with the same discovery API
    - Can be mixed in the same application
    - Support the same execution model
    
    Choose based on your needs:
    - Individual developer? → Decorators (fastest)
    - Full control needed? → Templates
    - Infrastructure team? → YAML (configuration management)
    """)


if __name__ == "__main__":
    asyncio.run(demo_all_three_methods())
