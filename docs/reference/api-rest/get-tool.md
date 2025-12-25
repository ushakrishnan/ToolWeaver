# Get Tool Details

- Method: GET
- Path: `/api/v1/tools/{tool_name}`
- Purpose: retrieve full schema for a specific tool

## Example (curl)
```bash
curl -s http://localhost:8000/api/v1/tools/receipt_ocr | jq .
```

## Example (Python)
```python
import requests
resp = requests.get("http://localhost:8000/api/v1/tools/receipt_ocr")
print(resp.json())
```

## Response (example)
```json
{
  "name": "receipt_ocr",
  "description": "Extracts text from receipt images",
  "type": "function",
  "provider": "python",
  "parameters": [
    {
      "name": "image_path",
      "type": "string",
      "description": "Local or S3 path",
      "required": true,
      "enum": null
    }
  ],
  "metadata": {}
}
```

## Links
- Server adapter: [orchestrator/adapters/fastapi_wrapper.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/orchestrator/adapters/fastapi_wrapper.py)
- Samples: [samples/03-github-operations](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/03-github-operations)
