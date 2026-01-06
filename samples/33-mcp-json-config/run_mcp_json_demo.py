import argparse
import asyncio
import os
import sys
from pathlib import Path

try:
    from orchestrator.tools.mcp_config_loader import load_mcp_servers_from_json
except Exception:
    # Fallback: add repo root to path when package isn't installed yet
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    try:
        from orchestrator.tools.mcp_config_loader import load_mcp_servers_from_json
    except Exception as e:  # pragma: no cover - guidance for users
        raise RuntimeError(
            "Package import failed. Install the ToolWeaver package first:\n"
            "  pip install toolweaver\n"
            "  # or for local dev: python -m pip install -e ."
        ) from e


async def main():
    parser = argparse.ArgumentParser(
        description="Register MCP servers from JSON config and optionally fetch tool definitions."
    )
    parser.add_argument(
        "--config",
        help="Path to JSON config (defaults to MCP_SERVERS_FILE or Claude path)",
        default=None,
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch tool definitions from each server (GET /tools).",
    )
    args = parser.parse_args()

    # Resolve config path
    cfg = args.config
    if not cfg:
        cfg = os.getenv("MCP_SERVERS_FILE") or os.getenv("CLAUDE_SERVERS_FILE")
        if not cfg:
            # Use sample by default
            cfg = str(Path(__file__).parent / "servers.json")

    print(f"Using config: {cfg}")

    adapters = load_mcp_servers_from_json(cfg)
    if not adapters:
        print("No adapters registered (empty or missing config).")
        return

    print("Registered MCP servers:")
    for name in adapters.keys():
        print(f"  - {name}")

    if not args.fetch:
        print("\nDry-run complete (skip network fetch). Use --fetch to query /tools.")
        return

    print("\nFetching tool definitions from servers...")
    total = 0
    fetch_tasks = [adapters[name].discover() for name in adapters]
    results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
    for name, result in zip(adapters.keys(), results, strict=False):
        if isinstance(result, Exception):
            print(f"  ! {name}: failed to fetch tools ({result})")
            continue
        count = len(result)
        total += count
        print(f"  * {name}: {count} tools discovered")

    print(f"\nTotal tools discovered across servers: {total}")


if __name__ == "__main__":
    asyncio.run(main())
