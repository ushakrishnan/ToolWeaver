# 34 – GitHub MCP Server

A FastAPI-based MCP server that exposes GitHub REST API operations as MCP tools. Demonstrates real-world MCP integration with a production API.

## Features

Implements 5 GitHub tools via MCP protocol:
- `list_repos` - List repositories for a user/org
- `get_repo` - Get detailed repository information
- `list_issues` - List issues for a repository
- `create_issue` - Create a new issue
- `search_code` - Search code across GitHub

## Prerequisites

### 1. Install ToolWeaver and deps

```powershell
# Option A: Use published package
pip install toolweaver

# Option B: Local dev (editable)
python -m pip install -e .

# Sample-specific deps
pip install -r samples/34-github-mcp-server/requirements.txt
```

### 2. Get a GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)" or "Generate new token (fine-grained)"
3. Required scopes: `repo`, `read:user`, `read:org`
4. Copy the token (starts with `ghp_`)

### 3. Set Up Token - Choose One Method

**Method A: .env file (Recommended)**
```powershell
# From repo root
echo 'GITHUB_TOKEN=ghp_your_token_here' > samples/34-github-mcp-server/.env
```

**Method B: Environment variable (Current session)**
```powershell
$env:GITHUB_TOKEN = "ghp_your_token_here"
python samples/34-github-mcp-server/server.py
```

**Method C: Environment variable (Permanent - Windows)**
```powershell
# PowerShell as Admin
[Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "ghp_...", "User")
```

**Method D: Home directory .env**
```powershell
echo 'GITHUB_TOKEN=ghp_your_token_here' > ~/.github_mcp.env
```

### 4. Verify Token Works

Before starting the server, test your token:
```powershell
$headers = @{'Authorization' = "Bearer ghp_your_token"}
Invoke-WebRequest -Uri "https://api.github.com/user" -Headers $headers -UseBasicParsing
```

If successful, you'll see your GitHub user info.

## Usage

### Start the MCP Server

The server auto-loads token from multiple locations (in order):
1. `samples/34-github-mcp-server/.env` (script directory)
2. `.env` (current working directory)
3. `~/.github_mcp.env` (home directory)
4. `GITHUB_TOKEN` environment variable

```powershell
# Start from repo root
python samples/34-github-mcp-server/server.py
```

You should see:
```
============================================================
GitHub MCP Server
============================================================
Available tools: 5
  - list_repos
  - get_repo
  - list_issues
  - create_issue
  - search_code

Endpoints:
  GET  http://localhost:9877/tools
  POST http://localhost:9877/execute

Docs: http://localhost:9877/docs
============================================================
```

If you see an error like `GITHUB_TOKEN environment variable is required!`, follow the Prerequisites section above to set up your token.

### Test with Sample 33

Update `samples/33-mcp-json-config/servers.json`:
```json
{
  "mcpServers": {
    "github": {
      "url": "http://localhost:9877",
      "protocol": "http"
    }
  }
}
```

Run discovery:
```powershell
python samples/33-mcp-json-config/run_mcp_json_demo.py --fetch
```

### Direct API Test

```powershell
# List tools
curl http://localhost:9877/tools

# Execute a tool
curl -X POST http://localhost:9877/execute `
  -H "Content-Type: application/json" `
  -d '{"name":"list_repos","params":{"per_page":5}}'
```

## Tool Examples

### List Your Repos
```json
{
  "name": "list_repos",
  "params": {
    "type": "owner",
    "per_page": 10
  }
}
```

### Get Repository Info
```json
{
  "name": "get_repo",
  "params": {
    "owner": "ushakrishnan",
    "repo": "ToolWeaver"
  }
}
```

### List Issues
```json
{
  "name": "list_issues",
  "params": {
    "owner": "microsoft",
    "repo": "vscode",
    "state": "open",
    "per_page": 5
  }
}
```

### Search Code
```json
{
  "name": "search_code",
  "params": {
    "query": "fastapi router language:python"
  }
}
```

## Architecture

```
┌─────────────────────┐
│ ToolWeaver Sample   │
│ (MCP JSON Config)   │
└──────────┬──────────┘
           │ HTTP MCP Protocol
           │ GET /tools
           │ POST /execute
           ▼
┌─────────────────────┐
│ GitHub MCP Server   │
│ (FastAPI)           │
└──────────┬──────────┘
           │ GitHub REST API
           │ (httpx + token)
           ▼
┌─────────────────────┐
│ api.github.com      │
└─────────────────────┘
```

## Security & Auth Best Practices

### Token Security
- ✓ Token loaded from environment/file, never hardcoded in code
- ✓ Token validated on server startup, fails early if missing
- ✓ Token never logged or exposed in responses
- ⚠️ **Don't commit `.env` files to git** - add to `.gitignore`
- ⚠️ Never share tokens in chat or version control
- ⚠️ Regenerate token if accidentally exposed

### How Auth Works

1. **Startup**: Server loads `GITHUB_TOKEN` from multiple locations, fails if not found
2. **Request**: MCP client (sample 33) sends requests to `POST /execute`
3. **Headers**: Server adds `Authorization: Bearer {token}` to all GitHub API calls
4. **Response**: Server returns results or auth error with guidance

### Troubleshooting Auth

**Problem: Server won't start - "GITHUB_TOKEN environment variable is required!"**
```
Solution:
  1. Check token is set: echo $env:GITHUB_TOKEN
  2. Create .env file: echo 'GITHUB_TOKEN=ghp_...' > samples/34-github-mcp-server/.env
  3. Verify token format (starts with ghp_)
```

**Problem: 401 Unauthorized when calling tools**
```
Error: "GitHub authentication failed. Token may be invalid or expired."
Solution:
  1. Verify token is valid: Invoke-WebRequest -Uri https://api.github.com/user -Headers @{Authorization="Bearer ghp_..."} -UseBasicParsing
  2. Check token hasn't expired at https://github.com/settings/tokens
  3. Regenerate token if needed
  4. Ensure token has repo, read:user, read:org scopes
```

**Problem: 403 Forbidden**
```
Error: "GitHub rate limit exceeded or insufficient permissions."
Solution:
  1. Check rate limit: curl -H "Authorization: Bearer TOKEN" https://api.github.com/rate_limit
  2. Wait for rate limit reset (typically 1 hour)
  3. Verify token scopes: https://github.com/settings/tokens
```

### Headers Being Sent

Every request to GitHub includes:
```python
{
    "Authorization": "Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
```

This ensures:
- ✓ Authentication with your token
- ✓ Latest GitHub API format
- ✓ Correct versioning

## Next Steps

- Add more GitHub tools (PRs, commits, workflows)
- Add error handling and rate limit detection
- Implement pagination for large result sets
- Add caching for frequently accessed data
