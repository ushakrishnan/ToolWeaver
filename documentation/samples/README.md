# ToolWeaver Samples

Complete guide to 28 runnable samples demonstrating all major ToolWeaver features using the **published PyPI package**.

**Total Samples:** 28  
**Package Source:** PyPI (`pip install toolweaver`)  
**Setup Status:** ✅ All configured with requirements.txt (no local imports)  
**Test Coverage:** All samples ready for distribution and user testing

---

## Key Difference from Examples

| Aspect | Examples | Samples |
|--------|----------|---------|
| **Package Source** | Local source (`sys.path.insert`) | Published PyPI package |
| **Installation** | Add orchestrator to path | `pip install toolweaver` |
| **Use Case** | Development & contribution | End-user distribution |
| **Requirements** | Local dev environment | Any Python environment |

---

## 🚀 Quick Start

```bash
cd samples/01-basic-receipt-processing
pip install -r requirements.txt
python process_receipt.py
```

### Troubleshooting: Windows Emoji Encoding

If you see garbled characters like `ΓÇó` instead of emoji on Windows:

**Quick Fix (temporary):**
```powershell
$env:PYTHONIOENCODING='utf-8'
python script.py
```

**Permanent Fix:** Add to PowerShell profile:
```powershell
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
```

---

## 📚 Samples by Category

### Basic Usage (Start Here)
1. **[01-basic-receipt-processing](../../samples/01-basic-receipt-processing)** - Simple tool registration & discovery with receipt OCR
2. **[02-receipt-with-categorization](../../samples/02-receipt-with-categorization)** - Multi-step workflow with LLM-based categorization
3. **[09-code-execution](../../samples/09-code-execution)** - Safe sandboxed code execution

### Tool Integration & Discovery
4. **[03-github-operations](../../samples/03-github-operations)** - Mock GitHub API tools
5. **[04-vector-search-discovery](../../samples/04-vector-search-discovery)** - Vector-based semantic tool search

### Workflow & Organization
6. **[05-workflow-library](../../samples/05-workflow-library)** - YAML workflow configuration and loading
7. **[23-adding-new-tools](../../samples/23-adding-new-tools)** - Add custom tools to the orchestrator

### Advanced Features
8. **[06-monitoring-observability](../../samples/06-monitoring-observability)** - Cost tracking and metrics collection
9. **[07-caching-optimization](../../samples/07-caching-optimization)** - Multi-layer caching strategy
10. **[08-hybrid-model-routing](../../samples/08-hybrid-model-routing)** - Route tasks to different models for cost optimization

### Agent & Planning Patterns
11. **[10-multi-step-planning](../../samples/10-multi-step-planning)** - LLM-based multi-step execution planning
12. **[11-programmatic-executor](../../samples/11-programmatic-executor)** - Batch processing without LLM overhead
13. **[12-sharded-catalog](../../samples/12-sharded-catalog)** - Scale to 1000+ tools with sharding
14. **[13-complete-pipeline](../../samples/13-complete-pipeline)** - End-to-end pipeline with all features

---

## 🧪 Running Samples

### Run Individual Sample

```bash
cd samples/01-basic-receipt-processing
pip install -r requirements.txt
python process_receipt.py
```

### Run All Samples (Test)

```bash
cd samples
python test_all_examples.py
```

Expected output: All 13 core samples pass structure validation ✅

---

## 📦 Dependencies

Each sample has its own `requirements.txt` with pinned versions for reproducibility.

Core dependency:
```
toolweaver==0.8.0
```

Additional dependencies vary by sample (pydantic, aiohttp, etc.) but all are specified in each sample's `requirements.txt`.

---

## 🤝 Contributing

For development with the local source:
- Use `examples/` folder instead
- Examples use `sys.path.insert()` to import from local orchestrator/
- Samples are for distribution and user testing

---

## 📞 Support

Issues or questions?
- Check [samples/README.md](../../samples/README.md) in the repo root for per-sample documentation
- Refer to [docs/getting-started/](../getting-started/) for setup guides
- See [docs/user-guide/](../user-guide/) for feature documentation
