"""
Demo script for the hybrid orchestrator.

Demonstrates execution of plans with:
- MCP workers (deterministic tools)
- Function calls (structured APIs)
- Code execution (sandboxed Python)
"""

import asyncio
import json
import sys

from orchestrator.hybrid_dispatcher import get_registered_functions
from orchestrator.orchestrator import execute_plan, final_synthesis


def load_plan(path='example_plan.json'):
    """Load execution plan from JSON file."""
    with open(path) as f:
        return json.load(f)


async def run_plan(plan_path):
    """Execute a plan and display results."""
    print(f"\n{'='*60}")
    print(f"Running plan: {plan_path}")
    print(f"{'='*60}\n")

    plan = load_plan(plan_path)
    print(f"Plan ID: {plan.get('request_id')}")
    print(f"Steps: {len(plan.get('steps', []))}")

    # Show registered functions
    registered = get_registered_functions()
    print(f"Registered functions: {', '.join(registered.keys()) if registered else 'none'}")
    print()

    try:
        context = await execute_plan(plan)
        synth = await final_synthesis(plan, context)

        print('\n' + '='*60)
        print('FINAL SYNTHESIS OUTPUT')
        print('='*60 + '\n')
        print(synth['synthesis'])
        print('\n' + '='*60)

        return context, synth
    except Exception as e:
        print(f"\n❌ Plan execution failed: {e}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Main entry point - run demo plans."""

    # Check command line args for plan selection
    if len(sys.argv) > 1:
        plan_path = sys.argv[1]
        await run_plan(plan_path)
    else:
        # Run both example plans
        print("\n" + "="*60)
        print("HYBRID ORCHESTRATOR DEMO")
        print("="*60)
        print("\nThis demo showcases:")
        print("  ✓ MCP Workers - Deterministic tools (OCR, parser, categorizer)")
        print("  ✓ Function Calls - Structured APIs (compute_tax, merge_items)")
        print("  ✓ Code Execution - Dynamic transformations (sandboxed Python)")
        print("\n" + "="*60)

        # Run original plan
        print("\n\n### Running Original Plan ###\n")
        try:
            await run_plan('example_plan.json')
        except Exception:
            print("\n⚠️  Original plan failed, continuing...\n")

        # Run hybrid plan
        print("\n\n### Running Hybrid Plan ###\n")
        try:
            await run_plan('example_plan_hybrid.json')
        except Exception:
            print("\n⚠️  Hybrid plan failed\n")


if __name__ == '__main__':
    asyncio.run(main())
