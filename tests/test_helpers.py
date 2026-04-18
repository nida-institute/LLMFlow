"""Helper functions for testing pipelines"""

from pathlib import Path


# ---------------------------------------------------------------------------
# Cursor sequence helpers for testing !window_advance
# ---------------------------------------------------------------------------

_cursor_seq: list = []


def set_cursor_seq(values):
    """Set up the cursor sequence for !window_advance tests."""
    global _cursor_seq
    _cursor_seq = list(values)


def cursor_pop(**_):
    """Pop next cursor value from the module-level sequence. Returns None when empty.

    Use as the inner step function in !window_advance tests:
        function: tests.test_helpers.cursor_pop
    """
    global _cursor_seq
    if _cursor_seq:
        return _cursor_seq.pop(0)
    return None


def mock_function(a, p):
    """Mock function for testing - concatenates parameters with underscore"""
    return f"{a}_{p}"


def transform_function(a, p):
    """Transform function for testing - concatenates parameters with underscore"""
    return f"{a}_{p}"


def save_text(path: str, content: str):
    """Write content to *path* and return the content string."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return content


def make_prefix(name: str) -> dict:
    """Return a dict with a 'prefix' key — simulates a cheap parse/setup step."""
    return {"prefix": name.lower().replace(" ", "_")}
