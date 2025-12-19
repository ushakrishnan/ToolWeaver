# Contributing to ToolWeaver

ToolWeaver is **package-first**: most users should consume the PyPI package and extend via decorators or plugins, not fork the repo. This guide keeps contributors and plugin authors aligned.

## Who should do what?
- **Package users (default):** Install from PyPI, register tools via decorators (Phase 2) or plugins; do **not** fork/patch core.
- **Plugin authors:** Publish separate packages; register via the plugin registry.
- **Core contributors:** Open PRs to improve the public API, templates, docs, and tests.

## Quick setup (core contributors)
1) Python 3.10+ and Git installed.
2) Clone:
```bash
git clone https://github.com/ushakrishnan/ToolWeaver.git
cd ToolWeaver
```
3) Create venv and install dev extras:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -e "./[dev]"
```
4) Run tests fast:
```bash
pytest --maxfail=1 --disable-warnings
```

## Expectations
- **Public vs internal:** Import only from `orchestrator` (public). Anything in `orchestrator._internal` can change without notice.
- **Type hints required:** New/modified code must be type hinted; mypy config lives in pyproject.
- **Logging:** Use the built-in logger from `orchestrator._internal.logger` (no extra deps).
- **Optional deps:** Guard optional features with the error helpers in `orchestrator._internal.errors`.
- **Docs & tests:** Every new public surface ships with docs and tests. Target 80%+ coverage.

## Workflow
1) **Discuss**: For large changes, open an Issue/Discussion first.
2) **Branch**: `git checkout -b feature/short-name`.
3) **Code**: Keep changes small and focused. Use type hints, add docstrings, and prefer `_internal` for implementation details.
4) **Test**: `pytest` (unit), add integration tests where relevant.
5) **Lint/Typecheck**: `ruff` and `mypy` per pyproject settings.
6) **Docs**: Update the relevant doc set:
    - `docs/for-package-users/` for user-facing guides
    - `docs/for-contributors/` for dev/architecture
7) **Commit**: Conventional, clear messages; include a brief bullet list of changes.
8) **PR**: Describe scope, risks, tests run, and any optional dependencies.

## Style & quality
- Formatting: black; Imports: isort/ruff; Lint: ruff per config.
- Types: mypy (strict overrides for config/_internal/plugins per pyproject).
- Logging: use `get_logger(__name__)`; avoid print.
- Security: validate and sanitize inputs using `_internal.validation` helpers.

## Tests
- Unit tests under `tests/` mirroring module paths.
- Mark slow/integration with `@pytest.mark.slow` or `@pytest.mark.integration`.
- Aim for <2 minute local run for unit/fast tests.

## Plugin authors
- Create a separate package and use the plugin registry:
```python
from orchestrator.plugins import register_plugin
from my_package.tools import MyPlugin

register_plugin("my-tools", MyPlugin())
```
- Declare entry points (optional) so plugins can auto-discover:
```toml
[project.entry-points."toolweaver.plugins"]
my_tools = "my_package.tools:MyPlugin"
```
- Keep optional deps out of core; document your extras.

## Security
- Never trust input from models or users; use validation and sanitization helpers.
- Avoid adding new optional deps to core installs; gate them with extras and runtime checks.

## Release notes
- Add a changelog entry under `.changelog/` (template provided) for user-facing changes.

## Getting help
- Issues for bugs, Discussions for ideas; include repro steps and environment details.

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
