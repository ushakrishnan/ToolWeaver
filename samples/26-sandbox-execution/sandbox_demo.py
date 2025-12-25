"""
Sample 26: Sandbox Execution Environments

Demonstrates how independent execution environments are created and isolated
in ToolWeaver for secure code execution.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator._internal.execution.sandbox import (
    SandboxEnvironment,
    ResourceLimits,
    create_sandbox
)


async def demo_independent_execution_environments():
    """
    Demonstrates how independent execution environments are created and isolated.
    """
    print("="*80)
    print("SAMPLE 26: Independent Execution Environments")
    print("="*80)
    
    # ============================================================================
    # EXAMPLE 1: Creating Independent Sandbox Instances
    # ============================================================================
    print("\n1. Creating Multiple Independent Sandboxes")
    print("-"*80)
    
    # Create sandbox 1
    sandbox1 = SandboxEnvironment(
        limits=ResourceLimits(max_duration=10.0, max_memory_mb=256)
    )
    print("✓ Sandbox 1 created with 256MB memory limit")
    
    # Create sandbox 2 (completely independent)
    sandbox2 = SandboxEnvironment(
        limits=ResourceLimits(max_duration=5.0, max_memory_mb=512)
    )
    print("✓ Sandbox 2 created with 512MB memory limit")
    
    # Using factory function
    sandbox3 = create_sandbox(use_docker=False, limits=ResourceLimits(max_duration=15.0))
    print("✓ Sandbox 3 created via factory function")
    
    
    # ============================================================================
    # EXAMPLE 2: Isolated Namespaces - Variables Don't Leak Between Executions
    # ============================================================================
    print("\n2. Demonstrating Namespace Isolation")
    print("-"*80)
    
    # Execute in sandbox 1
    code1 = """
secret_var = "Sandbox 1 Secret"
result = "executed in sandbox 1"
"""
    result1 = await sandbox1.execute(code1)
    print(f"Sandbox 1 execution: {result1.success}")
    print(f"  Output: {result1.output}")
    
    # Execute in sandbox 2 - try to access sandbox1's variable
    code2 = """
try:
    # This will fail because secret_var doesn't exist here
    accessed = secret_var
    result = f"Accessed: {accessed}"
except NameError as e:
    result = f"Cannot access sandbox1 variable: {e}"
"""
    result2 = await sandbox2.execute(code2)
    print(f"\nSandbox 2 execution: {result2.success}")
    print(f"  Output: {result2.output}")
    
    
    # ============================================================================
    # EXAMPLE 3: Context Injection - Controlled Variable Sharing
    # ============================================================================
    print("\n3. Context Injection (Controlled Sharing)")
    print("-"*80)
    
    # Execute with injected context
    code3 = """
# These variables come from context, not shared namespace
total = sum(numbers)
result = f"Sum of {len(numbers)} numbers = {total}"
"""
    context = {"numbers": [1, 2, 3, 4, 5]}
    result3 = await sandbox1.execute(code3, context=context)
    print(f"Execution with context: {result3.success}")
    print(f"  Output: {result3.output}")
    
    
    # ============================================================================
    # EXAMPLE 4: I/O Stream Isolation - Stdout Capture
    # ============================================================================
    print("\n4. I/O Stream Isolation")
    print("-"*80)
    
    # Sandbox 1 prints
    code_print1 = """
print("Message from Sandbox 1")
print("Line 2 from Sandbox 1")
"""
    result_p1 = await sandbox1.execute(code_print1)
    
    # Sandbox 2 prints
    code_print2 = """
print("Message from Sandbox 2")
print("Line 2 from Sandbox 2")
"""
    result_p2 = await sandbox2.execute(code_print2)
    
    print("Sandbox 1 captured stdout:")
    print(f"  {result_p1.stdout.strip()}")
    
    print("\nSandbox 2 captured stdout:")
    print(f"  {result_p2.stdout.strip()}")
    
    
    # ============================================================================
    # EXAMPLE 5: Security Restrictions - Forbidden Operations
    # ============================================================================
    print("\n5. Security Restrictions")
    print("-"*80)
    
    dangerous_code = """
# Try to use forbidden operations
import os
os.system("ls")
"""
    result_dangerous = await sandbox1.execute(dangerous_code)
    print(f"Dangerous code execution: {result_dangerous.success}")
    print(f"  Error: {result_dangerous.error}")
    print(f"  Error Type: {result_dangerous.error_type}")
    
    
    # ============================================================================
    # EXAMPLE 6: Timeout Enforcement
    # ============================================================================
    print("\n6. Timeout Enforcement (Resource Limits)")
    print("-"*80)
    
    # Create sandbox with short timeout
    sandbox_timeout = SandboxEnvironment(
        limits=ResourceLimits(max_duration=0.5)  # 500ms
    )
    
    slow_code = """
import asyncio

async def __main__():
    # Try to sleep for 2 seconds (will timeout at 500ms)
    await asyncio.sleep(2.0)
    return "Should not reach here"
"""
    result_timeout = await sandbox_timeout.execute(slow_code)
    print(f"Slow code execution: {result_timeout.success}")
    print(f"  Error: {result_timeout.error}")
    print(f"  Duration: {result_timeout.duration:.3f}s")
    
    
    # ============================================================================
    # EXAMPLE 7: The Key Mechanism - _create_safe_globals()
    # ============================================================================
    print("\n7. How Isolation Works: Safe Globals Dictionary")
    print("-"*80)
    print("""
Each sandbox.execute() call creates a NEW isolated environment:

1. Creates empty __builtins__: {'__builtins__': {}}
2. Adds only SAFE_BUILTINS (whitelist)
3. Injects context variables
4. Uses fresh local_vars: {} dictionary
5. Executes with: exec(compiled_code, safe_globals, local_vars)

This means:
- No access to parent process globals
- No access to dangerous functions (eval, exec, open, os, etc.)
- Cannot modify system state
- Cannot access other sandbox's variables
""")
    
    # Show what's in safe globals
    sandbox_demo = SandboxEnvironment()
    safe_globals = sandbox_demo._create_safe_globals({"user_var": "test"})
    print(f"Safe builtins count: {len(safe_globals['__builtins__'])}")
    print(f"Sample safe builtins: {list(safe_globals['__builtins__'].keys())[:10]}")
    print(f"User context included: {'user_var' in safe_globals}")
    
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("\n" + "="*80)
    print("SUMMARY: How Independent Execution Environments Are Created")
    print("="*80)
    print("""
Location: orchestrator/_internal/execution/sandbox.py

Creation Points:
1. Direct instantiation: SandboxEnvironment(limits=...)
2. Factory function: create_sandbox(use_docker=False, limits=...)
3. Automatic in ProgrammaticToolExecutor.__init__()

Independence Mechanisms:
✓ Namespace Isolation    - Each execution gets new safe_globals + local_vars
✓ Builtin Restriction    - Only whitelisted functions available
✓ I/O Capture           - stdout/stderr redirected per execution
✓ Timeout Enforcement    - asyncio.wait_for() with configurable limits
✓ AST Validation        - Forbidden operations detected before execution
✓ No Process Sharing    - Variables don't leak between sandboxes

Current: In-process isolation (logical separation)
Future:  Docker containers (process-level isolation) - Phase 5
""")


async def demo_programmatic_executor_usage():
    """
    Shows how ProgrammaticToolExecutor creates and uses sandboxes.
    """
    print("\n" + "="*80)
    print("BONUS: ProgrammaticToolExecutor Usage")
    print("="*80)
    
    try:
        from orchestrator._internal.catalog.tool_catalog import ToolCatalog
        from orchestrator._internal.execution.programmatic_executor import ProgrammaticToolExecutor
        from orchestrator import mcp_tool
        
        # Define a simple tool
        @mcp_tool(domain="math", description="Add two numbers")
        async def add_numbers(a: int, b: int) -> int:
            return a + b
        
        # Create tool catalog
        catalog = ToolCatalog()
        # Note: In real usage, tools are auto-registered via @mcp_tool decorator
        
        # Create executor - THIS CREATES THE SANDBOX!
        executor = ProgrammaticToolExecutor(
            tool_catalog=catalog,
            timeout=30,
            use_sandbox=True,  # This enables sandbox
            sandbox_limits=ResourceLimits(max_duration=10.0)
        )
        
        print("\n✓ ProgrammaticToolExecutor created")
        print(f"  Sandbox instance: {executor.sandbox}")
        print(f"  Sandbox limits: {executor.sandbox.limits}")
        
        # When executor.execute() is called, it uses this sandbox
        code = """
# This code will execute in the sandbox
result = 1 + 2 + 3
"""
        
        result = await executor.execute(code, context={})
        print(f"\n✓ Code executed in sandbox")
        print(f"  Success: {result.get('success', result.get('error') is None)}")
        
        print("\nKey Point: ProgrammaticToolExecutor.__init__() at line 107:")
        print("  self.sandbox = create_sandbox(use_docker=False, limits=sandbox_limits)")
    
    except ImportError as e:
        print(f"\n⚠ Bonus demo skipped (requires full ToolWeaver installation)")
        print(f"  Import error: {e}")
        print("\nThe core sandbox functionality demonstrated above works independently.")


if __name__ == "__main__":
    print("\n[OK] Running sandbox demonstrations...\n")
    asyncio.run(demo_independent_execution_environments())
    asyncio.run(demo_programmatic_executor_usage())
    print("\n[OK] Sample completed!")
