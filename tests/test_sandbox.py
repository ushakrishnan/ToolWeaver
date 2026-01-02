"""
Tests for sandbox execution environment.
"""


import pytest

from orchestrator._internal.execution.sandbox import (
    ExecutionResult,
    ResourceLimits,
    SandboxEnvironment,
    SandboxSecurityError,
    create_sandbox,
)


class TestResourceLimits:
    """Test ResourceLimits dataclass"""

    def test_default_limits(self):
        """Test default resource limits"""
        limits = ResourceLimits()

        assert limits.max_duration == 300.0
        assert limits.max_memory_mb == 512
        assert limits.max_cpu_percent == 50.0
        assert limits.allow_network is True
        assert limits.allow_file_io is False

    def test_custom_limits(self):
        """Test custom resource limits"""
        limits = ResourceLimits(
            max_duration=60.0,
            max_memory_mb=256,
            allow_network=False
        )

        assert limits.max_duration == 60.0
        assert limits.max_memory_mb == 256
        assert limits.allow_network is False


class TestSandboxValidation:
    """Test code validation"""

    def test_validate_safe_code(self):
        """Test validating safe code"""
        sandbox = SandboxEnvironment()

        code = """
x = 1 + 2
print(x)
"""

        # Should not raise
        sandbox.validate_code(code)

    def test_forbid_eval(self):
        """Test that eval is forbidden"""
        sandbox = SandboxEnvironment()

        code = "eval('1 + 1')"

        with pytest.raises(SandboxSecurityError) as exc_info:
            sandbox.validate_code(code)

        assert "eval" in str(exc_info.value)

    def test_forbid_exec(self):
        """Test that exec is forbidden"""
        sandbox = SandboxEnvironment()

        code = "exec('x = 1')"

        with pytest.raises(SandboxSecurityError) as exc_info:
            sandbox.validate_code(code)

        assert "exec" in str(exc_info.value)

    def test_forbid_open(self):
        """Test that open is forbidden"""
        sandbox = SandboxEnvironment()

        code = "open('/etc/passwd', 'r')"

        with pytest.raises(SandboxSecurityError) as exc_info:
            sandbox.validate_code(code)

        assert "open" in str(exc_info.value)

    def test_forbid_os_import(self):
        """Test that os module import is forbidden"""
        sandbox = SandboxEnvironment()

        code = "import os"

        with pytest.raises(SandboxSecurityError) as exc_info:
            sandbox.validate_code(code)

        assert "os" in str(exc_info.value)

    def test_forbid_subprocess_import(self):
        """Test that subprocess module import is forbidden"""
        sandbox = SandboxEnvironment()

        code = "import subprocess"

        with pytest.raises(SandboxSecurityError) as exc_info:
            sandbox.validate_code(code)

        assert "subprocess" in str(exc_info.value)

    def test_forbid_from_import(self):
        """Test that forbidden from imports are blocked"""
        sandbox = SandboxEnvironment()

        code = "from os import system"

        with pytest.raises(SandboxSecurityError) as exc_info:
            sandbox.validate_code(code)

        assert "os" in str(exc_info.value)

    def test_forbid_builtins_access(self):
        """Test that __builtins__ access is forbidden"""
        sandbox = SandboxEnvironment()

        code = "__builtins__.eval('1+1')"

        with pytest.raises(SandboxSecurityError) as exc_info:
            sandbox.validate_code(code)

        assert "__builtins__" in str(exc_info.value)

    def test_allow_safe_imports(self):
        """Test that safe imports are allowed"""
        sandbox = SandboxEnvironment()

        # asyncio is allowed
        code = "import asyncio"
        sandbox.validate_code(code)  # Should not raise

    def test_allow_module_with_permission(self):
        """Test allowing module when explicitly permitted"""
        sandbox = SandboxEnvironment(allowed_modules={'os'})

        code = "import os"
        sandbox.validate_code(code)  # Should not raise

    def test_syntax_error(self):
        """Test handling syntax errors"""
        sandbox = SandboxEnvironment()

        code = "if True"  # Missing colon

        with pytest.raises(SandboxSecurityError) as exc_info:
            sandbox.validate_code(code)

        assert "Syntax error" in str(exc_info.value)


@pytest.mark.asyncio
class TestSandboxExecution:
    """Test code execution in sandbox"""

    async def test_simple_execution(self):
        """Test executing simple code"""
        sandbox = SandboxEnvironment()

        code = """
result = 1 + 2
"""

        execution_result = await sandbox.execute(code)

        assert execution_result.success is True
        assert execution_result.error is None
        assert execution_result.duration > 0

    async def test_execution_with_context(self):
        """Test execution with context variables"""
        sandbox = SandboxEnvironment()

        code = """
result = x + y
"""

        context = {"x": 10, "y": 20}
        execution_result = await sandbox.execute(code, context)

        assert execution_result.success is True
        # result is in local_vars, not returned

    async def test_async_execution(self):
        """Test executing async code"""
        sandbox = SandboxEnvironment()

        code = """
import asyncio

async def __main__():
    await asyncio.sleep(0.1)
    return "done"
"""

        execution_result = await sandbox.execute(code)

        assert execution_result.success is True
        assert execution_result.output == "done"

    async def test_stdout_capture(self):
        """Test capturing stdout"""
        sandbox = SandboxEnvironment()

        code = """
print("Hello, World!")
print("Second line")
"""

        execution_result = await sandbox.execute(code)

        assert execution_result.success is True
        assert "Hello, World!" in execution_result.stdout
        assert "Second line" in execution_result.stdout

    async def test_exception_handling(self):
        """Test handling exceptions"""
        sandbox = SandboxEnvironment()

        code = """
result = 1 / 0  # Division by zero
"""

        execution_result = await sandbox.execute(code)

        assert execution_result.success is False
        assert execution_result.error is not None
        assert execution_result.error_type == "ZeroDivisionError"
        assert "ZeroDivisionError" in execution_result.stderr

    async def test_timeout_enforcement(self):
        """Test that timeouts are enforced"""
        limits = ResourceLimits(max_duration=0.5)  # 500ms timeout
        sandbox = SandboxEnvironment(limits=limits)

        code = """
import asyncio

async def __main__():
    await asyncio.sleep(2.0)  # Sleep longer than timeout
"""

        execution_result = await sandbox.execute(code)

        assert execution_result.success is False
        assert execution_result.error_type == "TimeoutError"
        assert "timeout" in execution_result.error.lower()

    async def test_security_error_during_execution(self):
        """Test security errors are caught"""
        sandbox = SandboxEnvironment()

        code = "eval('1 + 1')"

        execution_result = await sandbox.execute(code)

        assert execution_result.success is False
        assert execution_result.error_type == "SecurityError"

    async def test_safe_builtins_available(self):
        """Test that safe builtins are available"""
        sandbox = SandboxEnvironment()

        code = """
# Test various safe builtins
result = []
result.append(len([1, 2, 3]))
result.append(max([4, 2, 8]))
result.append(sum([1, 2, 3]))
result.append(sorted([3, 1, 2]))
"""

        execution_result = await sandbox.execute(code)

        assert execution_result.success is True

    async def test_typing_hints_available(self):
        """Test that typing hints are available"""
        sandbox = SandboxEnvironment()

        code = """
from typing import List, Dict, Optional

def func(x: Optional[List[int]]) -> Dict[str, int]:
    return {"count": len(x) if x else 0}

result = func([1, 2, 3])
"""

        execution_result = await sandbox.execute(code)

        assert execution_result.success is True

    async def test_asyncio_available(self):
        """Test that asyncio is available"""
        sandbox = SandboxEnvironment()

        code = """
import asyncio

async def __main__():
    await asyncio.sleep(0.01)
    return "async works"
"""

        execution_result = await sandbox.execute(code)

        assert execution_result.success is True
        assert execution_result.output == "async works"

    async def test_partial_execution_before_error(self):
        """Test that stdout is captured even when error occurs"""
        sandbox = SandboxEnvironment()

        code = """
print("Starting")
print("Working")
raise ValueError("Something went wrong")
print("Never reached")
"""

        execution_result = await sandbox.execute(code)

        assert execution_result.success is False
        assert "Starting" in execution_result.stdout
        assert "Working" in execution_result.stdout
        assert "Never reached" not in execution_result.stdout
        assert "ValueError" in execution_result.stderr


class TestSandboxFactory:
    """Test sandbox factory function"""

    def test_create_default_sandbox(self):
        """Test creating default sandbox"""
        sandbox = create_sandbox()

        assert isinstance(sandbox, SandboxEnvironment)

    def test_create_with_limits(self):
        """Test creating sandbox with custom limits"""
        limits = ResourceLimits(max_duration=60.0)
        sandbox = create_sandbox(limits=limits)

        assert isinstance(sandbox, SandboxEnvironment)
        assert sandbox.limits.max_duration == 60.0

    def test_docker_not_implemented_yet(self):
        """Test that Docker sandbox is not yet implemented"""
        with pytest.raises(NotImplementedError):
            create_sandbox(use_docker=True)


class TestExecutionResult:
    """Test ExecutionResult dataclass"""

    def test_success_result(self):
        """Test creating success result"""
        result = ExecutionResult(
            success=True,
            output="test",
            stdout="output",
            stderr="",
            duration=1.5
        )

        assert result.success is True
        assert result.output == "test"
        assert result.error is None
        assert result.error_type is None

    def test_failure_result(self):
        """Test creating failure result"""
        result = ExecutionResult(
            success=False,
            output=None,
            stdout="",
            stderr="error output",
            duration=0.5,
            error="Test error",
            error_type="ValueError"
        )

        assert result.success is False
        assert result.output is None
        assert result.error == "Test error"
        assert result.error_type == "ValueError"


@pytest.mark.asyncio
class TestComplexScenarios:
    """Test complex execution scenarios"""

    async def test_multiple_async_operations(self):
        """Test multiple async operations"""
        sandbox = SandboxEnvironment()

        code = """
import asyncio

async def __main__():
    async def task1():
        await asyncio.sleep(0.01)
        return "task1"

    async def task2():
        await asyncio.sleep(0.01)
        return "task2"

    results = await asyncio.gather(task1(), task2())
    return results
"""

        execution_result = await sandbox.execute(code)

        assert execution_result.success is True
        assert execution_result.output == ["task1", "task2"]

    async def test_exception_with_context(self):
        """Test exception handling with context"""
        sandbox = SandboxEnvironment()

        code = """
result = items[10]  # IndexError
"""

        context = {"items": [1, 2, 3]}
        execution_result = await sandbox.execute(code, context)

        assert execution_result.success is False
        assert execution_result.error_type == "IndexError"

    async def test_list_comprehension(self):
        """Test list comprehension execution"""
        sandbox = SandboxEnvironment()

        code = """
result = [x * 2 for x in range(5)]
"""

        execution_result = await sandbox.execute(code)

        assert execution_result.success is True

    async def test_dictionary_operations(self):
        """Test dictionary operations"""
        sandbox = SandboxEnvironment()

        code = """
data = {"a": 1, "b": 2}
result = {k: v * 2 for k, v in data.items()}
"""

        execution_result = await sandbox.execute(code)

        assert execution_result.success is True
