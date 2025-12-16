# Configuration Guide

## Overview

This system supports flexible configuration for both **large planner models** and **small worker models**, allowing you to use different providers based on your needs.

## Large Model Planner Configuration

The large model generates execution plans from natural language requests.

### Provider Options

| Provider | Best For | Configuration |
|----------|----------|---------------|
| **Azure OpenAI** | Enterprise, existing Azure setup | AZURE_OPENAI_* variables |
| **OpenAI** | Quick start, latest models | OPENAI_API_KEY |
| **Anthropic** | Claude models, streaming | ANTHROPIC_API_KEY |
| **Google Gemini** | Google ecosystem, multimodal | GOOGLE_API_KEY |

### Configuration Examples

#### Option 1: Azure OpenAI (Recommended for Enterprise)

```bash
# .env
PLANNER_PROVIDER=azure-openai
PLANNER_MODEL=gpt-4o                    # Your deployment name
AZURE_OPENAI_API_KEY=abc123...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

**Setup Steps:**
1. Create Azure OpenAI resource in Azure Portal
2. Deploy gpt-4o model (note the deployment name)
3. Copy API key and endpoint from Keys & Endpoint section
4. Add to `.env` file

#### Option 2: OpenAI Direct

```bash
# .env
PLANNER_PROVIDER=openai
PLANNER_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
```

**Setup Steps:**
1. Get API key from https://platform.openai.com/api-keys
2. Add to `.env` file

#### Option 3: Anthropic Claude

```bash
# .env
PLANNER_PROVIDER=anthropic
PLANNER_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...
```

#### Option 4: Google Gemini

```bash
# .env
PLANNER_PROVIDER=gemini
PLANNER_MODEL=gemini-1.5-pro
GOOGLE_API_KEY=AIza...
```

---

## Small Model Worker Configuration

Small models execute specific tasks like parsing and categorization efficiently.

### Backend Options

| Backend | Best For | Configuration |
|---------|----------|---------------|
| **Ollama** | Local development, privacy | OLLAMA_API_URL |
| **Azure AI Foundry** | Enterprise, managed inference | AZURE_SMALL_MODEL_* |
| **Transformers** | Custom models, full control | HuggingFace model path |

### Configuration Examples

#### Option 1: Ollama (Local - Free)

**Advantages:**
- ✅ Free, runs locally
- ✅ Privacy (data never leaves your machine)
- ✅ Fast inference on local GPU
- ✅ Easy model switching

```bash
# .env
USE_SMALL_MODEL=true
SMALL_MODEL_BACKEND=ollama
WORKER_MODEL=phi3
OLLAMA_API_URL=http://localhost:11434
```

**Setup Steps:**
```bash
# 1. Install Ollama
# Download from: https://ollama.ai

# 2. Pull Phi-3 model
ollama pull phi3

# 3. Verify it's running
ollama list

# 4. Test generation
ollama run phi3 "Hello"
```

**Available Models:**
- `phi3` - Microsoft Phi-3 (3.8B parameters)
- `phi3:medium` - Phi-3 Medium (14B parameters)
- `llama3.2` - Meta Llama 3.2 (3B parameters)
- `mistral` - Mistral 7B
- `gemma2:2b` - Google Gemma 2 (2B parameters)

#### Option 2: Azure AI Foundry (Cloud - Managed)

**Advantages:**
- ✅ Managed infrastructure
- ✅ Auto-scaling
- ✅ Enterprise support
- ✅ Azure AD integration

```bash
# .env
USE_SMALL_MODEL=true
SMALL_MODEL_BACKEND=azure
WORKER_MODEL=Phi-3-mini-4k-instruct      # Deployment name

# Option A: API Key Authentication
AZURE_SMALL_MODEL_ENDPOINT=https://your-endpoint.inference.ml.azure.com/score
AZURE_SMALL_MODEL_KEY=your-api-key

# Option B: Azure AD Authentication (recommended)
AZURE_SMALL_MODEL_ENDPOINT=https://your-endpoint.inference.ml.azure.com/score
AZURE_SMALL_MODEL_USE_AD=true
```

**Setup Steps for Azure AI Foundry:**

1. **Deploy Model in Azure AI Foundry:**
   - Go to Azure AI Foundry Studio (https://ai.azure.com)
   - Navigate to Model Catalog
   - Find Phi-3-mini-4k-instruct
   - Click "Deploy" → "Serverless API"
   - Note the deployment name and endpoint

2. **Get Credentials:**
   ```bash
   # For API Key:
   # Copy from deployment's "Consume" tab
   
   # For Azure AD:
   # Ensure you have "Cognitive Services User" role
   az login
   ```

3. **Configure .env:**
   ```bash
   AZURE_SMALL_MODEL_ENDPOINT=https://<your-workspace>.inference.ml.azure.com/score
   AZURE_SMALL_MODEL_KEY=<your-key>
   ```

**Available Models in Azure AI Foundry:**
- Phi-3-mini-4k-instruct (Microsoft)
- Phi-3-medium-4k-instruct (Microsoft)
- Llama-3.2-3B-Instruct (Meta)
- Mistral-7B-Instruct-v0.3 (Mistral AI)

#### Option 3: Transformers (Local - Advanced)

**Advantages:**
- ✅ Full control over model
- ✅ Custom fine-tuned models
- ✅ No external dependencies

```bash
# .env
USE_SMALL_MODEL=true
SMALL_MODEL_BACKEND=transformers
WORKER_MODEL=microsoft/Phi-3-mini-4k-instruct
```

**Setup Steps:**
```bash
# Install with local model support
pip install -e ".[local-models]"

# Models will auto-download on first use
```

**Requirements:**
- GPU with 8GB+ VRAM (or 16GB+ RAM for CPU inference)
- ~15GB disk space per model

---

## Configuration Matrix

### Recommended Combinations

| Use Case | Large Model | Small Model | Why |
|----------|-------------|-------------|-----|
| **Enterprise Production** | Azure OpenAI | Azure AI Foundry | Unified Azure billing, managed services |
| **Development/Testing** | Azure OpenAI | Ollama | Cost-effective, fast iteration |
| **Privacy-First** | OpenAI | Ollama | Sensitive data processed locally |
| **Quick Prototype** | OpenAI | Disabled | Fastest setup, single API |
| **Research** | Anthropic Claude | Transformers | Latest models, full control |

### Cost Comparison

**Scenario: Process 1000 receipts**

| Configuration | Planning Cost | Execution Cost | Total | Notes |
|---------------|---------------|----------------|-------|-------|
| GPT-4o only | $0.002 | $15.00 | **$15.00** | Baseline |
| GPT-4o + Ollama | $0.002 | $0.00 | **$0.002** | 99.98% savings |
| GPT-4o + Azure Foundry | $0.002 | $0.50 | **$0.502** | 96.7% savings |
| Claude + Ollama | $0.003 | $0.00 | **$0.003** | 99.98% savings |

---

## Environment Variables Reference

### Large Model Planner

```bash
# Required
PLANNER_PROVIDER=azure-openai|openai|anthropic|gemini
PLANNER_MODEL=<model-name-or-deployment>

# Azure OpenAI
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini
GOOGLE_API_KEY=AIza...
```

### Small Model Workers

```bash
# Required
USE_SMALL_MODEL=true|false
SMALL_MODEL_BACKEND=ollama|azure|transformers
WORKER_MODEL=<model-name>

# Ollama
OLLAMA_API_URL=http://localhost:11434

# Azure AI Foundry
AZURE_SMALL_MODEL_ENDPOINT=https://<endpoint>/score
AZURE_SMALL_MODEL_KEY=<key>
AZURE_SMALL_MODEL_USE_AD=true|false  # Optional: use Azure AD instead of key
```

---

## Testing Your Configuration

### Test Large Model Planner

```bash
python run_planner_demo.py "Process this receipt and categorize items"
```

**Expected Output:**
```
🧠 Initializing large model planner...
✓ Using azure-openai with model gpt-4o

Generated 5 steps:
  - step-1: receipt_ocr
  - step-2: line_item_parser
  ...
```

### Test Small Model Worker

```bash
# Enable in .env
USE_SMALL_MODEL=true

# Run demo
python run_demo.py
```

**Expected Output:**
```
INFO:orchestrator.workers:Using small model for line item parsing
INFO:orchestrator.small_model_worker:Phi-3 parsed 3 items
```

### Verify Configuration

```python
# Quick test script
import os
from dotenv import load_dotenv

load_dotenv()

print("Large Model Config:")
print(f"  Provider: {os.getenv('PLANNER_PROVIDER')}")
print(f"  Model: {os.getenv('PLANNER_MODEL')}")
print(f"  Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT', 'N/A')}")

print("\nSmall Model Config:")
print(f"  Enabled: {os.getenv('USE_SMALL_MODEL')}")
print(f"  Backend: {os.getenv('SMALL_MODEL_BACKEND')}")
print(f"  Model: {os.getenv('WORKER_MODEL')}")
```

---

## Troubleshooting

### Issue: "Failed to initialize planner"

**Solution:**
1. Check provider name matches: `azure-openai`, `openai`, `anthropic`, `gemini`
2. Verify API keys are set correctly
3. For Azure: Ensure endpoint ends with `/`
4. Check API version is current

### Issue: "Small model not responding"

**Ollama:**
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
# Windows: Restart from system tray
# Linux: sudo systemctl restart ollama
```

**Azure:**
```bash
# Test endpoint with curl
curl -X POST "YOUR_ENDPOINT" \
  -H "api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}]}'
```

### Issue: "Out of memory" with Transformers

**Solution:**
```python
# Use smaller model
WORKER_MODEL=microsoft/Phi-3-mini-4k-instruct  # 3.8B params

# Or switch to Ollama
SMALL_MODEL_BACKEND=ollama
```

---

## Migration Guide

### From OpenAI to Azure OpenAI

```bash
# Before
PLANNER_PROVIDER=openai
OPENAI_API_KEY=sk-...

# After
PLANNER_PROVIDER=azure-openai
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
PLANNER_MODEL=gpt-4o  # Your deployment name
```

### From No Small Model to Ollama

```bash
# Install Ollama
ollama pull phi3

# Update .env
USE_SMALL_MODEL=true
SMALL_MODEL_BACKEND=ollama
WORKER_MODEL=phi3

# Test
python run_demo.py
```

### From Ollama to Azure AI Foundry

```bash
# Deploy in Azure AI Foundry (see setup steps above)

# Update .env
SMALL_MODEL_BACKEND=azure
AZURE_SMALL_MODEL_ENDPOINT=<endpoint>
AZURE_SMALL_MODEL_KEY=<key>
```

---

## Best Practices

1. **Use Azure OpenAI + Azure AI Foundry** for enterprise (unified billing, support)
2. **Use Ollama for development** (free, fast iteration)
3. **Set USE_SMALL_MODEL=false** initially, enable once planner works
4. **Test with small datasets** before processing large batches
5. **Monitor costs** with Azure Cost Management
6. **Use Azure AD** instead of API keys when possible (better security)

---

## Next Steps

1. **Configure Large Model:** Choose provider and set credentials
2. **Test Planner:** Run `python run_planner_demo.py`
3. **Configure Small Model:** Choose Ollama or Azure
4. **Enable Small Model:** Set `USE_SMALL_MODEL=true`
5. **Test End-to-End:** Run `python run_demo.py`

For more details, see:
- [Two-Model Architecture](TWO_MODEL_ARCHITECTURE.md)
- [Azure Setup Guide](AZURE_SETUP.md)
