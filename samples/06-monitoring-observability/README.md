# Sample 06: Monitoring and Observability

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`


**Complexity:** ⭐⭐ Intermediate | **Time:** 10 minutes  
**Feature Demonstrated:** Production-grade monitoring with WandB and Prometheus

## Overview

### What This Example Does
Integrates WandB and Prometheus for real-time monitoring, cost tracking, and performance profiling.

### Key Features Showcased
- **WandB Integration**: ML operations tracking with dashboards
- **Prometheus Metrics**: Production monitoring with /metrics endpoint
- **Cost Tracking**: Per-operation cost attribution and analysis
- **Error Tracking**: Debug failures with detailed logging

### Why This Matters

This example demonstrates ToolWeaver's observability capabilities:
- Real-time metrics tracking with WandB
- Performance monitoring with Prometheus
- Cost tracking per operation
- Tool usage analytics
- Error tracking and debugging
- Custom metrics and dashboards

## Real-World Use Case

In production AI systems, you need to monitor:
- **Costs**: Which operations are expensive?
- **Performance**: Where are the bottlenecks?
- **Reliability**: What's the error rate?
- **Usage**: Which tools are used most?
- **Quality**: Are results accurate?

**Solution:** Integrated monitoring provides visibility without changing your code.

## How It Works

1. **Metrics Collection**: Automatic tracking of operations
2. **Cost Attribution**: Track spend per tool/workflow
3. **Performance Profiling**: Identify slow operations
4. **Error Tracking**: Log and analyze failures
5. **Dashboards**: Visualize metrics in WandB or Prometheus

## Architecture

```
Your Code
    ↓
Orchestrator (instrumented)
    ↓
┌───────────────┬─────────────────┐
↓               ↓                 ↓
WandB      Prometheus        Custom Logger
(ML ops)    (metrics)         (debugging)
```

## Metrics Tracked

### Performance Metrics
- Total execution time
- Per-tool latency
- Parallel efficiency
- Cache hit rate

### Cost Metrics
- Token usage per request
- API costs per operation
- Model costs (GPT-4 vs Phi-3)
- Total monthly spend

### Reliability Metrics
- Success/failure rate
- Error types and frequency
- Retry attempts
- Timeout incidents

### Usage Metrics
- Tool popularity
- Workflow patterns
- Peak usage times
- User distribution

## Files

- `monitoring_demo.py` - Main example script
- `.env` - Your API keys (don't commit!)
- `.env.example` - Template for setup
- `README.md` - This file

## Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your API keys to `.env`:
   ```
   AZURE_OPENAI_ENDPOINT=your_endpoint_here
   AZURE_OPENAI_KEY=your_key_here
   WANDB_API_KEY=your_wandb_key  # Get from wandb.ai
   ```

3. Install dependencies (from project root):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python monitoring_demo.py
```

### Example Output

```
=== Monitoring & Observability Example ===

Initializing monitoring backends...
✓ WandB initialized (project: toolweaver-demo)
✓ Prometheus initialized (port: 8000)

Running monitored operations...

Operation 1: Receipt Processing
  - Duration: 1.2s
  - Tokens: 3,450
  - Cost: $0.052
  - Tools used: 5
  - Status: success
  ✓ Logged to WandB

Operation 2: Batch Processing (10 receipts)
  - Duration: 4.8s
  - Tokens: 28,900
  - Cost: $0.434
  - Cache hits: 7/10 (70%)
  - Status: success
  ✓ Logged to WandB

Operation 3: Error Simulation
  - Duration: 0.8s
  - Error: API timeout
  - Retry attempts: 2
  - Final status: failure
  ✓ Error logged to WandB

Dashboard URLs:
- WandB: https://wandb.ai/your-team/toolweaver-demo/runs/xyz123
- Prometheus: http://localhost:8000/metrics
- Grafana: http://localhost:3000 (if configured)

Summary Statistics:
  Total requests: 12
  Success rate: 91.7% (11/12)
  Average latency: 1.6s
  Total tokens: 35,890
  Total cost: $0.538
  Cache hit rate: 70%
  
  Most used tools:
    1. receipt_ocr: 10 calls
    2. parse_items: 10 calls
    3. categorize: 8 calls
```

## Key Concepts

### 1. WandB Integration

```python
from orchestrator.monitoring import WandBMonitor

monitor = WandBMonitor(
    project="my-project",
    entity="my-team",
    config={"model": "gpt-4o"}
)

# Automatic tracking

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

with monitor.track_operation("process_receipt"):
    result = await orchestrator.execute(task)
    
# Manual logging

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

monitor.log_metrics({
    "cost": 0.052,
    "tokens": 3450,
    "latency": 1.2
})
```

### 2. Prometheus Metrics

```python
from orchestrator.monitoring import PrometheusMonitor

monitor = PrometheusMonitor(port=8000)

# Metrics automatically exposed at /metrics

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

# - request_duration_seconds (histogram)

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

# - request_total (counter)

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

# - token_usage_total (counter)

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

# - cost_dollars_total (counter)

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

# - tool_usage_total (counter by tool name)

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

```

### 3. Custom Monitoring

```python
from orchestrator.monitoring_backends import MonitoringBackend

class CustomMonitor(MonitoringBackend):
    def log_operation(self, operation, metrics):
        # Send to your logging service
        pass
    
    def log_error(self, error, context):
        # Send to error tracking
        pass
```

### 4. Multi-Backend Monitoring

```python
from orchestrator.monitoring import CompositeMonitor

monitor = CompositeMonitor(
    backends=[
        WandBMonitor(project="prod"),
        PrometheusMonitor(port=8000),
        CloudWatchMonitor(region="us-east-1"),
        CustomMonitor()
    ]
)

# All backends receive metrics simultaneously

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

```

## Benefits

**Cost Optimization**
- Identify expensive operations
- Track budget in real-time
- Optimize model selection

**Performance Tuning**
- Find bottlenecks
- Optimize caching
- Tune parallelization

**Reliability**
- Monitor error rates
- Track SLA compliance
- Set up alerts

**Business Intelligence**
- Understand usage patterns
- Capacity planning
- Feature adoption

## Configuration Options

```python
# WandB Configuration

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

WandBMonitor(
    project="my-project",           # Project name
    entity="my-team",                # Team/organization
    tags=["production", "v2"],      # Tags for filtering
    config={"model": "gpt-4"},      # Run configuration
    log_frequency=1                  # Log every N operations
)

# Prometheus Configuration

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

PrometheusMonitor(
    port=8000,                       # Metrics server port
    namespace="toolweaver",          # Metrics namespace
    buckets=[0.1, 0.5, 1, 2, 5],   # Histogram buckets
    enable_push_gateway=False        # Use push gateway
)
```

## Dashboard Examples

### WandB Dashboard
- Real-time cost tracking
- Latency percentiles (P50, P95, P99)
- Tool usage heatmap
- Error rate timeline
- Model comparison charts

### Prometheus/Grafana Dashboard
- Request rate (req/sec)
- Error rate (errors/sec)
- Latency distribution
- Resource utilization
- Cache effectiveness

## Advanced Features

The example demonstrates:
- Multi-backend monitoring
- Custom metrics
- Error tracking
- Cost attribution
- Performance profiling
- Dashboard setup

## Related Examples

- **Sample 01-03**: All can be monitored
- **Sample 07**: Cache monitoring
- **Sample 08**: Model cost comparison

## Learn More

- [Monitoring Documentation](../../docs/FEATURES_GUIDE.md#monitoring)
- [WandB Integration Guide](../../docs/README.md)
- [Production Deployment](../../docs/PRODUCTION_DEPLOYMENT.md)
