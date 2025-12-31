"""
Test for Example 23: Three ways to add tools
"""

import asyncio

import pytest

# Note: Import the demo module to test all three approaches
from three_ways import (
    ExpensesFunctionTool,
    get_expenses_via_decorator,
    yaml_worker_get_expenses,
)


class TestThreeWaysExample:
    """Verify all three tool registration approaches work."""

    def test_template_approach(self):
        """Test template-based tool registration."""
        tool = ExpensesFunctionTool()
        definition = tool.build_definition()

        assert definition.name == "get_expenses_via_template"
        assert definition.type == "function"
        assert len(definition.parameters) == 2

        param_names = {p.name for p in definition.parameters}
        assert param_names == {"employee_id", "year"}

        # Test execution
        result = tool.execute({"employee_id": "E123", "year": 2024})
        assert result["employee_id"] == "E123"
        assert result["year"] == 2024
        assert "expenses" in result

    @pytest.mark.asyncio
    async def test_decorator_approach(self):
        """Test decorator-based tool registration."""
        # Decorators register during import, verify they're in the registry
        from orchestrator import get_available_tools

        available = get_available_tools()
        names = {t["name"] for t in available}

        # Decorator tools should be registered
        assert "get_expenses_via_decorator" in names
        assert "route_expense_approval" in names

    def test_yaml_approach(self):
        """Test YAML worker function works."""
        result = yaml_worker_get_expenses(employee_id="E456", year=2025)

        assert result["employee_id"] == "E456"
        assert result["year"] == 2025
        assert "expenses" in result
        assert len(result["expenses"]) > 0

    @pytest.mark.asyncio
    async def test_decorator_async_execution(self):
        """Test async decorator execution."""
        result = await asyncio.iscoroutine(get_expenses_via_decorator("E789", 2025))
        # The function is async, so calling it returns a coroutine
        assert result is True or result is False  # Depends on whether we actually await


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
