# Installation

## Requirements
- Python 3.10+
- Optional: Redis for distributed cache (fallback file cache included)

## Platform-Specific Setup

For detailed setup instructions for your platform, see:
- **Windows, macOS, Linux:** [Cross-Platform Setup Guide](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/CROSS_PLATFORM_SETUP.md)
- **All Environment Variables:** [Configuration Reference](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/ENV_CONFIGURATION.md)
- **Verify Setup:** Run `python samples/verify_cross_platform.py` after installation

## Install from PyPI
```bash
pip install toolweaver
```

## Optional extras (choose what you need)
Use extras to pull in integrations without bloating installs.

| Extra | Includes | When to use | Why |
|-------|----------|-------------|-----|
| `toolweaver[azure]` | Azure AI Vision, Identity | Using Azure Computer Vision tools | Azure CV SDK for image analysis |
| `toolweaver[openai]` | OpenAI Python SDK | Using OpenAI models | GPT-4, ChatGPT API access |
| `toolweaver[anthropic]` | Anthropic SDK | Using Claude models | Claude 3, 3.5 API access |
| `toolweaver[redis]` | Redis client deps | You have Redis for distributed cache | Faster shared caching vs file cache |
| `toolweaver[vector-db]` | Qdrant client deps | You use semantic search/vector DB | Better tool retrieval at scale |
| `toolweaver[monitoring]` | WandB, Prometheus deps | You need metrics/export | Observability for prod |
| `toolweaver[all]` | All above | You want everything preinstalled | One-shot setup |

Examples:
```bash
pip install toolweaver[openai]              # Just OpenAI
pip install toolweaver[azure,anthropic]     # Multiple providers
pip install toolweaver[all]                 # Everything
```

Env hints
- Azure: `AZURE_CV_ENDPOINT=...`, `AZURE_CV_KEY=...`
- OpenAI: `OPENAI_API_KEY=...`
- Anthropic: `ANTHROPIC_API_KEY=...`
- Redis: `REDIS_URL=redis://...` (or `rediss://` for TLS)
- Vector/Qdrant: `QDRANT_URL=...`, `QDRANT_API_KEY=...`
- Metrics: `ANALYTICS_BACKEND=prometheus|otlp|sqlite`, plus backend-specific envs

## Verify
```bash
python - <<"PY"
from orchestrator import get_available_tools
print("Tools loaded:", len(get_available_tools()))
PY
```
