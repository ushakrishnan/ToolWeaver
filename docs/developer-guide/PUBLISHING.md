# Publishing ToolWeaver to PyPI

This guide shows how to package and publish ToolWeaver so users can install it with:
```bash
pip install toolweaver
```

## Prerequisites

### 1. Update pyproject.toml

First, let's update the version and author email:

```toml
[project]
name = "toolweaver"
version = "0.1.3"  # Match your release version
authors = [
    { name = "Usha Krishnan", email = "ushapriya.krishnan@gmail.com" }
]
```

### 2. Create PyPI Account

1. Go to https://pypi.org/ and create an account
2. Verify your email
3. (Optional) Go to https://test.pypi.org/ for testing first

### 3. Generate API Token

1. Log in to PyPI
2. Go to Account Settings → API tokens
3. Click "Add API token"
4. Name it "toolweaver-upload"
5. Scope: "Entire account" (or specific to toolweaver project later)
6. **Save the token** - you'll only see it once!

## Installation Steps

### Step 1: Install Build Tools

```bash
# Activate your venv
.\.venv\Scripts\Activate.ps1

# Install build tools
pip install --upgrade build twine
```

### Step 2: Build the Package

```bash
# Clean previous builds
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# Build distribution packages
python -m build
```

This creates:
- `dist/toolweaver-0.1.3-py3-none-any.whl` (wheel - faster install)
- `dist/toolweaver-0.1.3.tar.gz` (source distribution)

### Step 3: Test the Package Locally

```bash
# Install from local wheel
pip install dist/toolweaver-0.1.3-py3-none-any.whl

# Test import
python -c "from orchestrator.orchestrator import execute_plan; print('Success!')"

# Uninstall after testing
pip uninstall toolweaver -y
```

### Step 4: Upload to TestPyPI (Recommended First)

Test your package on TestPyPI before the real PyPI:

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*
```

When prompted:
- Username: `__token__`
- Password: `pypi-...` (your TestPyPI API token)

Then test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ toolweaver
```

### Step 5: Upload to PyPI (Production)

Once TestPyPI works:

```bash
# Upload to real PyPI
python -m twine upload dist/*
```

When prompted:
- Username: `__token__`
- Password: `pypi-...` (your PyPI API token)

## After Publishing

Users can now install with:

```bash
# Basic installation
pip install toolweaver

# With monitoring
pip install toolweaver[monitoring]

# With all features
pip install toolweaver[all]

# Specific version
pip install toolweaver==0.1.3
```

## Automated Publishing (GitHub Actions)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Then add `PYPI_API_TOKEN` to GitHub Secrets:
1. GitHub repo → Settings → Secrets and variables → Actions
2. New repository secret
3. Name: `PYPI_API_TOKEN`
4. Value: Your PyPI token

## Version Management

For future releases:

1. Update version in `pyproject.toml`:
   ```toml
   version = "0.1.4"
   ```

2. Commit and tag:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.1.4"
   git tag v0.1.4
   git push origin main --tags
   ```

3. Create GitHub release (triggers auto-publish if using Actions)

4. Or manually build and upload:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

## Checklist Before Publishing

- [ ] Update version in `pyproject.toml`
- [ ] Update `RELEASES.md` with release notes
- [ ] Test package builds: `python -m build`
- [ ] Test local installation
- [ ] Upload to TestPyPI first
- [ ] Test installation from TestPyPI
- [ ] Upload to PyPI
- [ ] Create GitHub release
- [ ] Test `pip install toolweaver`

## Common Issues

### "File already exists"
- You can't re-upload the same version
- Increment version number and rebuild

### Import errors after install
- Check `pyproject.toml` → `[tool.setuptools]` → `packages`
- Ensure all Python packages are listed

### Missing dependencies
- Users should install with extras: `pip install toolweaver[all]`
- Or specify dependencies in project's requirements.txt

## Package Info

After publishing, your package will be available at:
- **PyPI:** https://pypi.org/project/toolweaver/
- **Install:** `pip install toolweaver`
- **Source:** https://github.com/ushakrishnan/ToolWeaver

## Testing the Published Package

Create a fresh test environment:

```bash
# New directory
mkdir test-toolweaver
cd test-toolweaver

# New venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install from PyPI
pip install toolweaver[all]

# Test
python -c "from orchestrator.orchestrator import execute_plan; print('ToolWeaver installed successfully!')"
```

## Documentation Updates

After publishing, update README.md with:

```markdown
## Installation

```bash
pip install toolweaver
```

For all features:
```bash
pip install toolweaver[all]
```
\```

## Quick Start

```python
from orchestrator.orchestrator import execute_plan

# Your code here
```
\```
```

That's it! Your package is now on PyPI and can be used in any Python project.
