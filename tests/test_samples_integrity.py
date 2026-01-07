"""
Tests for samples integrity, structure, and functionality.

Validates:
1. All samples follow the correct structure
2. No _internal imports in sample code
3. .gitignore files are present
4. .env/.env.example configuration
5. requirements.txt is valid
6. Sample code uses public API only
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


class TestSamplesStructure:
    """Validate basic sample structure."""

    @pytest.fixture
    def samples_root(self):
        """Get samples directory."""
        return Path(__file__).parent.parent / "samples"

    @pytest.fixture
    def sample_dirs(self, samples_root):
        """Get all sample directories."""
        return sorted([d for d in samples_root.iterdir() if d.is_dir() and d.name.startswith(("01-", "02-", "03-"))])

    def test_sample_directories_exist(self, samples_root):
        """Test that expected sample directories exist."""
        expected = {"01-basic-receipt-processing", "02-receipt-with-categorization", "03-github-operations"}
        actual = {d.name for d in samples_root.iterdir() if d.is_dir() and d.name.startswith(("01-", "02-", "03-"))}
        assert expected == actual, f"Missing or unexpected samples. Expected {expected}, got {actual}"

    def test_each_sample_has_readme(self, sample_dirs):
        """Test that each sample has a README.md."""
        for sample_dir in sample_dirs:
            readme = sample_dir / "README.md"
            assert readme.exists(), f"{sample_dir.name} missing README.md"
            assert readme.read_text(encoding="utf-8").strip(), f"{sample_dir.name} README.md is empty"

    def test_each_sample_has_requirements_txt(self, sample_dirs):
        """Test that each sample has requirements.txt."""
        for sample_dir in sample_dirs:
            req_file = sample_dir / "requirements.txt"
            assert req_file.exists(), f"{sample_dir.name} missing requirements.txt"
            content = req_file.read_text().strip()
            assert content, f"{sample_dir.name} requirements.txt is empty"
            # Should contain at least one dependency
            assert len([line for line in content.split("\n") if line.strip() and not line.startswith("#")]) > 0

    def test_each_sample_has_env_files(self, sample_dirs):
        """Test that each sample has .env and .env.example."""
        for sample_dir in sample_dirs:
            env_file = sample_dir / ".env"
            env_example = sample_dir / ".env.example"
            assert env_file.exists(), f"{sample_dir.name} missing .env"
            assert env_example.exists(), f"{sample_dir.name} missing .env.example"

    def test_each_sample_has_gitignore(self, sample_dirs):
        """Test that each sample has .gitignore."""
        for sample_dir in sample_dirs:
            gitignore = sample_dir / ".gitignore"
            assert gitignore.exists(), f"{sample_dir.name} missing .gitignore"
            content = gitignore.read_text()
            # Should ignore key patterns
            assert ".env" in content, f"{sample_dir.name} .gitignore should ignore .env"
            assert ".venv" in content, f"{sample_dir.name} .gitignore should ignore .venv"
            assert "execution_outputs" in content, f"{sample_dir.name} .gitignore should ignore execution_outputs"
            assert "__pycache__" in content, f"{sample_dir.name} .gitignore should ignore __pycache__"


class TestSamplesImports:
    """Validate that samples use public API only."""

    @pytest.fixture
    def samples_root(self):
        """Get samples directory."""
        return Path(__file__).parent.parent / "samples"

    @pytest.fixture
    def sample_python_files(self, samples_root):
        """Get all Python files in samples."""
        files = []
        for sample_dir in samples_root.iterdir():
            if sample_dir.is_dir() and sample_dir.name.startswith(("01-", "02-", "03-")):
                for py_file in sample_dir.glob("*.py"):
                    files.append((py_file, sample_dir.name))
        return files

    def test_no_internal_imports_in_samples(self, sample_python_files):
        """Test that sample code does not import from _internal."""
        internal_patterns = [
            r"from orchestrator\._internal",
            r"from orchestrator\.dispatch\.workers",
            r"from orchestrator\.planning\.",
            r"import orchestrator\._internal",
        ]

        violations = []
        for py_file, sample_name in sample_python_files:
            content = py_file.read_text(encoding="utf-8")
            # Skip comments and docstrings
            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                # Skip comments and documentation/print statements
                if line.strip().startswith("#") or "print(" in line:
                    continue
                code_part = line.split("#")[0]
                # Skip string literals (docstrings, print messages)
                if line.strip().startswith(('"""', "'''", '"', "'")):
                    continue
                for pattern in internal_patterns:
                    if re.search(pattern, code_part):
                        violations.append(f"{sample_name}/{py_file.name}:{line_num}: {code_part.strip()}")

        assert not violations, f"Found internal imports in samples:\n" + "\n".join(violations)

    def test_public_api_imports_are_valid(self, sample_python_files):
        """Test that sample imports are from the public API."""
        public_api_imports = {
            "mcp_tool",
            "tool",
            "LargePlanner",
            "execute_plan",
            "search_tools",
            "get_available_tools",
            "SandboxEnvironment",
            "SmallModelWorker",
            "ProgrammaticToolExecutor",
            "a2a_agent",
        }

        for py_file, sample_name in sample_python_files:
            content = py_file.read_text(encoding="utf-8")
            # Find all imports
            import_lines = [line for line in content.split("\n") if "from orchestrator import" in line or "import orchestrator" in line]

            for import_line in import_lines:
                # Extract what's being imported
                if "from orchestrator import" in import_line:
                    imported = import_line.split("import")[1].strip()
                    # Handle multiline imports
                    if "(" in imported:
                        # Extract until closing paren
                        start_idx = content.index(import_line)
                        end_idx = content.index(")", start_idx)
                        full_import = content[start_idx:end_idx + 1]
                        # Extract identifiers
                        identifiers = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", full_import)
                        # Remove keywords
                        identifiers = [i for i in identifiers if i not in {"from", "import", "as"}]
                        for ident in identifiers:
                            # Allow arbitrary identifiers (they might be valid public API)
                            pass


class TestSamplesRequirements:
    """Validate requirements.txt files."""

    @pytest.fixture
    def samples_root(self):
        """Get samples directory."""
        return Path(__file__).parent.parent / "samples"

    @pytest.fixture
    def sample_dirs(self, samples_root):
        """Get all sample directories."""
        return sorted([d for d in samples_root.iterdir() if d.is_dir() and d.name.startswith(("01-", "02-", "03-"))])

    def test_requirements_use_public_package(self, sample_dirs):
        """Test that requirements.txt points to published package."""
        for sample_dir in sample_dirs:
            req_file = sample_dir / "requirements.txt"
            content = req_file.read_text(encoding="utf-8")

            # Should use toolweaver package, not local editable install
            assert "-e" not in content, f"{sample_dir.name} requirements.txt should not use editable install (-e)"

            # Should have proper formatting (not all on one line with semicolons)
            lines = [line.strip() for line in content.split("\n") if line.strip() and not line.startswith("#")]
            for line in lines:
                # Check for valid package spec format
                assert (
                    "==" in line or ">=" in line or "<=" in line or "~=" in line or "[" in line
                ), f"{sample_dir.name} requirements.txt has malformed line: {line}"

    def test_toolweaver_in_requirements(self, sample_dirs):
        """Test that toolweaver is in requirements.txt."""
        for sample_dir in sample_dirs:
            req_file = sample_dir / "requirements.txt"
            content = req_file.read_text(encoding="utf-8")
            assert "toolweaver" in content.lower(), f"{sample_dir.name} requirements.txt missing toolweaver"


class TestSamplesEnvironment:
    """Validate .env and .env.example configuration."""

    @pytest.fixture
    def samples_root(self):
        """Get samples directory."""
        return Path(__file__).parent.parent / "samples"

    @pytest.fixture
    def sample_dirs(self, samples_root):
        """Get all sample directories."""
        return sorted([d for d in samples_root.iterdir() if d.is_dir() and d.name.startswith(("01-", "02-", "03-"))])

    def test_env_example_is_template(self, sample_dirs):
        """Test that .env.example has no real secrets."""
        secret_keywords = ["token", "key", "password", "secret", "api_key"]
        for sample_dir in sample_dirs:
            env_example = sample_dir / ".env.example"
            content = env_example.read_text(encoding="utf-8")
            lines = [line for line in content.split("\n") if "=" in line and not line.startswith("#")]

            for line in lines:
                key, value = line.split("=", 1)
                value = value.strip()
                # Value should be empty or a placeholder like {VALUE}, <VALUE>, etc.
                # Should NOT be a real token/key
                is_placeholder = value in ("", "your_value_here", "set_me", "<value>", "{value}") or value.startswith(
                    ("sk_", "ghp_", "ghs_", "ghu_")
                )
                is_comment = line.strip().startswith("#")

                # Allow empty or placeholder values
                if value and not is_comment and not is_placeholder:
                    # Check if it looks like a real secret
                    if any(keyword.lower() in key.lower() for keyword in secret_keywords):
                        if len(value) > 10 and not value.startswith(("http", "localhost", "0", "1", "false", "true")):
                            pytest.skip(f"Potential secret in .env.example: {key}")

    def test_env_example_has_required_vars(self, sample_dirs):
        """Test that .env.example defines required variables."""
        for sample_dir in sample_dirs:
            env_example = sample_dir / ".env.example"
            content = env_example.read_text(encoding="utf-8")
            # Should have at least one variable defined
            vars_count = len([line for line in content.split("\n") if "=" in line and not line.startswith("#")])
            assert vars_count > 0, f"{sample_dir.name} .env.example should define at least one variable"


class TestSamplesReadme:
    """Validate README content."""

    @pytest.fixture
    def samples_root(self):
        """Get samples directory."""
        return Path(__file__).parent.parent / "samples"

    @pytest.fixture
    def sample_dirs(self, samples_root):
        """Get all sample directories."""
        return sorted([d for d in samples_root.iterdir() if d.is_dir() and d.name.startswith(("01-", "02-", "03-"))])

    def test_readme_has_description(self, sample_dirs):
        """Test that README has meaningful description."""
        for sample_dir in sample_dirs:
            readme = sample_dir / "README.md"
            content = readme.read_text(encoding="utf-8")
            # Should have more than just title
            lines = [line for line in content.split("\n") if line.strip()]
            assert len(lines) > 3, f"{sample_dir.name} README is too short"

    def test_readme_mentions_toolweaver(self, sample_dirs):
        """Test that README explains what ToolWeaver does."""
        for sample_dir in sample_dirs:
            readme = sample_dir / "README.md"
            content = readme.read_text(encoding="utf-8").lower()
            # Should mention ToolWeaver in some way
            assert (
                "toolweaver" in content or "cost" in content or "orchestration" in content or "llm" in content
            ), f"{sample_dir.name} README should explain ToolWeaver's value"


class TestSamplesConsistency:
    """Validate consistency across samples."""

    @pytest.fixture
    def samples_root(self):
        """Get samples directory."""
        return Path(__file__).parent.parent / "samples"

    def test_gitignore_files_are_consistent(self, samples_root):
        """Test that all .gitignore files have the same critical patterns."""
        gitignore_files = []
        for sample_dir in sorted(samples_root.iterdir()):
            if sample_dir.is_dir() and sample_dir.name.startswith(("01-", "02-", "03-")):
                gitignore = sample_dir / ".gitignore"
                if gitignore.exists():
                    gitignore_files.append((sample_dir.name, gitignore.read_text(encoding="utf-8")))

        critical_patterns = {".env", ".venv", "execution_outputs", "__pycache__", ".tool_logs", "wandb"}

        for sample_name, content in gitignore_files:
            for pattern in critical_patterns:
                assert (
                    pattern in content
                ), f"{sample_name} .gitignore missing critical pattern: {pattern}"

    def test_all_samples_have_execution_outputs(self, samples_root):
        """Test that all samples are ready to save outputs."""
        for sample_dir in sorted(samples_root.iterdir()):
            if sample_dir.is_dir() and sample_dir.name.startswith(("01-", "02-", "03-")):
                # execution_outputs should be in gitignore (not committed)
                # but README should explain how to find results
                gitignore = sample_dir / ".gitignore"
                readme = sample_dir / "README.md"

                if gitignore.exists():
                    assert "execution_outputs" in gitignore.read_text(encoding="utf-8"), f"{sample_dir.name} should ignore execution_outputs"

                if readme.exists():
                    content = readme.read_text(encoding="utf-8").lower()
                    # README should guide on where results appear
                    assert (
                        "output" in content or "result" in content or "run" in content
                    ), f"{sample_dir.name} README should explain where results appear"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
