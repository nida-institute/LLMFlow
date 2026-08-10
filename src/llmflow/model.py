"""Public object model for a pipeline (LLMFlow#187).

A pipeline YAML is an object tree (``pipeline → steps → step → saveas``); this module is
an object graph of the same shape, so reading a pipeline tells you the API calls. Every
attribute is a declared syntax key from ``PIPELINE_SCHEMA`` (raw/unresolved — resolution
is a method, added in a later slice); nesting mirrors the YAML's nesting.

The classes are a thin, hand-written, read-only view over the parsed config. They add
**shape only, no logic** — computed operations (resolve/run/lint/…) delegate to the
engine's existing single-implementation functions. The schema-mirror drift test keeps the
attribute set in lockstep with ``PIPELINE_SCHEMA``.

Reserved-word rule (total, mechanical): a syntax key that is a Python keyword gets a
trailing underscore — ``in`` → ``in_``, ``for`` → ``for_``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from llmflow.yaml_loader import load_pipeline_config


class Step:
    """Read-only view of one pipeline step; attributes are the step's declared keys."""

    def __init__(self, raw: Dict[str, Any]):
        self._raw = dict(raw)

    @property
    def name(self) -> Optional[str]:
        return self._raw.get("name")

    @property
    def type(self) -> Optional[str]:
        return self._raw.get("type")

    @property
    def function(self) -> Optional[str]:
        return self._raw.get("function")

    @property
    def prompt(self) -> Any:
        return self._raw.get("prompt")

    @property
    def model(self) -> Optional[str]:
        return self._raw.get("model")

    @property
    def max_tokens(self) -> Optional[int]:
        return self._raw.get("max_tokens")

    @property
    def temperature(self) -> Optional[float]:
        return self._raw.get("temperature")

    @property
    def timeout_seconds(self) -> Optional[float]:
        return self._raw.get("timeout_seconds")

    @property
    def in_(self) -> Any:
        """The ``in:`` key (renamed — ``in`` is a Python keyword)."""
        return self._raw.get("in")

    @property
    def inputs(self) -> Optional[Dict[str, Any]]:
        return self._raw.get("inputs")

    @property
    def outputs(self) -> Any:
        return self._raw.get("outputs")

    @property
    def append_to(self) -> Optional[str]:
        return self._raw.get("append_to")

    @property
    def steps(self) -> List["Step"]:
        """Nested steps (for ``for-each`` / ``if``), mirroring the YAML nesting."""
        return [Step(s) for s in (self._raw.get("steps") or [])]

    @property
    def for_(self) -> Optional[str]:
        """The ``for:`` key (renamed — ``for`` is a Python keyword)."""
        return self._raw.get("for")

    @property
    def condition(self) -> Optional[str]:
        return self._raw.get("condition")

    @property
    def saveas(self) -> Any:
        return self._raw.get("saveas")

    @property
    def require(self) -> Optional[List[Dict[str, Any]]]:
        return self._raw.get("require")

    @property
    def warn(self) -> Optional[List[Dict[str, Any]]]:
        return self._raw.get("warn")

    @property
    def retry(self) -> Optional[Dict[str, Any]]:
        return self._raw.get("retry")

    def __repr__(self) -> str:
        return f"Step(name={self.name!r}, type={self.type!r})"


class Pipeline:
    """Read-only view of a pipeline; attributes are the declared top-level keys.

    Declared values are raw (``${...}`` unexpanded). Resolved values come from the
    ``.resolve()`` method (added in a later slice), which returns a same-shaped view.
    """

    def __init__(self, config: Dict[str, Any]):
        self._config = dict(config)                       # full config (for resolution)
        self._root = self._config.get("pipeline", self._config)

    @property
    def name(self) -> Optional[str]:
        return self._root.get("name")

    @property
    def description(self) -> Optional[str]:
        return self._root.get("description")

    @property
    def variables(self) -> Dict[str, Any]:
        return self._root.get("variables") or {}

    @property
    def llm_config(self) -> Optional[Dict[str, Any]]:
        return self._root.get("llm_config")

    @property
    def linter_config(self) -> Optional[Dict[str, Any]]:
        return self._root.get("linter_config")

    @property
    def intermediate_file_directory(self) -> Optional[str]:
        return self._root.get("intermediate_file_directory")

    @property
    def output_file_directory(self) -> Optional[str]:
        return self._root.get("output_file_directory")

    @property
    def steps(self) -> List[Step]:
        return [Step(s) for s in (self._root.get("steps") or [])]

    def __repr__(self) -> str:
        return f"Pipeline(name={self.name!r}, steps={len(self.steps)})"


def load_pipeline(pipeline_file: Union[str, Path]) -> Pipeline:
    """Load a pipeline file into a :class:`Pipeline` object.

    Uses the engine's own loader (custom ``!tags`` supported). Raises ``FileNotFoundError``
    if the file is missing and ``yaml.YAMLError`` on a syntax error.
    """
    return Pipeline(load_pipeline_config(pipeline_file))
