"""Tests for GH #165: sp lint warns when function steps construct paths to outputs/ internally.

Covers:
  - Direct violation in the step function itself
  - Violation in a helper called by the step function (shallow check misses this)
  - Violation reached via transitive call chain (shallow check misses this)
  - Recursive functions don't cause infinite loops
  - Clean functions produce no warnings
  - f-string with outputs/ constant is caught
  - Missing module is skipped gracefully
  - Integration via lint_pipeline_full
"""

import ast
from pathlib import Path
import pytest

from llmflow.utils.linter import (
    _build_module_func_map,
    _collect_transitive_funcs,
    _output_path_violations,
    check_function_step_no_internal_paths,
    lint_pipeline_full,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _func_map(src: str) -> dict:
    return _build_module_func_map(ast.parse(src))


def _transitive(src: str, name: str) -> list:
    return _collect_transitive_funcs(name, _func_map(src))


def _make_plugin(tmp_path: Path, rel_path: str, code: str) -> Path:
    path = tmp_path / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code)
    return path


def _make_pipeline(tmp_path: Path, func_ref: str) -> Path:
    p = tmp_path / "pipeline.yaml"
    p.write_text(f"""
name: test
steps:
  - name: step1
    type: function
    function: {func_ref}
    inputs:
      value: "hello"
    output: result
""")
    return p


# ---------------------------------------------------------------------------
# _build_module_func_map
# ---------------------------------------------------------------------------

class TestBuildModuleFuncMap:

    def test_finds_top_level_functions(self):
        func_map = _func_map("def foo(): pass\ndef bar(): pass\n")
        assert "foo" in func_map
        assert "bar" in func_map

    def test_finds_nested_helper(self):
        src = "def outer():\n    def inner(): pass\n"
        func_map = _func_map(src)
        assert "outer" in func_map
        assert "inner" in func_map

    def test_empty_module(self):
        assert _func_map("x = 1\n") == {}


# ---------------------------------------------------------------------------
# _collect_transitive_funcs
# ---------------------------------------------------------------------------

class TestCollectTransitiveFuncs:

    def test_returns_start_function(self):
        result = _transitive("def foo(): pass\n", "foo")
        assert len(result) == 1
        assert result[0].name == "foo"

    def test_includes_directly_called_helper(self):
        src = "def foo():\n    bar()\ndef bar(): pass\n"
        names = {f.name for f in _transitive(src, "foo")}
        assert {"foo", "bar"} == names

    def test_follows_transitive_chain(self):
        src = "def foo():\n    bar()\ndef bar():\n    baz()\ndef baz(): pass\n"
        names = {f.name for f in _transitive(src, "foo")}
        assert {"foo", "bar", "baz"} == names

    def test_handles_direct_recursion(self):
        src = "def foo():\n    foo()\n"
        result = _transitive(src, "foo")
        assert len(result) == 1

    def test_handles_mutual_recursion(self):
        src = "def foo():\n    bar()\ndef bar():\n    foo()\n"
        names = {f.name for f in _transitive(src, "foo")}
        assert names == {"foo", "bar"}

    def test_unknown_name_returns_empty(self):
        assert _transitive("def foo(): pass\n", "nonexistent") == []

    def test_does_not_include_uncalled_functions(self):
        src = "def foo(): pass\ndef unrelated(): pass\n"
        names = {f.name for f in _transitive(src, "foo")}
        assert "unrelated" not in names


# ---------------------------------------------------------------------------
# _output_path_violations
# ---------------------------------------------------------------------------

class TestOutputPathViolations:

    def test_finds_string_literal(self):
        src = 'def foo():\n    path = "outputs/result.json"\n'
        violations = _output_path_violations(_transitive(src, "foo"))
        assert len(violations) == 1
        assert violations[0][0] == "foo"

    def test_finds_fstring_constant_part(self):
        src = 'def foo(name):\n    path = f"outputs/{name}"\n'
        violations = _output_path_violations(_transitive(src, "foo"))
        assert len(violations) == 1

    def test_finds_violation_in_helper(self):
        src = 'def foo():\n    _h()\ndef _h():\n    path = "outputs/x"\n'
        violations = _output_path_violations(_transitive(src, "foo"))
        assert len(violations) == 1
        assert violations[0][0] == "_h"

    def test_no_violation_for_clean_function(self):
        src = 'def foo(data):\n    return {"result": data}\n'
        assert _output_path_violations(_transitive(src, "foo")) == []

    def test_reports_caller_name_not_callee_when_direct(self):
        src = 'def foo():\n    x = "outputs/a"\n'
        name, _ = _output_path_violations(_transitive(src, "foo"))[0]
        assert name == "foo"


# ---------------------------------------------------------------------------
# check_function_step_no_internal_paths
# ---------------------------------------------------------------------------

class TestCheckFunctionStepNoInternalPaths:

    def test_direct_violation_caught(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "plugins/step.py",
            'def my_step(data):\n    path = "outputs/x.json"\n    return data\n')
        steps = [{"name": "s1", "function": "plugins.step.my_step"}]
        warnings = check_function_step_no_internal_paths(steps)
        assert any("outputs/" in w for w in warnings)
        assert any("my_step" in w for w in warnings)

    def test_helper_violation_caught(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "plugins/step.py",
            'def my_step(data):\n    return _helper(data)\n'
            '\ndef _helper(data):\n    path = "outputs/x.json"\n    return data\n')
        steps = [{"name": "s1", "function": "plugins.step.my_step"}]
        warnings = check_function_step_no_internal_paths(steps)
        assert any("outputs/" in w for w in warnings)
        assert any("_helper" in w for w in warnings)

    def test_transitive_violation_caught(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "plugins/step.py",
            'def my_step(d):\n    return h1(d)\n'
            '\ndef h1(d):\n    return h2(d)\n'
            '\ndef h2(d):\n    path = "outputs/x.json"\n    return d\n')
        steps = [{"name": "s1", "function": "plugins.step.my_step"}]
        warnings = check_function_step_no_internal_paths(steps)
        assert any("outputs/" in w for w in warnings)
        assert any("h2" in w for w in warnings)

    def test_clean_step_no_warning(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "plugins/step.py",
            'def my_step(data):\n    return {"result": data}\n')
        steps = [{"name": "s1", "function": "plugins.step.my_step"}]
        assert check_function_step_no_internal_paths(steps) == []

    def test_missing_module_skipped(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        steps = [{"name": "s1", "function": "nonexistent.module.func"}]
        assert check_function_step_no_internal_paths(steps) == []

    def test_step_without_function_key_skipped(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        steps = [{"name": "s1", "type": "llm", "prompt": {"file": "p.gpt"}}]
        assert check_function_step_no_internal_paths(steps) == []

    def test_violation_message_includes_step_name(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "plugins/step.py",
            'def my_step(data):\n    path = "outputs/x.json"\n    return data\n')
        steps = [{"name": "my_step_name", "function": "plugins.step.my_step"}]
        warnings = check_function_step_no_internal_paths(steps)
        assert any("my_step_name" in w for w in warnings)

    def test_helper_message_names_the_helper(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "plugins/step.py",
            'def step(data):\n    return bad(data)\n'
            '\ndef bad(d):\n    return open("outputs/x").read()\n')
        steps = [{"name": "s1", "function": "plugins.step.step"}]
        warnings = check_function_step_no_internal_paths(steps)
        assert any("bad" in w for w in warnings)
        assert not any(w for w in warnings if "step" in w and "bad" not in w)


# ---------------------------------------------------------------------------
# Integration: lint_pipeline_full
# ---------------------------------------------------------------------------

class TestLintPipelineFunctionIoIntegration:

    def test_direct_violation_appears_in_lint_warnings(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "plugins/step.py",
            'def my_step(data):\n    path = "outputs/x.json"\n    return data\n')
        p = _make_pipeline(tmp_path, "plugins.step.my_step")
        result = lint_pipeline_full(str(p))
        assert result.valid
        assert any("outputs/" in w for w in result.warnings)

    def test_helper_violation_appears_in_lint_warnings(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "plugins/step.py",
            'def my_step(data):\n    return _h(data)\n'
            '\ndef _h(d):\n    path = "outputs/x.json"\n    return d\n')
        p = _make_pipeline(tmp_path, "plugins.step.my_step")
        result = lint_pipeline_full(str(p))
        assert result.valid
        assert any("_h" in w for w in result.warnings)

    def test_clean_function_no_lint_warning(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_plugin(tmp_path, "plugins/step.py",
            'def my_step(data):\n    return {"result": data}\n')
        p = _make_pipeline(tmp_path, "plugins.step.my_step")
        result = lint_pipeline_full(str(p))
        assert result.valid
        assert not any("outputs/" in w for w in result.warnings)
