"""
Example 06: Monitoring and Observability

Demonstrates:
- WandB integration for ML operations tracking
- Prometheus metrics for production monitoring
- Cost tracking and attribution
- Performance profiling
- Error tracking and debugging

Use Case:
Production-grade monitoring for AI applications with real-time dashboards
"""

import asyncio
import os
import time
import random
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator.monitoring import WandBMonitor, PrometheusMonitor
from orchestrator.monitoring_backends import CompositeMonitor


# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


async def simulate_operation(name: str, duration: float, tokens: int, cost: float, success: bool = True):
    """Simulate an AI operation"""
    await asyncio.sleep(duration)
    return {
        "name": name,
        "duration": duration,
        "tokens": tokens,
        "cost": cost,
        "success": success,
        "timestamp": time.time()
    }


async def scenario1_basic_monitoring():
    """Scenario 1: Basic monitoring with WandB"""
    print("\n" + "="*60)
    print("SCENARIO 1: Basic Monitoring with WandB")
    print("="*60)
    
    # Initialize WandB
    wandb_key = os.getenv("WANDB_API_KEY")
    if not wandb_key:
        print("\n⚠ WANDB_API_KEY not set - using mock mode")
        print("  Set WANDB_API_KEY in .env for real tracking")
        monitor = None
    else:
        try:
            monitor = WandBMonitor(
                project="toolweaver-demo",
                tags=["example", "monitoring"],
                config={"model": "gpt-4o", "environment": "demo"}
            )
            print(f"\n✓ WandB initialized")
            print(f"  Project: toolweaver-demo")
        except Exception as e:
            print(f"\n⚠ WandB initialization failed: {e}")
            monitor = None
    
    # Run some operations
    print("\nRunning monitored operations...")
    
    operations = [
        ("receipt_ocr", 1.2, 3450, 0.052),
        ("text_parsing", 0.4, 1200, 0.018),
        ("categorization", 0.6, 2100, 0.032),
    ]
    
    for name, duration, tokens, cost in operations:
        result = await simulate_operation(name, duration, tokens, cost)
        
        if monitor:
            monitor.log_metrics({
                "operation": name,
                "duration": duration,
                "tokens": tokens,
                "cost": cost,
                "timestamp": result["timestamp"]
            })
        
        print(f"\n{name}:")
        print(f"  Duration: {duration}s")
        print(f"  Tokens: {tokens:,}")
        print(f"  Cost: ${cost:.3f}")
        print(f"  ✓ Logged to WandB" if monitor else "  (mock mode)")
    
    if monitor:
        print(f"\n✓ View dashboard: {monitor.get_run_url()}")


async def scenario2_prometheus_metrics():
    """Scenario 2: Prometheus metrics"""
    print("\n" + "="*60)
    print("SCENARIO 2: Prometheus Metrics")
    print("="*60)
    
    try:
        prometheus = PrometheusMonitor(
            port=8000,
            namespace="toolweaver"
        )
        print("\n✓ Prometheus metrics server started on port 8000")
        print("  Access metrics: http://localhost:8000/metrics")
        
        # Simulate operations
        print("\nRecording metrics...")
        for i in range(5):
            duration = 0.5 + random.random()
            tokens = random.randint(1000, 5000)
            cost = tokens * 0.00002
            
            prometheus.record_operation(
                operation="process_receipt",
                duration=duration,
                tokens=tokens,
                cost=cost,
                success=True
            )
            
            print(f"  Operation {i+1}: {duration:.2f}s, {tokens} tokens, ${cost:.4f}")
            await asyncio.sleep(0.1)
        
        print(f"\n✓ Metrics available at: http://localhost:8000/metrics")
        print("  Use with Grafana for visualization")
        
    except Exception as e:
        print(f"\n⚠ Prometheus initialization failed: {e}")
        print("  Port 8000 may be in use")


async def scenario3_cost_tracking():
    """Scenario 3: Cost tracking and attribution"""
    print("\n" + "="*60)
    print("SCENARIO 3: Cost Tracking & Attribution")
    print("="*60)
    
    print("\nSimulating batch processing...")
    
    # Simulate 10 receipts
    total_cost = 0.0
    total_tokens = 0
    total_time = 0.0
    cache_hits = 0
    
    for i in range(1, 11):
        is_cached = i > 3 and random.random() < 0.7
        
        if is_cached:
            duration = 0.1
            tokens = 100  # Cached result, minimal tokens
            cost = 0.002
            cache_hits += 1
        else:
            duration = 1.2
            tokens = 3500
            cost = 0.052
        
        result = await simulate_operation(f"receipt_{i}", duration, tokens, cost)
        
        total_cost += cost
        total_tokens += tokens
        total_time += duration
        
        status = "cached" if is_cached else "processed"
        print(f"  Receipt {i:2d}: {duration:4.1f}s | {tokens:5,} tokens | ${cost:.3f} | {status}")
    
    print(f"\nBatch Summary:")
    print(f"  Total time: {total_time:.1f}s")
    print(f"  Total tokens: {total_tokens:,}")
    print(f"  Total cost: ${total_cost:.3f}")
    print(f"  Cache hit rate: {cache_hits}/10 ({cache_hits*10}%)")
    print(f"  Savings from caching: ${(10 * 0.052 - total_cost):.3f} ({((10 * 0.052 - total_cost) / (10 * 0.052) * 100):.1f}%)")


async def scenario4_error_tracking():
    """Scenario 4: Error tracking"""
    print("\n" + "="*60)
    print("SCENARIO 4: Error Tracking & Debugging")
    print("="*60)
    
    print("\nSimulating operations with errors...")
    
    operations = [
        ("receipt_1", True, None),
        ("receipt_2", True, None),
        ("receipt_3", False, "API timeout after 30s"),
        ("receipt_4", True, None),
        ("receipt_5", False, "Invalid image format"),
        ("receipt_6", True, None),
    ]
    
    success_count = 0
    error_log = []
    
    for name, success, error in operations:
        if success:
            await simulate_operation(name, 1.0, 3000, 0.045, True)
            print(f"  {name}: ✓ success")
            success_count += 1
        else:
            print(f"  {name}: ✗ failed - {error}")
            error_log.append({"operation": name, "error": error, "timestamp": time.time()})
    
    print(f"\nError Summary:")
    print(f"  Success rate: {success_count}/{len(operations)} ({success_count/len(operations)*100:.1f}%)")
    print(f"  Errors: {len(error_log)}")
    for err in error_log:
        print(f"    - {err['operation']}: {err['error']}")


async def scenario5_performance_profiling():
    """Scenario 5: Performance profiling"""
    print("\n" + "="*60)
    print("SCENARIO 5: Performance Profiling")
    print("="*60)
    
    print("\nProfiling workflow steps...")
    
    steps = [
        ("upload_image", 0.15),
        ("ocr_extraction", 0.85),
        ("text_parsing", 0.25),
        ("categorization", 0.40),
        ("validation", 0.20),
        ("report_generation", 0.30),
    ]
    
    total_time = sum(t for _, t in steps)
    
    for name, duration in steps:
        await asyncio.sleep(duration * 0.1)  # Speed up for demo
        percentage = (duration / total_time) * 100
        bar = "█" * int(percentage / 5)
        print(f"  {name:20s}: {duration:4.2f}s  {bar} {percentage:5.1f}%")
    
    print(f"\nTotal workflow time: {total_time:.2f}s")
    print(f"\nBottlenecks:")
    sorted_steps = sorted(steps, key=lambda x: x[1], reverse=True)
    for i, (name, duration) in enumerate(sorted_steps[:3], 1):
        print(f"  {i}. {name}: {duration:.2f}s ({duration/total_time*100:.1f}%)")


async def main():
    """Run all monitoring scenarios"""
    print("\n" + "="*70)
    print(" "*15 + "MONITORING & OBSERVABILITY EXAMPLE")
    print("="*70)
    
    try:
        await scenario1_basic_monitoring()
        await scenario2_prometheus_metrics()
        await scenario3_cost_tracking()
        await scenario4_error_tracking()
        await scenario5_performance_profiling()
        
        print("\n" + "="*70)
        print("✓ All scenarios completed successfully!")
        print("="*70)
        
        print("\nKey Takeaways:")
        print("  1. WandB provides ML-focused tracking and dashboards")
        print("  2. Prometheus offers production-grade metrics")
        print("  3. Cost tracking identifies optimization opportunities")
        print("  4. Error tracking improves reliability")
        print("  5. Performance profiling reveals bottlenecks")
        
        print("\nNext Steps:")
        print("  1. Set up WandB account at wandb.ai")
        print("  2. Configure Grafana for Prometheus visualization")
        print("  3. Set up alerts for errors and cost thresholds")
        print("  4. Create custom dashboards for your metrics")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
