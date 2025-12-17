# Sample 08: Hybrid Model Routing

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`


**Complexity:** ⭐⭐⭐ Advanced | **Time:** 15 minutes  
**Feature Demonstrated:** Two-model architecture (GPT-4 planner + Phi-3 workers)

## Overview

### What This Example Does
Uses GPT-4 for planning and Phi-3 for execution, achieving 80-90% cost reduction.

### Key Features Showcased
- **Hybrid Architecture**: Large model for planning, small models for execution
- **Intelligent Routing**: Automatic task complexity detection
- **Cost Optimization**: 98.7% savings at scale (100+ tasks)
- **Performance**: Parallel execution with local small models

### Why This Matters

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