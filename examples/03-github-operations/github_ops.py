"""
Example 03: GitHub Operations with ToolWeaver

Demonstrates:
- External API integration with tools
- GitHub repository operations
- Search and filter patterns
- Mock implementation (no credentials needed)

Use Case:
Automate GitHub tasks through a unified tool interface
"""

import asyncio
from pathlib import Path
import sys
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator import mcp_tool, search_tools, get_available_tools


# ============================================================
# GitHub Tools - Demonstrate API Integration Pattern
# ============================================================

@mcp_tool(domain="github", description="List repositories for an organization")
async def list_repositories(org: str, limit: int = 10) -> dict:
    """List repositories from a GitHub organization."""
    # Mock data - in real usage, would call GitHub API
    mock_repos = [
        {"name": "ToolWeaver", "stars": 1200, "language": "Python", "description": "AI orchestrator"},
        {"name": "MCP-Server", "stars": 850, "language": "TypeScript", "description": "Model Context Protocol"},
        {"name": "AI-Agents", "stars": 600, "language": "Python", "description": "Agent framework"},
        {"name": "Cloud-SDK", "stars": 450, "language": "Go", "description": "Cloud utilities"},
        {"name": "Data-Pipeline", "stars": 320, "language": "Python", "description": "ETL framework"},
    ]
    
    return {
        "organization": org,
        "repositories": mock_repos[:limit],
        "total_count": len(mock_repos),
        "count": min(limit, len(mock_repos))
    }


@mcp_tool(domain="github", description="Get repository details and statistics")
async def get_repository_info(org: str, repo: str) -> dict:
    """Get detailed information about a repository."""
    repos = {
        "ToolWeaver": {
            "stars": 1200,
            "forks": 180,
            "issues": 23,
            "prs": 5,
            "language": "Python",
            "license": "Apache 2.0",
            "description": "Production-ready AI orchestrator"
        },
        "MCP-Server": {
            "stars": 850,
            "forks": 120,
            "issues": 15,
            "prs": 8,
            "language": "TypeScript",
            "license": "MIT",
            "description": "Model Context Protocol implementation"
        }
    }
    
    repo_data = repos.get(repo, {})
    if not repo_data:
        return {"error": f"Repository {repo} not found"}
    
    return {
        "organization": org,
        "repository": repo,
        **repo_data
    }


@mcp_tool(domain="github", description="Search repositories by programming language")
async def search_repositories_by_language(language: str, org: str = None) -> dict:
    """Search repositories by programming language."""
    lang_repos = {
        "Python": [
            {"name": "ToolWeaver", "org": "ushakrishnan", "stars": 1200},
            {"name": "AI-Agents", "org": "ushakrishnan", "stars": 600},
            {"name": "Data-Pipeline", "org": "ushakrishnan", "stars": 320},
        ],
        "TypeScript": [
            {"name": "MCP-Server", "org": "ushakrishnan", "stars": 850},
            {"name": "Web-SDK", "org": "ushakrishnan", "stars": 400},
        ],
        "Go": [
            {"name": "Cloud-SDK", "org": "ushakrishnan", "stars": 450},
        ]
    }
    
    repos = lang_repos.get(language, [])
    if org:
        repos = [r for r in repos if r.get("org") == org]
    
    return {
        "language": language,
        "organization": org or "all",
        "count": len(repos),
        "repositories": repos
    }


@mcp_tool(domain="github", description="Analyze repository statistics")
async def analyze_repository_stats(repos: List[Dict[str, Any]]) -> dict:
    """Analyze statistics across multiple repositories."""
    if not repos:
        return {"error": "No repositories provided"}
    
    total_stars = sum(r.get("stars", 0) for r in repos)
    total_forks = sum(r.get("forks", 0) for r in repos)
    avg_stars = total_stars // len(repos) if repos else 0
    
    languages = {}
    for repo in repos:
        lang = repo.get("language", "Unknown")
        languages[lang] = languages.get(lang, 0) + 1
    
    return {
        "repository_count": len(repos),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "average_stars": avg_stars,
        "languages": languages
    }


# ============================================================
# Main Demo
# ============================================================

async def main():
    """Run GitHub operations demonstration."""
    print("=" * 70)
    print("EXAMPLE 03: GitHub Operations")
    print("=" * 70)
    print()
    
    print("This example demonstrates GitHub repository operations")
    print("Note: Using mock data (no credentials needed)")
    print()
    
    # Step 1: List repositories
    print("Step 1: Listing repositories for organization...")
    org_result = await list_repositories({"org": "ushakrishnan", "limit": 5})
    print(f"   Found {org_result['count']} repositories:")
    for repo in org_result['repositories']:
        print(f"      • {repo['name']:20} ({repo['stars']:5} stars) - {repo['language']}")
    print()
    
    # Step 2: Get specific repository info
    print("Step 2: Getting details for ToolWeaver repository...")
    repo_info = await get_repository_info({"org": "ushakrishnan", "repo": "ToolWeaver"})
    print(f"   Stars: {repo_info['stars']}")
    print(f"   Forks: {repo_info['forks']}")
    print(f"   Issues: {repo_info['issues']}")
    print(f"   PRs: {repo_info['prs']}")
    print(f"   License: {repo_info['license']}")
    print()
    
    # Step 3: Search by language
    print("Step 3: Searching for Python repositories...")
    lang_search = await search_repositories_by_language({"language": "Python", "org": "ushakrishnan"})
    print(f"   Found {lang_search['count']} Python repositories:")
    for repo in lang_search['repositories']:
        print(f"      • {repo['name']:20} ({repo['stars']:5} stars)")
    print()
    
    # Step 4: Analyze stats
    print("Step 4: Analyzing repository statistics...")
    stats = await analyze_repository_stats({"repos": org_result['repositories']})
    print(f"   Total repositories: {stats['repository_count']}")
    print(f"   Total stars: {stats['total_stars']}")
    print(f"   Total forks: {stats['total_forks']}")
    print(f"   Average stars: {stats['average_stars']}")
    print(f"   Languages: {', '.join(stats['languages'].keys())}")
    print()
    
    # Step 5: Tool discovery
    print("Step 5: Discovering all GitHub tools...")
    github_tools = search_tools(domain="github")
    print(f"   Found {len(github_tools)} GitHub tools:")
    for tool in github_tools:
        print(f"      • {tool.name:30} - {tool.description}")
    print()
    
    print("=" * 70)
    print("✅ GitHub operations complete!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
