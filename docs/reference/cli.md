# CLI Reference

Browse tools from the command line.

```bash
python -m orchestrator.cli list
python -m orchestrator.cli search --query "receipt"
python -m orchestrator.cli info --tool receipt_ocr
```

Commands:
- `list`: List all available tools.
- `search --query <text>`: Search tools.
- `info --tool <name>`: Show details for a tool.
- `browse --query <text>`: Progressive detail browsing.
