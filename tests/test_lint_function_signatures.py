"""Tests: `sp lint` checks a function step's inputs against the callable's signature.

A `type: function` step has a contract — the signature of the function it names — and
these cover the name-level and arity-level mismatches that contract can catch statically.

Covers:
  - An input name the function does not accept
  - A required parameter the step does not supply
  - A `function:` path that does not import, and a name the module does not define
  - `context` is injected by the runner, so it is never reported as missing
  - `**kwargs` accepts unknown names, while a required named parameter stays required
  - `*args` lifts the positional upper bound
  - List-form `inputs:` is checked by arity, because names cannot bind positionally
  - Steps of other types, and non-dotted `function:` values, are skipped
  - Integration through `lint_pipeline_full`, which is the path `sp lint` runs
"""

import importlib
import os
import sys

import pytest

from llmflow.utils.linter import (
    check_function_step_signatures,
    lint_pipeline_full,
)

PKG = "plugins"


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _fresh_plugin_imports():
    """Drop the temporary package from sys.modules so each test imports its own files."""
    def purge():
        for name in [n for n in sys.modules if n == PKG or n.startswith(PKG + ".")]:
            del sys.modules[name]

    purge()
    yield
    purge()


def _make_plugin(tmp_path, module: str, code: str):
    path = tmp_path / PKG / f"{module}.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code)
    importlib.invalidate_caches()
    return path


_OMITTED = object()


def _step(func_ref: str, inputs=_OMITTED, name: str = "s1") -> dict:
    step = {"name": name, "type": "function", "function": func_ref}
    if inputs is not _OMITTED:
        step["inputs"] = inputs
    return step


def _make_pipeline(tmp_path, func_ref: str, inputs_yaml: str):
    path = tmp_path / "pipeline.yaml"
    path.write_text(
        f"""
name: test
steps:
  - name: step1
    type: function
    function: {func_ref}
    inputs:
{inputs_yaml}
    output: result
"""
    )
    return path


# ---------------------------------------------------------------------------
# An input the function does not accept
# ---------------------------------------------------------------------------

class TestUnknownInputName:

    def test_unaccepted_name_is_an_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content=None):\n    return content\n")
        errors = check_function_step_signatures([
            _step("plugins.derive.run", {"morphology": "x"})
        ])
        assert len(errors) == 1
        assert "morphology" in errors[0]

    def test_exact_match_is_clean(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content):\n    return content\n")
        assert check_function_step_signatures([
            _step("plugins.derive.run", {"content": "x"})
        ]) == []

    def test_error_names_the_step_and_the_function(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content=None):\n    return content\n")
        errors = check_function_step_signatures([
            _step("plugins.derive.run", {"morphology": "x"}, name="derive_boundary_fields")
        ])
        assert "derive_boundary_fields" in errors[0]
        assert "plugins.derive.run" in errors[0]

    def test_error_names_the_parameters_the_function_accepts(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content=None):\n    return content\n")
        errors = check_function_step_signatures([
            _step("plugins.derive.run", {"morphology": "x"})
        ])
        assert "content" in errors[0]

    def test_several_unaccepted_names_report_together(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content=None):\n    return content\n")
        errors = check_function_step_signatures([
            _step("plugins.derive.run", {"content": "x", "a": 1, "b": 2})
        ])
        assert len(errors) == 1
        assert "a" in errors[0] and "b" in errors[0]

    def test_a_rename_reports_the_unknown_name_and_the_missing_parameter(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content):\n    return content\n")
        errors = check_function_step_signatures([
            _step("plugins.derive.run", {"morphology": "x"})
        ])
        assert len(errors) == 2
        assert any("morphology" in e for e in errors)
        assert any("requires ['content']" in e for e in errors)


# ---------------------------------------------------------------------------
# A required parameter the step does not supply
# ---------------------------------------------------------------------------

class TestRequiredParameters:

    def test_missing_required_is_an_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content, book):\n    return content\n")
        errors = check_function_step_signatures([
            _step("plugins.derive.run", {"content": "x"})
        ])
        assert len(errors) == 1
        assert "book" in errors[0]

    def test_parameter_with_a_default_may_be_omitted(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content, book=None):\n    return content\n")
        assert check_function_step_signatures([
            _step("plugins.derive.run", {"content": "x"})
        ]) == []

    def test_absent_inputs_key_with_a_required_parameter_is_an_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content):\n    return content\n")
        errors = check_function_step_signatures([_step("plugins.derive.run")])
        assert len(errors) == 1
        assert "content" in errors[0]

    def test_absent_inputs_key_with_no_required_parameter_is_clean(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run():\n    return 1\n")
        assert check_function_step_signatures([_step("plugins.derive.run")]) == []

    def test_keyword_only_parameter_is_required(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(*, content):\n    return content\n")
        errors = check_function_step_signatures([_step("plugins.derive.run", {})])
        assert len(errors) == 1
        assert "content" in errors[0]

    def test_keyword_only_parameter_supplied_is_clean(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(*, content):\n    return content\n")
        assert check_function_step_signatures([
            _step("plugins.derive.run", {"content": "x"})
        ]) == []


# ---------------------------------------------------------------------------
# `context` is the runner's to inject
# ---------------------------------------------------------------------------

class TestContextParameter:

    def test_context_is_not_reported_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content, context):\n    return content\n")
        assert check_function_step_signatures([
            _step("plugins.derive.run", {"content": "x"})
        ]) == []

    def test_context_only_signature_needs_no_inputs(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(context):\n    return 1\n")
        assert check_function_step_signatures([_step("plugins.derive.run")]) == []


# ---------------------------------------------------------------------------
# **kwargs and *args
# ---------------------------------------------------------------------------

class TestVarKeywordAndVarPositional:

    def test_kwargs_accepts_an_unknown_name(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content, **kwargs):\n    return content\n")
        assert check_function_step_signatures([
            _step("plugins.derive.run", {"content": "x", "extra": 1})
        ]) == []

    def test_kwargs_does_not_satisfy_a_required_named_parameter(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content, **kwargs):\n    return content\n")
        errors = check_function_step_signatures([
            _step("plugins.derive.run", {"extra": 1})
        ])
        assert len(errors) == 1
        assert "content" in errors[0]

    def test_varargs_lifts_the_positional_upper_bound(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(*args):\n    return args\n")
        assert check_function_step_signatures([
            _step("plugins.derive.run", [1, 2, 3])
        ]) == []


# ---------------------------------------------------------------------------
# The `function:` path itself
# ---------------------------------------------------------------------------

class TestImportFailures:

    def test_unimportable_module_is_an_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        errors = check_function_step_signatures([_step("nonexistent.module.func", {})])
        assert len(errors) == 1
        assert "nonexistent.module" in errors[0]

    def test_name_the_module_does_not_define_is_an_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content):\n    return content\n")
        errors = check_function_step_signatures([
            _step("plugins.derive.missing", {"content": "x"})
        ])
        assert len(errors) == 1
        assert "missing" in errors[0]

    def test_module_that_raises_on_import_is_an_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", 'raise RuntimeError("boom")\n')
        errors = check_function_step_signatures([
            _step("plugins.derive.run", {"content": "x"})
        ])
        assert len(errors) == 1
        assert "boom" in errors[0]

    def test_a_non_callable_attribute_is_an_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "run = 3\n")
        errors = check_function_step_signatures([
            _step("plugins.derive.run", {"content": "x"})
        ])
        assert len(errors) == 1
        assert "callable" in errors[0]

    def test_an_engine_function_resolves(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert check_function_step_signatures([
            _step("llmflow.utils.io.load_json", {"file_path": "x.json"})
        ]) == []

    def test_lint_leaves_no_project_module_behind(self, tmp_path, monkeypatch):
        """Lint inspects. A run in the same process must import the project's plugins itself."""
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content):\n    return content\n")
        check_function_step_signatures([_step("plugins.derive.run", {"content": "x"})])
        assert "plugins.derive" not in sys.modules
        assert PKG not in sys.modules

    def test_it_leaves_engine_modules_alone(self, tmp_path, monkeypatch):
        """Only what came from the working directory is dropped; the engine is not this block's."""
        monkeypatch.chdir(tmp_path)
        check_function_step_signatures([
            _step("llmflow.utils.io.load_json", {"file_path": "x.json"})
        ])
        assert "llmflow.utils.io" in sys.modules

    def test_the_engine_module_object_is_the_same_one_afterwards(self, monkeypatch):
        """Evicting `llmflow` would hand the next import a fresh module object.

        Every reference the caller already holds — a patched name, the logger singleton — would
        then belong to a module nothing else is using. Linting from the engine's own repository is
        the ordinary case, so this is not a corner.
        """
        import llmflow.utils.io as io_module

        check_function_step_signatures([
            _step("llmflow.utils.io.load_json", {"file_path": "x.json"})
        ])
        assert sys.modules["llmflow.utils.io"] is io_module

    def test_a_stale_package_of_the_same_name_does_not_shadow_this_one(self, tmp_path,
                                                                       monkeypatch):
        """`plugins` is the conventional name, so several projects have one.

        Whichever was imported first stays in `sys.modules`, bound to its own directory, and every
        later `plugins.*` import resolves against it — so a lint of the second pipeline reports
        that its own plugin does not exist. The pipeline being linted owns the name.

        The first one here carries an `__init__.py` and the second does not, which is the case
        that bites: a regular package fixes `__path__` at import, where a namespace package
        recomputes it from `sys.path` and re-resolves on its own.
        """
        elsewhere = tmp_path / "elsewhere"
        _make_plugin(elsewhere, "other", "def run(content):\n    return content\n")
        (elsewhere / PKG / "__init__.py").write_text("")
        importlib.invalidate_caches()
        here = tmp_path / "here"
        _make_plugin(here, "derive", "def run(content):\n    return content\n")

        monkeypatch.chdir(elsewhere)
        assert check_function_step_signatures([
            _step("plugins.other.run", {"content": "x"})
        ]) == []

        monkeypatch.chdir(here)
        assert check_function_step_signatures([
            _step("plugins.derive.run", {"content": "x"})
        ]) == []


# ---------------------------------------------------------------------------
# List-form inputs are positional, so only arity is checkable
# ---------------------------------------------------------------------------

class TestListFormInputs:

    def test_matching_arity_is_clean(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(a, b):\n    return a\n")
        assert check_function_step_signatures([
            _step("plugins.derive.run", [1, 2])
        ]) == []

    def test_too_many_arguments_is_an_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(a, b):\n    return a\n")
        errors = check_function_step_signatures([
            _step("plugins.derive.run", [1, 2, 3])
        ])
        assert len(errors) == 1
        assert "3" in errors[0]

    def test_too_few_arguments_is_an_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(a, b):\n    return a\n")
        errors = check_function_step_signatures([
            _step("plugins.derive.run", [1])
        ])
        assert len(errors) == 1

    def test_optional_parameter_need_not_be_given(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(a, b=None):\n    return a\n")
        assert check_function_step_signatures([
            _step("plugins.derive.run", [1])
        ]) == []

    def test_a_required_keyword_only_parameter_cannot_be_supplied_positionally(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(a, *, b):\n    return a\n")
        errors = check_function_step_signatures([
            _step("plugins.derive.run", [1])
        ])
        assert len(errors) == 1
        assert "b" in errors[0]


# ---------------------------------------------------------------------------
# Steps this check does not speak for
# ---------------------------------------------------------------------------

class TestStepsThatAreSkipped:

    def test_llm_step_is_skipped(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert check_function_step_signatures([
            {"name": "s1", "type": "llm", "prompt": {"file": "p.gpt"}}
        ]) == []

    def test_non_dotted_function_value_is_skipped(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert check_function_step_signatures([_step("bare", {})]) == []

    def test_unresolved_variable_in_the_function_path_is_skipped(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert check_function_step_signatures([
            _step("${plugin_module}.run", {})
        ]) == []


# ---------------------------------------------------------------------------
# Integration through the path `sp lint` runs
# ---------------------------------------------------------------------------

class TestLintPipelineFullIntegration:

    def test_a_renamed_parameter_fails_lint(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content):\n    return content\n")
        pipeline = _make_pipeline(tmp_path, "plugins.derive.run", '      morphology: "x"')
        result = lint_pipeline_full(str(pipeline))
        assert not result.valid
        assert any("morphology" in e for e in result.errors)

    def test_correct_wiring_passes_lint(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content):\n    return content\n")
        pipeline = _make_pipeline(tmp_path, "plugins.derive.run", '      content: "x"')
        result = lint_pipeline_full(str(pipeline))
        assert result.valid, result.errors

    def test_lint_does_not_leave_the_working_directory_on_sys_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "derive", "def run(content):\n    return content\n")
        pipeline = _make_pipeline(tmp_path, "plugins.derive.run", '      content: "x"')
        before = list(sys.path)
        lint_pipeline_full(str(pipeline))
        assert os.getcwd() not in sys.path or os.getcwd() in before
