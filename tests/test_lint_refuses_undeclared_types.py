"""`sp lint` refuses a step type that nothing declares.

A step type is valid when the pipeline schema declares it, or when a built-in plugin registers it.
A project's own plugin is named by `plugin:` instead, so a step carrying that key is not checked
here. Anything else would fail only at run time, with `Unknown step type` — after every step
before it has run and been paid for.

The plugin names are a constant, so lint learns them without loading a plugin.
"""

from __future__ import annotations

import importlib

import pytest

from llmflow.pipeline_schema import declared_step_types
from llmflow.plugins.loader import BUILTIN_STEP_TYPES, KNOWN_PLUGIN_MODULES, SEEDED_STEP_TYPES
from llmflow.utils.linter import lint_pipeline_steps


def _errors(step: dict) -> list[str]:
    return lint_pipeline_steps([{"name": "s", **step}])


def _type_errors(step: dict) -> list[str]:
    return [e for e in _errors(step) if "step type" in e]


def test_an_undeclared_type_is_refused():
    [error] = _type_errors({"type": "no_such_step_type", "resource": "SBLGNT"})
    assert "'no_such_step_type'" in error


def test_a_misspelt_type_names_the_nearest_declared_one():
    [error] = _type_errors({"type": "scriptur", "resource": "SBLGNT"})
    assert "'scripture'" in error


@pytest.mark.parametrize("step_type", sorted(declared_step_types()))
def test_every_declared_type_is_accepted(step_type: str):
    assert _type_errors({"type": step_type}) == []


@pytest.mark.parametrize("step_type", sorted(BUILTIN_STEP_TYPES))
def test_every_built_in_plugin_type_is_accepted(step_type: str):
    assert _type_errors({"type": step_type}) == []


def test_a_project_plugin_is_named_by_plugin_and_not_checked():
    assert _type_errors({"type": "my_own_step", "plugin": "my_project.plugins.thing"}) == []


def test_the_plugin_types_lint_knows_are_the_ones_the_plugins_register():
    """The constant is what lint reads; registration is what the runner dispatches on.

    Each module's `register()` is called directly, so this checks the names without running
    discovery and without touching the shared registry.
    """
    registered = set(SEEDED_STEP_TYPES)
    for name in KNOWN_PLUGIN_MODULES:
        module = importlib.import_module(f"llmflow.plugins.{name}")
        if hasattr(module, "register"):
            registered |= set(module.register())
    assert registered == set(BUILTIN_STEP_TYPES)
