"""
Test monitoring integration in orchestrator.

Tests that W&B and other backends are automatically initialized
when enabled in .env file.
"""

import asyncio
import os

from orchestrator.orchestrator import execute_plan, get_monitor

# Simple test plan
test_plan = {
    "request_id": "test-monitoring-123",
    "steps": [
        {
            "id": "step1",
            "tool": "function_call",
            "input": {
                "name": "compute_tax",
                "args": {"amount": 100, "tax_rate": 0.1}
            }
        }
    ],
    "final_synthesis": {
        "prompt_template": "Results: {{steps}}"
    }
}

async def main():
    print("=" * 60)
    print("MONITORING INTEGRATION TEST")
    print("=" * 60)
    print()

    # Check monitoring configuration
    backends = os.getenv("MONITORING_BACKENDS", "local")
    print(f"✅ MONITORING_BACKENDS from .env: {backends}")
    print()

    # Get monitor (will be initialized on first plan execution)
    print("🔍 Testing orchestrator with monitoring...")
    print()

    try:
        # Execute plan (monitor will be auto-initialized)
        context = await execute_plan(test_plan)
        print()
        print("✅ Plan executed successfully!")
        print(f"📋 Result: {context}")
        print()

        # Get the monitor instance
        monitor = get_monitor()
        print(f"✅ Monitor initialized with {len(monitor.backends)} backend(s)")
        for backend in monitor.backends:
            backend_type = type(backend).__name__
            print(f"   - {backend_type}")
        print()

        # Check W&B
        if any('wandb' in str(type(b)).lower() for b in monitor.backends):
            print("✅ W&B backend is active!")
            print("📊 Check your dashboard at: https://wandb.ai/usha-krishnan/ToolWeaver")

        print()
        print("=" * 60)
        print("✅ Monitoring integration test complete!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
