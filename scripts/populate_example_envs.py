#!/usr/bin/env python3
"""Populate .env files in examples based on their .env.example files"""

import re
from pathlib import Path


def extract_env_keys_from_file(file_path):
    """Extract environment variable keys from a .env or .env.example file"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return []

    # Find all ENV_VAR_NAME patterns (uppercase with underscores)
    # Match lines like: ENV_VAR=value or # ENV_VAR=value
    pattern = r'^#?\s*([A-Z_][A-Z0-9_]*)='
    keys = []

    for line in content.split('\n'):
        match = re.search(pattern, line.strip())
        if match:
            key = match.group(1)
            if key not in keys:
                keys.append(key)

    return keys

def get_value_from_root_env(key):
    """Get value from root .env file"""
    env_path = Path('.env')
    if not env_path.exists():
        return None

    try:
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith(key + '='):
                    # Get everything after the first =
                    value = line.split('=', 1)[1]
                    return value
    except Exception:
        pass

    return None

def read_env_example(example_path):
    """Read .env.example file content"""
    env_example = example_path / '.env.example'
    if env_example.exists():
        try:
            with open(env_example, encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None
    return None

def populate_example_env(example_path):
    """Populate .env file based on .env.example"""
    env_example_content = read_env_example(example_path)

    if not env_example_content:
        return False, "No .env.example found"

    # Get keys from .env.example
    keys = extract_env_keys_from_file(example_path / '.env.example')

    if not keys:
        return False, "No environment variables found in .env.example"

    # Build new .env content with values from root .env
    lines = []
    for line in env_example_content.split('\n'):
        # Check if this is an environment variable line
        match = re.search(r'^#?\s*([A-Z_][A-Z0-9_]*)=', line.strip())

        if match:
            key = match.group(1)
            root_value = get_value_from_root_env(key)

            if root_value:
                # Use value from root .env
                lines.append(f"{key}={root_value}")
            else:
                # Keep original line from .env.example (with placeholder)
                lines.append(line)
        else:
            # Keep comments and blank lines as-is
            lines.append(line)

    # Write to .env
    env_path = example_path / '.env'
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return True, f"✓ Populated with {len(keys)} keys from .env.example"
    except Exception as e:
        return False, f"Error writing: {e}"

def main():
    """Main function"""
    examples_path = Path('examples')

    print("=" * 70)
    print("POPULATING .env FILES BASED ON .env.example")
    print("=" * 70)

    success_count = 0
    skip_count = 0

    for example_dir in sorted(examples_path.iterdir()):
        if not example_dir.is_dir() or example_dir.name.startswith('.'):
            continue

        env_example_path = example_dir / '.env.example'

        if not env_example_path.exists():
            print(f"⊘ {example_dir.name}: No .env.example file")
            skip_count += 1
            continue

        success, message = populate_example_env(example_dir)

        if success:
            print(f"✓ {example_dir.name}: {message}")
            success_count += 1
        else:
            print(f"✗ {example_dir.name}: {message}")

    print("\n" + "=" * 70)
    print(f"Populated: {success_count} | Skipped: {skip_count}")
    print("=" * 70)

if __name__ == '__main__':
    main()
