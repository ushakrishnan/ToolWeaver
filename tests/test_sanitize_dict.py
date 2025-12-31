import pytest

from orchestrator._internal.validation import (
    InvalidInputError,
    sanitize_dict,
)


def test_sanitize_dict_depth_limit():
    deep = {"a": {"b": {"c": {"d": {"e": {"f": {"g": "x"}}}}}}}
    # default max_depth=10; ensure it handles nested dicts
    out = sanitize_dict(deep)
    assert out["a"]["b"]["c"]["d"]["e"]["f"]["g"] == "x"

    # Exceed depth by configuring a lower threshold
    with pytest.raises(InvalidInputError):
        sanitize_dict(deep, max_depth=2)


def test_sanitize_dict_key_count_limit():
    big = {str(i): i for i in range(0, 105)}
    with pytest.raises(InvalidInputError):
        sanitize_dict(big, max_keys=100)
