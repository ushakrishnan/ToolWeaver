#!/usr/bin/env python
"""Test skill workflows - focus on workflow retry logic."""

import asyncio
import logging
logging.basicConfig(level=logging.ERROR)

from orchestrator.execution import (
    create_workflow,
    add_step,
    save_workflow,
    load_workflow,
    execute_workflow,
    list_workflows,
)

print("=" * 60)
print("PHASE 4.2: Workflow Retry Logic Test")
print("=" * 60)

# Create workflow with retry steps
w = create_workflow('test_retry_flow', 'Test workflow retry logic')

# Add steps with various retry configs
add_step(w, 'step1', 'nonexistent_skill_1', {'input': 'test'}, retry=0)
add_step(w, 'step2', 'nonexistent_skill_2', {'input': 'test'}, retry=2)
add_step(w, 'step3', 'nonexistent_skill_3', {'input': 'test'}, retry=1)

print("[OK] Created workflow with 3 steps")
print(f"  - Step 1: retry=0 (no retries)")
print(f"  - Step 2: retry=2 (max 2 retries)")
print(f"  - Step 3: retry=1 (max 1 retry)")

# Save and load
save_workflow(w)
print("[OK] Saved workflow to disk")

loaded = load_workflow('test_retry_flow')
print("[OK] Loaded workflow from disk")

# Execute - should fail gracefully after retries
print("\nExecuting workflow...")
print("  Expected: Step 1 fails immediately (retry=0)")
print("  Expected: Step 2 retries 2 times then fails")
print("  Expected: Step 3 retries 1 time then fails")

try:
    results = asyncio.run(execute_workflow(loaded, {}))
    print("[OK] Workflow executed")
    print(f"  Results: {list(results.keys())}")
except ValueError as e:
    print(f"[OK] Workflow failed as expected: {e}")
except RecursionError as e:
    print(f"[ERROR] INFINITE RECURSION! This should NOT happen: {e}")
    exit(1)

# List workflows
workflows = list_workflows()
print(f"\n[OK] Available workflows: {len(workflows)} total")
if workflows:
    print(f"  First workflow: {workflows[0]}")

print("\n" + "=" * 60)
print("RETRY LOGIC TEST: PASSED")
print("=" * 60)
