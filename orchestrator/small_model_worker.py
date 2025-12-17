"""
Shim module for backwards compatibility.

Re-exports small model worker from orchestrator.execution.small_model_worker.
"""

from .execution.small_model_worker import (
    SmallModelWorker,
    _repair_json,
    REQUESTS_AVAILABLE,
    TRANSFORMERS_AVAILABLE,
)

__all__ = [
    "SmallModelWorker",
    "_repair_json",
    "REQUESTS_AVAILABLE",
    "TRANSFORMERS_AVAILABLE",
]
