# Example 03: GitHub Operations with ToolWeaver

Demonstrates integrating external APIs (GitHub) through the ToolWeaver tool system.

## Features

- External API tool registration
- Repository search and filtering
- Repository statistics analysis
- Multi-step tool orchestration
- Mock implementation (no credentials needed)

## What You'll Learn

1. **Registering External Tools** - How to wrap external APIs as ToolWeaver tools
2. **API Integration** - Calling multiple tools in sequence
3. **Tool Discovery** - Finding and inspecting available tools
4. **Data Analysis** - Aggregating data from multiple tool calls

## Files

- `github_ops.py` - Main example demonstrating GitHub operations
- `requirements.txt` - Python dependencies
- `.env` - Environment configuration (optional)

## Running

```bash
python github_ops.py
```

**Output:**
```
EXAMPLE 03: GitHub Operations

Step 1: Listing repositories...
   Found 5 repositories:
      • ToolWeaver           ( 1200 stars) - Python
      • MCP-Server           (  850 stars) - TypeScript
      • AI-Agents            (  600 stars) - Python
      • Cloud-SDK            (  450 stars) - Go
      • Data-Pipeline        (  320 stars) - Python

Step 2: Getting details for ToolWeaver repository...
   Stars: 1200, Forks: 180, Issues: 23, PRs: 5

Step 3: Searching for Python repositories...
   Found 3 Python repositories

Step 4: Analyzing repository statistics...
   Total repositories: 5
   Total stars: 3420
   Average stars: 684

Step 5: Discovering all GitHub tools...
   Found 4 GitHub tools
```

## Key Concepts

### Tool Registration
```python
@mcp_tool(domain="github", description="List repositories for an organization")
async def list_repositories(org: str, limit: int = 10) -> dict:
    # Integrate with external API
    return {"repositories": [...]}
```

### Tool Calling
```python
result = await list_repositories({"org": "ushakrishnan", "limit": 5})
```

### Tool Discovery
```python
tools = search_tools(domain="github")
for tool in tools:
    print(f"{tool.name} - {tool.description}")
```

## Real-World Usage

This pattern works with:
- GitHub API (with actual tokens)
- Slack, Discord, Teams APIs
- Cloud provider APIs (AWS, Azure, GCP)
- Internal APIs and databases
- Third-party services

## Learning Path

- **Previous:** Example 02 - Receipt categorization (tool chaining)
- **Next:** Example 04 - Vector search discovery (advanced search)
- **Advanced:** Example 13 - Complete pipeline (production patterns)

## Complexity

- **Difficulty:** ⭐⭐ Intermediate
- **Concepts:** External APIs, tool registration, discovery
- **Time:** 10 minutes
