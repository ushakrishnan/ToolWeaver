# Tutorial: Sandbox Execution

## Simple Explanation
Safely run user-provided code: forbidden operations are blocked, outputs are captured, and long-running code is terminated.

## Technical Explanation
Sandboxed execution runs code in a restricted environment: limited builtins, no network, filtered environment, workspace-scoped file access, stdout/stderr capture, and timeouts/memory limits.

Demonstrates isolated execution environments, restricted builtins, and timeouts.

Run:
```bash
python samples/09-code-execution/code_execution_demo.py
```

Prerequisites:
- Install from PyPI: `pip install toolweaver`

Shows:
- Independent globals per sandbox
- Forbidden builtins/modules blocked
- STDOUT/STDERR capture
- Timeout enforcement

Files:
- [samples/09-code-execution/code_execution_demo.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/09-code-execution/code_execution_demo.py)
- [samples/09-code-execution/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/09-code-execution/README.md)
