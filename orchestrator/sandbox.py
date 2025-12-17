"""
Secure sandbox environment for code execution.

Provides isolated execution with resource limits, timeouts,
and security controls. Currently supports in-process execution
with restricted builtins. Docker support can be added when needed.
"""

import ast
import asyncio
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of code execution in sandbox"""
    success: bool
    output: Any
    stdout: str
    stderr: str
    duration: float
    error: Optional[str] = None
    error_type: Optional[str] = None


@dataclass
class ResourceLimits:
    """Resource limits for sandbox execution"""
    max_duration: float = 300.0  # seconds
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0
    allow_network: bool = True  # Allow MCP calls
    allow_file_io: bool = False


class SandboxSecurityError(Exception):
    """Raised when sandbox security is violated"""
    pass


class SandboxEnvironment:
    """
    Secure code execution environment.
    
    Features:
    - Resource limits (CPU, memory, time)
    - Restricted builtins (no eval, exec, __import__)
    - AST validation
    - Timeout enforcement
    - Stdout/stderr capture
    
    Future: Docker-based isolation (see Phase 5 of implementation plan)
    """
    
    # Forbidden functions that could be security risks
    FORBIDDEN_BUILTINS = {
        'eval', 'exec', 'compile', '__import__',
        'open',  # Use controlled file API instead
        'input',  # No interactive input in sandbox
    }
    
    # Forbidden modules that could be security risks
    FORBIDDEN_MODULES = {
        'os', 'sys', 'subprocess', 'socket',
        'shutil', 'tempfile', 'pickle',
    }
    
    # Allowed builtins for safe execution
    SAFE_BUILTINS = {
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 
        'bytes', 'chr', 'dict', 'dir', 'divmod', 'enumerate', 
        'filter', 'float', 'format', 'frozenset', 'getattr', 'hasattr',
        'hash', 'hex', 'int', 'isinstance', 'issubclass', 'iter',
        'len', 'list', 'map', 'max', 'min', 'next', 'oct', 'ord',
        'pow', 'range', 'repr', 'reversed', 'round', 'set', 'setattr',
        'slice', 'sorted', 'str', 'sum', 'tuple', 'type', 'zip',
        '__build_class__', '__name__', '__import__',  # Needed for imports
        # Async support
        'asyncio',
        # Type hints
        'Optional', 'List', 'Dict', 'Any', 'Set', 'Tuple',
        # Exceptions
        'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
        'AttributeError', 'RuntimeError',
        # Logging
        'print',  # Will be captured
    }
    
    def __init__(
        self,
        limits: Optional[ResourceLimits] = None,
        allowed_modules: Optional[Set[str]] = None
    ):
        self.limits = limits or ResourceLimits()
        self.allowed_modules = allowed_modules or set()
        
    def validate_code(self, code: str) -> None:
        """
        Validate code safety using AST analysis.
        
        Args:
            code: Python code to validate
            
        Raises:
            SandboxSecurityError: If code contains forbidden operations
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SandboxSecurityError(f"Syntax error: {e}")
        
        for node in ast.walk(tree):
            # Check for forbidden imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.FORBIDDEN_MODULES:
                        if alias.name not in self.allowed_modules:
                            raise SandboxSecurityError(
                                f"Forbidden import: {alias.name}"
                            )
            
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.FORBIDDEN_MODULES:
                    if node.module not in self.allowed_modules:
                        raise SandboxSecurityError(
                            f"Forbidden import: {node.module}"
                        )
            
            # Check for forbidden function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.FORBIDDEN_BUILTINS:
                        raise SandboxSecurityError(
                            f"Forbidden function: {node.func.id}"
                        )
            
            # Check for attribute access on builtins
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    if node.value.id == '__builtins__':
                        raise SandboxSecurityError(
                            "Direct __builtins__ access forbidden"
                        )
    
    def _create_safe_globals(
        self, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create safe globals dict with restricted builtins.
        
        Args:
            context: User-provided context variables
            
        Returns:
            Safe globals dictionary
        """
        # Start with empty builtins
        safe_globals = {'__builtins__': {}}
        
        # Add safe builtins
        import builtins
        for name in self.SAFE_BUILTINS:
            if hasattr(builtins, name):
                safe_globals['__builtins__'][name] = getattr(builtins, name)
        
        # Add asyncio (required for async code)
        safe_globals['asyncio'] = asyncio
        
        # Add typing hints
        from typing import Optional, List, Dict, Any, Set, Tuple
        safe_globals.update({
            'Optional': Optional,
            'List': List,
            'Dict': Dict,
            'Any': Any,
            'Set': Set,
            'Tuple': Tuple,
        })
        
        # Add user context
        safe_globals.update(context)
        
        return safe_globals
    
    async def execute(
        self, 
        code: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute code in sandbox with resource limits.
        
        Args:
            code: Python code to execute
            context: Variables to inject into execution context
            
        Returns:
            ExecutionResult with output and metadata
        """
        start_time = time.time()
        context = context or {}
        
        # Validate code safety
        try:
            self.validate_code(code)
        except SandboxSecurityError as e:
            return ExecutionResult(
                success=False,
                output=None,
                stdout="",
                stderr="",
                duration=0,
                error=str(e),
                error_type="SecurityError"
            )
        
        # Create safe execution environment
        safe_globals = self._create_safe_globals(context)
        local_vars = {}
        
        # Capture stdout/stderr
        from io import StringIO
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout_capture = StringIO()
        sys.stderr = stderr_capture = StringIO()
        
        try:
            # Execute with timeout
            async def execute_with_timeout():
                # Compile code
                try:
                    compiled = compile(code, '<sandbox>', 'exec')
                except SyntaxError as e:
                    raise SandboxSecurityError(f"Compilation error: {e}")
                
                # Execute
                exec(compiled, safe_globals, local_vars)
                
                # If there's an async function defined, run it
                if '__main__' in local_vars and asyncio.iscoroutinefunction(local_vars['__main__']):
                    return await local_vars['__main__']()
                
                # Otherwise return the last value or None
                return local_vars.get('result', None)
            
            # Run with timeout
            output = await asyncio.wait_for(
                execute_with_timeout(),
                timeout=self.limits.max_duration
            )
            
            duration = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                output=output,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                duration=duration
            )
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return ExecutionResult(
                success=False,
                output=None,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                duration=duration,
                error=f"Execution timeout after {self.limits.max_duration}s",
                error_type="TimeoutError"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_trace = traceback.format_exc()
            
            return ExecutionResult(
                success=False,
                output=None,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue() + "\n" + error_trace,
                duration=duration,
                error=str(e),
                error_type=type(e).__name__
            )
            
        finally:
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr


# Docker-based sandbox (Phase 5 implementation)
class DockerSandbox:
    """
    Docker-based sandbox for true isolation.
    
    Note: This is a placeholder for Phase 5 implementation.
    Requires docker package and running Docker daemon.
    
    Features to implement:
    - Container creation with resource limits
    - Volume mounting for code/data
    - Network restrictions (only allow MCP calls)
    - Container cleanup on exit
    - Multi-container execution for parallel tasks
    """
    
    def __init__(
        self,
        image: str = "python:3.11-slim",
        memory_limit: str = "512m",
        cpu_quota: int = 50000,  # 50% of one core
    ):
        self.image = image
        self.memory_limit = memory_limit
        self.cpu_quota = cpu_quota
        
        # Check if Docker is available
        try:
            import docker
            self.docker = docker.from_env()
            self.available = True
        except (ImportError, Exception) as e:
            logger.warning(f"Docker not available: {e}")
            self.available = False
    
    async def execute(
        self,
        code: str,
        context: Dict[str, Any],
        timeout: int = 300
    ) -> ExecutionResult:
        """
        Execute code in Docker container.
        
        Implementation plan (Phase 5):
        1. Create container with resource limits
        2. Mount code as volume
        3. Execute Python with code
        4. Capture stdout/stderr
        5. Cleanup container
        
        Args:
            code: Python code to execute
            context: Execution context
            timeout: Maximum execution time in seconds
            
        Returns:
            ExecutionResult
        """
        if not self.available:
            raise RuntimeError("Docker not available")
        
        # TODO: Phase 5 implementation
        # See implementation plan for full Docker integration
        raise NotImplementedError("Docker sandbox coming in Phase 5")


def create_sandbox(
    use_docker: bool = False,
    limits: Optional[ResourceLimits] = None
) -> SandboxEnvironment:
    """
    Factory function to create appropriate sandbox.
    
    Args:
        use_docker: Whether to use Docker-based sandbox
        limits: Resource limits for sandbox
        
    Returns:
        SandboxEnvironment or DockerSandbox instance
    """
    if use_docker:
        # Phase 5: Return DockerSandbox
        raise NotImplementedError("Docker sandbox coming in Phase 5")
    else:
        return SandboxEnvironment(limits=limits)
