# REST API Usage

## Simple Explanation
Call ToolWeaver tools over HTTP: list available tools, inspect details, and execute a tool by posting parameters.

## Technical Explanation
Expose tools via a service (e.g., FastAPI). Clients call the REST endpoints to discover and run tools remotely. Ensure consistent schemas and auth where needed.

**Endpoints**
- `GET /tools` — list tools
- `GET /tools/{name}` — tool details
- `POST /tools/{name}/execute` — run tool

**Try it**
- Run the client sample: [samples/29-rest-api-usage/rest_client_demo.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/29-rest-api-usage/rest_client_demo.py)
- See the README: [samples/29-rest-api-usage/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/29-rest-api-usage/README.md)

**Why run this**
- Verify HTTP integration from non‑Python clients
- Inspect endpoint shapes and payloads end‑to‑end
- Validate service wiring before building full apps

**Gotchas**
- Validate inputs server‑side; enforce timeouts and rate limits
- Log with secrets redaction; avoid sensitive data exposure
- Version your API routes for compatibility
