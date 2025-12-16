# Example 3: GitHub Operations with MCP

## What This Does

Connects to GitHub's remote MCP server to perform repository operations:
- List repository files
- Create issues
- Create pull requests
- Search code

**Complexity:** ⭐⭐⭐ Advanced  
**Concepts:** Remote MCP servers, GitHub integration, external APIs  
**Time:** 15 minutes

## What You'll Learn

- Connecting to GitHub's hosted MCP server
- Using remote MCP tools (36+ GitHub operations)
- Server-Sent Events (SSE) protocol
- Token-based authentication

## Prerequisites

- GitHub account
- Personal Access Token with scopes: `repo`, `read:org`, `workflow`

## Setup

1. **Create GitHub Token:**
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `read:org`, `workflow`, `read:user`
   - Copy token

2. **Configure environment:**
```bash
cp .env ../../.env
# Edit ../../.env and add:
#   GITHUB_TOKEN=ghp_your_token_here
#   GITHUB_OWNER=your-github-username
```

3. **Install ToolWeaver:**
```bash
pip install -e ../..
```

## Run

```bash
# Test connection
python test_connection.py

# List repository files
python list_repo_files.py owner/repo

# Create an issue
python create_issue.py

# Search code
python search_code.py "def main" owner/repo
```

## Available Operations

GitHub MCP provides 36+ tools organized in toolsets:

| Toolset | Tools |
|---------|-------|
| **repos** | get_file_contents, create_branch, create_or_update_file, list_commits |
| **issues** | create_issue, add_issue_comment, list_issues |
| **pull_requests** | create_pull_request, add_comment_to_pending_review |
| **actions** | list_workflows, trigger_workflow |
| **code_security** | list_code_scanning_alerts |

## Example Output

**List Files:**
```json
{
  "files": [
    {"name": "README.md", "type": "file", "size": 1024},
    {"name": "src/", "type": "dir"},
    {"name": "tests/", "type": "dir"}
  ]
}
```

**Create Issue:**
```json
{
  "number": 42,
  "title": "Feature: Add monitoring",
  "url": "https://github.com/owner/repo/issues/42"
}
```

## What's Happening

1. **Authentication** - Token-based auth with GitHub API
2. **MCP Connection** - HTTPS connection to `api.githubcopilot.com/mcp/`
3. **SSE Protocol** - Server-Sent Events for streaming responses
4. **Tool Execution** - Remote execution on GitHub's infrastructure

## Security Notes

- ✅ Token stored in `.env` (gitignored)
- ✅ Read-only mode available (`GITHUB_MCP_READONLY=true`)
- ✅ Fine-grained token scopes
- ⚠️ Never commit tokens to git

## Next Steps

- Automate repository workflows
- Build CI/CD integrations
- Create automated issue management
- Explore [GitHub MCP docs](https://github.com/github/github-mcp-server)
