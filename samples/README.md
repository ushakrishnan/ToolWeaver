# ToolWeaver Samples

**Standalone samples using ToolWeaver from PyPI.**

> Current status: PyPI package refresh is in progress. The samples here may lag behind the latest source. For the most up-to-date code paths, use [examples/](../examples/) until the refreshed package is published. Samples will be regenerated after the refresh.

These samples demonstrate how to use ToolWeaver in your own projects after installing it via `pip install toolweaver`.

## Difference from Examples

- **[examples/](../examples/)** - Development examples that use the local source code (canonical while PyPI refresh is pending)
- **[samples/](.)** - Production samples that use the PyPI package (will be refreshed after the package update)

## Coverage Status

- Not yet mirrored: [examples/03-github-operations/](../examples/03-github-operations/)
- Not yet mirrored: [examples/15-control-flow/](../examples/15-control-flow/)
- Legacy demos live only in [examples/legacy-demos/](../examples/legacy-demos/)
- [14-programmatic-execution](14-programmatic-execution/) is a placeholder; see [examples/14-programmatic-execution/](../examples/14-programmatic-execution/)

## Installation

```bash
pip install toolweaver[all]
```

Or for individual samples, install from the sample's `requirements.txt`:

```bash
cd samples/01-basic-receipt-processing
pip install -r requirements.txt
python process_receipt.py
```

## Available Samples

### Getting Started

- **[01-basic-receipt-processing](01-basic-receipt-processing/)** - Basic tool execution
- **[02-receipt-with-categorization](02-receipt-with-categorization/)** - Multi-step workflows  
- **[13-complete-pipeline](13-complete-pipeline/)** - Complete feature showcase

### Advanced Features

- **[04-vector-search-discovery](04-vector-search-discovery/)** - Tool discovery
- **[05-workflow-library](05-workflow-library/)** - Reusable workflows
- **[06-monitoring-observability](06-monitoring-observability/)** - WandB monitoring
- **[07-caching-optimization](07-caching-optimization/)** - Redis caching
- **[08-hybrid-model-routing](08-hybrid-model-routing/)** - Two-model architecture
- **[09-code-execution](09-code-execution/)** - Sandboxed execution
- **[10-multi-step-planning](10-multi-step-planning/)** - LLM-generated plans
- **[11-programmatic-executor](11-programmatic-executor/)** - Batch processing
- **[12-sharded-catalog](12-sharded-catalog/)** - Scale to 1000+ tools

## Usage Pattern

All samples follow this structure:

```
sample-name/
├── README.md              # Documentation
├── requirements.txt       # Dependencies (includes toolweaver)
├── main_script.py         # The sample code
├── .env.example          # Environment template
└── .env                  # Your credentials (gitignored)
```

## Quick Test

```bash
# Install ToolWeaver
pip install toolweaver

# Try the complete demo
cd samples/13-complete-pipeline
pip install -r requirements.txt
python complete_pipeline.py
```

## Configuration

Each sample includes `.env.example`. Copy to `.env` and add your credentials:

```bash
cp .env.example .env
# Edit .env with your API keys
```

## Support

- **Documentation:** [../docs/](../docs/)
- **Issues:** https://github.com/ushakrishnan/ToolWeaver/issues
- **PyPI:** https://pypi.org/project/toolweaver/
