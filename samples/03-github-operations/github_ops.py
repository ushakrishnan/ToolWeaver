"""
Example 03: GitHub Operations with ToolWeaver

Demonstrates:
- External API integration with tools
- Tool discovery by domain
- LLM-driven orchestration: LLM picks which tools to use
- Plan generation and execution

Use Case:
Show how ToolWeaver discovers tools and lets an LLM orchestrate them.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from orchestrator import LargePlanner, execute_plan, mcp_tool, search_tools

# Setup output folder (same structure as Sample 02)
OUTPUT_DIR = Path(__file__).parent / "execution_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
_ENV_PATH = Path(__file__).with_name(".env")
load_dotenv(_ENV_PATH)
load_dotenv()  # also allow root-level .env

GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "").strip()

if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN not set. Add your token to .env and try again.")
if not GITHUB_OWNER:
    raise RuntimeError("GITHUB_OWNER not set. Add your GitHub org/user to .env and try again.")

# Initialize planner for LLM-driven orchestration
planner = LargePlanner()


async def _github_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call GitHub REST API with token; run in a thread to avoid blocking the event loop."""

    def _request() -> dict[str, Any]:
        url = f"{GITHUB_API_URL}{path}"
        headers = {"Accept": "application/vnd.github+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code >= 400:
            raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text}")
        return resp.json()

    return await asyncio.to_thread(_request)


# ============================================================
# GitHub Tools - Demonstrate API Integration Pattern
# ============================================================


@mcp_tool(domain="github", description="List repositories for an organization")
async def list_repositories(org: str, limit: int = 10) -> dict:
    """List repositories from a GitHub organization or user."""
    try:
        data = await _github_get(f"/orgs/{org}/repos", params={"per_page": limit, "sort": "updated"})
    except RuntimeError as err:
        if "404" in str(err):
            data = await _github_get(f"/users/{org}/repos", params={"per_page": limit, "sort": "updated"})
        else:
            raise

    repos = [
        {
            "name": r.get("name"),
            "stars": r.get("stargazers_count", 0),
            "language": r.get("language") or "Unknown",
            "description": r.get("description") or "",
            "forks": r.get("forks_count", 0),
            "open_issues": r.get("open_issues_count", 0),
        }
        for r in data
    ][:limit]

    return {
        "organization": org,
        "repositories": repos,
        "total_count": len(repos),
        "count": len(repos),
    }


@mcp_tool(domain="github", description="Get repository details and statistics")
async def get_repository_info(org: str, repo: str) -> dict:
    """Get detailed information about a repository."""
    data = await _github_get(f"/repos/{org}/{repo}")

    return {
        "organization": org,
        "repository": repo,
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "issues": data.get("open_issues_count", 0),
        "language": data.get("language") or "Unknown",
        "license": (data.get("license") or {}).get("spdx_id") or "Unknown",
        "description": data.get("description") or "",
    }


@mcp_tool(domain="github", description="Search repositories by programming language")
async def search_repositories_by_language(language: str, org: str | None = None) -> dict[str, Any]:
    """Search repositories by programming language."""
    query = f"language:{language}"
    if org:
        query += f" org:{org}"

    data = await _github_get("/search/repositories", params={"q": query, "per_page": 20})
    repos = [
        {
            "name": r.get("name"),
            "org": (r.get("owner") or {}).get("login", ""),
            "stars": r.get("stargazers_count", 0),
            "language": r.get("language") or "Unknown",
            "description": r.get("description") or "",
        }
        for r in data.get("items", [])
    ]

    return {
        "language": language,
        "organization": org or "all",
        "count": len(repos),
        "repositories": repos,
    }


@mcp_tool(domain="github", description="Analyze repository statistics")
async def analyze_repository_stats(repos: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze statistics across multiple repositories."""
    if not repos:
        return {"error": "No repositories provided"}

    total_stars = sum(r.get("stars", 0) for r in repos)
    total_forks = sum(r.get("forks", 0) for r in repos)
    avg_stars = total_stars / len(repos) if repos else 0.0

    languages: dict[str, int] = {}
    for repo in repos:
        lang = repo.get("language", "Unknown")
        languages[lang] = languages.get(lang, 0) + 1

    return {
        "repository_count": len(repos),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "average_stars": round(avg_stars, 2),
        "languages": languages,
    }


# ============================================================
# Main Demo
# ============================================================


async def main():
    """Run GitHub operations demonstration."""
    start_time = datetime.now()
    execution_id = start_time.strftime("%Y%m%d_%H%M%S")
    
    print("=" * 70)
    print("EXAMPLE 03: GitHub Operations with ToolWeaver")
    print("=" * 70)
    print()

    print(f"Target: {GITHUB_OWNER} | API: {GITHUB_API_URL}")
    print(f"Execution ID: {execution_id}")
    print()

    # Step 1: Discover all GitHub tools
    print("Step 1: Discovering GitHub tools...")
    github_tools = search_tools(domain="github")
    print(f"   Found {len(github_tools)} tools:")
    for tool in github_tools:
        print(f"      - {tool.name:30} - {tool.description}")
    print()

    # Save tool discovery to JSON
    tools_file = OUTPUT_DIR / f"tools_{execution_id}.json"
    tools_data = [{"name": t.name, "description": t.description, "domain": t.domain} for t in github_tools]
    with open(tools_file, "w", encoding="utf-8") as f:
        json.dump(tools_data, f, indent=2, default=str)
    print(f"[*] Tools discovered: {tools_file}")
    print()

    # Step 2: Define a user request
    user_request = (
        f"List the top 5 repositories in {GITHUB_OWNER}, "
        "then search for Python repositories and provide statistics."
    )
    print(f"Step 2: User request:\n   {user_request}")
    print()

    # Step 3: LLM generates a plan
    print("Step 3: LLM generates execution plan...")
    execution_success = False
    
    try:
        plan = await planner.generate_plan(
            user_request=user_request,
            context={"github_owner": GITHUB_OWNER},
            available_tools=github_tools,
        )
        
        # Handle both dict and object responses
        steps = plan.get("steps") if isinstance(plan, dict) else plan.steps
        print(f"   Plan: {len(steps)} steps")
        for i, step in enumerate(steps, 1):
            step_name = step.get("tool_name") if isinstance(step, dict) else step.tool_name
            print(f"      {i}. {step_name}")
        print()
        
        # Save plan to JSON
        plan_file = OUTPUT_DIR / f"plan_{execution_id}.json"
        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, default=str)
        print(f"[*] Plan saved to: {plan_file}")
        print()

        # Step 4: Execute the plan
        print("Step 4: Executing plan...")
        results = await execute_plan(plan)
        print(f"   [OK] Plan executed successfully ({len(results)} tool calls)")
        print()
        execution_success = True
        
        # Save results to JSON
        results_file = OUTPUT_DIR / f"results_{execution_id}.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"[*] Results saved to: {results_file}")
        print()
        
    except Exception as e:
        print(f"   [Note] LLM planning needs config; using manual flow.")
        print(f"   Error: {e}")
        print()
        
        # Save error to JSON
        error_file = OUTPUT_DIR / f"error_{execution_id}.json"
        with open(error_file, "w", encoding="utf-8") as f:
            json.dump({"error": str(e), "timestamp": start_time.isoformat()}, f, indent=2)
        
        await _manual_flow(start_time, execution_id)
        execution_success = True
    
    # Save manifest entry
    manifest_file = OUTPUT_DIR / "manifest.json"
    manifest = {}
    if manifest_file.exists():
        with open(manifest_file, "r") as f:
            manifest = json.load(f)
    
    manifest[execution_id] = {
        "timestamp": start_time.isoformat(),
        "success": execution_success,
        "github_owner": GITHUB_OWNER,
        "tool_count": len(github_tools),
    }
    
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"[*] Manifest updated: {manifest_file}")
    print(f"[*] Results saved to folder: {OUTPUT_DIR}")
    print()


async def _manual_flow(start_time: datetime, execution_id: str):
    """Fallback: direct tool calls when LLM is unavailable."""
    print("Step 3 (Manual): Running direct tool calls...")
    print()

    results = {}
    
    # a) List repositories
    print("   a) Listing repositories...")
    org_result = await list_repositories({"org": GITHUB_OWNER, "limit": 5})
    results["list_repositories"] = org_result
    print(f"      Found {org_result['count']} repositories:")
    for repo in org_result['repositories']:
        print(f"         - {repo['name']:20} ({repo.get('stars', 0):5} stars) - {repo.get('language', 'Unknown')}")
    print()

    # b) Get repo info
    print("   b) Getting details for ToolWeaver...")
    repo_info = await get_repository_info({"org": GITHUB_OWNER, "repo": "ToolWeaver"})
    results["get_repository_info"] = repo_info
    print(f"      Stars: {repo_info['stars']}, Forks: {repo_info['forks']}, Issues: {repo_info['issues']}")
    print()

    # c) Search by language
    print("   c) Searching for Python repositories...")
    lang_search = await search_repositories_by_language({"language": "Python", "org": GITHUB_OWNER})
    results["search_repositories_by_language"] = lang_search
    print(f"      Found {lang_search['count']} Python repositories")
    print()

    # d) Analyze stats
    print("   d) Analyzing statistics...")
    stats = await analyze_repository_stats({"repos": org_result['repositories']})
    results["analyze_repository_stats"] = stats
    print(f"      Total: {stats['repository_count']} repos, {stats['total_stars']} stars, avg: {stats['average_stars']}")
    print()

    # Save manual flow results to JSON
    results_file = OUTPUT_DIR / f"results_{execution_id}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[*] Manual results saved to: {results_file}")
    print()

    print("=" * 70)
    print("[OK] GitHub operations complete!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
