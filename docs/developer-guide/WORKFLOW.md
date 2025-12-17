# Developer Workflow Guide

Best practices for working on ToolWeaver development.

## Setup: Always Use .venv

**Rule**: Always work in the virtual environment (`.venv`)

### Initial Setup

```powershell
# Create virtual environment (first time only)
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
python scripts/verify_install.py
```

### Daily Workflow

```powershell
# Start each session by activating venv
cd c:\Usha\UKRepos\ToolWeaver
.\.venv\Scripts\Activate.ps1

# Now you're ready to work
```

**Tip**: Your prompt will show `(.venv)` when activated.

---

## Dependency Management Workflow

### When Adding New Functionality

If you add code that imports new packages:

1. **Install the package in .venv**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   pip install <package-name>
   ```

2. **Update pyproject.toml immediately**
   ```powershell
   # Option A: Manual
   # Edit pyproject.toml and add to [project.dependencies]
   
   # Option B: Automated discovery
   python scripts/update_dependencies.py
   # Review the output and copy suggestions to pyproject.toml
   ```

3. **Update requirements.txt** (for backwards compatibility)
   - Add the same dependency to `requirements.txt`
   - Keep both files in sync

4. **Test the installation**
   ```powershell
   # Verify everything imports correctly
   python scripts/verify_install.py
   
   # Run tests to ensure nothing broke
   pytest tests/ -q
   ```

5. **Commit both config files**
   ```powershell
   git add pyproject.toml requirements.txt
   git commit -m "Add <package-name> dependency for <feature>"
   ```

### Recommended Workflow (Prevents Missing Dependencies)

**Best Practice**: Discover all dependencies automatically, then update configs

```powershell
# 1. Activate venv
.\.venv\Scripts\Activate.ps1

# 2. Install your new package(s) as you code
pip install <new-package>

# 3. After coding, scan for all imports
python scripts/update_dependencies.py

# 4. Review the output - it shows:
#    - What's imported
#    - What's installed 
#    - What versions
#    - Suggested pyproject.toml format

# 5. Copy suggestions to pyproject.toml and requirements.txt

# 6. Reinstall to verify config is correct
pip install -e ".[dev]"

# 7. Verify imports work
python scripts/verify_install.py

# 8. Run tests with coverage
pytest tests/ --cov=orchestrator --cov-report=term

# 9. Commit if all green
git add pyproject.toml requirements.txt
git commit -m "Update dependencies after adding <feature>"
```

---

## Testing Workflow

### Run Tests with Coverage

```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Run all tests with coverage
pytest tests/ --cov=orchestrator --cov-report=term-missing --cov-report=html

# Open coverage report
start htmlcov/index.html
```

### Common Test Commands

```powershell
# Quick test (no coverage)
pytest tests/ -q

# Test specific file
pytest tests/test_tool_search.py -v

# Test specific function
pytest tests/test_workflow.py::test_workflow_execution -v

# Skip slow tests (if marked)
pytest tests/ -m "not slow"

# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x
```

### Ignore Specific Tests

Some tests require optional dependencies or external services:

```powershell
# Skip GPU tests (requires torch)
pytest tests/ --ignore=tests/test_gpu_optimization.py

# Skip all examples/scripts (not core tests)
pytest tests/ --ignore=examples/ --ignore=scripts/
```

---

## Pre-Commit Checklist

Before committing code:

- [ ] Code is in `.venv`
- [ ] New dependencies added to `pyproject.toml`
- [ ] New dependencies added to `requirements.txt`
- [ ] `python scripts/verify_install.py` passes
- [ ] `pytest tests/ -q` passes (or document known failures)
- [ ] Coverage report reviewed (aim for >80%)
- [ ] Code formatted with `black orchestrator/ tests/`
- [ ] Linted with `ruff check orchestrator/ tests/`

### Quick Pre-Commit Commands

```powershell
.\.venv\Scripts\Activate.ps1

# Format code
black orchestrator/ tests/

# Lint
ruff check orchestrator/ tests/ --fix

# Verify dependencies
python scripts/verify_install.py

# Run tests
pytest tests/ --cov=orchestrator -q

# If all pass, commit!
```

---

## Publishing Workflow

Before publishing to PyPI:

```powershell
# 1. Ensure all dependencies are documented
python scripts/update_dependencies.py

# 2. Update version in pyproject.toml
# Edit: version = "0.1.4" (or appropriate version)

# 3. Run full test suite
pytest tests/ --cov=orchestrator --cov-report=term

# 4. Build package
pip install build
python -m build

# 5. Test installation locally
pip install dist/toolweaver-0.1.4-py3-none-any.whl

# 6. Upload to PyPI
pip install twine
twine upload dist/*

# 7. Tag release
git tag v0.1.4
git push origin v0.1.4
```

See [PUBLISHING.md](../docs/developer-guide/PUBLISHING.md) for detailed publishing instructions.

---

## Common Issues

### "ModuleNotFoundError: No module named 'X'"

**Solution**: 
```powershell
# Install the missing package
pip install <package-name>

# Then update config files
# Add to pyproject.toml [project.dependencies]
# Add to requirements.txt
```

### "pytest not found"

**Solution**: You're not in `.venv`
```powershell
.\.venv\Scripts\Activate.ps1
```

### "Import errors in tests/"

**Solution**: Install package in editable mode
```powershell
pip install -e ".[dev]"
```

### "Coverage report shows 0%"

**Solution**: Make sure you're testing the installed package
```powershell
# Reinstall in editable mode
pip install -e .

# Run tests with full path to orchestrator
pytest tests/ --cov=orchestrator
```

---

## Tips

1. **Always work in .venv** - Never install packages globally
2. **Update configs immediately** - Don't wait until later
3. **Use verify_install.py** - Catch missing deps early
4. **Run tests frequently** - Don't accumulate failures
5. **Check coverage** - Aim for >80% on new code
6. **Keep pyproject.toml and requirements.txt in sync** - Both should have same deps
7. **Use update_dependencies.py** - Automate discovery instead of manual tracking

---

## Quick Reference

```powershell
# Daily startup
.\.venv\Scripts\Activate.ps1

# Add new dependency
pip install <package>
# → Edit pyproject.toml + requirements.txt
python scripts/verify_install.py

# Before commit
black orchestrator/ tests/
ruff check orchestrator/ tests/ --fix
pytest tests/ -q

# Discover dependencies
python scripts/update_dependencies.py

# Test coverage
pytest tests/ --cov=orchestrator --cov-report=html
```
