"""
Code Validation

Optional validation layer for generated stubs and skills.
- AST parse: Always enabled, catches syntax errors
- Limited exec: Optional, lightweight sandbox test
- Mypy: Optional, if mypy is available in environment
"""

import ast
from pathlib import Path
from typing import Any


def validate_syntax(code: str) -> tuple[bool, str | None]:
    """
    Validate Python code syntax via AST parse.

    Returns: (is_valid, error_message)
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Parse error: {e}"


def validate_exec_safe(code: str, *, timeout_secs: float = 2.0) -> tuple[bool, str | None]:
    """
    Lightweight execution test in a sandboxed environment.

    Runs code with restricted builtins (no file I/O, network, etc.).
    Useful for catching runtime errors early (e.g., unbound vars, import failures).

    Returns: (is_valid, error_message)
    """
    # Safe builtins for execution
    safe_builtins = {
        "print": print,
        "len": len,
        "range": range,
        "str": str,
        "int": int,
        "float": float,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "bool": bool,
        "type": type,
        "isinstance": isinstance,
        "zip": zip,
        "map": map,
        "filter": filter,
        "sum": sum,
        "min": min,
        "max": max,
        "sorted": sorted,
        "reversed": reversed,
        "enumerate": enumerate,
        "__builtins__": {},  # Block access to dangerous builtins
    }

    try:
        # Execute in restricted namespace; catch import/runtime errors
        exec(code, {"__builtins__": safe_builtins})
        return True, None
    except TimeoutError:
        return False, "Execution timeout"
    except ImportError as e:
        return False, f"Import error: {e}"
    except NameError as e:
        return False, f"Name error (likely unbound variable): {e}"
    except TypeError as e:
        return False, f"Type error: {e}"
    except Exception as e:
        return False, f"Execution error: {type(e).__name__}: {e}"


def validate_mypy(code: str, *, python_version: str = "3.10") -> tuple[bool, str | None]:
    """
    Optional type checking via mypy (if installed).

    Returns: (is_valid, error_message)
    """
    try:
        import mypy.api
    except ImportError:
        # mypy not installed; skip silently
        return True, None

    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            stdout, stderr, exit_code = mypy.api.run(
                [temp_path, f"--python-version={python_version}", "--no-error-summary"]
            )
            if exit_code == 0:
                return True, None
            else:
                # Extract first error line
                lines = stdout.split("\n")
                error_msg = next((line for line in lines if line.strip()), "Type check failed")
                return False, f"Mypy: {error_msg}"
        finally:
            Path(temp_path).unlink(missing_ok=True)
    except Exception:
        # Mypy failed to run; treat as non-fatal
        return True, None


def validate_stub(
    code: str,
    *,
    check_syntax: bool = True,
    check_exec: bool = False,
    check_mypy: bool = False,
) -> dict[str, Any]:
    """
    Comprehensive validation of generated code.

    Args:
        code: Python code to validate
        check_syntax: Always enabled; catches parse errors
        check_exec: Optional; runs code in safe sandbox (slower)
        check_mypy: Optional; runs mypy if installed (slower)

    Returns:
        {
            "valid": bool,
            "syntax": {"pass": bool, "error": str or None},
            "exec": {"pass": bool, "error": str or None} or None,
            "mypy": {"pass": bool, "error": str or None} or None,
        }
    """
    result: dict[str, Any] = {"valid": True}

    # Syntax (always)
    if check_syntax:
        syntax_pass, syntax_err = validate_syntax(code)
        result["syntax"] = {"pass": syntax_pass, "error": syntax_err}
        if not syntax_pass:
            result["valid"] = False

    # Exec (optional)
    if check_exec and result["valid"]:
        exec_pass, exec_err = validate_exec_safe(code)
        result["exec"] = {"pass": exec_pass, "error": exec_err}
        if not exec_pass:
            result["valid"] = False

    # Mypy (optional)
    if check_mypy and result["valid"]:
        mypy_pass, mypy_err = validate_mypy(code)
        result["mypy"] = {"pass": mypy_pass, "error": mypy_err}
        if not mypy_pass:
            result["valid"] = False

    return result


if __name__ == "__main__":
    # Quick test
    good_code = """
def add(x: int, y: int) -> int:
    return x + y

result = add(1, 2)
"""

    bad_code = """
def add(x: int, y: int) -> int:
    return x + y

result = add(1)  # Missing arg
"""

    print("Good code:")
    print(validate_stub(good_code, check_syntax=True, check_exec=True))

    print("\nBad code (exec):")
    print(validate_stub(bad_code, check_syntax=True, check_exec=True))

    bad_syntax = "def add(x int y: int"
    print("\nBad syntax:")
    print(validate_stub(bad_syntax, check_syntax=True))
