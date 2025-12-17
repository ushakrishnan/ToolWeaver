"""
Execution subpackage

Exposes programmatic execution and sandbox-related modules via a
stable namespace without relocating files yet.
"""

from orchestrator import programmatic_executor as programmatic_executor
from orchestrator import sandbox as sandbox
from orchestrator import code_exec_worker as code_exec_worker
from orchestrator import small_model_worker as small_model_worker  # optional

__all__ = [
    "programmatic_executor",
    "sandbox",
    "code_exec_worker",
    "small_model_worker",
]
