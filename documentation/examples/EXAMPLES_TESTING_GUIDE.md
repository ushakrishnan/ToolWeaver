# Examples Testing Guide

Comprehensive testing strategy for all 29 ToolWeaver examples.

---

## 🚀 Pre-Testing Setup

### 1. Verify Dependencies
```bash
python scripts/verify_install.py
```

### 2. Verify .env Configuration
Each example should have:
```bash
ls -la examples/01-basic-receipt-processing/.env
```

Expected output: `.env` exists with populated values

### 3. Install Per-Example Dependencies
```bash
cd examples/01-basic-receipt-processing
pip install -r requirements.txt
```

---

## 🧪 Testing Strategies

### Strategy 1: Individual Example Testing

**Test single example:**
```bash
cd examples/01-basic-receipt-processing
python process_receipt.py
```

**Verify it works:**
- No import errors
- Script completes successfully
- Output is generated (receipts processed, etc.)

### Strategy 2: Batch Testing

**Run all examples with test script:**
```bash
cd examples
python test_all_examples.py
```

**This script:**
- Finds all example directories
- Checks for main.py or primary Python file
- Runs each with timeout
- Reports success/failure
- Generates summary

### Strategy 3: Integration Testing

**Test with multiple backends:**
```bash
# Test with OpenAI
OPENAI_API_KEY=sk-... python examples/01-basic-receipt-processing/process_receipt.py

# Test with Azure OpenAI
AZURE_OPENAI_KEY=... python examples/01-basic-receipt-processing/process_receipt.py

# Test with local Ollama
OLLAMA_HOST=http://localhost:11434 python examples/01-basic-receipt-processing/process_receipt.py
```

### Strategy 4: Performance Testing

**Measure execution time:**
```bash
time python examples/13-complete-pipeline/main.py
```

**Check resource usage:**
```bash
# On Windows
Get-Process -Name python | Select-Object WorkingSet

# On Linux/Mac
ps aux | grep python
```

---

## 📋 Test Categories

### Category 1: Basic Examples (No External APIs)
- 01-basic-receipt-processing (can use mock)
- 09-code-execution
- 15-control-flow

**Testing:** No API keys needed; use locally
```bash
OCR_MODE=mock python examples/01-basic-receipt-processing/process_receipt.py
```

### Category 2: LLM Examples (Need OpenAI/Azure/Anthropic)
- 02-receipt-with-categorization
- 10-multi-step-planning
- 22-end-to-end-showcase

**Testing:** Requires valid LLM API key
```bash
OPENAI_API_KEY=sk-... python examples/02-receipt-with-categorization/main.py
```

### Category 3: Integration Examples (GitHub, etc.)
- 03-github-operations
- 19-fetch-analyze-store
- 20-approval-workflow

**Testing:** Requires GitHub token
```bash
GITHUB_TOKEN=ghp_... python examples/03-github-operations/main.py
```

### Category 4: Advanced Examples (Multi-agent, Parallel)
- 16-agent-delegation
- 17-multi-agent-coordination
- 25-parallel-agents

**Testing:** Monitor for async/parallel execution
```bash
python examples/25-parallel-agents/main.py
# Watch for parallel output patterns
```

### Category 5: Deployment Examples (Production Setups)
- 13-complete-pipeline
- 27-cost-optimization
- 22-end-to-end-showcase

**Testing:** Full integration test with all services
```bash
python examples/13-complete-pipeline/main.py
# Verify all components work together
```

---

## ✅ Verification Checklist

For each example, verify:

- [ ] README.md exists and documents purpose
- [ ] requirements.txt exists
- [ ] .env and .env.example exist
- [ ] Python code files present
- [ ] Code runs without import errors
- [ ] Output is sensible (no errors/exceptions)
- [ ] Execution completes in reasonable time (<60s for basic)
- [ ] Documentation links work
- [ ] .env has correct keys for functionality

---

## 🐛 Troubleshooting

### Common Issues

**Import Error: `No module named 'orchestrator'`**
```bash
# Solution: Install in editable mode from root
cd ..  # Go to root
pip install -e ".[dev]"
cd examples/EXAMPLE_NAME
python main.py
```

**Error: `OPENAI_API_KEY not set`**
```bash
# Solution: Copy and populate .env
cp .env.example .env
# Edit .env with your API key
```

**Timeout or hanging**
```bash
# Solution: Run with timeout
timeout 30 python examples/EXAMPLE_NAME/main.py
# If hangs, check for network issues or infinite loops
```

**PermissionError or file access issues**
```bash
# Solution: Check file permissions
ls -la examples/EXAMPLE_NAME/
# Should be readable by current user
```

---

## 📊 Expected Test Results

### Success Metrics
- ✅ No import errors
- ✅ Script executes fully
- ✅ Proper exit code (0 for success)
- ✅ Output generated

### Failure Modes to Investigate
- ❌ Import errors → Check installation
- ❌ Authentication errors → Check .env keys
- ❌ Timeouts → Check API limits or network
- ❌ Runtime errors → Check example logs

---

## 📈 Test Progress Tracking

### Examples Status Matrix

Create a test results file to track:

```markdown
| Example | Status | LLM | GitHub | Redis | Notes |
|---------|--------|-----|--------|-------|-------|
| 01-basic | ✅ | OpenAI | - | - | Works with mock |
| 02-categorize | ✅ | OpenAI | - | - | Full categorization |
| 03-github | ✅ | - | ✅ | - | PRs working |
| ... | ... | ... | ... | ... | ... |
```

---

## 🔧 Advanced Testing

### Load Testing

```bash
# Test example with multiple concurrent runs
for i in {1..5}; do
    python examples/04-vector-search-discovery/main.py &
done
wait
```

### Stress Testing

```bash
# Test with large data
python examples/13-complete-pipeline/main.py --size=large
```

### Compatibility Testing

```bash
# Test with different Python versions
python3.10 examples/01-basic-receipt-processing/process_receipt.py
python3.11 examples/01-basic-receipt-processing/process_receipt.py
python3.12 examples/01-basic-receipt-processing/process_receipt.py
```

---

## 📚 Related Documentation

- [Examples Overview](README.md) - All examples listing
- [Testing Strategy](../for-contributors/testing.md) - Unit test strategy
- [Developer Guide](../developer-guide/WORKFLOW.md) - Development workflow
- [TEST_COVERAGE_REPORT.md](../internal/test-reports/TEST_COVERAGE_REPORT.md) - Coverage metrics

