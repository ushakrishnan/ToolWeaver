# MCP Adapter Endpoints

A minimal external adapter (sample) exposing two endpoints.

Sample server: [samples/24-external-mcp-adapter/server.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/24-external-mcp-adapter/server.py)

## List Tools
- Method: GET
- Path: `/tools`

Example:
```bash
curl -s http://localhost:8080/tools | jq .
```

## Execute
- Method: POST
- Path: `/execute`
- Body:
```json
{"name": "process_user", "params": {"user": {"id": 123, "name": "Ada"}}}
```
Example:
```bash
curl -s -X POST http://localhost:8080/execute \
  -H 'Content-Type: application/json' \
  -d '{"name": "process_user", "params": {"user": {"id": 123}}}' | jq .
```

## Why
- Simple demo for integrating external tools/services.
- Echo-style responses illustrate payload structure.

## Links
- Sample server: [samples/24-external-mcp-adapter/server.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/24-external-mcp-adapter/server.py)
