"""Public object model for a pipeline (LLMFlow#187).

A pipeline YAML is an object tree (``pipeline → steps → step → saveas``); this module is
an object graph of the same shape, so reading a pipeline tells you the API calls. Every
attribute is a declared syntax key from ``PIPELINE_SCHEMA`` (raw/unresolved for ``Pipeline``;
resolved for ``ResolvedPipeline``); nesting mirrors the YAML's nesting.

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

from llmflow.utils.context import build_run_context
from llmflow.utils.context import resolve as resolve_value
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

    def render_prompt(self, context: Dict[str, Any]) -> str:
        """Render this step's ``prompt`` with variable substitution (delegates to the
        engine's ``render_prompt``). Requires the step to declare a ``prompt``.
        """
        from llmflow.steps.llm import render_prompt as _render_prompt

        prompt = self._raw.get("prompt")
        if prompt is None:
            raise ValueError("Step.render_prompt() requires the step to declare a 'prompt'")
        return _render_prompt(prompt, context)

    def __repr__(self) -> str:
        return f"Step(name={self.name!r}, type={self.type!r})"


class _PipelineView:
    """Shared read-only view of a pipeline's non-directory attributes.

    ``Pipeline`` (declared/raw) and ``ResolvedPipeline`` (resolved) share these; they differ
    only in the directory keys — ``str`` when declared, ``Path`` once resolved — so those are
    declared separately on each rather than overridden (keeps the types honest).
    """

    def __init__(self, config: Dict[str, Any], source: Optional[Union[str, Path]] = None):
        self._config = dict(config)                       # full config (for resolution)
        self._root = self._config.get("pipeline", self._config)
        self._source = Path(source) if source is not None else None  # for path-based delegations

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
    def steps(self) -> List[Step]:
        return [Step(s) for s in (self._root.get("steps") or [])]

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r}, steps={len(self.steps)})"


class Pipeline(_PipelineView):
    """Read-only view of a pipeline; attributes are the declared top-level keys (raw).

    Declared values are raw (``${...}`` unexpanded). Resolved values come from
    :meth:`resolve`, which returns a same-shaped :class:`ResolvedPipeline`.
    """

    @property
    def intermediate_file_directory(self) -> Optional[str]:
        return self._root.get("intermediate_file_directory")

    @property
    def output_file_directory(self) -> Optional[str]:
        return self._root.get("output_file_directory")

    def resolve(self, vars: Optional[Dict[str, Any]] = None) -> "ResolvedPipeline":
        """Return a resolved view: ``${...}`` expanded and *vars* (``--var``) applied.

        Same shape as this ``Pipeline``; directory attributes come back as ``Path``. Uses
        the engine's own context builder and resolver, so the result matches a real run.
        """
        context = build_run_context(self._config, vars)
        resolved = resolve_value(self._config, context)
        # A directory key can be overridden via --var (vars win in the context). The config's
        # own raw value for the key doesn't reference itself, so take the key's resolved value
        # from the context — that is what a real run would use.
        root = resolved.get("pipeline", resolved)
        for key in ("intermediate_file_directory", "output_file_directory"):
            raw = context.get(key)
            if raw is not None:
                root[key] = resolve_value(raw, context)
        return ResolvedPipeline(resolved)

    def lint(self, vars: Optional[Dict[str, Any]] = None, *, rewind_to: Optional[str] = None):
        """Lint the pipeline, returning the engine's ``LintResult`` (``.valid`` /
        ``.errors`` / ``.warnings``). Requires a pipeline loaded from a file.
        """
        from llmflow.utils.linter import lint_pipeline_full

        if self._source is None:
            raise ValueError("Pipeline.lint() needs a pipeline loaded from a file")
        return lint_pipeline_full(self._source, vars=vars, rewind_to=rewind_to)

    def run(
        self,
        vars: Optional[Dict[str, Any]] = None,
        *,
        dry_run: bool = False,
        rewind_to: Optional[str] = None,
        stop_after: Optional[str] = None,
        resume: bool = False,
        verbose: bool = False,
        skip_lint: bool = False,
        log_file: str = "llmflow.log",
    ):
        """Run the pipeline (delegates to the engine's ``run_pipeline``).

        Like ``sp run``, this calls LLMs, writes outputs, and may take time.
        """
        from llmflow.runner import run_pipeline

        return run_pipeline(
            self._source or self._config,
            vars=vars,
            dry_run=dry_run,
            rewind_to=rewind_to,
            stop_after=stop_after,
            resume=resume,
            verbose=verbose,
            skip_lint=skip_lint,
            log_file=log_file,
        )

    def schemas(self) -> Dict[str, str]:
        """Return ``{step_name: schema_file}`` for every step (including nested) that
        declares a JSON schema file via ``response_format.json_schema.schema_file``.

        Config-only: reads declared (raw) paths; it does not read prompt files or resolve
        ``${...}`` (call :meth:`resolve` first if you need resolved paths).
        """
        found: Dict[str, str] = {}

        def _walk(steps: Any) -> None:
            for step in steps or []:
                rf = step.get("response_format")
                if isinstance(rf, dict):
                    js = rf.get("json_schema")
                    if isinstance(js, dict) and js.get("schema_file"):
                        found[step.get("name")] = js["schema_file"]
                _walk(step.get("steps"))

        _walk(self._root.get("steps"))
        return found


class ResolvedPipeline(_PipelineView):
    """A resolved view of a pipeline (``${...}`` expanded, ``--var`` applied).

    Built by :meth:`Pipeline.resolve`. Same shape as :class:`Pipeline`; the directory keys
    are returned as ``Path`` objects.
    """

    @property
    def intermediate_file_directory(self) -> Optional[Path]:
        v = self._root.get("intermediate_file_directory")
        return Path(v) if v else None

    @property
    def output_file_directory(self) -> Optional[Path]:
        v = self._root.get("output_file_directory")
        return Path(v) if v else None


def load_pipeline(pipeline_file: Union[str, Path]) -> Pipeline:
    """Load a pipeline file into a :class:`Pipeline` object.

    Uses the engine's own loader (custom ``!tags`` supported). Raises ``FileNotFoundError``
    if the file is missing and ``yaml.YAMLError`` on a syntax error.
    """
    return Pipeline(load_pipeline_config(pipeline_file), source=pipeline_file)
