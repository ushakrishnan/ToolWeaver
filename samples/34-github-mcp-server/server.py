"""
GitHub MCP Server - Exposes GitHub REST API as MCP tools.

Implements the MCP protocol (HTTP endpoints) to provide GitHub operations
as discoverable tools that can be called via ToolWeaver's MCP adapters.

Start: python server.py
Test: python samples/33-mcp-json-config/run_mcp_json_demo.py --fetch
"""

import os
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load env from multiple possible locations
env_paths = [
    ".env",  # Current directory
    os.path.join(os.path.dirname(__file__), ".env"),  # Script directory
    os.path.join(os.getcwd(), ".env"),  # Working directory
    os.path.expanduser("~/.github_mcp.env"),  # Home directory
]

for env_path in env_paths:
    if os.path.exists(env_path):
        print(f"Loading .env from: {env_path}")
        load_dotenv(env_path)
        break
else:
    print("No .env file found, relying on environment variables")
    load_dotenv()  # Load from current environment

app = FastAPI(title="GitHub MCP Server")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    error_msg = (
        "❌ GITHUB_TOKEN environment variable is required!\n\n"
        "Set it one of these ways:\n"
        "  1. Create .env file in the sample directory:\n"
        "     echo GITHUB_TOKEN=ghp_... > samples/34-github-mcp-server/.env\n"
        "  2. Set environment variable:\n"
        "     $env:GITHUB_TOKEN = 'ghp_...'\n"
        "  3. Create ~/.github_mcp.env with your token\n\n"
        "Get a token from: https://github.com/settings/tokens\n"
        "Required scopes: repo, read:user, read:org"
    )
    print(error_msg)
    raise RuntimeError("GITHUB_TOKEN environment variable is required")

print(f"\n[OK] GitHub token loaded: {GITHUB_TOKEN[:20]}...")
print("[OK] Starting GitHub MCP Server on http://localhost:9877")

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


# MCP Tool Definitions (ToolWeaver ToolDefinition format)
TOOLS = [
    {
        "name": "list_repos",
        "type": "mcp",
        "description": "List repositories for the authenticated user or a specified user/org",
        "provider": "github",
        "parameters": [
            {
                "name": "username",
                "type": "string",
                "description": "GitHub username or org (optional, defaults to authenticated user)",
                "required": False,
            },
            {
                "name": "type",
                "type": "string",
                "description": "Type of repos to list",
                "required": False,
                "enum": ["all", "owner", "member"],
            },
            {
                "name": "per_page",
                "type": "integer",
                "description": "Results per page (max 100)",
                "required": False,
                "default": 30,
            },
        ],
    },
    {
        "name": "get_repo",
        "type": "mcp",
        "description": "Get detailed information about a specific repository",
        "provider": "github",
        "parameters": [
            {"name": "owner", "type": "string", "description": "Repository owner", "required": True},
            {"name": "repo", "type": "string", "description": "Repository name", "required": True},
        ],
    },
    {
        "name": "list_issues",
        "type": "mcp",
        "description": "List issues for a repository",
        "provider": "github",
        "parameters": [
            {"name": "owner", "type": "string", "description": "Repository owner", "required": True},
            {"name": "repo", "type": "string", "description": "Repository name", "required": True},
            {
                "name": "state",
                "type": "string",
                "description": "Issue state filter",
                "required": False,
                "enum": ["open", "closed", "all"],
                "default": "open",
            },
            {"name": "per_page", "type": "integer", "description": "Results per page", "required": False, "default": 30},
        ],
    },
    {
        "name": "create_issue",
        "type": "mcp",
        "description": "Create a new issue in a repository",
        "provider": "github",
        "parameters": [
            {"name": "owner", "type": "string", "description": "Repository owner", "required": True},
            {"name": "repo", "type": "string", "description": "Repository name", "required": True},
            {"name": "title", "type": "string", "description": "Issue title", "required": True},
            {"name": "body", "type": "string", "description": "Issue body (optional)", "required": False},
            {
                "name": "labels",
                "type": "array",
                "description": "Labels to apply",
                "required": False,
                "items": {"type": "string"},
            },
        ],
    },
    {
        "name": "search_code",
        "type": "mcp",
        "description": "Search for code across GitHub repositories",
        "provider": "github",
        "parameters": [
            {"name": "query", "type": "string", "description": "Search query", "required": True},
            {"name": "per_page", "type": "integer", "description": "Results per page", "required": False, "default": 30},
        ],
    },
]


class ExecuteRequest(BaseModel):
    name: str
    params: dict[str, Any]


@app.get("/")
async def root():
    return {
        "service": "GitHub MCP Server",
        "version": "1.0.0",
        "tools": len(TOOLS),
    }


@app.get("/tools")
async def get_tools():
    """MCP discovery endpoint - returns available tools."""
    return TOOLS


@app.post("/execute")
async def execute_tool(request: ExecuteRequest):
    """MCP execution endpoint - executes a tool by name."""
    tool_name = request.name
    params = request.params

    # Validate auth before attempting tool execution
    if not GITHUB_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="GitHub token not configured. Set GITHUB_TOKEN environment variable."
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if tool_name == "list_repos":
                return await _list_repos(client, params)
            elif tool_name == "get_repo":
                return await _get_repo(client, params)
            elif tool_name == "list_issues":
                return await _list_issues(client, params)
            elif tool_name == "create_issue":
                return await _create_issue(client, params)
            elif tool_name == "search_code":
                return await _search_code(client, params)
            else:
                raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail=f"GitHub authentication failed. Token may be invalid or expired. Response: {e.response.text}"
                ) from e
            elif e.response.status_code == 403:
                raise HTTPException(
                    status_code=403,
                    detail="GitHub rate limit exceeded or insufficient permissions. Required scopes: repo, read:user, read:org"
                ) from e
            raise HTTPException(status_code=e.response.status_code, detail=str(e)) from e


async def _list_repos(client: httpx.AsyncClient, params: dict[str, Any]):
    username = params.get("username")
    repo_type = params.get("type", "all")
    per_page = params.get("per_page", 30)

    if username:
        url = f"{GITHUB_API}/users/{username}/repos"
    else:
        url = f"{GITHUB_API}/user/repos"

    resp = await client.get(
        url,
        headers=HEADERS,
        params={"type": repo_type, "per_page": per_page, "sort": "updated"},
    )
    resp.raise_for_status()
    repos = resp.json()

    return {
        "count": len(repos),
        "repos": [
            {
                "name": r["name"],
                "full_name": r["full_name"],
                "description": r.get("description"),
                "url": r["html_url"],
                "stars": r["stargazers_count"],
                "language": r.get("language"),
            }
            for r in repos
        ],
    }


async def _get_repo(client: httpx.AsyncClient, params: dict[str, Any]):
    owner = params["owner"]
    repo = params["repo"]
    url = f"{GITHUB_API}/repos/{owner}/{repo}"

    resp = await client.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()

    return {
        "name": data["name"],
        "full_name": data["full_name"],
        "description": data.get("description"),
        "url": data["html_url"],
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "language": data.get("language"),
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
    }


async def _list_issues(client: httpx.AsyncClient, params: dict[str, Any]):
    owner = params["owner"]
    repo = params["repo"]
    state = params.get("state", "open")
    per_page = params.get("per_page", 30)

    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    resp = await client.get(
        url,
        headers=HEADERS,
        params={"state": state, "per_page": per_page},
    )
    resp.raise_for_status()
    issues = resp.json()

    return {
        "count": len(issues),
        "issues": [
            {
                "number": i["number"],
                "title": i["title"],
                "state": i["state"],
                "url": i["html_url"],
                "created_at": i["created_at"],
                "user": i["user"]["login"],
            }
            for i in issues
        ],
    }


async def _create_issue(client: httpx.AsyncClient, params: dict[str, Any]):
    owner = params["owner"]
    repo = params["repo"]
    title = params["title"]
    body = params.get("body", "")
    labels = params.get("labels", [])

    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    resp = await client.post(
        url,
        headers=HEADERS,
        json={"title": title, "body": body, "labels": labels},
    )
    resp.raise_for_status()
    issue = resp.json()

    return {
        "number": issue["number"],
        "title": issue["title"],
        "url": issue["html_url"],
        "state": issue["state"],
    }


async def _search_code(client: httpx.AsyncClient, params: dict[str, Any]):
    query = params["query"]
    per_page = params.get("per_page", 30)

    url = f"{GITHUB_API}/search/code"
    resp = await client.get(
        url,
        headers=HEADERS,
        params={"q": query, "per_page": per_page},
    )
    resp.raise_for_status()
    data = resp.json()

    return {
        "total_count": data["total_count"],
        "items": [
            {
                "name": item["name"],
                "path": item["path"],
                "repo": item["repository"]["full_name"],
                "url": item["html_url"],
            }
            for item in data["items"]
        ],
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("GitHub MCP Server")
    print("="*60)
    print(f"Available tools: {len(TOOLS)}")
    for tool in TOOLS:
        print(f"  - {tool['name']}")
    print("\nEndpoints:")
    print("  GET  http://localhost:9877/tools")
    print("  POST http://localhost:9877/execute")
    print("\nDocs: http://localhost:9877/docs")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=9877, log_level="info")
