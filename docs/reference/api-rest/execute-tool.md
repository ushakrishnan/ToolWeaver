# Execute Tool

- Method: POST
- Path: `/api/v1/tools/{tool_name}/execute`
- Purpose: run a tool with given parameters

## Request Body
```json
{
  "params": {
    "image_path": "s3://bucket/receipt.jpg"
  }
}
```

## Example (curl)
```bash
curl -s -X POST \
  http://localhost:8000/api/v1/tools/receipt_ocr/execute \
  -H 'Content-Type: application/json' \
  -d '{"params": {"image_path": "/tmp/receipt.jpg"}}' | jq .
```

## Example (Python)
```python
import requests
payload = {"params": {"image_path": "/tmp/receipt.jpg"}}
resp = requests.post("http://localhost:8000/api/v1/tools/receipt_ocr/execute", json=payload)
print(resp.json())
```

## Response (example)
```json
{
  "text": "Receipt total $10.99 ...",
  "confidence": 0.92
}
```

## Errors
- 404 if `tool_name` not found
- 400 if parameters are invalid

## Links
- Server adapter: [orchestrator/adapters/fastapi_wrapper.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/orchestrator/adapters/fastapi_wrapper.py)
- Samples: [samples/09-code-execution](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/09-code-execution)
