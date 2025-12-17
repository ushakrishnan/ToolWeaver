# Scripts Directory

Utility scripts for testing, validating, and managing ToolWeaver components.

## Dependency Management

### update_dependencies.py
**Purpose**: Automatically discover and verify dependencies by scanning all Python files

**Usage**:
```powershell
.\.venv\Scripts\Activate.ps1
python scripts/update_dependencies.py
```

**What it does**:
- Scans all `.py` files in `orchestrator/`, `tests/`, `examples/`
- Identifies external packages (filters out stdlib)
- Shows currently installed versions
- Generates suggested `pyproject.toml` updates

**When to use**: 
- After adding new functionality with new imports
- Before publishing a new version
- To audit current dependencies

---

### verify_install.py
**Purpose**: Test that all required dependencies can be imported

**Usage**:
```powershell
.\.venv\Scripts\Activate.ps1
python scripts/verify_install.py
```

**What it does**:
- Attempts to import all core dependencies
- Attempts to import all dev dependencies  
- Reports which optional dependencies are available
- Exit code 0 = success, 1 = missing required deps

**When to use**:
- After fresh install (`pip install -e '.[dev]'`)
---

## Testing Scripts
## Files

### test_cloud_connections.py
**Purpose**: Validate Qdrant and Redis Cloud connections

**Usage**:
```powershell
python scripts/test_cloud_connections.py
```

---

## Manual Integration Testing Scripts

**Note**: These are NOT part of the automated test suite (`tests/`). They require live service credentials and are for manual validation only.

### test_cloud_connections.py
**Purpose**: Validate Qdrant and Redis Cloud connections

**Prerequisites**:
- `.env` configured with `QDRANT_URL`, `REDIS_URL`, credentials

**Usage**:
```powershell
python scripts/test_cloud_connections.py
```

**Tests**:
- Qdrant Cloud: Connection, collections, vector counts
- Redis Cloud: Connection, ping, read/write, memory usage
- Pretty formatted output with status indicators

**When to use**: After setting up cloud services or changing credentials in `.env`

---

### test_azure_cv.py
**Purpose**: Test Azure Computer Vision OCR endpoint

**Prerequisites**:
- `.env` configured with `AZURE_CV_ENDPOINT`, `AZURE_CV_KEY` (or Azure AD auth)

**Usage**:
```powershell
python scripts/test_azure_cv.py
```

**Tests**:
**Tests**:
- Qdrant Cloud: Connection, collections, vector counts
- Redis Cloud: Connection, ping, read/write, memory usage
- Pretty formatted output with status indicators

**When to use**: After setting up cloud services or changing credentials in `.env`

---

### test_azure_cv.py
**Purpose**: Test Azure Computer Vision OCR endpoint

**Usage**:
```powershell
python scripts/test_azure_cv.py
```

**Tests**:
- Azure CV endpoint connectivity
- Azure AD authentication
- OCR mode configuration

---

### test_improvements.py
**Purpose**: Test multiple component improvements

**Tests**:
1. Phi-3 JSON prompts with retry logic
2. JSON repair function
3. Azure Computer Vision integration

**Usage**:
```powershell
python scripts/test_improvements.py
```

---

### test_phi3_output.py
**Purpose**: Test Phi-3 small model output formatting

**Usage**:
```powershell
python scripts/test_phi3_output.py
```

**Tests**:
- Phi-3 response parsing
- JSON output formatting
- Receipt line item extraction

---

## Note

These are **manual test scripts** for debugging and validation, not pytest tests.

For automated test suite, use:
```powershell
pytest tests/ -v
```
