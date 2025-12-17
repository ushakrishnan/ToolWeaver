"""
Example: Using ToolWeaver with Different Monitoring Backends

Shows how to configure and use local, W&B, and Prometheus monitoring.
"""

import asyncio
import os
from orchestrator.monitoring import ToolUsageMonitor


# ============================================================
# Example 1: Local Backend (Default - No Setup Required)
# ============================================================

def example_local_monitoring():
    """
    Local file-based monitoring.
    
    Benefits:
    - Zero dependencies
    - Works offline
    - Privacy-friendly (no external services)
    - Good for: Development, personal use, enterprise
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Local Monitoring (Default)")
    print("="*80)
    
    # Create monitor (defaults to local backend)
    monitor = ToolUsageMonitor()
    
    # Or explicitly specify
    # monitor = ToolUsageMonitor(backends="local", log_dir=".tool_logs")
    
    # Log some tool calls
    monitor.log_tool_call("github_list_repos", success=True, latency=0.45)
    monitor.log_tool_call("github_get_commits", success=True, latency=0.32)
    monitor.log_tool_call("github_create_pr", success=False, latency=1.2, error="Auth failed")
    
    # Log search
    monitor.log_search_query("github repositories", num_results=5, latency=0.008, cache_hit=True)
    
    # Log tokens
    monitor.log_token_usage(input_tokens=1500, output_tokens=200, cached_tokens=1200)
    
    # Get summary
    summary = monitor.get_summary()
    print(f"\n✅ Logged to: .tool_logs/")
    print(f"   Total calls: {summary['overview']['total_tool_calls']}")
    print(f"   Cache hit rate: {summary['overview']['cache_hit_rate']:.1%}")
    print(f"\n💾 Log files:")
    print(f"   - .tool_logs/tool_calls_2025-12-16.jsonl")
    print(f"   - .tool_logs/search_queries_2025-12-16.jsonl")
    print(f"   - .tool_logs/token_usage_2025-12-16.jsonl")


# ============================================================
# Example 2: Weights & Biases Integration
# ============================================================

def example_wandb_monitoring():
    """
    W&B monitoring for experiment tracking.
    
    Setup:
    1. pip install wandb
    2. wandb login
    3. Set WANDB_API_KEY in .env
    
    Benefits:
    - Beautiful dashboards
    - Experiment comparison
    - Team collaboration
    - Version tracking
    
    Good for: ML teams, A/B testing, research
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Weights & Biases Monitoring")
    print("="*80)
    
    # Check if W&B is available
    try:
        import wandb
    except ImportError:
        print("⚠️  W&B not installed. Run: pip install wandb")
        return
    
    if not os.getenv("WANDB_API_KEY"):
        print("⚠️  WANDB_API_KEY not set. Set it in .env or run: wandb login")
        return
    
    # Create monitor with W&B backend
    monitor = ToolUsageMonitor(
        backends="wandb",
        backend_config={
            "wandb": {
                "project": "toolweaver-demo",
                "run_name": "experiment-1",
                "config": {
                    "model": "gpt-4o",
                    "prompt_version": "v2.1"
                }
            }
        }
    )
    
    # Log tool calls
    monitor.log_tool_call("receipt_ocr", success=True, latency=0.55)
    monitor.log_tool_call("line_item_parser", success=True, latency=0.31)
    
    # Log search
    monitor.log_search_query("receipt processing", num_results=8, latency=0.012)
    
    # Log tokens
    monitor.log_token_usage(input_tokens=2000, output_tokens=300, cached_tokens=1800)
    
    print(f"\n✅ Metrics sent to W&B")
    print(f"   View at: https://wandb.ai/your-team/toolweaver-demo")
    print(f"\n📊 Available visualizations:")
    print(f"   - Tool latency over time")
    print(f"   - Error rates by tool")
    print(f"   - Token usage trends")
    print(f"   - Cache hit rates")
    
    # Flush to ensure data is sent
    monitor.flush()


# ============================================================
# Example 3: Prometheus for Production
# ============================================================

def example_prometheus_monitoring():
    """
    Prometheus metrics for production monitoring.
    
    Setup:
    1. pip install prometheus-client
    2. Set PROMETHEUS_PORT in .env (default: 8000)
    3. Configure Prometheus to scrape endpoint
    
    Benefits:
    - Production-grade monitoring
    - Integrates with Grafana
    - Kubernetes/Docker friendly
    - AlertManager support
    
    Good for: Production deployments, DevOps, SRE teams
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Prometheus Monitoring")
    print("="*80)
    
    # Check if prometheus_client is available
    try:
        import prometheus_client
    except ImportError:
        print("⚠️  Prometheus client not installed. Run: pip install prometheus-client")
        return
    
    # Create monitor with Prometheus backend
    monitor = ToolUsageMonitor(
        backends="prometheus",
        backend_config={
            "prometheus": {
                "port": 8000
            }
        }
    )
    
    # Log tool calls
    monitor.log_tool_call("database_query", success=True, latency=0.15)
    monitor.log_tool_call("api_call", success=True, latency=0.42)
    monitor.log_tool_call("cache_lookup", success=True, latency=0.002)
    
    # Log search
    monitor.log_search_query("database tools", num_results=3, latency=0.005, cache_hit=True)
    
    # Log tokens
    monitor.log_token_usage(input_tokens=1000, output_tokens=150, cached_tokens=800)
    
    print(f"\n✅ Prometheus metrics server running on port 8000")
    print(f"   Metrics endpoint: http://localhost:8000/metrics")
    print(f"\n📊 Exposed metrics:")
    print(f"   - toolweaver_tool_calls_total")
    print(f"   - toolweaver_tool_errors_total")
    print(f"   - toolweaver_tool_latency_seconds")
    print(f"   - toolweaver_search_queries_total")
    print(f"   - toolweaver_cache_hits_total")
    print(f"   - toolweaver_tokens_total")
    print(f"\n🔧 Prometheus scrape config (add to prometheus.yml):")
    print(f"   scrape_configs:")
    print(f"     - job_name: 'toolweaver'")
    print(f"       static_configs:")
    print(f"         - targets: ['localhost:8000']")


# ============================================================
# Example 4: Multiple Backends
# ============================================================

def example_multi_backend_monitoring():
    """
    Use multiple backends simultaneously.
    
    Useful for:
    - Development: Local files + W&B for experiments
    - Staging: Local + Prometheus for pre-prod testing
    - Production: Prometheus + Local for backup
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Multiple Backends")
    print("="*80)
    
    # Create monitor with multiple backends
    monitor = ToolUsageMonitor(
        backends=["local", "wandb", "prometheus"],
        backend_config={
            "local": {"log_dir": ".tool_logs"},
            "wandb": {"project": "toolweaver-prod", "run_name": "prod-1"},
            "prometheus": {"port": 8001}
        }
    )
    
    # Log some activity
    monitor.log_tool_call("payment_processor", success=True, latency=0.85)
    monitor.log_search_query("payment tools", num_results=4, latency=0.009)
    monitor.log_token_usage(input_tokens=1500, output_tokens=250)
    
    print(f"\n✅ Metrics sent to all backends:")
    print(f"   📁 Local: .tool_logs/")
    print(f"   🎨 W&B: https://wandb.ai/your-team/toolweaver-prod")
    print(f"   📊 Prometheus: http://localhost:8001/metrics")
    
    # Get summary (from in-memory aggregation)
    summary = monitor.get_summary()
    print(f"\n📈 Summary:")
    print(f"   Total calls: {summary['overview']['total_tool_calls']}")
    
    # Flush all backends
    monitor.flush()


# ============================================================
# Example 5: Production Usage Pattern
# ============================================================

async def example_production_pattern():
    """
    Realistic production usage with monitoring.
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: Production Pattern")
    print("="*80)
    
    # Initialize from environment
    backends = os.getenv("MONITORING_BACKENDS", "local").split(",")
    
    monitor = ToolUsageMonitor(backends=backends)
    
    print(f"✅ Monitoring backends: {backends}")
    
    # Simulate tool usage
    tools = [
        ("github_list_repos", True, 0.45),
        ("github_get_commits", True, 0.32),
        ("github_create_pr", True, 0.88),
        ("slack_send_message", True, 0.21),
    ]
    
    for tool_name, success, latency in tools:
        monitor.log_tool_call(tool_name, success, latency)
        print(f"   📞 {tool_name}: {latency:.2f}s")
        await asyncio.sleep(0.1)  # Simulate async work
    
    # Log aggregated metrics
    monitor.log_search_query("github operations", num_results=6, latency=0.012)
    monitor.log_token_usage(input_tokens=2500, output_tokens=400, cached_tokens=2000)
    
    # Print summary
    from orchestrator.monitoring import print_metrics_report
    print_metrics_report(monitor)
    
    # Flush at shutdown
    monitor.flush()


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print("\n🔍 TOOLWEAVER MONITORING EXAMPLES\n")
    
    # Run examples
    example_local_monitoring()
    
    # Uncomment to try other backends:
    # example_wandb_monitoring()
    # example_prometheus_monitoring()
    # example_multi_backend_monitoring()
    
    # asyncio.run(example_production_pattern())
    
    print("\n" + "="*80)
    print("💡 TIP: Set MONITORING_BACKENDS in .env to configure backends")
    print("="*80)
    print("\nOptions:")
    print("  MONITORING_BACKENDS=local           # Default, file-based")
    print("  MONITORING_BACKENDS=wandb           # W&B for experiments")
    print("  MONITORING_BACKENDS=prometheus      # Production metrics")
    print("  MONITORING_BACKENDS=local,wandb,prometheus  # All backends")
    print()
