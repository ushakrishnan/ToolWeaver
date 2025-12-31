"""
Demo: Control Flow Patterns

Demonstrates how control flow patterns enable advanced agentic workflows:
- Polling loops
- Parallel execution
- Conditional branching
- Retry with backoff
- Sequential processing
"""

import asyncio

from orchestrator._internal.execution.sandbox import SandboxEnvironment
from orchestrator._internal.workflows.control_flow_patterns import (
    ControlFlowPatterns,
    create_conditional_code,
    create_parallel_code,
    create_polling_code,
    create_retry_code,
)


async def demo_pattern_detection():
    """Demo: Automatic pattern detection from task descriptions"""
    print("\n" + "=" * 80)
    print("DEMO 1: Automatic Pattern Detection")
    print("=" * 80)

    tasks = [
        "Wait until the deployment completes",
        "Process all files in the folder concurrently",
        "If the test passes, deploy to production, else notify team",
        "Retry the API call up to 3 times with backoff"
    ]

    for task in tasks:
        pattern = ControlFlowPatterns.detect_pattern_need(task)
        print(f"\nTask: {task}")
        print(f"   -> Detected pattern: {pattern.value if pattern else 'None'}")


async def demo_polling_pattern():
    """Demo: Generate and execute polling code"""
    print("\n" + "=" * 80)
    print("DEMO 2: Polling Pattern")
    print("=" * 80)

    # Generate polling code
    code = create_polling_code(
        check_function="check_build_status",
        check_params='build_id="abc123"',
        completion_condition='status.state == "completed"',
        poll_interval=2.0,
        on_complete="result = status"
    )

    print("\nGenerated polling code:")
    print("-" * 40)
    print(code)
    print("-" * 40)

    # Execute with mock status check
    sandbox = SandboxEnvironment()

    execution_code = f"""
import asyncio

class Status:
    def __init__(self, state):
        self.state = state

# Mock status check function
check_count = 0
async def check_build_status(build_id):
    global check_count
    check_count += 1
    print(f"Check {{check_count}}: Checking build {{build_id}}...")
    if check_count >= 3:
        return Status("completed")
    return Status("running")

{code}

result = "Polling completed after checks: " + str(check_count)
"""

    print("\nExecuting polling simulation...")
    result = await sandbox.execute(execution_code)

    if result.success:
        print("[OK] Success!")
        print(f"Output: {result.stdout.strip()}")
        print(f"Duration: {result.duration:.2f}s")
    else:
        print(f"[FAIL] Failed: {result.error}")


async def demo_parallel_pattern():
    """Demo: Generate and execute parallel processing code"""
    print("\n" + "=" * 80)
    print("DEMO 3: Parallel Pattern")
    print("=" * 80)

    # Generate parallel code
    code = create_parallel_code(
        items_var="files",
        list_function="list_files",
        list_params='folder="/data"',
        process_function="process_file",
        item_param="file_id=item.id"
    )

    print("\nGenerated parallel code:")
    print("-" * 40)
    print(code)
    print("-" * 40)

    # Execute with mock file processing
    sandbox = SandboxEnvironment()

    execution_code = f"""
import asyncio

class File:
    def __init__(self, id, name):
        self.id = id
        self.name = name

async def list_files(folder):
    print(f"Listing files in {{folder}}")
    return [
        File("1", "file1.txt"),
        File("2", "file2.txt"),
        File("3", "file3.txt"),
        File("4", "file4.txt"),
        File("5", "file5.txt"),
    ]

async def process_file(file_id):
    await asyncio.sleep(0.1)  # Simulate processing
    return f"Processed {{file_id}}"

{code}

result = f"Processed {{len(results)}} files in parallel"
print(result)
"""

    print("\nExecuting parallel simulation...")
    result = await sandbox.execute(execution_code)

    if result.success:
        print("[OK] Success!")
        print(f"Output: {result.stdout.strip()}")
        print(f"Duration: {result.duration:.2f}s")
    else:
        print(f"[FAIL] Failed: {result.error}")


async def demo_conditional_pattern():
    """Demo: Generate and execute conditional code"""
    print("\n" + "=" * 80)
    print("DEMO 4: Conditional Pattern")
    print("=" * 80)

    # Generate conditional code
    code = create_conditional_code(
        condition="test_result.passed",
        true_action="await deploy_to_production()",
        false_action="await notify_team('Tests failed')"
    )

    print("\nGenerated conditional code:")
    print("-" * 40)
    print(code)
    print("-" * 40)

    # Execute with mock test result
    sandbox = SandboxEnvironment()

    for passed in [True, False]:
        execution_code = f"""
import asyncio

class TestResult:
    def __init__(self, passed):
        self.passed = passed

test_result = TestResult({passed})

async def deploy_to_production():
    print("🚀 Deploying to production...")
    return "Deployed"

async def notify_team(message):
    print(f"📧 Notifying team: {{message}}")
    return "Notified"

{code}
"""

        print(f"\n  Test result: {'PASSED' if passed else 'FAILED'}")
        result = await sandbox.execute(execution_code)

        if result.success:
            print(f"  {result.stdout.strip()}")


async def demo_retry_pattern():
    """Demo: Generate and execute retry code"""
    print("\n" + "=" * 80)
    print("DEMO 5: Retry Pattern")
    print("=" * 80)

    # Generate retry code
    code = create_retry_code(
        result_var="data",
        operation="fetch_data_from_api()",
        max_retries=3,
        base_backoff=1.0
    )

    print("\nGenerated retry code:")
    print("-" * 40)
    print(code)
    print("-" * 40)

    # Execute with mock API that fails twice then succeeds
    sandbox = SandboxEnvironment()

    execution_code = f"""
import asyncio

call_count = 0

async def fetch_data_from_api():
    global call_count
    call_count += 1
    print(f"API call attempt {{call_count}}")
    
    if call_count < 3:
        raise Exception(f"API Error: Temporary failure")
    
    return {{"status": "success", "data": "Result"}}

{code}

result = f"Success after {{call_count}} attempts: {{data}}"
print(result)
"""

    print("\nExecuting retry simulation...")
    result = await sandbox.execute(execution_code)

    if result.success:
        print("[OK] Success!")
        print(f"Output: {result.stdout.strip()}")
        print(f"Duration: {result.duration:.2f}s")
    else:
        print(f"[FAIL] Failed: {result.error}")


async def demo_pattern_comparison():
    """Demo: Compare performance of different patterns"""
    print("\n" + "=" * 80)
    print("DEMO 6: Pattern Performance Comparison")
    print("=" * 80)

    sandbox = SandboxEnvironment()

    # Sequential vs Parallel processing
    sequential_code = """
import asyncio

items = list(range(5))

async def process_item(item):
    await asyncio.sleep(0.1)
    return item * 2

results = []
for item in items:
    result = await process_item(item)
    results.append(result)

print(f"Sequential: Processed {len(results)} items")
"""

    parallel_code = """
import asyncio

items = list(range(5))

async def process_item(item):
    await asyncio.sleep(0.1)
    return item * 2

results = await asyncio.gather(*[process_item(item) for item in items])

print(f"Parallel: Processed {len(results)} items")
"""

    print("\n  Running sequential processing...")
    seq_result = await sandbox.execute(sequential_code)
    seq_time = seq_result.duration

    print("\n  Running parallel processing...")
    par_result = await sandbox.execute(parallel_code)
    par_time = par_result.duration

    print("\n  Results:")
    print(f"    Sequential: {seq_time:.2f}s")
    print(f"    Parallel:   {par_time:.2f}s")
    print(f"    Speedup:    {seq_time/par_time:.1f}x faster")


async def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print(" " * 25 + "CONTROL FLOW PATTERNS DEMO")
    print("=" * 80)

    print("\nThis demo shows how control flow patterns enable:")
    print("  • Efficient polling without context bloat")
    print("  • Parallel execution for batch operations")
    print("  • Conditional branching for decision making")
    print("  • Automatic retry with exponential backoff")
    print("  • Sequential processing with early exit")

    try:
        await demo_pattern_detection()
        await demo_polling_pattern()
        await demo_parallel_pattern()
        await demo_conditional_pattern()
        await demo_retry_pattern()
        await demo_pattern_comparison()

        print("\n" + "=" * 80)
        print("[OK] All demos completed successfully!")
        print("=" * 80)

        print("\nKey Benefits:")
        print("  1. No context growth during polling loops")
        print("  2. 3-5x speedup on batch operations")
        print("  3. Automatic error recovery with backoff")
        print("  4. Type-safe, testable code generation")
        print("  5. Composable patterns for complex workflows")

    except Exception as e:
        print(f"\n[FAIL] Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
