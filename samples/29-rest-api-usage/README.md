# REST API Usage

Call the ToolWeaver REST endpoints to list and execute tools from an external client.

Note: Requires a running REST server exposing ToolWeaver tools. If you use FastAPI integration, start your service first.

## Run
```bash
python samples/29-rest-api-usage/rest_client_demo.py
```

## Prerequisites
- Install from PyPI:
```bash
pip install toolweaver
pip install -r samples/29-rest-api-usage/requirements.txt
```
- Requires a running ToolWeaver REST server (start your service before running the client).

## What it shows
- GET /tools
- GET /tools/{name}
- POST /tools/{name}/execute
