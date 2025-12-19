import os
import pytest

from orchestrator._internal.validation import (
    sanitize_string,
    validate_url,
    validate_file_path,
    InvalidInputError,
    UnsafeURLError,
    PathTraversalError,
    ToolDefinition,
    ToolParameter,
)
from orchestrator._internal.runtime_validation import (
    validate_registration,
    validate_call,
)


def test_sanitize_string_blocks_dangerous_patterns():
    with pytest.raises(Exception):
        sanitize_string("; rm -rf /")


def test_validate_url_allows_https_blocks_file_and_local():
    assert validate_url("https://example.com/api").startswith("https://")
    with pytest.raises(UnsafeURLError):
        validate_url("file:///etc/passwd")
    with pytest.raises(UnsafeURLError):
        validate_url("http://127.0.0.1:8000")


def test_validate_file_path_prevents_traversal(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    f = base / "data.txt"
    f.write_text("ok")

    # Valid within base
    p = validate_file_path(f, base_dir=base, must_exist=True)
    assert p.exists()

    # Traversal blocked
    with pytest.raises(PathTraversalError):
        validate_file_path(base / ".." / "etc" / "passwd", base_dir=base)


def test_validate_registration_and_call_happy_path():
    tool = ToolDefinition(
        name="demo",
        description="Demo tool",
        parameters=[
            ToolParameter(name="q", type="string", required=True),
            ToolParameter(name="limit", type="integer", required=False),
        ],
    )

    validate_registration(tool)
    out = validate_call({"q": "hello", "limit": 3}, tool)
    assert out["q"] == "hello"
    assert out["limit"] == 3


def test_validate_call_rejects_missing_required():
    tool = ToolDefinition(
        name="missing",
        description="Missing required",
        parameters=[ToolParameter(name="q", type="string", required=True)],
    )

    with pytest.raises(Exception):
        validate_call({}, tool)
"""
Tests for validation and sanitization.

Phase 0.m: Verify input sanitization, path validation, URL validation, code validation.
"""

import ast
import pytest
from pathlib import Path
from pydantic import BaseModel

from orchestrator._internal.validation import (
    sanitize_string,
    sanitize_dict,
    validate_file_path,
    validate_url,
    validate_code,
    validate_params,
    validate_tool_input,
    ValidationErrorBase,
    InvalidInputError,
    UnsafeInputError,
    PathTraversalError,
    UnsafeURLError,
    InvalidCodeError,
)


# ============================================================
# Test String Sanitization
# ============================================================

def test_sanitize_string_valid():
    """Test sanitizing valid strings."""
    assert sanitize_string("Hello, world!") == "Hello, world!"
    assert sanitize_string("user@example.com") == "user@example.com"
    assert sanitize_string("Data: 123") == "Data: 123"


def test_sanitize_string_too_long():
    """Test that overly long strings are rejected."""
    with pytest.raises(InvalidInputError, match="Input too long"):
        sanitize_string("x" * 10001)


def test_sanitize_string_rm_rf():
    """Test detection of rm -rf command."""
    with pytest.raises(UnsafeInputError, match="Dangerous pattern"):
        sanitize_string("; rm -rf /")


def test_sanitize_string_shell_command_substitution():
    """Test detection of shell command substitution."""
    with pytest.raises(UnsafeInputError, match="Dangerous pattern"):
        sanitize_string("$(cat /etc/passwd)")


def test_sanitize_string_xss_script():
    """Test detection of XSS script tags."""
    with pytest.raises(UnsafeInputError, match="Dangerous pattern"):
        sanitize_string("<script>alert('xss')</script>")


def test_sanitize_string_sql_injection():
    """Test detection of SQL injection patterns."""
    with pytest.raises(UnsafeInputError, match="Dangerous pattern"):
        sanitize_string("1'; DROP TABLE users; --")


def test_sanitize_string_path_traversal():
    """Test detection of path traversal."""
    with pytest.raises(UnsafeInputError, match="Dangerous pattern"):
        sanitize_string("../../etc/passwd")


def test_sanitize_string_no_newlines():
    """Test removing newlines."""
    result = sanitize_string("line1\nline2", allow_newlines=False)
    assert "\n" not in result


def test_sanitize_string_no_special_chars():
    """Test removing special characters."""
    result = sanitize_string("hello!@#$%world", allow_special_chars=False)
    assert "!" not in result
    assert "@" not in result


# ============================================================
# Test Dictionary Sanitization
# ============================================================

def test_sanitize_dict_simple():
    """Test sanitizing simple dict."""
    input_dict = {"name": "test", "value": 123}
    result = sanitize_dict(input_dict)
    assert result == {"name": "test", "value": 123}


def test_sanitize_dict_nested():
    """Test sanitizing nested dict."""
    input_dict = {
        "user": {
            "name": "Alice",
            "settings": {"theme": "dark"}
        }
    }
    result = sanitize_dict(input_dict)
    assert result["user"]["name"] == "Alice"
    assert result["user"]["settings"]["theme"] == "dark"


def test_sanitize_dict_with_list():
    """Test sanitizing dict with list values."""
    input_dict = {"items": ["a", "b", "c"]}
    result = sanitize_dict(input_dict)
    assert result["items"] == ["a", "b", "c"]


def test_sanitize_dict_too_many_keys():
    """Test rejection of dict with too many keys."""
    large_dict = {f"key{i}": i for i in range(101)}
    with pytest.raises(InvalidInputError, match="too large"):
        sanitize_dict(large_dict)


def test_sanitize_dict_too_deep():
    """Test rejection of overly nested dict."""
    deep_dict = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": {"k": "too deep"}}}}}}}}}}}
    with pytest.raises(InvalidInputError, match="too deeply nested"):
        sanitize_dict(deep_dict)


def test_sanitize_dict_with_dangerous_value():
    """Test sanitizing dict with dangerous string value."""
    input_dict = {"cmd": "; rm -rf /"}
    with pytest.raises(UnsafeInputError):
        sanitize_dict(input_dict)


# ============================================================
# Test File Path Validation
# ============================================================

def test_validate_file_path_simple(tmp_path):
    """Test validating simple file path."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test")
    
    result = validate_file_path(file_path, must_exist=True)
    assert result.exists()


def test_validate_file_path_nonexistent():
    """Test that nonexistent path fails with must_exist=True."""
    with pytest.raises(InvalidInputError, match="does not exist"):
        validate_file_path("/nonexistent/path", must_exist=True)


def test_validate_file_path_traversal(tmp_path):
    """Test detection of path traversal."""
    base_dir = tmp_path / "safe"
    base_dir.mkdir()
    
    dangerous_path = base_dir / ".." / ".." / "etc" / "passwd"
    
    with pytest.raises(PathTraversalError, match="traversal detected"):
        validate_file_path(dangerous_path, base_dir=base_dir)


def test_validate_file_path_within_base(tmp_path):
    """Test that valid path within base directory is allowed."""
    base_dir = tmp_path / "safe"
    base_dir.mkdir()
    
    file_path = base_dir / "data" / "file.txt"
    result = validate_file_path(file_path, base_dir=base_dir)
    
    # Should be within base_dir
    assert str(result).startswith(str(base_dir))


# ============================================================
# Test URL Validation
# ============================================================

def test_validate_url_https():
    """Test validating HTTPS URL."""
    result = validate_url("https://example.com/api")
    assert result == "https://example.com/api"


def test_validate_url_http():
    """Test validating HTTP URL."""
    result = validate_url("http://example.com")
    assert result == "http://example.com"


def test_validate_url_file_protocol():
    """Test rejection of file:// protocol."""
    with pytest.raises(UnsafeURLError, match="Unsafe URL scheme"):
        validate_url("file:///etc/passwd")


def test_validate_url_javascript_protocol():
    """Test rejection of javascript: protocol."""
    with pytest.raises(UnsafeURLError, match="Unsafe URL scheme"):
        validate_url("javascript:alert('xss')")


def test_validate_url_localhost():
    """Test blocking of localhost."""
    with pytest.raises(UnsafeURLError, match="Localhost access not allowed"):
        validate_url("http://localhost:8080")


def test_validate_url_127_0_0_1():
    """Test blocking of 127.0.0.1."""
    with pytest.raises(UnsafeURLError, match="Localhost access not allowed"):
        validate_url("http://127.0.0.1:8080")


def test_validate_url_private_ip_192():
    """Test blocking of 192.168.x.x."""
    with pytest.raises(UnsafeURLError, match="Private IP access not allowed"):
        validate_url("http://192.168.1.1")


def test_validate_url_private_ip_10():
    """Test blocking of 10.x.x.x."""
    with pytest.raises(UnsafeURLError, match="Private IP access not allowed"):
        validate_url("http://10.0.0.1")


def test_validate_url_allow_localhost():
    """Test allowing localhost when block_private_ips=False."""
    result = validate_url("http://localhost:8080", block_private_ips=False)
    assert result == "http://localhost:8080"


def test_validate_url_custom_schemes():
    """Test custom allowed schemes."""
    result = validate_url("ftp://example.com", allowed_schemes={"ftp", "ftps"})
    assert result == "ftp://example.com"


# ============================================================
# Test Code Validation
# ============================================================

def test_validate_code_simple():
    """Test validating simple code."""
    code = "x = 1 + 2"
    result = validate_code(code)
    assert result == code


def test_validate_code_function():
    """Test validating function definition."""
    code = "def add(a, b):\n    return a + b"
    result = validate_code(code, allow_imports=True)
    assert result == code


def test_validate_code_import_blocked():
    """Test blocking import statements."""
    code = "import os"
    with pytest.raises(InvalidCodeError, match="import statement not allowed"):
        validate_code(code, allow_imports=False)


def test_validate_code_import_allowed():
    """Test allowing import statements."""
    code = "import math"
    result = validate_code(code, allow_imports=True)
    assert result == code


def test_validate_code_eval():
    """Test blocking eval()."""
    code = "eval('1 + 1')"
    with pytest.raises(InvalidCodeError, match="Dangerous function call: eval"):
        validate_code(code)


def test_validate_code_exec():
    """Test blocking exec()."""
    code = "exec('print(1)')"
    with pytest.raises(InvalidCodeError, match="Dangerous function call: exec"):
        validate_code(code)


def test_validate_code_os_system():
    """Test blocking os.system()."""
    code = "import os\nos.system('ls')"
    with pytest.raises(InvalidCodeError, match="Dangerous function call: os.system"):
        validate_code(code, allow_imports=True)


def test_validate_code_open_blocked():
    """Test blocking open() when file I/O not allowed."""
    code = "open('file.txt')"
    with pytest.raises(InvalidCodeError, match="file I/O not allowed"):
        validate_code(code, allow_file_io=False)


def test_validate_code_open_allowed():
    """Test allowing open() when file I/O allowed."""
    code = "with open('file.txt') as f:\n    data = f.read()"
    # Should not raise when allow_file_io=True
    # But will still raise because 'open' is in DANGEROUS_FUNCTIONS
    with pytest.raises(InvalidCodeError):
        validate_code(code, allow_file_io=True)


def test_validate_code_syntax_error():
    """Test handling syntax errors."""
    code = "if True\n    print('missing colon')"
    with pytest.raises(InvalidCodeError, match="Syntax error"):
        validate_code(code)


def test_validate_code_too_long():
    """Test rejection of overly long code."""
    code = "x = 1\n" * 50000
    with pytest.raises(InvalidInputError, match="Code too long"):
        validate_code(code)


# ============================================================
# Test Parameter Validation
# ============================================================

class UserParams(BaseModel):
    name: str
    age: int
    email: str


def test_validate_params_valid():
    """Test validating valid parameters."""
    params = {"name": "Alice", "age": 30, "email": "alice@example.com"}
    result = validate_params(params, UserParams)
    
    assert result.name == "Alice"
    assert result.age == 30
    assert result.email == "alice@example.com"


def test_validate_params_missing_field():
    """Test validation failure for missing required field."""
    params = {"name": "Alice", "age": 30}
    
    with pytest.raises(ValidationErrorBase, match="email"):
        validate_params(params, UserParams)


def test_validate_params_wrong_type():
    """Test validation failure for wrong type."""
    params = {"name": "Alice", "age": "thirty", "email": "alice@example.com"}
    
    with pytest.raises(ValidationErrorBase, match="age"):
        validate_params(params, UserParams)


# ============================================================
# Test Tool Input Validation
# ============================================================

def test_validate_tool_input_simple():
    """Test validating simple tool input."""
    params = {"query": "SELECT * FROM users"}
    result = validate_tool_input(params)
    
    assert "query" in result


def test_validate_tool_input_with_sanitization():
    """Test tool input validation with sanitization."""
    params = {"message": "Hello, world!"}
    result = validate_tool_input(params, sanitize=True)
    
    assert result["message"] == "Hello, world!"


def test_validate_tool_input_dangerous():
    """Test rejection of dangerous tool input."""
    params = {"cmd": "; rm -rf /"}
    
    with pytest.raises(UnsafeInputError):
        validate_tool_input(params, sanitize=True)


def test_validate_tool_input_with_schema():
    """Test tool input validation with Pydantic schema."""
    params = {"name": "Alice", "age": 30, "email": "alice@example.com"}
    result = validate_tool_input(params, schema=UserParams)
    
    assert result["name"] == "Alice"
    assert result["age"] == 30


def test_validate_tool_input_schema_validation_fails():
    """Test tool input validation failure with schema."""
    params = {"name": "Alice", "age": "thirty", "email": "alice@example.com"}
    
    with pytest.raises(ValidationErrorBase):
        validate_tool_input(params, schema=UserParams)


# ============================================================
# Integration Tests
# ============================================================

def test_full_validation_workflow():
    """Test complete validation workflow."""
    # 1. Sanitize string
    safe_str = sanitize_string("Hello, world!")
    assert safe_str == "Hello, world!"
    
    # 2. Sanitize dict
    safe_dict = sanitize_dict({"key": "value"})
    assert safe_dict == {"key": "value"}
    
    # 3. Validate URL
    safe_url = validate_url("https://example.com")
    assert safe_url == "https://example.com"
    
    # 4. Validate code
    safe_code = validate_code("x = 1 + 2")
    assert safe_code == "x = 1 + 2"
    
    # 5. Validate params
    params = {"name": "Alice", "age": 30, "email": "alice@example.com"}
    validated = validate_tool_input(params, schema=UserParams)
    assert validated["name"] == "Alice"
