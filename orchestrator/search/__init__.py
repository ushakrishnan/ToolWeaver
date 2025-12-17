"""
Search & Indexing subpackage

Provides stable imports for search/indexing modules without moving files.
"""

from orchestrator import vector_search as vector_search
from orchestrator import sharded_catalog as sharded_catalog

__all__ = [
    "vector_search",
    "sharded_catalog",
]
