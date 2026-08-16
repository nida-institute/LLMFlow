"""Debug output directory utilities.

The debug directory holds the evidence a conclusion is audited from: the exact request
sent to the model, its unedited reply, and the run log. That evidence used to survive
exactly one run.

`_clear_debug_dir()` did `shutil.rmtree()` at the start of every run, on a directory keyed
by pipeline filename alone. Running the same pipeline for Ruth and then for Mark therefore
deleted the entire Ruth run — reported from Ears to Hear, LLMFlow#198. Nothing warned; the
run reported success.

Two changes, because they save different files:

* **The run key is part of the path.** CLI ``--var`` values are what distinguish one run of
  a pipeline from the next, so they name the directory. This is what saves ``llmflow.log``,
  whose filename is fixed and would be overwritten however carefully we treated the rest.
* **Nothing is deleted.** Files are written over in place. This is what saves the request
  and response dumps, whose filenames already carry the passage and so do not collide
  between passages.

The larger layout redesign — sequence numbers, attempt numbers, and a run manifest so that
``sp tools replay`` stops pairing files by sorting their names — remains open in #198.
"""

import re
from pathlib import Path
from typing import Any, Dict, Optional

from llmflow.utils.context import resolve

#: Used when a run has no CLI variables to distinguish it. Stable rather than a timestamp:
#: a timestamp would mint a new directory on every run and grow without bound, and nobody
#: has decided a retention rule (#198).
DEFAULT_RUN_KEY = "default"

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _slug(text: str) -> str:
    """Reduce a value to something safe as a single path segment."""
    return _UNSAFE.sub("-", str(text)).strip("-") or "value"


def run_key_for(cli_vars: Optional[Dict[str, Any]]) -> str:
    """Name this run from the variables that distinguish it.

    CLI ``--var`` values are the right signal by construction: they are what the operator
    varied. Keys are sorted so the same run always lands in the same directory regardless
    of the order they were typed in.
    """
    if not cli_vars:
        return DEFAULT_RUN_KEY
    parts = [f"{_slug(k)}-{_slug(v)}" for k, v in sorted(cli_vars.items())]
    return "_".join(parts) or DEFAULT_RUN_KEY


def _get_debug_dir(
    pipeline_config: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_name: str = "pipeline",
    run_key: Optional[str] = None,
) -> str:
    """Return the debug output directory for this run.

    ``run_key`` is optional so that callers which have not been threaded through — and
    older captured directories — keep working; without it the layout is the pre-#198 one.
    """
    import os

    raw = pipeline_config.get("intermediate_file_directory")
    if raw:
        resolved = resolve(str(raw), context)
        base = Path(str(resolved)) / "debug" / pipeline_name
    else:
        base = Path(os.getcwd()) / "outputs" / "debug" / pipeline_name

    # A run with no distinguishing variables gets no extra path segment: the subdirectory
    # exists to name what varied, and when nothing varied there is nothing to name. This
    # also leaves the layout unchanged for pipelines that take no --var, so existing paths,
    # docs and habits keep working.
    if run_key and run_key != DEFAULT_RUN_KEY:
        base = base / run_key
    return str(base)


def _clear_debug_dir(
    pipeline_config: Dict[str, Any],
    context: Dict[str, Any],
    dry_run: bool,
    pipeline_name: str = "pipeline",
    run_key: Optional[str] = None,
) -> None:
    """Make sure this run's debug directory exists. Deletes nothing.

    Named ``_clear_`` for continuity with its callers; it no longer clears. Files from a
    previous run of the *same* key are written over as the run reaches them, so a stale
    file lingers rather than an entire run's evidence disappearing. That trade is
    deliberate: a leftover file is confusing, a deleted audit trail is unrecoverable.
    """
    if dry_run:
        return
    debug_dir = Path(_get_debug_dir(pipeline_config, context, pipeline_name, run_key))
    debug_dir.mkdir(parents=True, exist_ok=True)
