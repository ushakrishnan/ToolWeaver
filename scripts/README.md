# Scripts Directory

Utility scripts for testing and validating ToolWeaver components manually.

## Files

### test_cloud_connections.py
**Purpose**: Validate Qdrant and Redis Cloud connections

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
