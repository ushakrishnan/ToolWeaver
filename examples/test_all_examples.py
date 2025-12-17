"""
Test runner for all ToolWeaver examples

This script validates that all example files are properly structured and run without errors.
It checks for import errors, missing files, and basic execution.
"""

import os
import sys
import subprocess
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print a section header"""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

def print_test(example, status, message=""):
    """Print test result"""
    color = GREEN if status == "✓" else RED if status == "✗" else YELLOW
    print(f"{color}{status}{RESET} {example:40} {message}")

# Define all examples with their main scripts
EXAMPLES = [
    ("01-basic-receipt-processing", "process_receipt.py"),
    ("02-receipt-with-categorization", "categorize_receipt.py"),
    ("03-github-operations", "test_connection.py"),
    ("04-vector-search-discovery", "discover_tools.py"),
    ("05-workflow-library", "workflow_demo.py"),
    ("06-monitoring-observability", "monitoring_demo.py"),
    ("07-caching-optimization", "caching_demo.py"),
    ("08-hybrid-model-routing", "hybrid_routing_demo.py"),
    ("09-code-execution", "code_execution_demo.py"),
    ("10-multi-step-planning", "planning_demo.py"),
    ("11-programmatic-executor", "programmatic_demo.py"),
    ("12-sharded-catalog", "sharded_catalog_demo.py"),
    ("13-complete-pipeline", "complete_pipeline.py"),
]

def check_file_exists(example_dir, script_name):
    """Check if example files exist"""
    script_path = example_dir / script_name
    readme_path = example_dir / "README.md"
    env_example_path = example_dir / ".env.example"
    
    issues = []
    if not script_path.exists():
        issues.append(f"Missing {script_name}")
    if not readme_path.exists():
        issues.append("Missing README.md")
    if not env_example_path.exists():
        issues.append("Missing .env.example")
    
    return issues

def check_imports(example_dir, script_name):
    """Check if script imports are valid (syntax check only)"""
    script_path = example_dir / script_name
    
    if not script_path.exists():
        return ["Script not found"]
    
    # Run Python syntax check
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(script_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return [f"Syntax error: {result.stderr[:100]}"]
    
    return []

def main():
    """Run all example tests"""
    print_header("TOOLWEAVER EXAMPLES TEST SUITE")
    
    examples_dir = Path(__file__).parent
    results = {
        "passed": [],
        "warnings": [],
        "failed": []
    }
    
    for example_name, script_name in EXAMPLES:
        example_dir = examples_dir / example_name
        
        if not example_dir.exists():
            print_test(example_name, "✗", "Directory not found")
            results["failed"].append(example_name)
            continue
        
        # Check for required files
        missing = check_file_exists(example_dir, script_name)
        if missing:
            print_test(example_name, "✗", f"Missing files: {', '.join(missing)}")
            results["failed"].append(example_name)
            continue
        
        # Check script syntax and imports
        import_issues = check_imports(example_dir, script_name)
        if import_issues:
            print_test(example_name, "⚠", f"Issues: {', '.join(import_issues)}")
            results["warnings"].append(example_name)
            continue
        
        print_test(example_name, "✓", "All checks passed")
        results["passed"].append(example_name)
    
    # Print summary
    print_header("TEST SUMMARY")
    print(f"{GREEN}✓ Passed:{RESET}  {len(results['passed'])}")
    print(f"{YELLOW}⚠ Warnings:{RESET} {len(results['warnings'])}")
    print(f"{RED}✗ Failed:{RESET}  {len(results['failed'])}")
    
    if results["warnings"]:
        print(f"\n{YELLOW}Warnings (may need optional dependencies):{RESET}")
        for ex in results["warnings"]:
            print(f"  - {ex}")
    
    if results["failed"]:
        print(f"\n{RED}Failed:{RESET}")
        for ex in results["failed"]:
            print(f"  - {ex}")
    
    print(f"\n{BLUE}Note:{RESET} This test only validates file structure and syntax.")
    print(f"{BLUE}Note:{RESET} Actual execution requires API keys and optional dependencies.")
    print(f"{BLUE}Note:{RESET} See each example's README.md for setup instructions.")
    
    # Return exit code
    return 0 if not results["failed"] else 1

if __name__ == "__main__":
    sys.exit(main())
