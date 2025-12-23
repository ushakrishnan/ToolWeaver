#!/usr/bin/env python3
"""Create requirements.txt for all examples"""

from pathlib import Path

# Common dependencies for ToolWeaver examples
COMMON_REQUIREMENTS = """# ToolWeaver Example Dependencies

# Core ToolWeaver
toolweaver>=0.6.0

# Azure services (if using Azure)
azure-identity>=1.13.0
azure-cognitiveservices-vision-computervision>=9.0.0

# LLM providers (optional - install as needed)
openai>=1.3.0
anthropic>=0.7.0

# Utilities
python-dotenv>=1.0.0
requests>=2.31.0
aiohttp>=3.9.0

# Optional features
redis>=5.0.0
qdrant-client>=2.4.0
wandb>=0.15.0
"""

FULL_REQUIREMENTS = """# ToolWeaver Example - Full Dependencies

# Core packages
toolweaver>=0.6.0
python-dotenv>=1.0.0

# Azure services
azure-identity>=1.13.0
azure-cognitiveservices-vision-computervision>=9.0.0
azure-storage-blob>=12.18.0

# LLM providers
openai>=1.3.0
anthropic>=0.7.0
google-generativeai>=0.3.0

# Data processing
pandas>=2.0.0
numpy>=1.24.0
pillow>=10.0.0

# Async/concurrency
aiohttp>=3.9.0
asyncio-contextmanager>=1.0.0

# Caching & search
redis>=5.0.0
qdrant-client>=2.4.0

# Monitoring & observability
wandb>=0.15.0
prometheus-client>=0.19.0

# Utilities
requests>=2.31.0
pydantic>=2.0.0
click>=8.0.0
"""

def create_requirements_files():
    """Create requirements.txt for examples"""
    examples_path = Path('examples')
    
    print("=" * 70)
    print("CREATING requirements.txt FOR EXAMPLES")
    print("=" * 70)
    
    created = 0
    skipped = 0
    
    for example_dir in sorted(examples_path.iterdir()):
        if not example_dir.is_dir() or example_dir.name.startswith('.'):
            continue
        
        req_path = example_dir / 'requirements.txt'
        
        # Skip if already exists
        if req_path.exists():
            skipped += 1
            continue
        
        # Decide which requirements to use
        # Full for complex examples, common for simple ones
        complex_examples = [
            '04-vector-search-discovery',
            '06-monitoring-observability',
            '07-caching-optimization',
            '10-multi-step-planning',
            '13-complete-pipeline',
            '22-end-to-end-showcase',
        ]
        
        if example_dir.name in complex_examples:
            requirements = FULL_REQUIREMENTS
        else:
            requirements = COMMON_REQUIREMENTS
        
        with open(req_path, 'w') as f:
            f.write(requirements)
        
        created += 1
        print(f"✓ Created {example_dir.name}/requirements.txt")
    
    print(f"\n✓ Created {created} requirements.txt files")
    print(f"⊘ Skipped {skipped} examples (already have requirements.txt)")

if __name__ == '__main__':
    create_requirements_files()
