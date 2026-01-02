# Adding New Samples - Cross-Platform Checklist

Use this checklist when creating new ToolWeaver samples to ensure they work on Windows, macOS, and Linux.

## Quick Checklist

- [ ] **Paths:** Use `pathlib.Path` for all file operations
- [ ] **Subprocesses:** Use `subprocess.run(..., capture_output=True, text=True)`
- [ ] **Async:** Use `asyncio.run()` at entry point
- [ ] **Env vars:** Load via `python-dotenv` in `.env`
- [ ] **Console output:** No hardcoded ANSI codes; handle encoding
- [ ] **Tests:** Run on Windows, macOS (Intel & Apple Silicon), Linux

## Detailed Patterns

### ✅ DO: File Paths

```python
from pathlib import Path

# ✅ Works on all platforms
config_file = Path(__file__).parent / "config.yaml"
cache_dir = Path.home() / ".toolweaver" / "cache"
output_file = Path("output") / "results.json"

# Convert to string when needed
config_path_str = str(config_file)
```

### ❌ DON'T: Hardcoded Paths

```python
# ❌ Linux only
config_file = "/home/user/project/config.yaml"

# ❌ Windows only
config_file = "C:\\Users\\user\\project\\config.yaml"

# ❌ Shell path expansion (platform-dependent)
config_file = "~/project/config.yaml"  # Doesn't work in Python
```

---

### ✅ DO: Subprocess Execution

```python
import subprocess
import sys

# ✅ Works on all platforms
result = subprocess.run(
    [sys.executable, "-m", "pip", "list"],
    capture_output=True,
    text=True
)
print(result.stdout)  # Output as string
```

### ❌ DON'T: Shell-Specific Commands

```python
# ❌ Unix only
result = subprocess.run("ls -la", shell=True)

# ❌ Windows only
result = subprocess.run("dir", shell=True)

# ❌ Platform detection anti-pattern
if platform.system() == "Windows":
    result = subprocess.run("dir", shell=True)
else:
    result = subprocess.run("ls -la", shell=True)
```

---

### ✅ DO: Async/Await

```python
import asyncio

async def process_data():
    """Process data asynchronously."""
    await asyncio.sleep(1)
    return "done"

# Entry point
if __name__ == "__main__":
    result = asyncio.run(process_data())
    print(result)
```

### ❌ DON'T: Platform-Specific Event Loops

```python
# ❌ Windows-specific (doesn't work on Unix)
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ❌ Unix-specific (doesn't work on Windows with async subprocesses)
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
```

---

### ✅ DO: Environment Variables

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load from .env file (works everywhere)
load_dotenv()

# Read variables
api_key = os.getenv("AZURE_OPENAI_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

# With defaults
log_level = os.getenv("LOG_LEVEL", "INFO")
```

### ❌ DON'T: Shell-Specific Environment Setup

```python
# ❌ Bash only (doesn't work on Windows)
export_cmd = "export API_KEY=value"

# ❌ Assuming environment is pre-configured
# Without loading .env or checking if vars exist
api_key = os.environ["API_KEY"]  # May crash if not set
```

---

### ✅ DO: Console Output

```python
# ✅ Use Unicode that works everywhere
print("✅ Task completed")
print("❌ Task failed")
print("⚠️  Warning")

# ✅ Handle encoding properly in Python 3.7+
import sys
print("Testing UTF-8: 你好世界", file=sys.stderr)
```

### ❌ DON'T: Hardcoded ANSI Codes

```python
# ❌ Doesn't work on Windows without extra setup
print("\033[92m✅ Green text\033[0m")

# ❌ Assumes console can render
print("→ Arrow ← ← ←")  # May show as ? on some Windows consoles
```

If you need colors on all platforms, use a library:

```python
# ✅ Use colorama for cross-platform colors
from colorama import Fore, Style, init
init()  # Initialize for Windows

print(f"{Fore.GREEN}✅ Success{Style.RESET_ALL}")
print(f"{Fore.RED}❌ Failed{Style.RESET_ALL}")
```

---

### ✅ DO: Virtual Environments

Document setup for all platforms in README:

```markdown
## Setup

**Windows (PowerShell):**
\`\`\`powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
\`\`\`

**macOS/Linux (Bash):**
\`\`\`bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
\`\`\`
```

### ❌ DON'T: Assume Environment

```markdown
# ❌ Only shows Bash commands
## Setup

\`\`\`bash
source .venv/bin/activate
pip install -r requirements.txt
\`\`\`
```

---

### ✅ DO: .env Files

**`.env.example`** (commit to git):
```dotenv
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=YOUR_KEY_HERE
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Optional
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
```

**`.env`** (add to `.gitignore`):
```dotenv
# User's actual credentials
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
AZURE_OPENAI_KEY=sk-1234567890abcdef
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

**`requirements.txt`**:
```
toolweaver
python-dotenv
requests
aiohttp
```

### ❌ DON'T: Hardcoded Credentials

```python
# ❌ NEVER do this
API_KEY = "sk-123456789"  # Will be committed to git!

# ❌ Assume environment is set
api_key = os.environ["API_KEY"]  # Crashes if not set
```

---

### ✅ DO: Line Endings

Let Git handle this automatically:

**`.gitattributes`** (in repo root):
```
* text=auto
*.py text eol=lf
*.txt text eol=lf
.env* text eol=lf
```

This ensures:
- Files checked out as LF on all platforms
- No `\r\n` on Windows (which Python doesn't care about, but is cleaner)

---

### ✅ DO: Character Encoding

```python
# -*- coding: utf-8 -*-
"""Sample with international characters.

This works on Windows, macOS, and Linux with proper encoding.
"""

def greet(name: str) -> str:
    """Greet someone. Supports: Café, naïve, 你好, مرحبا"""
    return f"Hello {name}! 👋"

if __name__ == "__main__":
    print(greet("Alice"))  # Works everywhere
```

---

## Sample Checklist Template

When adding a new sample, verify these items:

```markdown
# New Sample: [Title]

## Checklist

### Code Structure
- [ ] Uses `pathlib.Path` for all file operations
- [ ] No hardcoded paths (`/home/...`, `C:\...`)
- [ ] `subprocess.run()` uses `capture_output=True, text=True`
- [ ] Async code uses `asyncio.run()` at entry point
- [ ] No platform-specific `if platform.system()` checks

### Configuration
- [ ] `.env.example` file with template variables
- [ ] `.env` in `.gitignore`
- [ ] Uses `python-dotenv` to load config
- [ ] README documents all required variables

### Documentation
- [ ] README with Windows/macOS/Linux setup instructions
- [ ] Shows activation of virtual environment for each OS
- [ ] Lists all dependencies in `requirements.txt`
- [ ] Includes expected output/behavior

### Testing
- [ ] Tested on Windows 11 (PowerShell 7)
- [ ] Tested on macOS (Intel)
- [ ] Tested on Ubuntu/Linux
- [ ] All imports available and working
- [ ] Output matches expected format

### Submission
- [ ] No secrets in `.env.example`
- [ ] No `__pycache__` or `.venv` included
- [ ] All files have correct line endings (LF)
- [ ] README.md is comprehensive
```

---

## Platform-Specific Testing

### Quick Test on All Platforms

**Minimal test script:**
```python
# test_sample.py
import platform
import sys
from pathlib import Path

print(f"Platform: {platform.system()}")
print(f"Python: {sys.version}")
print(f"Path.home(): {Path.home()}")

# Test subprocess
import subprocess
result = subprocess.run([sys.executable, "-c", "print('Hello')"], capture_output=True, text=True)
assert result.returncode == 0

# Test async
import asyncio
asyncio.run(asyncio.sleep(0))

print("✅ All platform checks passed")
```

Run on each platform:
```bash
# Windows
python test_sample.py

# macOS/Linux
python3 test_sample.py
```

---

## Common Pitfalls

### Pitfall 1: Assumes Bash
```python
# ❌ Wrong
os.system("export VAR=value")

# ✅ Correct
os.environ["VAR"] = "value"
```

### Pitfall 2: Hardcoded Home Directory
```python
# ❌ Wrong
cache_dir = "/home/user/.toolweaver/cache"

# ✅ Correct
cache_dir = Path.home() / ".toolweaver" / "cache"
```

### Pitfall 3: No Virtual Environment Instructions
```markdown
# ❌ No activation shown
pip install -r requirements.txt

# ✅ Shows per-platform activation
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Pitfall 4: Missing .env.example
```python
# ❌ Crashes if API key not set
api_key = os.environ["API_KEY"]

# ✅ Fails gracefully with helpful message
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("Set AZURE_OPENAI_KEY in .env")
```

### Pitfall 5: Shell=True
```python
# ❌ Breaks on other platforms
subprocess.run("python main.py", shell=True)

# ✅ Works on all platforms
subprocess.run([sys.executable, "main.py"])
```

---

## Useful Resources

- **Documentation:**
  - [CROSS_PLATFORM_SETUP.md](CROSS_PLATFORM_SETUP.md)
  - [ENV_CONFIGURATION.md](ENV_CONFIGURATION.md)
  
- **Tools:**
  - [verify_cross_platform.py](verify_cross_platform.py) - Verify setup

- **Python Docs:**
  - [`pathlib.Path`](https://docs.python.org/3/library/pathlib.html)
  - [`subprocess.run()`](https://docs.python.org/3/library/subprocess.html#subprocess.run)
  - [`asyncio`](https://docs.python.org/3/library/asyncio.html)
  - [`os.environ`](https://docs.python.org/3/library/os.html#os.environ)

---

## Quick Reference Card

| Task | Windows | macOS/Linux |
|------|---------|-------------|
| Create venv | `python -m venv .venv` | `python3 -m venv .venv` |
| Activate | `.\.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| Set env var | `$env:VAR="value"` | `export VAR="value"` |
| File path | `Path(__file__).parent` | `Path(__file__).parent` |
| Run Python | `python main.py` | `python3 main.py` |

**Key:** Use pathlib for paths, subprocess.run() for execution, .env for config. Works everywhere!

---

**Last Updated:** January 2, 2026
