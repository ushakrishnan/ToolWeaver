# How to Monitor Performance

Step-by-step guide to track metrics, costs, and performance for your ToolWeaver workflows.

## Prerequisites

- Working ToolWeaver project
- Basic understanding of [ToolWeaver concepts](../concepts/overview.md)

## What You'll Accomplish

By the end of this guide, you'll have:

✅ Metrics collection for tool execution  
✅ Cost tracking per operation  
✅ Performance monitoring dashboards  
✅ Error tracking and logging  
✅ WandB or Prometheus integration  

**Estimated time:** 20 minutes

---

## Step 1: Install Monitoring Dependencies

```bash
# Install with monitoring support
pip install toolweaver[monitoring]

# Or install individually
pip install prometheus-client  # For Prometheus
pip install wandb              # For WandB (ML tracking)
```

---

## Step 2: Basic Metrics Collection

### 2.1 Create Metrics Collector

**File:** `monitoring/metrics.py`

```python
from dataclasses import dataclass, field
import time
from typing import Dict, Any

@dataclass
class MetricsCollector:
    """Collect and aggregate metrics."""
    operations: list = field(default_factory=list)
    
    def record(
        self,
        operation: str,
        duration: float,
        tokens: int = 0,
        cost: float = 0.0,
        success: bool = True,
        error: str = ""
    ):
        """Record an operation."""
        self.operations.append({
            "operation": operation,
            "duration": duration,
            "tokens": tokens,
            "cost": cost,
            "success": success,
            "error": error,
            "timestamp": time.time()
        })
    
    def summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if not self.operations:
            return {"count": 0}
        
        successes = sum(1 for o in self.operations if o["success"])
        total_cost = sum(o["cost"] for o in self.operations)
        avg_duration = sum(o["duration"] for o in self.operations) / len(self.operations)
        
        return {
            "total_operations": len(self.operations),
            "successes": successes,
            "failures": len(self.operations) - successes,
            "success_rate": successes / len(self.operations),
            "total_cost_usd": round(total_cost, 4),
            "avg_duration_s": round(avg_duration, 3),
            "total_tokens": sum(o["tokens"] for o in self.operations)
        }
    
    def cost_by_operation(self) -> Dict[str, float]:
        """Get cost breakdown by operation type."""
        costs = {}
        for op in self.operations:
            name = op["operation"]
            costs[name] = costs.get(name, 0.0) + op["cost"]
        return {k: round(v, 4) for k, v in costs.items()}

# Global collector
metrics = MetricsCollector()
```

### 2.2 Track Tool Execution

```python
import time

async def execute_with_metrics(tool_name: str, params: dict):
    """Execute tool with metrics tracking."""
    
    start_time = time.time()
    
    try:
        result = await orchestrator.execute_tool(tool_name, params)
        
        # Record success
        duration = time.time() - start_time
        metrics.record(
            operation=tool_name,
            duration=duration,
            tokens=result.get("tokens_used", 0),
            cost=result.get("cost", 0.0),
            success=True
        )
        
        return result
    
    except Exception as e:
        # Record failure
        duration = time.time() - start_time
        metrics.record(
            operation=tool_name,
            duration=duration,
            success=False,
            error=str(e)
        )
        raise

# Usage
result = await execute_with_metrics("gpt4_vision", {"image": "receipt.jpg"})

# Print summary
print(metrics.summary())
```

---

## Step 3: Set Up Prometheus Metrics

### 3.1 Install Prometheus Client

```bash
pip install prometheus-client
```

### 3.2 Create Prometheus Exporter

**File:** `monitoring/prometheus_exporter.py`

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Define metrics
tool_executions = Counter(
    'toolweaver_tool_executions_total',
    'Total tool executions',
    ['tool_name', 'status']
)

tool_duration = Histogram(
    'toolweaver_tool_duration_seconds',
    'Tool execution duration',
    ['tool_name']
)

tool_cost = Counter(
    'toolweaver_tool_cost_usd_total',
    'Total cost in USD',
    ['tool_name']
)

active_operations = Gauge(
    'toolweaver_active_operations',
    'Currently active operations'
)

async def execute_with_prometheus(tool_name: str, params: dict):
    """Execute tool with Prometheus metrics."""
    
    active_operations.inc()
    start_time = time.time()
    
    try:
        result = await orchestrator.execute_tool(tool_name, params)
        
        # Record metrics
        duration = time.time() - start_time
        tool_executions.labels(tool_name=tool_name, status='success').inc()
        tool_duration.labels(tool_name=tool_name).observe(duration)
        tool_cost.labels(tool_name=tool_name).inc(result.get("cost", 0.0))
        
        return result
    
    except Exception as e:
        tool_executions.labels(tool_name=tool_name, status='failure').inc()
        raise
    
    finally:
        active_operations.dec()

# Start Prometheus HTTP server
start_http_server(8000)  # Metrics available at http://localhost:8000/metrics
print("Prometheus metrics available at http://localhost:8000/metrics")
```

### 3.3 Query Prometheus Metrics

```bash
# Query total executions
curl http://localhost:8000/metrics | grep toolweaver_tool_executions_total

# Query average duration
curl http://localhost:8000/metrics | grep toolweaver_tool_duration_seconds
```

---

## Step 4: Set Up WandB Integration

### 4.1 Install WandB

```bash
pip install wandb

# Login to WandB
wandb login
```

### 4.2 Create WandB Logger

**File:** `monitoring/wandb_logger.py`

```python
import wandb
import time

class WandBLogger:
    def __init__(self, project: str = "toolweaver", entity: str = None):
        """Initialize WandB logging."""
        self.run = wandb.init(
            project=project,
            entity=entity,
            config={
                "orchestrator": "toolweaver",
                "version": "1.0"
            }
        )
    
    async def log_execution(self, tool_name: str, params: dict):
        """Log tool execution to WandB."""
        
        start_time = time.time()
        
        try:
            result = await orchestrator.execute_tool(tool_name, params)
            
            # Log metrics
            duration = time.time() - start_time
            wandb.log({
                f"{tool_name}/duration": duration,
                f"{tool_name}/cost": result.get("cost", 0.0),
                f"{tool_name}/tokens": result.get("tokens_used", 0),
                f"{tool_name}/status": "success",
                "step": wandb.run.step
            })
            
            return result
        
        except Exception as e:
            wandb.log({
                f"{tool_name}/status": "failure",
                f"{tool_name}/error": str(e)
            })
            raise
    
    def log_summary(self, metrics: dict):
        """Log summary statistics."""
        wandb.log({
            "summary/total_operations": metrics["total_operations"],
            "summary/success_rate": metrics["success_rate"],
            "summary/total_cost": metrics["total_cost_usd"],
            "summary/avg_duration": metrics["avg_duration_s"]
        })

# Usage
logger = WandBLogger(project="receipt-processing")

# Log executions
result = await logger.log_execution("gpt4_vision", {"image": "receipt.jpg"})

# Log summary
logger.log_summary(metrics.summary())

# Finish run
wandb.finish()
```

---

## Step 5: Track Costs Per Operation

### 5.1 Cost Attribution

```python
class CostTracker:
    def __init__(self):
        self.costs = {}  # {operation: cost}
        self.counts = {}  # {operation: count}
    
    def record(self, operation: str, cost: float):
        """Record cost for an operation."""
        self.costs[operation] = self.costs.get(operation, 0.0) + cost
        self.counts[operation] = self.counts.get(operation, 0) + 1
    
    def report(self):
        """Print cost breakdown."""
        print("\n=== Cost Report ===")
        print(f"Total cost: ${sum(self.costs.values()):.4f}\n")
        
        # Sort by cost (descending)
        sorted_ops = sorted(self.costs.items(), key=lambda x: x[1], reverse=True)
        
        for operation, cost in sorted_ops:
            count = self.counts[operation]
            avg = cost / count
            print(f"{operation}:")
            print(f"  Total: ${cost:.4f}")
            print(f"  Calls: {count}")
            print(f"  Avg: ${avg:.6f}")
    
    def most_expensive(self, n: int = 5):
        """Get N most expensive operations."""
        sorted_ops = sorted(self.costs.items(), key=lambda x: x[1], reverse=True)
        return sorted_ops[:n]

tracker = CostTracker()

# Track costs
async def execute_with_cost_tracking(tool_name: str, params: dict):
    result = await orchestrator.execute_tool(tool_name, params)
    tracker.record(tool_name, result.get("cost", 0.0))
    return result

# After processing
tracker.report()
print("\nTop 5 most expensive operations:")
for op, cost in tracker.most_expensive(5):
    print(f"  {op}: ${cost:.4f}")
```

---

## Step 6: Error Tracking

### 6.1 Track Error Rates

```python
from collections import defaultdict

class ErrorTracker:
    def __init__(self):
        self.errors = defaultdict(list)  # {tool_name: [errors]}
        self.total_calls = defaultdict(int)
    
    def record_call(self, tool_name: str, success: bool, error: str = ""):
        """Record a tool call."""
        self.total_calls[tool_name] += 1
        if not success:
            self.errors[tool_name].append({
                "error": error,
                "timestamp": time.time()
            })
    
    def error_rate(self, tool_name: str) -> float:
        """Get error rate for a tool."""
        total = self.total_calls[tool_name]
        errors = len(self.errors[tool_name])
        return errors / total if total > 0 else 0.0
    
    def report(self):
        """Print error report."""
        print("\n=== Error Report ===")
        for tool_name in self.total_calls:
            rate = self.error_rate(tool_name)
            print(f"{tool_name}:")
            print(f"  Total calls: {self.total_calls[tool_name]}")
            print(f"  Errors: {len(self.errors[tool_name])}")
            print(f"  Error rate: {rate:.1%}")

error_tracker = ErrorTracker()

async def execute_with_error_tracking(tool_name: str, params: dict):
    try:
        result = await orchestrator.execute_tool(tool_name, params)
        error_tracker.record_call(tool_name, success=True)
        return result
    except Exception as e:
        error_tracker.record_call(tool_name, success=False, error=str(e))
        raise

# After processing
error_tracker.report()
```

---

## Step 7: Real-World Example

Complete monitoring setup for receipt processing pipeline.

**File:** `pipeline/monitored_pipeline.py`

```python
from monitoring.metrics import MetricsCollector
from monitoring.prometheus_exporter import execute_with_prometheus
from monitoring.wandb_logger import WandBLogger
from monitoring.cost_tracker import CostTracker
from monitoring.error_tracker import ErrorTracker

class MonitoredReceiptPipeline:
    def __init__(self):
        self.metrics = MetricsCollector()
        self.cost_tracker = CostTracker()
        self.error_tracker = ErrorTracker()
        self.wandb_logger = WandBLogger(project="receipt-processing")
    
    async def process_receipt(self, receipt_id: str):
        """Process receipt with full monitoring."""
        
        # Step 1: OCR extraction
        try:
            text = await execute_with_prometheus(
                "gpt4_vision",
                {"receipt_id": receipt_id}
            )
            self.cost_tracker.record("ocr", 0.10)
            self.error_tracker.record_call("ocr", success=True)
        except Exception as e:
            self.error_tracker.record_call("ocr", success=False, error=str(e))
            raise
        
        # Step 2: Parse items
        try:
            items = await execute_with_prometheus(
                "parse_items",
                {"text": text}
            )
            self.cost_tracker.record("parse", 0.02)
            self.error_tracker.record_call("parse", success=True)
        except Exception as e:
            self.error_tracker.record_call("parse", success=False, error=str(e))
            raise
        
        # Step 3: Categorize
        try:
            categorized = await execute_with_prometheus(
                "categorize",
                {"items": items}
            )
            self.cost_tracker.record("categorize", 0.01)
            self.error_tracker.record_call("categorize", success=True)
        except Exception as e:
            self.error_tracker.record_call("categorize", success=False, error=str(e))
            raise
        
        return categorized
    
    async def process_batch(self, receipt_ids: list):
        """Process batch with monitoring."""
        
        results = []
        
        for receipt_id in receipt_ids:
            try:
                result = await self.process_receipt(receipt_id)
                results.append(result)
            except Exception as e:
                print(f"Receipt {receipt_id} failed: {e}")
                results.append({"error": str(e)})
        
        # Report metrics
        print(self.metrics.summary())
        self.cost_tracker.report()
        self.error_tracker.report()
        
        # Log to WandB
        self.wandb_logger.log_summary(self.metrics.summary())
        
        return results

# Usage
pipeline = MonitoredReceiptPipeline()
results = await pipeline.process_batch(receipt_ids)
```

---

## Verification

Test your monitoring setup:

```python
async def verify_monitoring():
    """Verify monitoring is working."""
    
    print("Testing monitoring setup...")
    
    # Test 1: Metrics collection
    metrics = MetricsCollector()
    metrics.record("test_op", duration=1.5, tokens=100, cost=0.05)
    summary = metrics.summary()
    assert summary["count"] == 1, "Metrics not recording"
    print("✓ Metrics collection working")
    
    # Test 2: Cost tracking
    tracker = CostTracker()
    tracker.record("test_tool", 0.10)
    tracker.record("test_tool", 0.15)
    assert tracker.costs["test_tool"] == 0.25, "Cost tracking not working"
    print("✓ Cost tracking working")
    
    # Test 3: Error tracking
    error_tracker = ErrorTracker()
    error_tracker.record_call("test_tool", success=True)
    error_tracker.record_call("test_tool", success=False, error="Test error")
    assert error_tracker.error_rate("test_tool") == 0.5, "Error tracking not working"
    print("✓ Error tracking working")
    
    print("\n✅ All checks passed!")

# Run verification
await verify_monitoring()
```

---

## Common Issues

### Issue 1: Prometheus Metrics Not Visible

**Symptom:** `/metrics` endpoint returns 404

**Solution:** Ensure HTTP server is started

```python
from prometheus_client import start_http_server

# Start server on port 8000
start_http_server(8000)
print("Metrics available at http://localhost:8000/metrics")
```

### Issue 2: WandB Not Logging

**Symptom:** No data in WandB dashboard

**Solution:** Check authentication and project name

```bash
# Re-authenticate
wandb login

# Verify project exists
wandb projects
```

### Issue 3: High Memory Usage

**Symptom:** Metrics collector using too much memory

**Solution:** Implement metrics rotation

```python
class RotatingMetricsCollector:
    def __init__(self, max_operations: int = 10000):
        self.operations = []
        self.max_operations = max_operations
    
    def record(self, **kwargs):
        self.operations.append(kwargs)
        
        # Rotate if exceeds max
        if len(self.operations) > self.max_operations:
            self.operations = self.operations[-self.max_operations:]
```

---

## Next Steps

- **Tutorial:** [Error Recovery](../tutorials/error-recovery.md) - Monitor error rates
- **Sample:** [06-monitoring-observability](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/06-monitoring-observability) - Complete example
- **Deep Dive:** [Analytics Guide](../reference/deep-dives/analytics-guide.md) - Advanced analytics

## Related Guides

- [Optimize Tool Costs](optimize-tool-costs.md) - Track and reduce costs
- [Implement Retry Logic](implement-retry-logic.md) - Monitor retry metrics
- [Configure A2A Agents](configure-a2a-agents.md) - Monitor agent performance
