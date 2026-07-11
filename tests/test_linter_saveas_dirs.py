"""Tests for linter saveas directory containment check, including partial resolution."""
import yaml
from pathlib import Path
from llmflow.utils.linter import lint_pipeline_full

# A real function the linter can resolve for schema-valid function steps.
_FN = "tests.test_helpers.mock_function"


def _write_pipeline(tmp_path: Path, content: dict) -> str:
    p = tmp_path / "pipeline.yaml"
    p.write_text(yaml.dump(content))
    return str(p)


def _step(name: str, saveas: str) -> dict:
    return {
        "name": name,
        "type": "function",
        "function": _FN,
        "outputs": "result",
        "saveas": saveas,
    }


def _base(tmp_path: Path, **kwargs) -> dict:
    base = {
        "name": "Test",
        "version": 1.0,
        "steps": [],
    }
    base.update(kwargs)
    return base


class TestSaveasDirectoryCheck:
    """Linter warns when saveas paths fall outside declared directories."""

    def test_fully_resolved_path_under_intermediate_no_warning(self, tmp_path):
        pipeline = _base(
            tmp_path,
            intermediate_file_directory="outputs/intermediate",
            steps=[_step("do_work", "outputs/intermediate/build-book/result.json")],
        )
        result = lint_pipeline_full(_write_pipeline(tmp_path, pipeline))
        dir_warnings = [w for w in result.warnings if "saveas path" in w and "not under" in w]
        assert not dir_warnings, f"Unexpected warning: {dir_warnings}"

    def test_fully_resolved_path_under_output_no_warning(self, tmp_path):
        pipeline = _base(
            tmp_path,
            output_file_directory="outputs/book-summaries",
            steps=[_step("summary", "outputs/book-summaries/57-PHM/result.json")],
        )
        result = lint_pipeline_full(_write_pipeline(tmp_path, pipeline))
        dir_warnings = [w for w in result.warnings if "saveas path" in w and "not under" in w]
        assert not dir_warnings, f"Unexpected warning: {dir_warnings}"

    def test_path_outside_both_dirs_produces_warning(self, tmp_path):
        pipeline = _base(
            tmp_path,
            intermediate_file_directory="outputs/intermediate",
            output_file_directory="outputs/book-summaries",
            steps=[_step("stray", "outputs/segmentation-review/result.md")],
        )
        result = lint_pipeline_full(_write_pipeline(tmp_path, pipeline))
        dir_warnings = [w for w in result.warnings if "saveas path" in w and "not under" in w]
        assert len(dir_warnings) == 1
        assert "stray" in dir_warnings[0]

    def test_partially_resolved_intermediate_prefix_no_warning(self, tmp_path):
        """${build_dir}/${runtime_var}/... — prefix resolves to outputs/intermediate/build-book
        which is under intermediate_file_directory."""
        pipeline = _base(
            tmp_path,
            intermediate_file_directory="outputs/intermediate",
            variables={"build_dir": "outputs/intermediate/build-book"},
            steps=[_step("book_step", "${build_dir}/${runtime_chapter}/result.json")],
        )
        result = lint_pipeline_full(_write_pipeline(tmp_path, pipeline))
        dir_warnings = [w for w in result.warnings if "saveas path" in w and "not under" in w]
        assert not dir_warnings, f"Unexpected warning: {dir_warnings}"

    def test_partially_resolved_output_prefix_no_warning(self, tmp_path):
        """Path whose resolvable prefix is under output_file_directory should not warn."""
        pipeline = _base(
            tmp_path,
            output_file_directory="outputs/book-summaries",
            variables={
                "book_output_dir": "outputs/book-summaries/57-PHM",
                "book_output_prefix": "outputs/book-summaries/57-PHM/57-PHM",
            },
            steps=[_step("build_hierarchy", "${book_output_prefix}-book-summary.json")],
        )
        result = lint_pipeline_full(_write_pipeline(tmp_path, pipeline))
        dir_warnings = [w for w in result.warnings if "saveas path" in w and "not under" in w]
        assert not dir_warnings, f"Unexpected warning: {dir_warnings}"

    def test_root_level_dir_key_resolved_during_lint(self, tmp_path):
        """intermediate_file_directory as a root-level key (not in variables:) must be
        included in the linter's resolution context so derived saveas paths resolve."""
        pipeline = _base(
            tmp_path,
            intermediate_file_directory="outputs/intermediate",
            variables={"build_dir": "${intermediate_file_directory}/build-book"},
            steps=[_step("step_a", "${build_dir}/${runtime_book}/result.json")],
        )
        result = lint_pipeline_full(_write_pipeline(tmp_path, pipeline))
        dir_warnings = [w for w in result.warnings if "saveas path" in w and "not under" in w]
        assert not dir_warnings, f"Unexpected warning: {dir_warnings}"

    def test_no_declared_dirs_no_containment_check(self, tmp_path):
        """When neither directory is declared, the containment check is skipped."""
        pipeline = _base(
            tmp_path,
            steps=[_step("step_a", "anywhere/result.json")],
        )
        result = lint_pipeline_full(_write_pipeline(tmp_path, pipeline))
        dir_warnings = [w for w in result.warnings if "not under intermediate_file_directory" in w]
        assert not dir_warnings

    def test_fully_unresolved_prefix_skipped_not_warned(self, tmp_path):
        """When the entire path starts with an unresolved runtime variable, the resolved
        prefix is empty — containment cannot be determined, so no warning is emitted."""
        pipeline = _base(
            tmp_path,
            intermediate_file_directory="outputs/intermediate",
            steps=[_step("dynamic_step", "${runtime_path}/result.json")],
        )
        result = lint_pipeline_full(_write_pipeline(tmp_path, pipeline))
        dir_warnings = [
            w for w in result.warnings
            if "saveas path" in w and "not under" in w and "dynamic_step" in w
        ]
        assert not dir_warnings, f"Should skip check when prefix is empty: {dir_warnings}"
