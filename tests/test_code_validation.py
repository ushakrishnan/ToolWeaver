import pytest

from orchestrator._internal.validation import (
    validate_code,
    InvalidCodeError,
    InvalidInputError,
)


def test_validate_code_blocks_import_and_eval():
    with pytest.raises(InvalidCodeError):
        validate_code("import os\nos.system('echo hi')")
    with pytest.raises(InvalidCodeError):
        validate_code("eval('1+1')")


def test_validate_code_blocks_file_io():
    with pytest.raises(InvalidCodeError):
        validate_code("open('x.txt','w')")


def test_validate_code_allows_import_when_flag_set():
    # Should allow import lines when allow_imports=True, but still block dangerous calls
    with pytest.raises(InvalidCodeError):
        validate_code("import os\nos.system('echo hi')", allow_imports=True)
    # Simple import without dangerous calls passes
    assert validate_code("import math\nx = math.sqrt(4)", allow_imports=True).startswith("import math")


def test_validate_code_length_limit():
    long_code = "x=1\n" * 60000
    with pytest.raises(InvalidInputError):
        validate_code(long_code)
