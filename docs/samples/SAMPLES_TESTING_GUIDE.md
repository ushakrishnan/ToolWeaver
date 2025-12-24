# Samples Testing Guide

Comprehensive testing strategy for the 28 ToolWeaver samples using the published PyPI package.

---

## 🚀 Pre-Testing Setup

### 1. Verify Python Installation
```bash
python --version  # Should be 3.8+
```

### 2. Install Sample Dependencies
Each sample is self-contained with its own `requirements.txt`:

```bash
cd samples/01-basic-receipt-processing
pip install -r requirements.txt
```

### 3. Verify Installation
```bash
pip show toolweaver
# Should show: Version: 0.7.0
```

---

## 🧪 Testing Strategies

### Strategy 1: Individual Sample Testing

**Run a single sample:**
```bash
cd samples/01-basic-receipt-processing
python process_receipt.py
```

**Expected behavior:**
- No import errors (orchestrator should import from PyPI)
- Script completes successfully
- Output is generated (receipts processed, etc.)
- No local sys.path hacks needed

### Strategy 2: Batch Testing

**Run all samples with test validation:**
```bash
cd samples
python test_all_examples.py
```

**Expected output:**
```
Running structure validation for 13 examples...
[OK] 01-basic-receipt-processing
[OK] 02-receipt-with-categorization
...
13/13 passed
```

---

## ✅ Core Samples Test Coverage

| Sample | Category | Status | Notes |
|--------|----------|--------|-------|
| 01 | Basic | ✅ | Tool registration & search |
| 02 | Workflow | ✅ | Multi-step chaining |
| 03 | Integration | ✅ | Mock GitHub API |
| 04 | Discovery | ✅ | Vector search (CPU-only) |
| 05 | Config | ✅ | YAML workflows |
| 06 | Monitoring | ✅ | Cost tracking |
| 07 | Caching | ✅ | Multi-layer cache |
| 08 | Routing | ✅ | Model selection |
| 09 | Execution | ✅ | Safe code execution |
| 10 | Planning | ✅ | Multi-step plans |
| 11 | Programmatic | ✅ | Batch processing |
| 12 | Scaling | ✅ | Sharded catalog |
| 13 | Pipeline | ✅ | End-to-end demo |

---

## 🔧 Troubleshooting

### Import Errors
**Issue:** `ModuleNotFoundError: No module named 'orchestrator'`

**Solution:**
```bash
pip install toolweaver==0.7.0
```

Samples should NOT use `sys.path.insert()`. If you see that, you're looking at `examples/`, not `samples/`.

### Emoji Encoding on Windows
**Issue:** Garbled output like `ΓÇó` instead of `[OK]` or emoji

**Solution (temporary):**
```powershell
$env:PYTHONIOENCODING='utf-8'
python script.py
```

**Solution (permanent):**
```powershell
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
# Restart PowerShell
```

### Missing .env Files
**Issue:** Script fails because .env is missing

**Solution:**
```bash
# Each sample has .env.example
cd samples/01-basic-receipt-processing
cp .env.example .env
```

Most samples work without .env (use mock data), but some require it for optional features.

---

## 🎯 Testing Checklist

Before distributing samples:

- [ ] All 13 core samples pass `test_all_examples.py`
- [ ] Each sample runs without requiring local source code
- [ ] No `sys.path.insert()` in any sample (use PyPI package only)
- [ ] All `requirements.txt` pin `toolweaver==0.7.0`
- [ ] No .env secrets committed (only .env.example)
- [ ] Emoji output renders correctly on Windows (or shows ASCII like `[OK]`)
- [ ] README links in samples/README.md are accurate

---

## 📊 Performance Expectations

**Typical sample runtimes (with mock data):**
- Basic examples (01-04): < 1 second
- Workflow examples (05-09): < 2 seconds
- Planning examples (10-13): < 5 seconds (depends on mock iteration count)

If samples run significantly slower, check:
- Local system performance
- Network conditions (some might have optional network calls)
- CPU load (semantic search uses local embeddings)

---

## 🚀 Advanced Testing

### Run All Samples Sequentially
```bash
for dir in samples/*/; do
    cd "$dir"
    echo "Testing $dir..."
    pip install -r requirements.txt > /dev/null 2>&1
    python *.py > /dev/null 2>&1 && echo "✅ PASS" || echo "❌ FAIL"
    cd ../..
done
```

### Validate Requirements.txt Consistency
```bash
cd samples
grep "toolweaver" */requirements.txt | grep -v "==0.5.0" && echo "Found mismatched versions" || echo "✅ All pinned to 0.5.0"
```

### Check for Local Imports
```bash
grep -r "sys.path.insert" samples/ && echo "❌ Found local imports" || echo "✅ Clean (PyPI only)"
```

---

## 📞 Reporting Issues

When reporting sample issues, include:
1. **Which sample:** (e.g., "samples/01-basic-receipt-processing")
2. **Python version:** `python --version`
3. **Error message:** Full traceback
4. **System:** OS and PowerShell/terminal version
5. **Steps to reproduce:** Exact commands you ran

---

## 🔄 Updating Samples

When updating samples (e.g., new version):

1. **Update orchestrator version** in all `requirements.txt`:
   ```bash
   toolweaver==0.5.1  # or new version
   ```

2. **Test all samples:**
   ```bash
   cd samples && python test_all_examples.py
   ```

3. **Commit and tag release:**
   ```bash
   git tag v0.5.1
   git push --tags
   ```
