# Example 08: Hybrid Model Routing

**Capability Demonstrated:** Two-model architecture (GPT-4 planner + Phi-3 worker) for cost optimization

## What This Shows

- Large model (GPT-4) for planning and complex reasoning
- Small model (Phi-3) for execution tasks (parsing, classification)
- Automatic routing based on task complexity
- 80-90% cost reduction compared to large-model-only approach

## Architecture

```
User Query → GPT-4 (Planner) → Execution Plan
              $0.03/request         ↓
                           ┌────────┴────────┐
                           ↓                 ↓
                      Phi-3 Worker    Phi-3 Worker
                     $0.0001/call    $0.0001/call
```

## Cost Comparison

**Large Model Only (GPT-4 for everything):**
- 100 tasks × $0.03 = $3.00

**Hybrid (GPT-4 planner + Phi-3 workers):**
- 1 plan × $0.03 = $0.03
- 100 tasks × $0.0001 = $0.01
- Total: $0.04 (98.7% savings!)

## Setup

```bash
cp .env.example .env
python hybrid_routing_demo.py
```

## Files

- `hybrid_routing_demo.py` - Main demonstration
- `.env` / `.env.example` - Configuration
- `README.md` - This file