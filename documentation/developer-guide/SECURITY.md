# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please email [your-email@example.com] or create a private security advisory on GitHub.

**Please do NOT create a public issue for security vulnerabilities.**

## Security Best Practices

### 1. Never Commit Secrets
- ✅ Use `.env` files for all API keys and secrets (already in `.gitignore`)
- ✅ Use Azure AD authentication when possible (no keys to manage)
- ✅ Rotate API keys regularly

### 2. Environment Variables
The following should NEVER be committed:
- `AZURE_OPENAI_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `AZURE_CV_KEY`
- Any `*_API_KEY` or `*_SECRET`

### 3. Azure AD Authentication (Recommended)
When using Azure services, prefer Azure AD over API keys:
```bash
# .env
AZURE_OPENAI_USE_AD=true
AZURE_CV_USE_AD=true
```

Then authenticate with:
```bash
az login
```

### 4. Code Execution Sandbox
This project includes sandboxed code execution. Security measures:
- ✅ Restricted builtins (no `open`, `eval`, `exec`, `__import__`)
- ✅ Process isolation with multiprocessing
- ✅ Timeout limits
- ⚠️ Still recommend running in isolated environments for production

### 5. Production Deployment
- Use managed identities instead of API keys
- Enable Azure Key Vault for secrets management
- Run code execution in isolated containers
- Implement rate limiting
- Monitor for unusual API usage

## Known Limitations

1. **Code Execution**: Sandboxed but not cryptographically secure. Use containers in production.
2. **API Costs**: No built-in rate limiting. Monitor usage to prevent unexpected costs.
3. **Model Hallucinations**: LLM-generated plans should be validated before execution.

## Updates

Security-related updates will be documented in release notes.
