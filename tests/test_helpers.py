"""Helper functions for testing pipelines"""

from pathlib import Path


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
