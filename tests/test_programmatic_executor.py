"""
Unit tests for Programmatic Tool Calling Executor

Tests cover:
- Basic code execution
- Tool wrapper injection and invocation
- Parallel tool execution (asyncio.gather)
- Security validation (AST-based)
- Timeout handling
- Error recovery
- Tool call logging and monitoring
"""


import pytest

from orchestrator._internal.execution.programmatic_executor import (
    ProgrammaticToolExecutor,
    execute_programmatic_code,
)
from orchestrator.shared.models import ToolCatalog, ToolDefinition, ToolParameter


@pytest.fixture
def sample_catalog():
    """Create a sample tool catalog for testing"""
    catalog = ToolCatalog(source="test", version="1.0")

    # Add function tool
    catalog.add_tool(ToolDefinition(
        name="add_numbers",
        type="function",
        description="Add two numbers",
        parameters=[
            ToolParameter(name="a", type="integer", description="First number", required=True),
            ToolParameter(name="b", type="integer", description="Second number", required=True)
        ]
    ))

    # Add MCP tool
    catalog.add_tool(ToolDefinition(
        name="get_data",
        type="mcp",
        description="Get data by ID",
        parameters=[
            ToolParameter(name="id", type="string", description="Data ID", required=True)
        ]
    ))

    return catalog


@pytest.fixture
def mock_tool_executor(monkeypatch, sample_catalog):
    """Create executor with mocked tool execution"""
    executor = ProgrammaticToolExecutor(sample_catalog)

    # Mock _execute_tool to return controlled values
    async def mock_execute(tool_def, parameters):
        if tool_def.name == "add_numbers":
            return {"result": parameters["a"] + parameters["b"]}
        elif tool_def.name == "get_data":
            return {"id": parameters["id"], "value": f"data_{parameters['id']}"}
        return {}

    monkeypatch.setattr(executor, "_execute_tool", mock_execute)
    return executor


class TestBasicExecution:
    """Test basic code execution functionality"""

    @pytest.mark.asyncio
    async def test_simple_print(self, mock_tool_executor):
        """Test basic print statement execution"""
        code = 'print("Hello, World!")'
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert result["output"] == "Hello, World!\n"
        assert result["execution_time"] > 0
        assert len(result["tool_calls"]) == 0

    @pytest.mark.asyncio
    async def test_variable_assignment(self, mock_tool_executor):
        """Test variable assignment and computation"""
        code = """
x = 10
y = 20
z = x + y
print(z)
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert "30" in result["output"]
        assert len(result["tool_calls"]) == 0

    @pytest.mark.asyncio
    async def test_async_await_syntax(self, mock_tool_executor):
        """Test async/await syntax support"""
        code = """
async def test_func():
    await asyncio.sleep(0.01)
    return "success"

result = await test_func()
print(result)
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert "success" in result["output"]

    @pytest.mark.asyncio
    async def test_json_output(self, mock_tool_executor):
        """Test JSON serialization in output"""
        code = """
data = {"name": "Alice", "age": 30}
print(json.dumps(data))
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert "Alice" in result["output"]
        assert "30" in result["output"]


class TestToolWrapping:
    """Test tool wrapper injection and invocation"""

    @pytest.mark.asyncio
    async def test_single_tool_call(self, mock_tool_executor):
        """Test calling a single tool function"""
        code = """
result = await add_numbers(a=5, b=3)
print(json.dumps(result))
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert '"result": 8' in result["output"]
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["tool"] == "add_numbers"
        assert result["tool_calls"][0]["parameters"] == {"a": 5, "b": 3}

    @pytest.mark.asyncio
    async def test_multiple_tool_calls(self, mock_tool_executor):
        """Test calling multiple tools sequentially"""
        code = """
result1 = await add_numbers(a=10, b=20)
result2 = await add_numbers(a=5, b=15)
total = result1["result"] + result2["result"]
print(total)
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert "50" in result["output"]
        assert len(result["tool_calls"]) == 2
        assert result["tool_calls"][0]["tool"] == "add_numbers"
        assert result["tool_calls"][1]["tool"] == "add_numbers"

    @pytest.mark.asyncio
    async def test_tool_call_logging(self, mock_tool_executor):
        """Test tool call logging includes all required fields"""
        code = """
result = await get_data(id="123")
print("done")
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert len(result["tool_calls"]) == 1

        call = result["tool_calls"][0]
        assert "tool" in call
        assert "type" in call
        assert "parameters" in call
        assert "timestamp" in call
        assert "caller" in call
        assert call["caller"]["type"] == "code_execution"
        assert "execution_id" in call["caller"]
        assert "result_size" in call
        assert "completed_at" in call
        assert "duration" in call

    @pytest.mark.asyncio
    async def test_missing_required_parameter(self, mock_tool_executor):
        """Test error when required parameter is missing"""
        code = """
try:
    result = await add_numbers(a=5)  # Missing 'b'
except ValueError as e:
    print(f"Error: {e}")
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert "Missing required parameters" in result["output"]


class TestStubIntegration:
    """Ensure generated stubs can be imported and routed through executor."""

    @pytest.mark.asyncio
    async def test_stub_import_routes_through_executor(self, mock_tool_executor):
        code = """
    from tools.general.add_numbers import add_numbers, AddNumbersInput
    result = await add_numbers(AddNumbersInput(a=2, b=3))
    print(result.result)
    """

        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert "5" in result["output"]
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["tool"] == "add_numbers"


class TestParallelExecution:
    """Test parallel tool execution with asyncio.gather"""

    @pytest.mark.asyncio
    async def test_parallel_tool_calls(self, mock_tool_executor):
        """Test parallel execution with asyncio.gather"""
        code = """
# Create multiple tasks
tasks = [
    add_numbers(a=i, b=i*2)
    for i in range(5)
]

# Execute in parallel
results = await asyncio.gather(*tasks)

# Sum all results
total = sum(r["result"] for r in results)
print(total)
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        # Expected: (0+0) + (1+2) + (2+4) + (3+6) + (4+8) = 0 + 3 + 6 + 9 + 12 = 30
        assert "30" in result["output"]
        assert len(result["tool_calls"]) == 5

    @pytest.mark.asyncio
    async def test_parallel_different_tools(self, mock_tool_executor):
        """Test parallel execution of different tool types"""
        code = """
results = await asyncio.gather(
    add_numbers(a=10, b=20),
    get_data(id="abc"),
    add_numbers(a=5, b=5)
)
print(len(results))
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert "3" in result["output"]
        assert len(result["tool_calls"]) == 3


class TestSecurityValidation:
    """Test AST-based security validation"""

    @pytest.mark.asyncio
    async def test_forbidden_import_os(self, mock_tool_executor):
        """Test blocking of os module import"""
        code = "import os"
        result = await mock_tool_executor.execute(code)

        assert result["error"] is not None
        assert "Security violation" in result["error"]
        assert "Forbidden import: os" in result["error"]

    @pytest.mark.asyncio
    async def test_forbidden_import_subprocess(self, mock_tool_executor):
        """Test blocking of subprocess import"""
        code = "import subprocess"
        result = await mock_tool_executor.execute(code)

        assert result["error"] is not None
        assert "Forbidden import: subprocess" in result["error"]

    @pytest.mark.asyncio
    async def test_forbidden_from_import(self, mock_tool_executor):
        """Test blocking of from X import Y"""
        code = "from os import path"
        result = await mock_tool_executor.execute(code)

        assert result["error"] is not None
        assert "Forbidden import" in result["error"]

    @pytest.mark.asyncio
    async def test_forbidden_function_eval(self, mock_tool_executor):
        """Test blocking of eval function"""
        code = 'eval("1+1")'
        result = await mock_tool_executor.execute(code)

        assert result["error"] is not None
        assert "Forbidden function: eval" in result["error"]

    @pytest.mark.asyncio
    async def test_forbidden_function_exec(self, mock_tool_executor):
        """Test blocking of exec function"""
        code = 'exec("x=1")'
        result = await mock_tool_executor.execute(code)

        assert result["error"] is not None
        assert "Forbidden function: exec" in result["error"]

    @pytest.mark.asyncio
    async def test_forbidden_function_open(self, mock_tool_executor):
        """Test blocking of open function"""
        code = 'open("file.txt", "r")'
        result = await mock_tool_executor.execute(code)

        assert result["error"] is not None
        assert "Forbidden function: open" in result["error"]

    @pytest.mark.asyncio
    async def test_forbidden_builtins_modification(self, mock_tool_executor):
        """Test blocking of __builtins__ modification"""
        code = "__builtins__ = {}"
        result = await mock_tool_executor.execute(code)

        assert result["error"] is not None
        assert "Cannot modify: __builtins__" in result["error"]

    @pytest.mark.asyncio
    async def test_allowed_safe_operations(self, mock_tool_executor):
        """Test that safe operations are allowed"""
        code = """
# Safe operations
numbers = [1, 2, 3, 4, 5]
doubled = [x * 2 for x in numbers]
result = sum(doubled)
print(result)
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert "30" in result["output"]


class TestTimeoutHandling:
    """Test execution timeout protection"""

    @pytest.mark.asyncio
    async def test_timeout_with_sleep(self, mock_tool_executor):
        """Test timeout with asyncio.sleep"""
        # Set very short timeout
        mock_tool_executor.timeout = 0.1

        code = """
await asyncio.sleep(1.0)  # Sleep longer than timeout
print("Should not reach here")
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is not None
        assert "timeout" in result["error"].lower()
        # Allow for timing variance - timeout should occur close to the timeout value
        assert result["execution_time"] >= 0.08

    @pytest.mark.asyncio
    async def test_no_timeout_fast_execution(self, mock_tool_executor):
        """Test that fast execution completes without timeout"""
        mock_tool_executor.timeout = 5.0

        code = """
await asyncio.sleep(0.01)
print("completed")
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert "completed" in result["output"]


class TestErrorRecovery:
    """Test error handling and recovery"""

    @pytest.mark.asyncio
    async def test_python_syntax_error(self, mock_tool_executor):
        """Test handling of Python syntax errors"""
        code = "x = "  # Incomplete statement
        result = await mock_tool_executor.execute(code)

        assert result["error"] is not None
        assert "SyntaxError" in result["error"]

    @pytest.mark.asyncio
    async def test_runtime_exception(self, mock_tool_executor):
        """Test handling of runtime exceptions"""
        code = """
x = 1
y = 0
z = x / y  # Division by zero
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is not None
        assert "ZeroDivisionError" in result["error"]

    @pytest.mark.asyncio
    async def test_exception_with_partial_output(self, mock_tool_executor):
        """Test that output before exception is captured"""
        code = """
print("Before error")
raise ValueError("Test error")
print("After error")
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is not None
        assert "ValueError: Test error" in result["error"]
        assert "Before error" in result["output"]
        assert "After error" not in result["output"]


class TestToolCallLimits:
    """Test tool call limits and resource protection"""

    @pytest.mark.asyncio
    async def test_max_tool_calls_limit(self, mock_tool_executor):
        """Test that tool call limit is enforced"""
        # Set very low limit
        mock_tool_executor.max_tool_calls = 3

        code = """
for i in range(10):
    try:
        result = await add_numbers(a=i, b=i)
    except RuntimeError as e:
        print(f"Stopped at {i}: {e}")
        break
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert "Exceeded max tool calls" in result["output"]
        assert len(result["tool_calls"]) == 3


class TestConvenienceFunction:
    """Test convenience function for quick usage"""

    @pytest.mark.asyncio
    async def test_execute_programmatic_code(self, sample_catalog, monkeypatch):
        """Test convenience function"""
        # Mock the execute_tool method
        async def mock_execute(self, tool_def, parameters):
            if tool_def.name == "add_numbers":
                return {"result": parameters["a"] + parameters["b"]}
            return {}

        # Patch the method
        monkeypatch.setattr(ProgrammaticToolExecutor, "_execute_tool", mock_execute)

        code = """
result = await add_numbers(a=100, b=200)
print(result["result"])
"""
        result = await execute_programmatic_code(code, sample_catalog)

        assert result["error"] is None
        assert "300" in result["output"]


class TestContextInjection:
    """Test context variable injection"""

    @pytest.mark.asyncio
    async def test_context_variables(self, mock_tool_executor):
        """Test that context variables are available in code"""
        code = """
print(f"user_id: {user_id}")
print(f"session: {session}")
"""
        context = {
            "user_id": "user_123",
            "session": "abc-def-ghi"
        }

        result = await mock_tool_executor.execute(code, context=context)

        assert result["error"] is None
        assert "user_id: user_123" in result["output"]
        assert "session: abc-def-ghi" in result["output"]

    @pytest.mark.asyncio
    async def test_context_with_tool_calls(self, mock_tool_executor):
        """Test using context in tool calls"""
        code = """
data = await get_data(id=entity_id)
print(json.dumps(data))
"""
        context = {"entity_id": "entity_456"}

        result = await mock_tool_executor.execute(code, context=context)

        assert result["error"] is None
        assert "entity_456" in result["output"]


class TestExecutionMetadata:
    """Test execution metadata and monitoring"""

    @pytest.mark.asyncio
    async def test_execution_id_uniqueness(self, sample_catalog):
        """Test that each execution gets unique ID"""
        executor1 = ProgrammaticToolExecutor(sample_catalog)
        executor2 = ProgrammaticToolExecutor(sample_catalog)

        assert executor1.execution_id != executor2.execution_id

    @pytest.mark.asyncio
    async def test_execution_time_measurement(self, mock_tool_executor):
        """Test execution time is measured"""
        code = """
await asyncio.sleep(0.05)
print("done")
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert result["execution_time"] >= 0.05
        assert result["execution_time"] < 1.0  # Reasonable upper bound

    @pytest.mark.asyncio
    async def test_tool_call_duration(self, mock_tool_executor):
        """Test that individual tool call durations are tracked"""
        code = """
result = await add_numbers(a=1, b=2)
print("done")
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert len(result["tool_calls"]) == 1

        call = result["tool_calls"][0]
        assert "duration" in call
        assert call["duration"] >= 0
        assert call["completed_at"] >= call["timestamp"]


class TestSafeBuiltins:
    """Test safe builtins functionality"""

    @pytest.mark.asyncio
    async def test_safe_collection_operations(self, mock_tool_executor):
        """Test that safe collection operations work"""
        code = """
numbers = list(range(10))
filtered = [x for x in numbers if x % 2 == 0]
result = sum(filtered)
print(result)
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert "20" in result["output"]  # 0+2+4+6+8 = 20

    @pytest.mark.asyncio
    async def test_safe_string_operations(self, mock_tool_executor):
        """Test that safe string operations work"""
        code = """
text = "Hello, World!"
upper = text.upper()
length = len(upper)
print(f"{upper} ({length})")
"""
        result = await mock_tool_executor.execute(code)

        assert result["error"] is None
        assert "HELLO, WORLD!" in result["output"]
        assert "13" in result["output"]
