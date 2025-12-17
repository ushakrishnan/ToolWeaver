"""Shim module for backwards compatibility. Re-exports from orchestrator.tools."""
from .tools.vector_search import VectorToolSearchEngine
__all__ = ["VectorToolSearchEngine"]
