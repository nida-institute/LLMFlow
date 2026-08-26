"""Tests that package resources are correctly bundled and locatable.

These tests guard against the class of bug where a file is accessible during
development (repo-root path resolution) but missing from installed wheels
(no force-include declaration in pyproject.toml).

The original incident: data/models.json was absent from force-include, causing
a "Model metadata file not found" warning in every consumer project that
installed LLMFlow from a wheel.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import llmflow.modules.telemetry as telemetry_module
from llmflow.modules.telemetry import _find_models_file, _load_models_data

REPO_ROOT = Path(__file__).parent.parent

# ── Paths that code accesses via importlib.resources.files("llmflow") ────────
# If you add a new resource path here you must also add it to
# [tool.hatch.build.targets.wheel.force-include] in pyproject.toml.
IMPORTLIB_RESOURCE_PATHS = [
    "data/models.json",
    "docs/ai-context",
    "docs/audits",
]

# ── Paths that code accesses via Path(llmflow.__file__).parent / ... ─────────
# These must live inside src/llmflow/ — they are packaged automatically.
PACKAGE_INTERNAL_TEMPLATES = [
    "templates/sp/disciplines",
    "templates/sp/skills/audit-prompts",
    "templates/sp/skills/release",
]


# ─────────────────────────────────────────────────────────────────────────────
# force-include contract tests
# ─────────────────────────────────────────────────────────────────────────────

def test_force_include_source_paths_exist():
    """Every path accessed via importlib.resources must exist as a source file/dir."""
    for source_path in IMPORTLIB_RESOURCE_PATHS:
        full_path = REPO_ROOT / source_path
        assert full_path.exists(), (
            f"Resource source '{source_path}' not found at {full_path}.\n"
            "If this file was moved, update pyproject.toml force-include and the "
            "code that accesses it via importlib.resources."
        )


def test_force_include_declares_all_resource_paths():
    """pyproject.toml force-include must declare every path accessed via importlib.resources.

    This is the test that would have caught the data/models.json omission before
    it reached a consumer project.
    """
    pyproject_content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for source_path in IMPORTLIB_RESOURCE_PATHS:
        assert f'"{source_path}"' in pyproject_content, (
            f"'{source_path}' is not declared in pyproject.toml "
            "[tool.hatch.build.targets.wheel.force-include].\n"
            "Installed wheels will be missing this resource. Add:\n"
            f'  "{source_path}" = "llmflow/{source_path}"'
        )


def test_package_internal_templates_exist_in_src():
    """Templates accessed via Path(llmflow.__file__).parent must be inside src/llmflow/.

    Files inside src/llmflow/ are bundled automatically — no force-include needed.
    If a template moves outside that tree, it must be added to force-include instead.
    """
    pkg_root = REPO_ROOT / "src" / "llmflow"
    for template_path in PACKAGE_INTERNAL_TEMPLATES:
        full_path = pkg_root / template_path
        assert full_path.exists(), (
            f"Template '{template_path}' not found inside src/llmflow/.\n"
            "Templates must be inside the package directory to be included in wheels, "
            "or declared in pyproject.toml force-include."
        )


# ─────────────────────────────────────────────────────────────────────────────
# _find_models_file() behaviour tests
# ─────────────────────────────────────────────────────────────────────────────

def test_find_models_file_prefers_importlib_resources_when_available(tmp_path, monkeypatch):
    """_find_models_file() returns the importlib.resources path when it exists.

    This simulates the installed-wheel environment where data/models.json lives
    inside site-packages/llmflow/data/ and is found via importlib.resources.
    """
    monkeypatch.setattr(telemetry_module, "_models_cache", None)

    fake_models = tmp_path / "models.json"
    fake_models.write_text('{"models": {}}', encoding="utf-8")

    mock_ref = MagicMock()
    mock_ref.__str__ = MagicMock(return_value=str(fake_models))

    mock_pkg = MagicMock()
    mock_pkg.joinpath.return_value = mock_ref

    with patch("llmflow.modules.telemetry.importlib.resources.files", return_value=mock_pkg):
        result = _find_models_file()

    assert result == fake_models


def test_find_models_file_falls_back_to_dev_path_when_importlib_absent(monkeypatch):
    """_find_models_file() falls back to the repo-root path when importlib.resources fails.

    This simulates an editable/dev install where the file lives at data/models.json
    relative to the repo root rather than inside the package directory.
    """
    monkeypatch.setattr(telemetry_module, "_models_cache", None)

    mock_ref = MagicMock()
    mock_ref.__str__ = MagicMock(return_value="/nonexistent/path/models.json")

    mock_pkg = MagicMock()
    mock_pkg.joinpath.return_value = mock_ref

    with patch("llmflow.modules.telemetry.importlib.resources.files", return_value=mock_pkg):
        result = _find_models_file()

    expected = Path(telemetry_module.__file__).parent.parent.parent.parent / "data" / "models.json"
    assert result == expected


def test_find_models_file_falls_back_when_importlib_raises(monkeypatch):
    """_find_models_file() falls back gracefully when importlib.resources raises."""
    monkeypatch.setattr(telemetry_module, "_models_cache", None)

    with patch(
        "llmflow.modules.telemetry.importlib.resources.files",
        side_effect=Exception("package not found"),
    ):
        result = _find_models_file()

    expected = Path(telemetry_module.__file__).parent.parent.parent.parent / "data" / "models.json"
    assert result == expected


# ─────────────────────────────────────────────────────────────────────────────
# _load_models_data() fallback behaviour tests
# ─────────────────────────────────────────────────────────────────────────────

def test_load_models_data_returns_empty_fallback_when_file_missing(monkeypatch):
    """_load_models_data() returns an empty-but-valid dict when models.json is absent.

    Cost calculation is unavailable but the process should not crash.
    """
    monkeypatch.setattr(telemetry_module, "_models_cache", None)

    with patch(
        "llmflow.modules.telemetry._find_models_file",
        return_value=Path("/nonexistent/models.json"),
    ):
        result = _load_models_data()

    assert result["models"] == {}
    assert result["model_patterns"] == {}
    assert result["metadata_version"] == "0.0"


def test_load_models_data_returns_empty_fallback_on_invalid_json(monkeypatch, tmp_path):
    """_load_models_data() returns an empty-but-valid dict when models.json is malformed."""
    monkeypatch.setattr(telemetry_module, "_models_cache", None)

    bad_json = tmp_path / "models.json"
    bad_json.write_text("{ this is not valid json }", encoding="utf-8")

    with patch("llmflow.modules.telemetry._find_models_file", return_value=bad_json):
        result = _load_models_data()

    assert result["models"] == {}
    assert result["model_patterns"] == {}


def test_load_models_data_caches_result(monkeypatch, tmp_path):
    """_load_models_data() reads the file only once; subsequent calls use the cache."""
    monkeypatch.setattr(telemetry_module, "_models_cache", None)

    models_file = tmp_path / "models.json"
    models_file.write_text(
        '{"metadata_version": "1.0", "last_updated": "2026-01-01", "models": {}, "model_patterns": {}}',
        encoding="utf-8",
    )

    call_count = 0
    real_find = lambda: models_file  # noqa: E731

    def counting_find():
        nonlocal call_count
        call_count += 1
        return models_file

    with patch("llmflow.modules.telemetry._find_models_file", side_effect=counting_find):
        _load_models_data()
        _load_models_data()
        _load_models_data()

    assert call_count == 1, "_find_models_file should only be called once; result should be cached"
