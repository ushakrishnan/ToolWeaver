# How to Create Skill Packages

Step-by-step guide to package reusable tools as skills for sharing across projects and teams.

## Prerequisites

- Working ToolWeaver project
- Basic understanding of [MCP tools](add-a-tool.md)
- Familiarity with [Skill Library](../reference/deep-dives/skill-library.md)

## What You'll Accomplish

By the end of this guide, you'll have:

✅ Tool saved as reusable skill  
✅ Skill loaded in multiple workflows  
✅ Skill versioning and updates  
✅ Shared skill library for team  
✅ Skill validation and testing  

**Estimated time:** 20 minutes

---

## Step 1: Save Tool as Skill

### 1.1 Basic Skill Creation

```python
from orchestrator import mcp_tool
from orchestrator.skills import save_tool_as_skill

# Define a reusable tool
@mcp_tool(domain="receipts", description="Extract text from receipt")
async def receipt_ocr(image_uri: str) -> dict:
    """Extract text from receipt image."""
    # Implementation
    return {"text": "Receipt data", "confidence": 0.98}

# Save as skill
save_tool_as_skill(
    tool=receipt_ocr,
    skill_name="receipt_ocr_v1",
    skill_path="skills/",
    version="1.0.0",
    description="OCR extraction for receipts"
)

print("✓ Skill saved: skills/receipt_ocr_v1.json")
```

### 1.2 Skill File Format

The saved skill (`skills/receipt_ocr_v1.json`):

```json
{
  "name": "receipt_ocr_v1",
  "version": "1.0.0",
  "domain": "receipts",
  "description": "Extract text from receipt",
  "schema": {
    "type": "object",
    "properties": {
      "image_uri": {
        "type": "string",
        "description": "URI of receipt image"
      }
    },
    "required": ["image_uri"]
  },
  "implementation": "receipt_ocr",
  "created_at": "2024-12-26T10:30:00Z",
  "tags": ["ocr", "receipts", "vision"]
}
```

---

## Step 2: Load and Use Skills

### 2.1 Load Skill in Workflow

```python
from orchestrator.skills import load_tool_from_skill

# Load skill
receipt_ocr_tool = load_tool_from_skill(
    skill_name="receipt_ocr_v1",
    skill_path="skills/"
)

# Use loaded skill
result = await receipt_ocr_tool.execute({"image_uri": "receipt_123.jpg"})
print(result)
```

### 2.2 Load All Skills from Directory

```python
from orchestrator.skills import load_skills_from_directory

# Load all skills
skills = load_skills_from_directory("skills/")

print(f"Loaded {len(skills)} skills:")
for skill in skills:
    print(f"  - {skill.name} v{skill.version}")

# Register with orchestrator
for skill in skills:
    orchestrator.register_tool(skill)
```

---

## Step 3: Version Skills

### 3.1 Semantic Versioning

```python
# Version 1.0.0 - Initial release
save_tool_as_skill(
    tool=receipt_ocr,
    skill_name="receipt_ocr",
    version="1.0.0"
)

# Version 1.1.0 - Add confidence threshold parameter
@mcp_tool(domain="receipts")
async def receipt_ocr_v2(image_uri: str, min_confidence: float = 0.8) -> dict:
    """Extract text with configurable confidence threshold."""
    # Enhanced implementation
    return {"text": "data", "confidence": 0.95}

save_tool_as_skill(
    tool=receipt_ocr_v2,
    skill_name="receipt_ocr",
    version="1.1.0"
)

# Version 2.0.0 - Breaking change (different return format)
@mcp_tool(domain="receipts")
async def receipt_ocr_v3(image_uri: str) -> dict:
    """Extract text with structured line items."""
    return {
        "lines": [{"text": "Item 1", "bbox": [0, 0, 100, 20]}],
        "confidence": 0.98
    }

save_tool_as_skill(
    tool=receipt_ocr_v3,
    skill_name="receipt_ocr",
    version="2.0.0"
)
```

### 3.2 Load Specific Version

```python
from orchestrator.skills import load_skill_version

# Load specific version
tool_v1 = load_skill_version("receipt_ocr", version="1.0.0")
tool_v2 = load_skill_version("receipt_ocr", version="2.0.0")

# Load latest version
tool_latest = load_skill_version("receipt_ocr", version="latest")
```

---

## Step 4: Create Shared Skill Library

### 4.1 Directory Structure

```
skills/
├── receipts/
│   ├── receipt_ocr_v1.0.0.json
│   ├── receipt_ocr_v1.1.0.json
│   ├── parse_items_v1.0.0.json
│   └── categorize_v1.0.0.json
├── analysis/
│   ├── financial_analysis_v1.0.0.json
│   └── risk_assessment_v1.0.0.json
└── index.json
```

### 4.2 Skill Index

**File:** `skills/index.json`

```json
{
  "skills": [
    {
      "name": "receipt_ocr",
      "latest_version": "1.1.0",
      "domain": "receipts",
      "description": "Extract text from receipts",
      "tags": ["ocr", "vision"],
      "versions": ["1.0.0", "1.1.0"]
    },
    {
      "name": "financial_analysis",
      "latest_version": "1.0.0",
      "domain": "analysis",
      "description": "Analyze financial data",
      "tags": ["finance", "analysis"],
      "versions": ["1.0.0"]
    }
  ]
}
```

### 4.3 Skill Library Manager

```python
import json
from pathlib import Path
from typing import List, Optional

class SkillLibrary:
    """Manage shared skill library."""
    
    def __init__(self, library_path: str = "skills/"):
        self.library_path = Path(library_path)
        self.index_file = self.library_path / "index.json"
        self.index = self._load_index()
    
    def _load_index(self) -> dict:
        """Load skill index."""
        if not self.index_file.exists():
            return {"skills": []}
        
        with open(self.index_file) as f:
            return json.load(f)
    
    def _save_index(self):
        """Save skill index."""
        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2)
    
    def add_skill(
        self,
        name: str,
        version: str,
        domain: str,
        description: str,
        tags: List[str] = None
    ):
        """Add skill to library index."""
        
        # Find existing skill entry
        skill_entry = next(
            (s for s in self.index["skills"] if s["name"] == name),
            None
        )
        
        if skill_entry:
            # Update existing
            if version not in skill_entry["versions"]:
                skill_entry["versions"].append(version)
            skill_entry["latest_version"] = version
        else:
            # Create new entry
            self.index["skills"].append({
                "name": name,
                "latest_version": version,
                "domain": domain,
                "description": description,
                "tags": tags or [],
                "versions": [version]
            })
        
        self._save_index()
    
    def list_skills(self, domain: str = None, tag: str = None) -> List[dict]:
        """List skills with optional filtering."""
        
        skills = self.index["skills"]
        
        if domain:
            skills = [s for s in skills if s["domain"] == domain]
        
        if tag:
            skills = [s for s in skills if tag in s.get("tags", [])]
        
        return skills
    
    def get_skill_info(self, name: str) -> Optional[dict]:
        """Get skill metadata."""
        return next(
            (s for s in self.index["skills"] if s["name"] == name),
            None
        )

# Usage
library = SkillLibrary("skills/")

# Add skill to library
library.add_skill(
    name="receipt_ocr",
    version="1.1.0",
    domain="receipts",
    description="Extract text from receipts",
    tags=["ocr", "vision"]
)

# List all receipt skills
receipt_skills = library.list_skills(domain="receipts")
for skill in receipt_skills:
    print(f"{skill['name']} v{skill['latest_version']}: {skill['description']}")
```

---

## Step 5: Validate Skills

### 5.1 Schema Validation

```python
from orchestrator.skills import validate_skill_schema

def validate_skill(skill_path: str) -> bool:
    """Validate skill file format and schema."""
    
    try:
        with open(skill_path) as f:
            skill_data = json.load(f)
        
        # Check required fields
        required = ["name", "version", "domain", "description", "schema"]
        for field in required:
            if field not in skill_data:
                print(f"✗ Missing required field: {field}")
                return False
        
        # Validate schema format
        if not validate_skill_schema(skill_data["schema"]):
            print("✗ Invalid schema format")
            return False
        
        print(f"✓ Skill {skill_data['name']} v{skill_data['version']} is valid")
        return True
    
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False

# Validate all skills
import glob

for skill_file in glob.glob("skills/**/*.json", recursive=True):
    if skill_file.endswith("index.json"):
        continue
    validate_skill(skill_file)
```

### 5.2 Test Skill Execution

```python
async def test_skill(skill_name: str, test_cases: list):
    """Test skill with sample inputs."""
    
    # Load skill
    tool = load_tool_from_skill(skill_name)
    
    print(f"Testing {skill_name}...")
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases):
        try:
            result = await tool.execute(test_case["input"])
            
            # Validate output
            if test_case.get("expected"):
                if result == test_case["expected"]:
                    print(f"  ✓ Test {i+1} passed")
                    passed += 1
                else:
                    print(f"  ✗ Test {i+1} failed: unexpected output")
                    failed += 1
            else:
                print(f"  ✓ Test {i+1} executed")
                passed += 1
        
        except Exception as e:
            print(f"  ✗ Test {i+1} failed: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return passed == len(test_cases)

# Usage
test_cases = [
    {"input": {"image_uri": "test1.jpg"}},
    {"input": {"image_uri": "test2.jpg"}},
]

await test_skill("receipt_ocr", test_cases)
```

---

## Step 6: Sync Skill Updates

### 6.1 Update Skill from Source

```python
from orchestrator.skills import sync_skill_from_source

# Update skill when source tool changes
@mcp_tool(domain="receipts")
async def receipt_ocr_updated(image_uri: str, language: str = "en") -> dict:
    """Extract text with language support."""
    # New implementation
    return {"text": "data", "language": language}

# Sync skill (creates new version)
sync_skill_from_source(
    source_tool=receipt_ocr_updated,
    skill_name="receipt_ocr",
    new_version="1.2.0",
    skill_path="skills/"
)

print("✓ Skill updated to v1.2.0")
```

### 6.2 Batch Update Multiple Skills

```python
async def update_all_skills_from_source(tools: list):
    """Update all skills from their source tools."""
    
    for tool in tools:
        skill_name = tool.__name__
        
        # Get current version from library
        skill_info = library.get_skill_info(skill_name)
        if not skill_info:
            print(f"⊗ Skill {skill_name} not in library")
            continue
        
        current_version = skill_info["latest_version"]
        
        # Increment minor version
        major, minor, patch = current_version.split(".")
        new_version = f"{major}.{int(minor)+1}.{patch}"
        
        # Sync
        sync_skill_from_source(
            source_tool=tool,
            skill_name=skill_name,
            new_version=new_version
        )
        
        print(f"✓ Updated {skill_name}: {current_version} → {new_version}")
```

---

## Step 7: Share Skills with Team

### 7.1 Package Skills for Distribution

```bash
# Create distribution package
cd skills/
tar -czf skills-v1.0.tar.gz receipts/ analysis/ index.json

# Share via file system or cloud storage
# aws s3 cp skills-v1.0.tar.gz s3://company-skills/
```

### 7.2 Install Skills from Package

```python
import tarfile
import shutil

def install_skill_package(package_path: str, install_dir: str = "skills/"):
    """Install skills from package."""
    
    # Extract package
    with tarfile.open(package_path, "r:gz") as tar:
        tar.extractall(install_dir)
    
    print(f"✓ Skills installed to {install_dir}")
    
    # Load library index
    library = SkillLibrary(install_dir)
    skills = library.list_skills()
    
    print(f"Available skills: {len(skills)}")
    for skill in skills:
        print(f"  - {skill['name']} v{skill['latest_version']}")

# Usage
install_skill_package("skills-v1.0.tar.gz")
```

---

## Verification

Test your skill packaging:

```python
async def verify_skill_packaging():
    """Verify skill creation and loading."""
    
    print("Testing skill packaging...")
    
    # Test 1: Save skill
    @mcp_tool(domain="test")
    async def test_tool(input: str) -> str:
        return f"output: {input}"
    
    save_tool_as_skill(
        tool=test_tool,
        skill_name="test_skill",
        version="1.0.0",
        skill_path="test_skills/"
    )
    print("✓ Skill saved")
    
    # Test 2: Load skill
    loaded_tool = load_tool_from_skill("test_skill", "test_skills/")
    assert loaded_tool is not None
    print("✓ Skill loaded")
    
    # Test 3: Execute skill
    result = await loaded_tool.execute({"input": "test"})
    assert "output" in result
    print("✓ Skill execution working")
    
    # Cleanup
    shutil.rmtree("test_skills/")
    
    print("\n✅ All checks passed!")

await verify_skill_packaging()
```

---

## Common Issues

### Issue 1: Skill Load Fails

**Symptom:** `FileNotFoundError` when loading skill

**Solution:** Check skill path and file exists

```python
skill_path = Path("skills/receipt_ocr_v1.0.0.json")
if not skill_path.exists():
    print(f"✗ Skill not found: {skill_path}")
```

### Issue 2: Version Conflict

**Symptom:** Multiple versions loaded simultaneously

**Solution:** Use explicit version loading

```python
# Load specific version
tool = load_skill_version("receipt_ocr", version="1.0.0")
```

### Issue 3: Schema Drift

**Symptom:** Skill schema doesn't match current implementation

**Solution:** Re-run validation after upgrades

```python
# Validate all skills after upgrade
for skill_file in glob.glob("skills/**/*.json"):
    validate_skill(skill_file)
```

---

## Next Steps

- **Deep Dive:** [Skill Library](../reference/deep-dives/skill-library.md) - Advanced patterns
- **Deep Dive:** [Skills Packaging](../reference/deep-dives/skills-packaging.md) - Distribution strategies
- **Tutorial:** [Add a Tool](add-a-tool.md) - Create tools for packaging

## Related Guides

- [Extend with Plugins](extend-with-plugins.md) - Runtime extensions
- [Add a Tool](add-a-tool.md) - Create reusable tools
- [Orchestrate with Code](orchestrate-with-code.md) - Use skills in workflows
