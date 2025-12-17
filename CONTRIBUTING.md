# Contributing to ToolWeaver

Thank you for considering contributing to ToolWeaver! This document provides guidelines and instructions for contributing.

## \ud83d\udc4b Getting Started

### Prerequisites
- Python 3.8+
- Git
- Basic understanding of async Python
- Familiarity with AI/LLM concepts

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/ushakrishnan/ToolWeaver.git
   cd ToolWeaver
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   # source .venv/bin/activate     # Linux/Mac
   ```

3. **Install in Development Mode**
   ```bash
   pip install -e ".[dev]"         # With dev tools
   # pip install -e ".[all]"       # With all features
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (see docs/CONFIGURATION.md)
   ```

5. **Run Tests**
   ```bash
   pytest                          # All tests
   pytest -v                       # Verbose output
   pytest tests/test_tool_search.py # Specific test
   ```

## \ud83d\udcdd Code Structure

### Key Directories

```
orchestrator/
├── orchestrator.py              # Main orchestration engine
├── planner.py                   # LLM planning (GPT-4/Claude)
├── workers.py                   # MCP worker execution
├── small_model_worker.py        # Small model (Phi-3/Llama)
├── tool_search.py               # Hybrid tool search
├── tool_discovery.py            # Auto-discovery
├── workflow.py                  # Workflow engine
├── monitoring.py                # Monitoring system
└── functions.py                 # Function registry

examples/                        # Development examples (use local source)
samples/                         # User examples (use PyPI package)
tests/                           # Test suite
docs/                            # Documentation
```

### Import Conventions

**In examples/ (development):**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from orchestrator import execute_plan  # Local source
```

**In samples/ (users):**
```python
from orchestrator import execute_plan  # Installed package
```

## \ud83d\udd27 Contributing Guidelines

### 1. Choose What to Work On

- **Bug Fixes**: Check [Issues](https://github.com/ushakrishnan/ToolWeaver/issues)
- **Features**: Discuss in Issues first
- **Documentation**: Always welcome
- **Examples**: Add new examples to `examples/`

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 3. Make Your Changes

#### Code Quality
- Follow PEP 8 style guidelines
- Use type hints where possible
- Add docstrings to functions/classes
- Keep functions focused and small

#### Testing
- Add tests for new functionality
- Ensure all existing tests pass
- Aim for >80% code coverage

```bash
pytest                           # Run tests
pytest --cov=orchestrator       # Check coverage
```

#### Documentation
- Update relevant docs in appropriate `docs/` subdirectory:
  - `docs/user-guide/` - User-facing features
  - `docs/developer-guide/` - Architecture/implementation
  - `docs/deployment/` - Production setup
  - `docs/reference/` - Technical details
- Add docstrings to new functions
- Update README.md if adding major features
- Add example if introducing new capability

### 4. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "Add semantic search for tool discovery

- Implement hybrid BM25 + embedding search
- Add caching for embeddings (24h TTL)
- Reduce token usage by 90%
- Add tests for search accuracy"
```

**Commit Message Format:**
- First line: Brief summary (50 chars max)
- Blank line
- Detailed description with bullet points
- Reference issues: "Fixes #123" or "Relates to #456"

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title describing the change
- Description of what changed and why
- Reference to related issues
- Screenshots/examples if UI/output changes

## \ud83e\uddea Testing Guidelines

### Writing Tests

Place tests in `tests/` directory:

```python
# tests/test_your_feature.py
import pytest
from orchestrator.your_module import your_function

def test_your_feature():
    """Test that your feature works correctly."""
    result = your_function(input_data)
    assert result == expected_output

@pytest.mark.asyncio
async def test_async_feature():
    """Test async functionality."""
    result = await async_function()
    assert result.status == "success"
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_tool_search.py

# Specific test function
pytest tests/test_tool_search.py::test_hybrid_search

# With coverage
pytest --cov=orchestrator --cov-report=html

# Verbose output
pytest -v -s
```

## \ud83d\udcda Adding Examples

### For Development (examples/)

Add to `examples/` when demonstrating:
- New features requiring source code modifications
- Advanced usage patterns
- Integration testing
- Development workflows

### For Users (samples/)

Add to `samples/` when providing:
- Standalone usage examples
- Getting started tutorials
- Production use cases
- Best practices demonstrations

**Sample Template:**
```
samples/XX-feature-name/
├── script.py           # Main script
├── requirements.txt    # toolweaver==X.X.X + dependencies
├── README.md          # Usage instructions
└── .env.example       # Environment template
```

## \ud83d\udce6 Package Structure

### Adding Dependencies

**Core Dependencies** (pyproject.toml):
```toml
dependencies = [
    "pydantic>=2.0.0",
    "anyio>=4.0.0",
    # ... existing
]
```

**Optional Dependencies**:
```toml
[project.optional-dependencies]
monitoring = ["wandb>=0.16.0", "prometheus-client>=0.19.0"]
redis = ["redis>=5.0.0"]
your-feature = ["new-package>=1.0.0"]
```

### Version Bumping

Update version in `pyproject.toml`:
```toml
[project]
name = "toolweaver"
version = "0.1.4"  # Increment appropriately
```

## \ud83d\udea6 Code Review Process

### What Reviewers Look For

1. **Correctness**: Does it work as intended?
2. **Tests**: Are there adequate tests?
3. **Documentation**: Is it documented?
4. **Code Quality**: Is it clean and maintainable?
5. **Performance**: Does it introduce bottlenecks?
6. **Security**: Are there security concerns?

### Addressing Feedback

- Be responsive to review comments
- Ask questions if feedback is unclear
- Make requested changes promptly
- Push updates to the same branch

## \ud83c\udf93 Best Practices

### Async Programming
```python
# Good: Use async/await properly
async def process_items(items):
    results = await asyncio.gather(*[process_item(i) for i in items])
    return results

# Bad: Blocking in async function
async def process_items(items):
    return [process_item(i) for i in items]  # Not awaited!
```

### Error Handling
```python
# Good: Specific exceptions with context
try:
    result = await api_call()
except httpx.HTTPError as e:
    logger.error(f"API call failed: {e}")
    raise ToolExecutionError(f"Failed to call API: {e}") from e

# Bad: Catching everything silently
try:
    result = await api_call()
except:
    pass
```

### Type Hints
```python
# Good: Clear type hints
def process_plan(plan: Dict[str, Any]) -> ExecutionResult:
    ...

# Better: Use Pydantic models
def process_plan(plan: ExecutionPlan) -> ExecutionResult:
    ...
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)

# Good: Structured logging with context
logger.info("Processing plan", extra={
    "request_id": plan.request_id,
    "num_steps": len(plan.steps)
})

# Bad: Print statements
print("Processing plan...")
```

## \ud83d\udcac Communication

### Where to Ask Questions

- **GitHub Issues**: Bug reports, feature requests
- **Pull Request Comments**: Code-specific questions
- **Discussions**: General questions, ideas

### Be Respectful

- Follow the [Code of Conduct](CODE_OF_CONDUCT.md)
- Be patient with reviewers
- Provide context in questions
- Help others when you can

## \ud83c\udf89 Recognition

Contributors will be:
- Listed in release notes
- Acknowledged in documentation
- Added to CONTRIBUTORS.md

## \ud83d\udcdd Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update `docs/RELEASES.md`
3. Run full test suite
4. Build package: `python -m build`
5. Upload to PyPI: `twine upload dist/*`
6. Create Git tag: `git tag v0.1.4`
7. Push tag: `git push origin v0.1.4`
8. Create GitHub release

## \u2753 Questions?

If you have questions:
1. Check existing documentation in `docs/`
2. Search existing Issues
3. Create a new Issue with your question

Thank you for contributing to ToolWeaver! \ud83d\ude80
