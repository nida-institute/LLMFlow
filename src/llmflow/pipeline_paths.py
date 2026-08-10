"""Public API: resolve a pipeline's directories and variables without running it.

Consumers (CLI scripts, tools, tests) often need a pipeline's resolved paths from
*outside* a run. This composes the same context construction (``build_run_context``)
and ``${...}`` expansion (``resolve``) the runner uses, so it cannot drift from
real-run behavior. See LLMFlow#186.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

from llmflow.utils.context import build_run_context, resolve
from llmflow.yaml_loader import load_pipeline_config


@dataclass
class ResolvedPipelinePaths:
    """A pipeline's resolved directories and variables, as a run would see them."""

    intermediate_file_directory: Optional[Path]
    output_file_directory: Optional[Path]
    variables: Dict[str, Any] = field(default_factory=dict)


def resolve_pipeline_paths(
    pipeline_file: Union[str, Path],
    vars: Optional[Dict[str, Any]] = None,
) -> ResolvedPipelinePaths:
    """Return a pipeline's resolved directories and variables.

    Loads *pipeline_file* with the engine's YAML loader, builds the run context with the
    same precedence a real run uses (root directory keys -> ``variables:`` -> *vars* /
    ``--var``, which win), and expands ``${...}`` / derived variables. Directory keys the
    pipeline does not declare come back as ``None``.

    Args:
        pipeline_file: Path to the pipeline YAML.
        vars: Optional overrides equivalent to ``sp run --var key=value``.
    """
    config = load_pipeline_config(pipeline_file)
    context = build_run_context(config, vars)

    def _resolve_dir(key: str) -> Optional[Path]:
        raw = context.get(key)
        return Path(str(resolve(str(raw), context))) if raw else None

    pipeline_root = config.get("pipeline", config)
    raw_vars = pipeline_root.get("variables", {}) or {}
    resolved_vars = {k: resolve(v, context) for k, v in raw_vars.items()}

    return ResolvedPipelinePaths(
        intermediate_file_directory=_resolve_dir("intermediate_file_directory"),
        output_file_directory=_resolve_dir("output_file_directory"),
        variables=resolved_vars,
    )
