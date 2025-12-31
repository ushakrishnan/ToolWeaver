"""
Quick test for W&B monitoring integration.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from orchestrator._internal.observability.monitoring import ToolUsageMonitor


def test_wandb():
    """Test W&B integration with configured credentials."""

    print("\n" + "="*80)
    print("TESTING WEIGHTS & BIASES INTEGRATION")
    print("="*80)

    # Check environment
    wandb_key = os.getenv("WANDB_API_KEY")
    wandb_project = os.getenv("WANDB_PROJECT", "toolweaver")

    if not wandb_key:
        print("❌ WANDB_API_KEY not set in .env")
        return False

    print(f"✅ WANDB_API_KEY found: {wandb_key[:10]}...")
    print(f"✅ Project: {wandb_project}")

    # Try to import wandb
    try:
        import wandb
        print(f"✅ wandb package installed (version {wandb.__version__})")
    except ImportError:
        print("❌ wandb not installed. Run: pip install wandb")
        return False

    print("\n📊 Creating monitor with W&B backend...")

    try:
        # Create monitor with W&B
        monitor = ToolUsageMonitor(
            backends=["local", "wandb"],
            backend_config={
                "wandb": {
                    "project": wandb_project,
                    "run_name": "test-run-1",
                    "config": {
                        "test": "monitoring_integration",
                        "model": "gpt-4o"
                    }
                }
            }
        )

        print("✅ Monitor created successfully")

        # Log some test data
        print("\n📝 Logging test metrics...")

        monitor.log_tool_call("test_tool_1", success=True, latency=0.45)
        monitor.log_tool_call("test_tool_2", success=True, latency=0.32)
        monitor.log_tool_call("test_tool_3", success=False, latency=1.2, error="Test error")

        monitor.log_search_query("test query", num_results=5, latency=0.008, cache_hit=True)

        monitor.log_token_usage(input_tokens=1500, output_tokens=200, cached_tokens=1200)

        print("✅ Metrics logged successfully")

        # Get summary
        summary = monitor.get_summary()
        print("\n📈 Summary:")
        print(f"   Total calls: {summary['overview']['total_tool_calls']}")
        print(f"   Cache hit rate: {summary['overview']['cache_hit_rate']:.1%}")

        # Flush W&B
        print("\n🔄 Flushing W&B data...")
        monitor.flush()

        print("\n✅ SUCCESS! W&B integration working")
        print("\n🌐 View your metrics at:")
        print(f"   https://wandb.ai/{os.getenv('WANDB_ENTITY', 'your-username')}/{wandb_project}")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_wandb()
    sys.exit(0 if success else 1)
