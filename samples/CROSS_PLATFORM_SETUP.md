# Cross-Platform Setup Guide

This guide ensures ToolWeaver samples work seamlessly on **Windows**, **macOS**, and **Linux**.

## Platform Support Matrix

| Feature | Windows | macOS | Linux |
|---------|---------|-------|-------|
| Python 3.10-3.13 | ✅ | ✅ | ✅ |
| Virtual Environments | ✅ | ✅ | ✅ |
| `.env` configuration | ✅ | ✅ | ✅ |
| File paths (pathlib) | ✅ | ✅ | ✅ |
| Subprocess execution | ✅ | ✅ | ✅ |
| Redis/Docker | ✅ | ✅ | ✅ |
| Azure integration | ✅ | ✅ | ✅ |
| Code sandboxing | ✅ | ✅ | ✅ |

## Setup Instructions by OS

### 🪟 Windows (PowerShell 7+)

**1. Create Virtual Environment**
```powershell
# Create venv
python -m venv .venv

# Activate venv
.\.venv\Scripts\Activate.ps1

# If execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**2. Install ToolWeaver**
```powershell
pip install --upgrade pip
pip install toolweaver
```

**3. Configure Environment**
```powershell
# Copy template
cp .env.example .env

# Edit with your API keys
notepad .env
# or
code .env
```

**4. Run Sample**
```powershell
# If seeing garbled output, set encoding:
$env:PYTHONIOENCODING='utf-8'
python process_receipt.py

# Make it permanent in profile:
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
```

### 🍎 macOS (Intel & Apple Silicon)

**1. Create Virtual Environment**
```bash
# Create venv
python3 -m venv .venv

# Activate venv
source .venv/bin/activate
```

**2. Install ToolWeaver**
```bash
pip install --upgrade pip
pip install toolweaver
```

**3. Configure Environment**
```bash
# Copy template
cp .env.example .env

# Edit with your API keys
nano .env
# or
code .env
```

**4. Run Sample**
```bash
python process_receipt.py
```

**Note (Apple Silicon M1/M2/M3):** If you hit performance issues with sandboxed code execution, it's a platform limitation. Most tools will work fine. For compute-intensive sandboxing, consider:
- Running on Intel Mac via Rosetta 2 (automatic, may be slower)
- Using cloud-based execution instead

### 🐧 Linux (Ubuntu/Debian/Rocky/CentOS)

**1. Create Virtual Environment**
```bash
# Create venv
python3 -m venv .venv

# Activate venv
source .venv/bin/activate
```

**2. Install ToolWeaver**
```bash
pip install --upgrade pip
pip install toolweaver
```

**3. Configure Environment**
```bash
# Copy template
cp .env.example .env

# Edit with your API keys
nano .env
# or
code .env
```

**4. Run Sample**
```bash
python process_receipt.py
```

---

## Common Issues & Solutions

### Issue: `ModuleNotFoundError: No module named 'toolweaver'`

**Windows:**
```powershell
# Check that venv is activated
.\.venv\Scripts\Activate.ps1

# Reinstall
pip install --force-reinstall toolweaver
```

**macOS/Linux:**
```bash
# Check that venv is activated
which python  # Should show .venv/bin/python

# Reinstall
pip install --force-reinstall toolweaver
```

---

### Issue: `UnicodeEncodeError` or Garbled Output

**Windows only:**
```powershell
# Set encoding for current session
$env:PYTHONIOENCODING='utf-8'
python process_receipt.py

# Or set permanently
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
```

**macOS/Linux:** Unlikely, but if it happens:
```bash
export PYTHONIOENCODING=utf-8
python process_receipt.py
```

---

### Issue: `Permission denied` or `.env` File Issues

**Windows:**
- Use PowerShell 7+ (not cmd.exe)
- Right-click → "Run as administrator" if needed
- Use `code .env` or `notepad .env` to edit

**macOS/Linux:**
```bash
# Fix permissions if needed
chmod 644 .env
chmod 755 .venv/bin/python
```

---

### Issue: `ConnectionError` with Redis/Docker

**All Platforms:**
```bash
# Check if Docker is running
docker ps

# If not, start Docker Desktop (Windows/macOS) or:
# Linux:
sudo systemctl start docker

# Test Redis
docker run -d -p 6379:6379 redis:latest
redis-cli ping  # Should return PONG
```

---

### Issue: `.env` Not Being Loaded

**All Platforms:**
```python
# Verify in code
from dotenv import load_dotenv
import os

load_dotenv()  # Explicit load
api_key = os.getenv("AZURE_OPENAI_KEY")
print(f"API Key loaded: {api_key is not None}")
```

---

## Environment Variables Reference

All samples use these variables (all are optional except where noted):

```bash
# Azure OpenAI (for most samples)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4  # Model deployment name

# Azure Computer Vision (for OCR samples)
AZURE_CV_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_CV_KEY=your-key-here

# OpenAI (alternative to Azure)
OPENAI_API_KEY=sk-...

# Anthropic (alternative to Azure)
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Caching & Search
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-key-here

# Optional: Monitoring
WANDB_API_KEY=your-key-here
WANDB_PROJECT=my-project

# Optional: Logging
TOOLWEAVER_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Optional: Cache location (default: ~/.toolweaver/cache)
TOOLWEAVER_CACHE_PATH=/custom/cache/path
```

---

## File Path Handling

All samples use **`pathlib.Path`** which is cross-platform:

```python
from pathlib import Path

# ✅ Works on all platforms
config_file = Path(__file__).parent / ".env"
cache_dir = Path.home() / ".toolweaver" / "cache"

# ✅ String conversion also works
env_path = str(Path(__file__).parent / ".env")

# ❌ Avoid hardcoded paths
# DON'T: "/home/user/project/config.env" (Linux-only)
# DON'T: "C:\\Users\\user\\project\\config.env" (Windows-only)
```

---

## Testing Across Platforms

### Quick Validation

Run the test suite to verify setup:

**Windows:**
```powershell
.\.venv\Scripts\Activate.ps1
python ../test_all_examples.py
```

**macOS/Linux:**
```bash
source .venv/bin/activate
python ../test_all_examples.py
```

### Platform-Specific Tests

```bash
# Test file operations
python -c "from pathlib import Path; print(Path.home())"

# Test subprocess
python -c "import subprocess; print(subprocess.run(['python', '--version'], capture_output=True, text=True).stdout)"

# Test async execution
python -c "import asyncio; asyncio.run(asyncio.sleep(0))"

# Test Azure connectivity (if configured)
python -c "from azure.identity import DefaultAzureCredential; print('Azure SDK OK')"
```

---

## Docker Compatibility

All samples work in Docker containers (Linux base):

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .

# Install
RUN pip install toolweaver

# Configure
COPY .env.example .env

# Run
CMD ["python", "process_receipt.py"]
```

Build and run:
```bash
docker build -t toolweaver-sample .
docker run --env-file .env toolweaver-sample
```

---

## Performance Notes

| Platform | Performance | Notes |
|----------|-------------|-------|
| **Windows** | ✅ Excellent | Native Python, fastest subprocess calls |
| **macOS (Intel)** | ✅ Excellent | Native, same as Linux |
| **macOS (Apple Silicon)** | ⚠️ Good | Rosetta 2 translation may impact sandboxing; LLM queries are fast |
| **Linux** | ✅ Excellent | Best for production, most cloud platforms |

---

## Getting Help

1. **Check logs:** Errors are written to console and logs
2. **Verify setup:** Run `python ../test_all_examples.py`
3. **Check .env:** Ensure API keys are correct (try copy-pasting from source)
4. **GitHub Issues:** https://github.com/ushakrishnan/ToolWeaver/issues

---

## Next Steps

After successful setup:
1. Explore other samples: `cd ../02-receipt-with-categorization`
2. Modify a sample for your use case
3. Create your own tool using `@mcp_tool` decorator
4. Check [../README.md](../README.md) for full documentation

---

**Last Updated:** January 2, 2026  
**Tested:** Python 3.10-3.13 on Windows 11, macOS 14, Ubuntu 22.04
