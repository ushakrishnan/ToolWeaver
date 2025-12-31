#!/usr/bin/env python3
"""Organize root files and create example .env files"""

import shutil
from pathlib import Path


def organize_root_files():
    """Move root files to appropriate documentation folders"""

    root_org_map = {
        # Mypy reports
        'mypy_errors.txt': 'docs/internal/mypy-reports/',
        'mypy_errors_full.txt': 'docs/internal/mypy-reports/',
        'mypy_errors_updated.txt': 'docs/internal/mypy-reports/',
        'mypy_final.txt': 'docs/internal/mypy-reports/',
        'mypy_full.txt': 'docs/internal/mypy-reports/',
        'mypy_latest.txt': 'docs/internal/mypy-reports/',
        'mypy_output.txt': 'docs/internal/mypy-reports/',
        'mypy_output2.txt': 'docs/internal/mypy-reports/',
        'analyze_mypy.py': 'docs/internal/mypy-reports/',

        # Completion & analysis reports
        'PHASE_3_4_COMPLETION_SUMMARY.md': 'docs/internal/completion-reports/',
        'PROJECT_COMPLETION_SUMMARY.md': 'docs/internal/completion-reports/',
        'QUICK_WINS_COMPLETION_SUMMARY.md': 'docs/internal/completion-reports/',

        # Test reports
        'TEST_COVERAGE_REPORT.md': 'docs/internal/test-reports/',
        'FAILING_TESTS_ANALYSIS.md': 'docs/internal/test-reports/',
        'FINAL_STATUS_REPORT.md': 'docs/internal/test-reports/',
        'benchmark_results.txt': 'docs/internal/test-reports/',

        # Other
        'NOTICE': 'docs/legal/',
    }

    print("=" * 70)
    print("ORGANIZING ROOT FILES")
    print("=" * 70)

    for file, target_dir in root_org_map.items():
        src = Path(file)
        if src.exists():
            # Create target directory
            Path(target_dir).mkdir(parents=True, exist_ok=True)
            dst = Path(target_dir) / file

            # Move file
            shutil.move(str(src), str(dst))
            print(f"✓ {file} → {target_dir}")
        else:
            print(f"⊘ {file} not found (already moved?)")

    print(f"\n✓ Moved {sum(1 for f in root_org_map if Path(f).exists())} files")

def get_env_config():
    """Extract configuration from main .env"""
    config = {}
    env_file = Path('.env')

    if not env_file.exists():
        print("⊘ .env not found")
        return config

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()

    return config

def create_example_env_files():
    """Create .env files in example directories"""

    examples_path = Path('examples')
    env_config = get_env_config()

    # Critical keys for examples
    critical_keys = [
        'AZURE_CV_ENDPOINT',
        'AZURE_USE_AD',
        'OCR_MODE',
        'PLANNER_PROVIDER',
        'PLANNER_MODEL',
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_VERSION',
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'USE_SMALL_MODEL',
        'SMALL_MODEL_BACKEND',
        'WORKER_MODEL',
        'OLLAMA_API_URL',
        'QDRANT_URL',
        'QDRANT_API_KEY',
        'QDRANT_COLLECTION',
        'REDIS_URL',
        'REDIS_PASSWORD',
        'MONITORING_BACKENDS',
        'WANDB_API_KEY',
        'GITHUB_TOKEN',
        'GITHUB_OWNER',
    ]

    print("\n" + "=" * 70)
    print("CREATING EXAMPLE .ENV FILES")
    print("=" * 70)

    created_count = 0
    skipped_count = 0

    for example_dir in sorted(examples_path.iterdir()):
        if not example_dir.is_dir() or example_dir.name.startswith('.'):
            continue

        env_path = example_dir / '.env'

        # Skip if already exists
        if env_path.exists():
            skipped_count += 1
            continue

        # Create .env with values from main .env
        created_count += 1
        env_content = "# ToolWeaver Configuration\n"
        env_content += "# Copy values from your main .env file or populate with your own\n\n"

        for key in critical_keys:
            value = env_config.get(key, '')
            if value and not value.startswith('your-'):
                env_content += f"{key}={value}\n"
            else:
                env_content += f"# {key}=\n"

        with open(env_path, 'w') as f:
            f.write(env_content)

        print(f"✓ Created {example_dir.name}/.env")

    print(f"\n✓ Created {created_count} .env files")
    print(f"⊘ Skipped {skipped_count} examples (already have .env)")

def check_examples():
    """Check example quality"""

    examples_path = Path('examples')

    print("\n" + "=" * 70)
    print("EXAMPLE QUALITY CHECK")
    print("=" * 70)

    examples_data = []
    for example_dir in sorted(examples_path.iterdir()):
        if not example_dir.is_dir() or example_dir.name.startswith('.'):
            continue

        has_readme = (example_dir / 'README.md').exists()
        has_env = (example_dir / '.env').exists()
        has_requirements = (example_dir / 'requirements.txt').exists()
        has_python = any(example_dir.glob('*.py'))

        examples_data.append({
            'name': example_dir.name,
            'readme': has_readme,
            'env': has_env,
            'requirements': has_requirements,
            'python': has_python,
        })

    print(f"\nTotal examples: {len(examples_data)}")
    print("\nQuality breakdown:")

    with_readme = sum(1 for e in examples_data if e['readme'])
    with_env = sum(1 for e in examples_data if e['env'])
    with_requirements = sum(1 for e in examples_data if e['requirements'])
    with_python = sum(1 for e in examples_data if e['python'])

    print(f"  • With README.md: {with_readme}/{len(examples_data)} (target: all)")
    print(f"  • With .env: {with_env}/{len(examples_data)} (target: all)")
    print(f"  • With requirements.txt: {with_requirements}/{len(examples_data)}")
    print(f"  • With Python code: {with_python}/{len(examples_data)}")

    return examples_data

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("TOOLWEAVER: FILE ORGANIZATION SCRIPT")
    print("=" * 70)

    # Check examples first
    examples = check_examples()

    # Organize root files
    organize_root_files()

    # Create env files
    create_example_env_files()

    print("\n" + "=" * 70)
    print("✓ ORGANIZATION COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Verify files were moved correctly")
    print("  2. Update any .env files with your API keys")
    print("  3. Run examples to test")
    print()
