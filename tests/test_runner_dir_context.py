"""Tests that root-level pipeline dir keys are seeded into the runtime context."""
import sys
import yaml
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from llmflow.runner import run_pipeline

# A real function the linter can resolve — needed because lint validates function names.
_FN = "tests.test_helpers.mock_function"


def _make_pipeline(tmp_path: Path, content: dict) -> str:
    p = tmp_path / "pipeline.yaml"
    p.write_text(yaml.dump(content))
    return str(p)


def _install_capture_func(captured: list) -> None:
    """Install a fake module whose capture_context records the full context."""
    mod = MagicMock()

    def capture_context(context=None):
        if context is not None:
            captured.append(dict(context))
        return "ok"

    mod.capture_context = capture_context
    sys.modules["_test_capture_mod"] = mod


def _capture_step(name: str = "cap") -> dict:
    return {
        "name": name,
        "type": "function",
        "function": "_test_capture_mod.capture_context",
    }


class TestRootLevelDirKeysInContext:
    """intermediate_file_directory and output_file_directory declared at pipeline root
    must be present in the runtime context so ${...} references resolve at runtime."""

    def test_intermediate_dir_seeded_into_context(self, tmp_path):
        captured = []
        _install_capture_func(captured)

        pipeline_path = _make_pipeline(tmp_path, {
            "name": "Test",
            "version": 1.0,
            "intermediate_file_directory": "outputs/intermediate",
            "steps": [_capture_step()],
        })

        run_pipeline(pipeline_path, skip_lint=True)

        assert captured, "capture_context was never called with context"
        assert captured[0].get("intermediate_file_directory") == "outputs/intermediate"

    def test_output_dir_seeded_into_context(self, tmp_path):
        captured = []
        _install_capture_func(captured)

        pipeline_path = _make_pipeline(tmp_path, {
            "name": "Test",
            "version": 1.0,
            "output_file_directory": "outputs/book-summaries",
            "steps": [_capture_step()],
        })

        run_pipeline(pipeline_path, skip_lint=True)

        assert captured, "capture_context was never called with context"
        assert captured[0].get("output_file_directory") == "outputs/book-summaries"

    def test_both_dirs_seeded_when_both_declared(self, tmp_path):
        captured = []
        _install_capture_func(captured)

        pipeline_path = _make_pipeline(tmp_path, {
            "name": "Test",
            "version": 1.0,
            "intermediate_file_directory": "outputs/intermediate",
            "output_file_directory": "outputs/book-summaries",
            "steps": [_capture_step()],
        })

        run_pipeline(pipeline_path, skip_lint=True)

        assert captured, "capture_context was never called with context"
        assert captured[0].get("intermediate_file_directory") == "outputs/intermediate"
        assert captured[0].get("output_file_directory") == "outputs/book-summaries"

    def test_absent_dirs_not_in_context(self, tmp_path):
        """When neither directory is declared, neither key pollutes the context."""
        captured = []
        _install_capture_func(captured)

        pipeline_path = _make_pipeline(tmp_path, {
            "name": "Test",
            "version": 1.0,
            "steps": [_capture_step()],
        })

        run_pipeline(pipeline_path, skip_lint=True)

        assert captured, "capture_context was never called with context"
        assert "intermediate_file_directory" not in captured[0]
        assert "output_file_directory" not in captured[0]

    def test_cli_vars_override_dir_declarations(self, tmp_path):
        """CLI --var should win over pipeline root declarations (vars override _dir_ctx)."""
        captured = []
        _install_capture_func(captured)

        pipeline_path = _make_pipeline(tmp_path, {
            "name": "Test",
            "version": 1.0,
            "intermediate_file_directory": "outputs/intermediate",
            "steps": [_capture_step()],
        })

        run_pipeline(
            pipeline_path,
            vars={"intermediate_file_directory": "custom/path"},
            skip_lint=True,
        )

        assert captured, "capture_context was never called with context"
        assert captured[0].get("intermediate_file_directory") == "custom/path"

    def test_derived_variable_resolves_using_dir_key(self, tmp_path):
        """A pipeline variable that references ${intermediate_file_directory} via ${...}
        should resolve fully because the root-level key is in context before variables
        are merged (allowing runtime resolve() calls to find it)."""
        captured = []
        _install_capture_func(captured)

        pipeline_path = _make_pipeline(tmp_path, {
            "name": "Test",
            "version": 1.0,
            "intermediate_file_directory": "outputs/intermediate",
            "variables": {
                "build_dir": "${intermediate_file_directory}/build-book",
            },
            "steps": [_capture_step()],
        })

        run_pipeline(pipeline_path, skip_lint=True)

        assert captured, "capture_context was never called with context"
        # The dir key must be present so saveas resolution (which calls resolve()) works.
        assert captured[0].get("intermediate_file_directory") == "outputs/intermediate"
        # The derived variable should have been evaluated (it's in the YAML variables block,
        # which is stored literally; resolve() expands it on use).
        assert "build_dir" in captured[0]
