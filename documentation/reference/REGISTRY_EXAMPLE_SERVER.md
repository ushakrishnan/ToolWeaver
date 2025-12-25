# Registry Example Server

Serve the sample `registry.json` locally for development.

## Option 1: Simple static server (Python)

Windows PowerShell:

```powershell
cd docs/reference
python -m http.server 8090
# Now available at: http://127.0.0.1:8090/registry.json
```

Set the env var so ToolWeaver uses it:

```powershell
$env:MCP_REGISTRY_URL = "http://127.0.0.1:8090/registry.json"
```

## Option 2: Minimal custom server

```python
# run_registry_server.py
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from pathlib import Path

ROOT = Path(__file__).parent

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Only serve registry.json
        return str(ROOT / "registry.json")

if __name__ == "__main__":
    with TCPServer(("127.0.0.1", 8090), Handler) as httpd:
        print("Serving registry at http://127.0.0.1:8090/registry.json")
        httpd.serve_forever()
```

Run it:

```powershell
python docs/reference/run_registry_server.py
$env:MCP_REGISTRY_URL = "http://127.0.0.1:8090/registry.json"
```

Security: Use trusted registries only; prefer HTTPS and signed catalogs in production.
