# ToolWeaver Examples

This directory contains example scripts demonstrating ToolWeaver functionality.

## Quick Start Examples

### Basic Usage
- **usage_examples.py** - Simple examples of tool registration and execution

### Discovery & Search
- **test_discovery.py** - Tool discovery validation (discovers 14 tools)
- **test_search.py** - Semantic search demo (6 queries with relevance scores)
- **demo_auto_discover.py** - Phase 2 automatic discovery integration

### Advanced Features
- **demo_integrated.py** - Full pipeline: discovery → search → planning (30 tools)
- **demo_tool_examples.py** - Tool usage examples showing 72% → 90%+ accuracy improvement

### Testing Connection
- **test_azure_connection.py** - Verify Azure OpenAI connection and credentials

## Running Examples

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Run any example
python examples/demo_integrated.py
python examples/test_discovery.py
python examples/demo_tool_examples.py
```

## What Each Example Demonstrates

| Example | Features | Output |
|---------|----------|--------|
| **usage_examples.py** | Basic tool registration, function decorators | Tool catalog operations |
| **test_discovery.py** | Automatic tool discovery, caching | 14 tools discovered in 1ms |
| **test_search.py** | Semantic search, relevance scoring | Top 10 tools for 6 queries |
| **demo_auto_discover.py** | Full discovery orchestration | Complete tool catalog |
| **demo_integrated.py** | Discovery + search + planning | 3-step receipt processing |
| **demo_tool_examples.py** | Tool examples, parameter accuracy | Cost-benefit analysis |
| **test_azure_connection.py** | Azure AD authentication | Connection validation |

## Requirements

All examples require:
- Python 3.11+
- Virtual environment activated
- Environment variables configured (see `.env.example`)
- Azure OpenAI credentials (for planning examples)

Optional for semantic search examples:
- sentence-transformers
- rank-bm25
- torch
- scikit-learn

See main [requirements.txt](../requirements.txt) for complete dependencies.
