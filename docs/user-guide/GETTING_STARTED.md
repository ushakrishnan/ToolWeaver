# Getting Started with ToolWeaver

Welcome! This guide will help you get started with ToolWeaver, whether you're a new user or a developer.

## \ud83d\udd0d Choose Your Path

### \ud83d\udc64 I Want to Use ToolWeaver (User Path)
**Goal:** Use ToolWeaver in your projects  
**Time:** 10 minutes  
**\u2192 Follow:** [User Quick Start](#user-quick-start)

### \ud83d\udc68\u200d\ud83d\udcbb I Want to Contribute (Developer Path)
**Goal:** Modify ToolWeaver or contribute features  
**Time:** 20 minutes  
**\u2192 Follow:** [Developer Quick Start](#developer-quick-start)

---

## \ud83d\udc64 User Quick Start

### Step 1: Install ToolWeaver

```bash
pip install toolweaver
```

**With optional features:**
```bash
pip install toolweaver[monitoring]  # W&B monitoring
pip install toolweaver[redis]       # Redis caching
pip install toolweaver[vector]      # Vector search
pip install toolweaver[all]         # Everything
```

### Step 2: Try Your First Sample

```bash
# Download a sample (or browse on GitHub)
# https://github.com/ushakrishnan/ToolWeaver/tree/main/samples

# Navigate to sample directory
cd samples/01-basic-receipt-processing

# Install dependencies
pip install -r requirements.txt

# Configure (optional for testing)
cp .env.example .env
# Edit .env with your API keys if you have them

# Run!
python process_receipt.py
```

### Step 3: Use in Your Project

Create a new file `my_project.py`:

```python
import asyncio
from orchestrator.orchestrator import execute_plan

# Define your execution plan
plan = {
    "request_id": "my-first-plan",
    "steps": [
        {
            "id": "step1",
            "tool": "your_tool_name",
            "input": {"param": "value"}
        }
    ]
}

async def main():
    # Execute the plan
    result = await execute_plan(plan)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python my_project.py
```

### Step 4: Explore Samples

Browse all samples:
- [samples/README.md](../samples/README.md) - Full list with descriptions

**Recommended Learning Path:**
1. **Sample 01**: Basic Receipt Processing - Simplest example
2. **Sample 02**: Receipt with Categorization - Multi-step workflow
3. **Sample 04**: Tool Discovery - Automatic tool finding
4. **Sample 13**: Complete Pipeline - Everything together

### Step 5: Read Documentation

- [FEATURES_GUIDE.md](FEATURES_GUIDE.md) - All features explained
- [CONFIGURATION.md](CONFIGURATION.md) - Setup API providers
- [WORKFLOW_USAGE_GUIDE.md](WORKFLOW_USAGE_GUIDE.md) - Build workflows
- [../developer-guide/ARCHITECTURE.md](../developer-guide/ARCHITECTURE.md) - How it works

---

## \ud83d\udc68\u200d\ud83d\udcbb Developer Quick Start

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/ushakrishnan/ToolWeaver.git
cd ToolWeaver

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
# source .venv/bin/activate

# Install in editable mode
pip install -e .

# Or with all features
pip install -e ".[all]"
```

### Step 2: Configure Environment

```bash
# Copy example environment
cp .env.example .env

# Edit .env with your credentials
# Minimum required for testing:
#   PLANNER_PROVIDER=openai
#   OPENAI_API_KEY=sk-...
```

See [CONFIGURATION.md](CONFIGURATION.md) for detailed setup.

### Step 3: Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_tool_search.py
```

### Step 4: Try Examples

```bash
# Navigate to an example
cd examples/01-basic-receipt-processing

# Run it
python process_receipt.py
```

**Browse all examples:**
- [examples/README.md](../examples/README.md)

### Step 5: Make Changes

1. **Create a branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes** in:
   - `orchestrator/` - Core code
   - `examples/` - New examples
   - `tests/` - Tests for your changes

3. **Run tests:**
   ```bash
   pytest
   ```

4. **Commit and push:**
   ```bash
   git add .
   git commit -m "Add my feature"
   git push origin feature/my-feature
   ```

5. **Create Pull Request** on GitHub

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

---

## \ud83d\udcc1 Project Structure Overview

```
ToolWeaver/
├── orchestrator/           # Core package
│   ├── orchestrator.py    # Main engine
│   ├── planner.py         # LLM planning
│   ├── tool_search.py     # Tool discovery
│   └── ...
│
├── samples/               # \ud83d\udc64 For Users
│   ├── 01-basic-receipt-processing/
│   ├── 02-receipt-with-categorization/
│   └── ...
│   ├── README.md          # Samples overview
│   └── TEST_RESULTS.md    # Test report
│
├── examples/              # \ud83d\udc68\u200d\ud83d\udcbb For Developers
│   ├── 01-basic-receipt-processing/
│   ├── 02-receipt-with-categorization/
│   └── ...
│   ├── README.md          # Examples overview
│   └── TESTING_REPORT.md  # Test report
│
├── tests/                 # Test suite
│   ├── test_tool_search.py
│   ├── test_workflow.py
│   └── ...
│
├── docs/                  # Documentation
│   ├── GETTING_STARTED.md # This file
│   ├── CONFIGURATION.md   # Setup guide
│   ├── FEATURES_GUIDE.md  # All features
│   └── ...
│
├── README.md              # Main documentation
├── CONTRIBUTING.md        # Contribution guide
├── pyproject.toml         # Package config
└── requirements.txt       # Dependencies
```

## \ud83e\udd14 Samples vs Examples

| Aspect | **samples/** | **examples/** |
|--------|------------|-------------|
| **For** | End Users | Developers |
| **Install** | `pip install toolweaver` | `pip install -e .` |
| **Source** | PyPI package | Local source code |
| **Modify** | No (reference only) | Yes (edit directly) |
| **Import** | `from orchestrator import ...` | Same, but from local |

**When to use samples/:**
- Learning how to use ToolWeaver
- Building applications with ToolWeaver
- Reference implementations

**When to use examples/:**
- Contributing to ToolWeaver
- Testing new features
- Debugging issues

## \u2699\ufe0f Configuration Options

### Minimal Configuration (.env)

```bash
# Large Model for Planning (required)
PLANNER_PROVIDER=openai
OPENAI_API_KEY=sk-...

# That's it for basic usage!
```

### Full Configuration

```bash
# === Planning Model (Large) ===
PLANNER_PROVIDER=azure-openai
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_USE_AD=true  # Use Azure AD instead of API key

# === Small Models (Optional) ===
USE_SMALL_MODEL=true
SMALL_MODEL_BACKEND=ollama
WORKER_MODEL=phi3

# === Monitoring (Optional) ===
MONITORING_BACKENDS=local,wandb
WANDB_PROJECT=toolweaver
WANDB_ENTITY=your-username

# === Caching (Optional) ===
REDIS_URL=redis://localhost:6379

# === Vector Search (Optional) ===
QDRANT_URL=http://localhost:6333
```

See [CONFIGURATION.md](CONFIGURATION.md) for all options.

## \ud83d\ude80 Next Steps

### For Users
1. \u2705 Completed Quick Start
2. \ud83d\udcd6 Read [FEATURES_GUIDE.md](FEATURES_GUIDE.md)
3. \ud83d\udcda Browse more [samples](../samples/)
4. \ud83d\udee0\ufe0f Build your first project
5. \ud83d\udcac Ask questions in [Issues](https://github.com/ushakrishnan/ToolWeaver/issues)

### For Developers
1. \u2705 Completed Quick Start
2. \ud83d\udcd6 Read [ARCHITECTURE.md](ARCHITECTURE.md)
3. \ud83e\uddea Run all tests: `pytest`
4. \ud83d\udd0d Explore [examples](../examples/)
5. \ud83d\udcdd Read [CONTRIBUTING.md](../CONTRIBUTING.md)
6. \ud83d\ude80 Start contributing!

## \ud83c\udfaf Common Use Cases

### 1. Receipt Processing
```python
# Extract text, parse items, categorize expenses
# See: samples/02-receipt-with-categorization/
```

### 2. GitHub Automation
```python
# List files, create issues, search code
# See: samples/03-github-operations/
```

### 3. Multi-Step Workflows
```python
# Chain multiple tools with dependencies
# See: samples/05-workflow-library/
```

### 4. Cost Optimization
```python
# Use small models for execution (80-90% savings)
# See: samples/08-hybrid-model-routing/
```

### 5. Production Monitoring
```python
# Track performance, costs, and usage
# See: samples/06-monitoring-observability/
```

## \u2753 Troubleshooting

### ImportError: No module named 'orchestrator'

**Problem:** ToolWeaver not installed

**Solution:**
```bash
# For users:
pip install toolweaver

# For developers:
pip install -e .
```

### API Key Errors

**Problem:** Missing or invalid API keys

**Solution:**
1. Check `.env` file exists
2. Verify keys are correct
3. Ensure provider matches key type
   ```bash
   # OpenAI
   PLANNER_PROVIDER=openai
   OPENAI_API_KEY=sk-...
   
   # Azure
   PLANNER_PROVIDER=azure-openai
   AZURE_OPENAI_ENDPOINT=https://...
   ```

### Tests Failing

**Problem:** Tests fail after setup

**Solution:**
```bash
# Reinstall dependencies
pip install -e ".[dev]"

# Run specific test to see error
pytest -v tests/test_tool_search.py
```

### Still Stuck?

1. Check [Issues](https://github.com/ushakrishnan/ToolWeaver/issues) for similar problems
2. Read relevant documentation in `docs/`
3. Create a new Issue with:
   - What you're trying to do
   - What you expected
   - What actually happened
   - Error messages
   - Your environment (OS, Python version)

## \ud83d\udcda Additional Resources

- **Main README**: [README.md](../README.md)
- **Features**: [FEATURES_GUIDE.md](FEATURES_GUIDE.md)
- **Configuration**: [CONFIGURATION.md](CONFIGURATION.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Contributing**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **PyPI Package**: https://pypi.org/project/toolweaver/
- **GitHub Repository**: https://github.com/ushakrishnan/ToolWeaver

---

**Ready to start?** Head to [samples/](../samples/) or [examples/](../examples/) depending on your path!

Welcome to the ToolWeaver community! \ud83c\udf89
