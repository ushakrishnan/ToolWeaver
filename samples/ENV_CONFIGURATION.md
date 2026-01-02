# Environment Configuration Guide

All ToolWeaver samples use a `.env` file for configuration. This guide explains each variable and how to set it up for your environment.

## Quick Setup

```bash
# Copy the template
cp .env.example .env

# Edit with your credentials
nano .env        # Linux/macOS
notepad .env     # Windows
code .env        # All platforms with VS Code
```

## Configuration by Platform

### Windows (PowerShell)

Set environment variables for the current session:

```powershell
# Set single variable
$env:AZURE_OPENAI_KEY = "your-key-here"

# Or source from .env file programmatically
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#].+?)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```

**Make changes permanent:**
```powershell
[Environment]::SetEnvironmentVariable("AZURE_OPENAI_KEY", "your-key-here", "User")
```

### macOS/Linux (Bash)

Set environment variables:

```bash
# Set single variable
export AZURE_OPENAI_KEY="your-key-here"

# Or make permanent by adding to ~/.bashrc or ~/.zshrc
echo 'export AZURE_OPENAI_KEY="your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## Core Configuration

### Azure OpenAI (Primary LLM Provider)

Used by all samples for natural language understanding and planning.

**`AZURE_OPENAI_ENDPOINT`** (required for Azure)
```
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
```
- Replace `your-resource-name` with your Azure resource name
- Get from Azure Portal → OpenAI resource → Endpoints

**`AZURE_OPENAI_KEY`** (required for Azure)
```
AZURE_OPENAI_KEY=your-api-key-here
```
- Get from Azure Portal → OpenAI resource → Keys and Endpoints
- Never commit this to source control

**`AZURE_OPENAI_DEPLOYMENT`** (required for Azure)
```
AZURE_OPENAI_DEPLOYMENT=gpt-4
```
- Model deployment name in your Azure resource
- Common values: `gpt-4`, `gpt-35-turbo`, `gpt-4-turbo`

**`AZURE_OPENAI_API_VERSION`** (optional)
```
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```
- Default: Latest stable version
- Use newer versions for latest features

### Alternative LLM Providers

Use **one** of these if you don't have Azure OpenAI:

**OpenAI:**
```
OPENAI_API_KEY=sk-...
```
- Get from https://platform.openai.com/account/api-keys
- Requires valid billing setup

**Anthropic (Claude):**
```
ANTHROPIC_API_KEY=sk-ant-...
```
- Get from https://console.anthropic.com/

## Optional Configuration

### Azure Computer Vision (for OCR samples)

Used by receipt-processing samples to extract text from images.

**`AZURE_CV_ENDPOINT`**
```
AZURE_CV_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
```
- Get from Azure Portal → Computer Vision resource

**`AZURE_CV_KEY`**
```
AZURE_CV_KEY=your-cv-key-here
```
- Get from Azure Portal → Computer Vision resource → Keys

**`AZURE_USE_AD`** (if using Azure AD instead of key)
```
AZURE_USE_AD=true
```
- Set to `true` if Local Authentication is disabled
- Uses your Azure AD credentials automatically

**`OCR_MODE`** (for development)
```
OCR_MODE=mock    # Use fake data (no Azure needed)
OCR_MODE=azure   # Use real Azure Computer Vision
```

### Caching & Search

**Redis (distributed cache, optional):**
```
REDIS_URL=redis://localhost:6379
# With password
REDIS_URL=redis://:password@localhost:6379
# TLS (production)
REDIS_URL=rediss://localhost:6380
```
- Default: Local file-based cache (no setup required)
- Enables multi-process caching
- Set up: `docker run -d -p 6379:6379 redis:latest`

**Qdrant (vector search, optional):**
```
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-api-key  # If using Qdrant Cloud
```
- Default: In-memory search
- Set up local: `docker run -d -p 6333:6333 qdrant/qdrant`
- Set up cloud: https://cloud.qdrant.io/

### Monitoring & Observability

**Weights & Biases (W&B):**
```
WANDB_API_KEY=your-wandb-key
WANDB_PROJECT=my-project-name
```
- Optional for production monitoring
- Get key from https://wandb.ai/
- Tracks costs, latency, token usage

**Prometheus Metrics (optional):**
```
ANALYTICS_BACKEND=prometheus
PROMETHEUS_PUSH_GATEWAY=http://localhost:9091
```
- For self-hosted monitoring
- Set up: Docker + Grafana

**OpenTelemetry (optional):**
```
ANALYTICS_BACKEND=otlp
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-grafana-cloud-endpoint
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer%20your-token
```
- For Grafana Cloud observability

### Logging

**`TOOLWEAVER_LOG_LEVEL`** (optional)
```
TOOLWEAVER_LOG_LEVEL=INFO
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```
- Default: `INFO`
- Use `DEBUG` for troubleshooting

**`TOOLWEAVER_LOG_FILE`** (optional)
```
TOOLWEAVER_LOG_FILE=/var/log/toolweaver.log
```
- Write logs to file instead of console

### Paths & Storage

**`TOOLWEAVER_CACHE_PATH`** (optional)
```
TOOLWEAVER_CACHE_PATH=~/.toolweaver/cache
```
- Local cache directory
- Default: `~/.toolweaver/cache`

**`TOOLWEAVER_SKILL_PATH`** (optional)
```
TOOLWEAVER_SKILL_PATH=~/.toolweaver/skills
```
- Where skills are installed
- Default: `~/.toolweaver/skills`

## Example Configurations

### Minimal (Local Development)
```bash
# .env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### Standard (Development with Monitoring)
```bash
# .env
# LLM
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Optional: OCR
AZURE_CV_ENDPOINT=https://your-cv-resource.cognitiveservices.azure.com/
AZURE_CV_KEY=your-cv-key
OCR_MODE=azure

# Optional: Monitoring
WANDB_API_KEY=your-wandb-key
WANDB_PROJECT=my-project

# Logging
TOOLWEAVER_LOG_LEVEL=INFO
```

### Production (Fully Configured)
```bash
# .env
# LLM
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# OCR
AZURE_CV_ENDPOINT=https://your-cv-resource.cognitiveservices.azure.com/
AZURE_CV_KEY=your-cv-key
AZURE_USE_AD=true

# Caching
REDIS_URL=rediss://prod-user:password@redis.production.com:6380

# Vector Search
QDRANT_URL=https://cluster.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-key

# Monitoring
WANDB_API_KEY=your-wandb-key
WANDB_PROJECT=production

ANALYTICS_BACKEND=otlp
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-grafana-cloud-endpoint
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer%20your-token

# Logging
TOOLWEAVER_LOG_LEVEL=WARNING
TOOLWEAVER_LOG_FILE=/var/log/toolweaver.log

# Paths
TOOLWEAVER_CACHE_PATH=/var/cache/toolweaver
TOOLWEAVER_SKILL_PATH=/opt/toolweaver/skills
```

## Platform-Specific Notes

### Windows

**Path format:**
```dotenv
# Use forward slashes or double backslashes
TOOLWEAVER_CACHE_PATH=/Users/username/.toolweaver/cache
# or
TOOLWEAVER_CACHE_PATH=C:\\Users\\username\\.toolweaver\\cache
```

**Setting in PowerShell:**
```powershell
$env:AZURE_OPENAI_KEY = "your-key-with-special-chars!@#"  # Quotes handle special chars
```

### macOS/Linux

**Path format:**
```dotenv
# Use standard forward slashes
TOOLWEAVER_CACHE_PATH=~/.toolweaver/cache
# or
TOOLWEAVER_CACHE_PATH=/home/username/.toolweaver/cache
```

**Setting in Bash:**
```bash
export AZURE_OPENAI_KEY='your-key-with-$pecial-chars'  # Single quotes prevent expansion
```

## Security Best Practices

1. **Never commit `.env` to git**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use `.env.example` for non-secret config**
   ```bash
   # .env.example (committed to git)
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_KEY=YOUR_KEY_HERE  # Users fill in actual values
   ```

3. **Protect your .env file**
   ```bash
   chmod 600 .env  # Only owner can read (Linux/macOS)
   ```

4. **Use Azure Key Vault in production**
   ```python
   from azure.identity import DefaultAzureCredential
   from azure.keyvault.secrets import SecretClient
   
   credential = DefaultAzureCredential()
   client = SecretClient(vault_url="https://your-keyvault.vault.azure.com/", credential=credential)
   secret = client.get_secret("AZURE_OPENAI_KEY")
   ```

5. **Rotate keys regularly**
   - Change keys quarterly
   - Disable old keys immediately after rotation

## Verification

Test your configuration:

```bash
# Windows
.\.venv\Scripts\Activate.ps1
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(f'API Key set: {bool(os.getenv(\"AZURE_OPENAI_KEY\"))}')"

# macOS/Linux
source .venv/bin/activate
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(f'API Key set: {bool(os.getenv(\"AZURE_OPENAI_KEY\"))}')"
```

Expected output:
```
API Key set: True
```

## Troubleshooting

### Variables Not Loading

**Problem:** `.env` variables not being used

**Solution:**
```python
from dotenv import load_dotenv
import os

# Explicit load
load_dotenv()  # Loads from .env in current directory
load_dotenv('path/to/.env')  # Loads from specific path

# Verify
print(os.getenv('AZURE_OPENAI_KEY'))  # Should show your key
```

### Special Characters in Keys

**Problem:** Keys with `$`, `!`, `&` etc. cause issues

**Solution:** Use quotes in `.env`:
```dotenv
# ✅ Works
API_KEY="your-key-with-$pecial-chars"

# ❌ May fail
API_KEY=your-key-with-$pecial-chars
```

### Docker Environment Variables

**Pass variables to container:**
```bash
docker run --env-file .env mycontainer
docker run -e AZURE_OPENAI_KEY="value" mycontainer
```

### Azure Authentication Issues

**Problem:** "Unauthorized" or "Authentication failed"

**Solution:**
1. Verify key/endpoint in Azure Portal
2. Check key hasn't expired or been disabled
3. Verify deployment name matches your model
4. Check API version compatibility

```python
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

# Using Azure AD instead of keys
client = AzureOpenAI(
    api_version="2024-08-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    credential=DefaultAzureCredential()
)
```

## See Also

- [CROSS_PLATFORM_SETUP.md](CROSS_PLATFORM_SETUP.md) - Full setup guide for all platforms
- [Azure Setup Guide](../docs/deployment/azure-setup.md) - Detailed Azure configuration
- [Redis Setup Guide](../docs/deployment/redis-setup.md) - Caching configuration
- [Monitoring Setup](../docs/deployment/sqlite-grafana-setup.md) - Observability configuration

---

**Last Updated:** January 2, 2026
