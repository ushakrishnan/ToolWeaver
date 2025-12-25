import os
import json
import requests

BASE_URL = os.environ.get("TOOLWEAVER_BASE_URL", "http://localhost:8000/api/v1")


def main() -> None:
    # List tools
    r = requests.get(f"{BASE_URL}/tools")
    r.raise_for_status()
    tools = r.json()
    print("Tools:", json.dumps(tools[:3], indent=2))

    if not tools:
        print("No tools available; ensure server is running and configured.")
        return

    name = tools[0]["name"] if isinstance(tools[0], dict) else tools[0].get("name")
    print(f"Using tool: {name}")

    # Get tool details
    r = requests.get(f"{BASE_URL}/tools/{name}")
    r.raise_for_status()
    print("Tool details:", json.dumps(r.json(), indent=2))

    # Execute tool with sample params
    payload = {"params": {}}
    r = requests.post(f"{BASE_URL}/tools/{name}/execute", json=payload)
    r.raise_for_status()
    print("Execution result:", json.dumps(r.json(), indent=2))


if __name__ == "__main__":
    main()
