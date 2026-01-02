#!/usr/bin/env python3
"""
Cross-Platform ToolWeaver Sample Verification

Tests that samples are properly configured for Windows, macOS, and Linux.
Run this after setup to verify everything works on your platform.

Usage:
    python verify_cross_platform.py
"""

import os
import platform
import sys
from pathlib import Path

from dotenv import load_dotenv


def print_header(text):
    """Print a section header"""
    print(f"\n{'=' * 70}")
    print(f"{text:^70}")
    print(f"{'=' * 70}\n")


def print_check(check_name, passed, message=""):
    """Print a check result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {check_name:40} {message}")


def main():
    """Run cross-platform verification"""
    print_header("TOOLWEAVER CROSS-PLATFORM VERIFICATION")

    # Platform info
    print(f"Platform:     {platform.system()} {platform.release()}")
    print(f"Python:       {sys.version.split()[0]}")
    print(f"Executable:   {sys.executable}")
    print()

    all_passed = True

    # ============================================================
    # Check 1: Python Version
    # ============================================================
    print_header("1. Python Version Check")
    py_version = sys.version_info
    check_passed = py_version >= (3, 10)
    print_check(
        "Python 3.10+",
        check_passed,
        f"(installed: {py_version.major}.{py_version.minor}.{py_version.micro})"
    )
    all_passed = all_passed and check_passed

    # ============================================================
    # Check 2: Pathlib Support (cross-platform paths)
    # ============================================================
    print_header("2. File Path Support (Cross-Platform)")
    try:
        test_path = Path.home() / ".toolweaver" / "test"
        print_check("Path.home()", True, str(Path.home()))
        print_check("Path joining", True, "Using /")
        print_check("Path string conversion", True, f"'{str(test_path)}'")
    except Exception as e:
        print_check("Path operations", False, str(e))
        all_passed = False

    # ============================================================
    # Check 3: Environment Variables
    # ============================================================
    print_header("3. Environment Variable Support")
    try:
        # Test setting/reading
        test_key = "TOOLWEAVER_TEST_VAR_" + platform.system()
        os.environ[test_key] = "test_value"
        retrieved = os.getenv(test_key)
        check_passed = retrieved == "test_value"
        print_check("Set/Get env vars", check_passed, f"set '{test_key}' = '{retrieved}'")
        all_passed = all_passed and check_passed
    except Exception as e:
        print_check("Environment variables", False, str(e))
        all_passed = False

    # ============================================================
    # Check 4: .env File Loading
    # ============================================================
    print_header("4. .env Configuration File")
    try:
        current_dir = Path(__file__).parent
        env_path = current_dir / ".env.example"

        if env_path.exists():
            check_passed = True
            print_check(".env.example exists", check_passed, str(env_path))

            # Try loading
            load_dotenv(env_path, override=True)
            print_check(".env loading", True, "dotenv.load_dotenv() works")
        else:
            print_check(".env.example exists", False, f"Not found in {current_dir}")
    except Exception as e:
        print_check(".env loading", False, str(e))
        all_passed = False

    # ============================================================
    # Check 5: Core Dependencies
    # ============================================================
    print_header("5. Core Dependencies")
    core_deps = [
        ("os", "os"),
        ("sys", "sys"),
        ("pathlib", "pathlib"),
        ("dotenv", "python-dotenv"),
        ("pydantic", "pydantic"),
        ("requests", "requests"),
    ]

    for import_name, package_name in core_deps:
        try:
            __import__(import_name)
            print_check(f"Import {package_name:20}", True)
        except ImportError:
            print_check(f"Import {package_name:20}", False, "pip install it")
            all_passed = False

    # ============================================================
    # Check 6: Subprocess Execution
    # ============================================================
    print_header("6. Subprocess Support (for code execution)")
    try:
        import subprocess

        # Test basic execution
        result = subprocess.run(
            [sys.executable, "-c", "print('Hello')"],
            capture_output=True,
            text=True
        )
        check_passed = result.returncode == 0
        print_check("subprocess.run()", check_passed, f"return code: {result.returncode}")
        all_passed = all_passed and check_passed
    except Exception as e:
        print_check("subprocess execution", False, str(e))
        all_passed = False

    # ============================================================
    # Check 7: Async Support
    # ============================================================
    print_header("7. Async/Await Support")
    try:
        import asyncio

        async def test_async():
            await asyncio.sleep(0)
            return True

        result = asyncio.run(test_async())
        print_check("asyncio.run()", result)
        all_passed = all_passed and result
    except Exception as e:
        print_check("asyncio support", False, str(e))
        all_passed = False

    # ============================================================
    # Check 8: Encoding Support
    # ============================================================
    print_header("8. Character Encoding Support")
    try:
        # Test UTF-8
        test_strings = [
            ("ASCII", "Hello"),
            ("UTF-8", "Hello 世界 🌍"),
            ("Special chars", "Café, naïve, résumé"),
        ]

        for name, text in test_strings:
            try:
                encoded = text.encode('utf-8')
                decoded = encoded.decode('utf-8')
                check_passed = decoded == text
                print_check(f"Encoding: {name:25}", check_passed)
                all_passed = all_passed and check_passed
            except Exception as e:
                print_check(f"Encoding: {name:25}", False, str(e))
                all_passed = False

    except Exception as e:
        print_check("Encoding support", False, str(e))
        all_passed = False

    # ============================================================
    # Check 9: Optional Features
    # ============================================================
    print_header("9. Optional Features (For Advanced Samples)")
    optional_deps = [
        ("redis", "redis"),
        ("qdrant_client", "qdrant-client"),
        ("wandb", "wandb"),
        ("azure.identity", "azure-identity"),
        ("openai", "openai"),
    ]

    for import_name, package_name in optional_deps:
        try:
            __import__(import_name)
            print_check(f"Optional: {package_name:20}", True)
        except ImportError:
            print_check(f"Optional: {package_name:20}", False, "pip install (optional)")

    # ============================================================
    # Summary
    # ============================================================
    print_header("VERIFICATION SUMMARY")

    if all_passed:
        print("✅ All required checks passed!")
        print("\nNext steps:")
        print("  1. Copy .env.example to .env")
        print("     cp .env.example .env")
        print("  2. Add your API keys to .env")
        print("  3. Run a sample:")
        print("     cd samples/01-basic-receipt-processing")
        print("     python process_receipt.py")
        print()
        print("For detailed setup instructions, see:")
        print("  • CROSS_PLATFORM_SETUP.md")
        print("  • ENV_CONFIGURATION.md")
        return 0
    else:
        print("❌ Some checks failed. See above for details.")
        print("\nFor help:")
        print("  • See CROSS_PLATFORM_SETUP.md#common-issues--solutions")
        print("  • Check Python version: python --version")
        print("  • Reinstall: pip install --force-reinstall toolweaver")
        return 1


if __name__ == "__main__":
    sys.exit(main())
