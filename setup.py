"""
Setup script for ToolWeaver.

Modern Python projects use pyproject.toml for configuration.
This setup.py is provided for backward compatibility only.

Installation:
    pip install -e .                    # Core dependencies
    pip install -e ".[monitoring]"      # + W&B + Prometheus
    pip install -e ".[dev]"             # + development tools
    pip install -e ".[all]"             # Everything
"""

from setuptools import setup

# All configuration is in pyproject.toml
# This file exists only for backward compatibility
setup()
