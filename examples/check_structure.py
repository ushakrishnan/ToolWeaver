"""
Script to verify all examples have standardized structure
"""
import os
from pathlib import Path

def check_readme_structure(readme_path):
    """Check if README has required sections"""
    required_sections = [
        "# Example",
        "## Overview",
        "## Prerequisites", 
        "## Setup",
        "## Usage",
        "## Expected Output",
        "## Key Concepts",
        "## Related Examples"
    ]
    
    with open(readme_path, 'r') as f:
        content = f.read()
    
    missing = []
    for section in required_sections:
        if section not in content:
            missing.append(section)
    
    return missing

def main():
    examples_dir = Path(__file__).parent
    
    for example_dir in sorted(examples_dir.glob("[0-9]*")):
        readme = example_dir / "README.md"
        if readme.exists():
            missing = check_readme_structure(readme)
            if missing:
                print(f"\n{example_dir.name}:")
                print(f"  Missing sections: {', '.join(missing)}")
            else:
                print(f"✓ {example_dir.name}")

if __name__ == "__main__":
    main()
