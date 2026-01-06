# Why Auth Works Now - Technical Explanation

## The Problem We Solved

### Original Issue: Token Not Found
When the server started, it couldn't find `GITHUB_TOKEN` because:

1. **Directory context**: `load_dotenv()` looks in current working directory
2. **Server started from root**: But token was in `samples/34-github-mcp-server/.env`
3. **No explicit path**: Server didn't tell dotenv where to look
4. **Silent failure**: If token missing, server didn't fail until first GitHub API call

### Symptoms
```
401 Unauthorized from GitHub API
→ No clear "token missing" error
→ Confusing debugging experience
```

## The Solution: Multi-Path Env Loading

### How It Works Now

When the server starts, it looks for `.env` in order:

```python
env_paths = [
    ".env",                              # Current working directory
    os.path.join(os.path.dirname(__file__), ".env"),  # Script directory
    os.path.join(os.getcwd(), ".env"),   # Working directory again
    os.path.expanduser("~/.github_mcp.env"),  # Home directory
]
```

**Example**: If you run from repo root:
```powershell
cd C:\ushak-projects\ToolWeaver
python samples/34-github-mcp-server/server.py

# Server finds token at:
# samples/34-github-mcp-server/.env ✓ FOUND HERE
```

### Early Failure Detection

```python
if not GITHUB_TOKEN:
    error_msg = (
        "❌ GITHUB_TOKEN environment variable is required!\n\n"
        "Set it one of these ways:\n"
        "  1. Create .env file in the sample directory...\n"
        ...
    )
    print(error_msg)
    raise RuntimeError(...)  # ← FAILS HERE, not later
```

**Result**: Clear error message before server starts!

## How Headers Are Sent

Every GitHub API call includes:

```python
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",     # ← Your token
    "Accept": "application/vnd.github+json",       # ← GitHub API format
    "X-GitHub-Api-Version": "2022-11-28",         # ← API version
}
```

### Example Request Flow

```
User calls: list_repos
        ↓
Sample 33 sends: POST /execute {name: "list_repos", params: {...}}
        ↓
GitHub MCP Server validates token (first check)
        ↓
Server calls: GET https://api.github.com/user/repos
              Headers: {Authorization: "Bearer ghp_ZKNln..."}
        ↓
GitHub validates token
        ↓
Return: Your repos data ✓
```

## Token Scope Requirements

Your token needs these scopes for the tools to work:

| Scope | Used By | Permissions |
|-------|---------|------------|
| `repo` | All tools | Full control of public & private repos |
| `read:user` | list_repos, get_repo | Read user profile |
| `read:org` | list_repos | Read organization info |

Check your token scopes at: https://github.com/settings/tokens

## Validation Layers

The server now has multiple validation points:

```
Layer 1: Startup
├─ Check GITHUB_TOKEN env var exists
├─ Check token format (should start with "ghp_")
└─ Fail if missing → Print helpful instructions

Layer 2: Endpoint Request
├─ Validate token before each /execute call
└─ Return 401 if missing with guidance

Layer 3: GitHub API Call
├─ Send Authorization header with token
├─ GitHub validates token signature
└─ Return 401/403 with specific error if invalid

Layer 4: Error Response
├─ Catch httpx.HTTPStatusError
├─ Check status code (401 = auth failed, 403 = rate limit)
└─ Return helpful error message to caller
```

## Why This Pattern Works

### ✓ Environment Loading
- Multiple path search ensures token is found
- Doesn't require specific working directory
- User-friendly error messages

### ✓ Header Management  
- Headers applied to every request automatically
- User doesn't need to worry about Bearer prefix
- Consistent across all GitHub API calls

### ✓ Error Handling
- Early failure at startup (not runtime)
- Clear, actionable error messages
- Specific HTTP status codes for debugging

### ✓ Security
- Token never logged (only first 20 chars shown)
- Token never hardcoded in code
- Token loaded from env, not config files
- Supports secure token storage methods

## Best Practices Applied

| Practice | Implementation |
|----------|-----------------|
| **Fail Fast** | Validate token on startup |
| **Explicit Errors** | Show exactly what's needed |
| **Multiple Sources** | Check .env, env vars, home dir |
| **Centralized Auth** | All headers in one place |
| **Consistent Headers** | Same headers for every call |
| **Error Context** | Status codes + helpful messages |

## Testing Auth

### Verify Token Works

```powershell
$headers = @{'Authorization' = "Bearer ghp_..."}
Invoke-WebRequest -Uri "https://api.github.com/user" `
    -Headers $headers -UseBasicParsing
```

### Test Server Token Loading

```powershell
# Check if token loads successfully
python samples/34-github-mcp-server/server.py
# Should print: [OK] GitHub token loaded: ghp_...
```

### Test Tool Execution

```powershell
# Execute a tool (will fail if token invalid)
$body = @{name='get_repo'; params=@{owner='ushakrishnan'; repo='ToolWeaver'}} | ConvertTo-Json
Invoke-WebRequest -Uri 'http://localhost:9877/execute' `
    -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing
```

## Debugging Checklist

When auth fails, check:

- [ ] Token exists: `echo $env:GITHUB_TOKEN`
- [ ] Token format: Starts with `ghp_`
- [ ] Token valid: Test at https://api.github.com
- [ ] Server started: Check port 9877
- [ ] Token has scopes: repo, read:user, read:org
- [ ] Not rate limited: Check GitHub rate limit status
- [ ] .env file readable: Check file permissions
