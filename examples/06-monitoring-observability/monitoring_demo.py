"""
Example 06: Monitoring and Observability

Demonstrates:
- Tracking tool execution metrics
- Performance monitoring
- Cost attribution
- Error tracking

Use Case:
Production-grade monitoring for AI applications
"""

import asyncio
import time
import random
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, field

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator import mcp_tool, search_tools


# ============================================================
# Monitoring Infrastructure
# ============================================================

@dataclass
class ExecutionMetrics:
    """Track execution metrics for a tool call."""
    tool_name: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    tokens_used: int = 0
    cost_usd: float = 0.0
    success: bool = True
    error_msg: str = ""
    
    def complete(self):
        """Mark execution as complete."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000


@dataclass
class MetricsCollector:
    """Collect and aggregate metrics."""
    operations: list = field(default_factory=list)
    
    def record(self, op_name: str, duration: float, tokens: int, cost: float, success: bool = True):
        """Record an operation."""
        self.operations.append({
            "name": op_name,
            "duration": duration,
            "tokens": tokens,
            "cost": cost,
            "success": success,
            "timestamp": time.time()
        })
    
    def summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if not self.operations:
            return {"count": 0, "cost": 0.0, "avg_duration": 0.0}
        
        total_cost = sum(o["cost"] for o in self.operations)
        avg_duration = sum(o["duration"] for o in self.operations) / len(self.operations)
        success = sum(1 for o in self.operations if o["success"])
        
        return {
            "count": len(self.operations),
            "success": success,
            "failed": len(self.operations) - success,
            "total_cost_usd": round(total_cost, 4),
            "avg_duration_s": round(avg_duration, 3),
            "total_tokens": sum(o["tokens"] for o in self.operations)
        }


# Global collector
metrics = MetricsCollector()

# ============================================================
# Monitored Tools
# ============================================================

@mcp_tool(domain="receipts", description="OCR with metrics")
async def receipt_ocr(image_uri: str) -> dict:
    """Extract text from receipt."""
    start = time.time()
    await asyncio.sleep(1.2)
    duration = time.time() - start
    metrics.record("ocr", duration, 3450, 0.052)
    return {"text": "Receipt data", "confidence": 0.98}


@mcp_tool(domain="parsing", description="Parse items with metrics")
async def parse_items(text: str) -> dict:
    """Parse items from text."""
    start = time.time()
    await asyncio.sleep(0.4)
    duration = time.time() - start
    metrics.record("parse", duration, 1200, 0.018)
    return {"items": [{"name": "Burger", "price": 12.99}]}


@mcp_tool(domain="analysis", description="Categorize items with metrics")
async def categorize_items(items: list) -> dict:
    """Categorize items."""
    start = time.time()
    await asyncio.sleep(0.6)
    duration = time.time() - start
    metrics.record("categorize", duration, 2100, 0.032)
    return {"food": items, "other": []}


async def scenario1_basic_monitoring():
    """Scenario 1: Basic monitoring"""
    print("\n" + "="*70)
    print("SCENARIO 1: Tool Execution Monitoring")
    print("="*70)
    
    print("\nMonitoring tool execution...")
    
    await receipt_ocr({"image_uri": "receipt.jpg"})
    await parse_items({"text": "receipt data"})
    await categorize_items({"items": []})
    
    summary = metrics.summary()
    print(f"\nExecution Summary:")
    print(f"  Operations: {summary['count']}")
    print(f"  Total Cost: ${summary['total_cost_usd']:.4f}")
    print(f"  Avg Duration: {summary['avg_duration_s']:.3f}s")
    print(f"  Success Rate: {summary['success']}/{summary['count']}")


async def scenario2_cost_tracking():
    """Scenario 2: Cost tracking"""
    print("\n" + "="*70)
    print("SCENARIO 2: Cost Tracking & Attribution")
    print("="*70)
    
    print("\nSimulating batch processing...")
    
    total_cost = 0.0
    cache_hits = 0
    
    for i in range(1, 11):
        is_cached = i > 3 and random.random() < 0.7
        
        if is_cached:
            cost = 0.002
            cache_hits += 1
        else:
            cost = 0.052
        
        total_cost += cost
        status = "cached" if is_cached else "processed"
        print(f"  Receipt {i:2d}: ${cost:.4f} | {status}")
    
    print(f"\nBatch Summary:")
    print(f"  Total cost: ${total_cost:.3f}")
    print(f"  Cache hit rate: {cache_hits}/10")
    savings = (10 * 0.052 - total_cost)
    print(f"  Savings: ${savings:.3f}")


async def scenario3_error_tracking():
    """Scenario 3: Error tracking"""
    print("\n" + "="*70)
    print("SCENARIO 3: Error Tracking & Debugging")
    print("="*70)
    
    print("\nSimulating operations with errors...")
    
    operations = [
        ("receipt_1", True, None),
        ("receipt_2", True, None),
        ("receipt_3", False, "API timeout"),
        ("receipt_4", True, None),
        ("receipt_5", False, "Invalid format"),
        ("receipt_6", True, None),
    ]
    
    success_count = 0
    error_log = []
    
    for name, success, error in operations:
        if success:
            print(f"  {name}: ✓ success")
            success_count += 1
            metrics.record(name, 1.0, 3000, 0.045)
        else:
            print(f"  {name}: ✗ failed - {error}")
            error_log.append({"op": name, "error": error})
    
    print(f"\nError Summary:")
    print(f"  Success rate: {success_count}/{len(operations)} ({100*success_count//len(operations)}%)")
    for err in error_log:
        print(f"    {err['op']}: {err['error']}")


async def scenario4_performance_profiling():
    """Scenario 4: Performance profiling"""
    print("\n" + "="*70)
    print("SCENARIO 4: Performance Profiling")
    print("="*70)
    
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
        percentage = (duration / total_time) * 100
        bar = "=" * int(percentage / 5)
        print(f"  {name:20s}: {duration:5.2f}s {bar:12} {percentage:5.1f}%")
    
    print(f"\nTotal: {total_time:.2f}s")
    print(f"\nBottlenecks:")
    for i, (name, duration) in enumerate(sorted(steps, key=lambda x: -x[1])[:3], 1):
        print(f"  {i}. {name}: {duration:.2f}s ({100*duration/total_time:.1f}%)")


async def main():
    """Run monitoring scenarios."""
    print("\n" + "="*70)
    print("EXAMPLE 06: Monitoring & Observability")
    print("="*70)
    
    await scenario1_basic_monitoring()
    await scenario2_cost_tracking()
    await scenario3_error_tracking()
    await scenario4_performance_profiling()
    
    print("\n" + "="*70)
    print("FINAL METRICS REPORT")
    print("="*70)
    
    summary = metrics.summary()
    print(f"\nTotal Operations: {summary['count']}")
    print(f"  Successful: {summary['success']}")
    print(f"  Failed: {summary['failed']}")
    print(f"Total Cost: ${summary['total_cost_usd']:.4f}")
    print(f"Avg Duration: {summary['avg_duration_s']:.3f}s")
    print(f"Total Tokens: {summary['total_tokens']:,}")
    
    print("\n" + "="*70)
    print("✓ Monitoring demonstration complete!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
