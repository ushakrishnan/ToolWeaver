"""
Verify Installation Script

Tests that all dependencies can be imported successfully.
Run this after updating dependencies to ensure everything works.

Usage:
    python scripts/verify_install.py
"""

import importlib
import sys


def check_imports(imports: list[tuple[str, str]]) -> bool:
    """
    Check if all imports work.
    
    Args:
        imports: List of (module_name, package_name) tuples
    
    Returns:
        True if all imports succeed, False otherwise
    """
    all_ok = True

    for module_name, package_name in imports:
        try:
            importlib.import_module(module_name)
            print(f"✓ {package_name:30s} ({module_name})")
        except ImportError as e:
            print(f"✗ {package_name:30s} ({module_name}) - {e}")
            all_ok = False

    return all_ok


def main():
    """Main verification."""
    print("="*70)
    print("🔍 Verifying ToolWeaver Dependencies")
    print("="*70)

    # Core dependencies
    print("\n📦 Core Dependencies:")
    core_imports = [
        ('pydantic', 'pydantic'),
        ('anyio', 'anyio'),
        ('dotenv', 'python-dotenv'),
        ('requests', 'requests'),
        ('httpx', 'httpx'),
        ('aiohttp', 'aiohttp'),
        ('azure.ai.vision.imageanalysis', 'azure-ai-vision-imageanalysis'),
        ('azure.identity', 'azure-identity'),
        ('openai', 'openai'),
        ('anthropic', 'anthropic'),
        ('numpy', 'numpy'),
        ('sentence_transformers', 'sentence-transformers'),
        ('rank_bm25', 'rank-bm25'),
    ]
    core_ok = check_imports(core_imports)

    # Dev dependencies
    print("\n🧪 Dev Dependencies:")
    dev_imports = [
        ('pytest', 'pytest'),
        ('pytest_asyncio', 'pytest-asyncio'),
        ('pytest_mock', 'pytest-mock'),
        ('pytest_cov', 'pytest-cov'),
        ('black', 'black'),
        ('ruff', 'ruff'),
        ('mypy', 'mypy'),
    ]
    dev_ok = check_imports(dev_imports)

    # Optional dependencies
    print("\n🔧 Optional Dependencies:")
    optional_imports = [
        ('qdrant_client', 'qdrant-client'),
        ('redis', 'redis'),
        ('wandb', 'wandb'),
        ('prometheus_client', 'prometheus-client'),
    ]
    optional_ok = check_imports(optional_imports)

    # Summary
    print("\n" + "="*70)
    if core_ok and dev_ok:
        print("✅ All required dependencies installed successfully!")
        if not optional_ok:
            print("⚠️  Some optional dependencies missing (this is OK)")
        return 0
    else:
        print("❌ Some required dependencies are missing!")
        print("\n💡 To install missing dependencies:")
        print("   pip install -e '.[dev]'")
        return 1


if __name__ == '__main__':
    sys.exit(main())
