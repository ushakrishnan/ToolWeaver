# List Tools

- Method: GET
- Path: `/api/v1/tools`
- Purpose: enumerate all available tools with summary schemas

## Example (curl)
```bash
curl -s http://localhost:8000/api/v1/tools | jq .
```

## Example (Python)
```python
import requests
resp = requests.get("http://localhost:8000/api/v1/tools")
print(resp.json())
```

## Response (example)
```json
{
  "count": 3,
  "tools": [
    {
      "name": "receipt_ocr",
      "description": "Extracts text from receipt images",
      "type": "function",
      "parameters": [
        {"name": "image_path", "type": "string", "description": "Local or S3 path", "required": true}
      ]
    },
    {
      "name": "categorize_expenses",
      "description": "Categorize line items",
      "type": "function",
      "parameters": [
        {"name": "items", "type": "array", "description": "Line items", "required": true}
      ]
    }
  ]
}
```

## Links
- Server adapter: [orchestrator/adapters/fastapi_wrapper.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/orchestrator/adapters/fastapi_wrapper.py)
- Tools examples: [samples/03-github-operations](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/03-github-operations)
- Concepts: [Tools & Discovery](../../concepts/overview.md)
