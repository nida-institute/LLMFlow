"""Public object model for a pipeline (LLMFlow#187).

A pipeline YAML is an object tree (``pipeline → steps → step → saveas``); this module is
an object graph of the same shape, so reading a pipeline tells you the API calls. Every
attribute is a declared syntax key from ``PIPELINE_SCHEMA`` (raw/unresolved for ``Pipeline``;
resolved for ``ResolvedPipeline``); nesting mirrors the YAML's nesting.

The classes are a thin, read-only view over the parsed config. They add **shape only, no
logic** — computed operations (resolve/run/lint/…) delegate to the engine's existing
single-implementation functions.

``Step``'s attributes are *generated* from ``PIPELINE_SCHEMA`` rather than hand-written,
so drift between the schema and the model is impossible by construction. The model is
flat and generic: it exposes the union of every type's keys, while *validation* is
per-type in the linter (see ``pipeline_schema.allowed_step_keys``). A key that does not
apply to a step's type simply reads as ``None``.

Attribute-name rule (total, mechanical): a syntax key that is not a usable Python
identifier is mapped — a Python keyword gets a trailing underscore (``in`` → ``in_``,
``for`` → ``for_``), and a hyphen becomes an underscore (``group-by`` → ``group_by``).
"""
from __future__ import annotations

from keyword import iskeyword
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from llmflow.pipeline_schema import step_keys
from llmflow.utils.context import build_run_context
from llmflow.utils.context import resolve as resolve_value
from llmflow.yaml_loader import load_pipeline_config


def api_name(key: str) -> str:
    """The Python attribute name for a pipeline syntax *key*."""
    name = key.replace("-", "_")
    return f"{name}_" if iskeyword(name) else name


# attribute name -> syntax key, for every key PIPELINE_SCHEMA declares on a step.
_STEP_ATTRS: Dict[str, str] = {api_name(k): k for k in step_keys()}


class Step:
    """Read-only view of one pipeline step; attributes are the step's declared keys.

    The attributes are generated from ``PIPELINE_SCHEMA`` at import time (see
    :func:`_generate_step_attributes`), so the set is exactly the schema's step
    vocabulary. Keys not present on this step read as ``None``; ``steps`` returns nested
    :class:`Step` objects.
    """

    if TYPE_CHECKING:
        # The attributes are installed at import time from PIPELINE_SCHEMA, so a static
        # checker cannot see them. This tells it the surface is dynamic; the runtime
        # source of truth is the schema, and the drift test proves the two agree.
        def __getattr__(self, name: str) -> Any: ...

    def __init__(self, raw: Dict[str, Any]):
        self._raw = dict(raw)

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


def _step_property(key: str) -> property:
    """A read-only property returning the step's *key*, or ``None`` if absent."""

    def read_nested_steps(self):
        """Nested steps (``for-each`` / ``window`` / ``if``), mirroring the YAML."""
        return [Step(s) for s in (self._raw.get("steps") or [])]

    def read_key(self):
        return self._raw.get(key)

    read = read_nested_steps if key == "steps" else read_key
    if read is read_key:
        read.__doc__ = f"The step's ``{key}:`` key (``None`` when not declared)."
    read.__name__ = api_name(key)
    return property(read)


def _generate_step_attributes() -> None:
    """Install one read-only property on ``Step`` per declared step key.

    Generated rather than hand-written so the attribute set cannot drift from
    ``PIPELINE_SCHEMA`` — the schema is the only place the vocabulary is declared. They
    are real properties (not ``__getattr__``), so ``dir(Step)`` and autocomplete still
    show the full surface.
    """
    for attr, key in _STEP_ATTRS.items():
        setattr(Step, attr, _step_property(key))


_generate_step_attributes()


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

    def schemas(self) -> Dict[str, Dict[str, str]]:
        """Return ``{step_name: {"path": schema_file, "kind": ...}}`` for every step (including
        nested) that references a JSON schema. ``kind`` is one of:

        - ``"response_format"`` — an LLM step's ``response_format.json_schema.schema_file``
        - ``"validator"`` — a ``json_schema_validator`` step's ``inputs.schema_path``
        - ``"frontmatter"`` — the step's ``.gpt`` prompt frontmatter ``schema:``

        Prompt files are resolved against the pipeline's ``prompts_dir`` (default ``prompts``)
        with the engine's own resolver; a step whose prompt cannot be found or parsed, or whose
        prompt path is templated, contributes no frontmatter schema. When a step references a
        schema by more than one route, precedence is response_format > validator > frontmatter.
        """
        prompts_dir = str(self._root.get("prompts_dir") or "prompts")
        found: Dict[str, Dict[str, str]] = {}

        def _prompt_schema(prompt: Any) -> Optional[str]:
            if isinstance(prompt, dict):
                prompt = prompt.get("file")
            if not isinstance(prompt, str) or "${" in prompt:
                return None
            from llmflow.utils.io import resolve_prompt_path
            from llmflow.utils.linter import parse_prompt_header

            try:
                path = resolve_prompt_path(prompt, prompts_dir)
                header = parse_prompt_header(str(path)) or {}
            except Exception:
                return None
            schema = header.get("schema")
            return schema if isinstance(schema, str) else None

        def _walk(steps: Any) -> None:
            for step in steps or []:
                name = step.get("name")
                if name is None:
                    _walk(step.get("steps"))
                    continue

                path: Optional[str] = None
                kind: Optional[str] = None

                rf = step.get("response_format")
                if isinstance(rf, dict):
                    js = rf.get("json_schema")
                    if isinstance(js, dict) and js.get("schema_file"):
                        path, kind = js["schema_file"], "response_format"

                if path is None and step.get("type") == "json_schema_validator":
                    inputs = step.get("inputs")
                    if isinstance(inputs, dict) and inputs.get("schema_path"):
                        path, kind = inputs["schema_path"], "validator"

                if path is None and step.get("prompt") is not None:
                    sch = _prompt_schema(step.get("prompt"))
                    if sch:
                        path, kind = sch, "frontmatter"

                if path is not None and kind is not None:
                    found[name] = {"path": path, "kind": kind}
                _walk(step.get("steps"))

        _walk(self._root.get("steps"))
        return found

    def saveas(self) -> Dict[str, Any]:
        """Return ``{step_name: saveas}`` for every step (including nested) that declares a
        ``saveas:`` target.

        Declared (raw) values — each is a string or a ``{path, group_by_prefix}`` mapping.
        Call :meth:`resolve` and read ``step.saveas`` for resolved paths.
        """
        found: Dict[str, Any] = {}

        def _walk(steps: Any) -> None:
            for step in steps or []:
                name = step.get("name")
                if step.get("saveas") is not None and name is not None:
                    found[name] = step["saveas"]
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
