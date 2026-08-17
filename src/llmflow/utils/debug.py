"""Debug output directory utilities.

The debug directory holds the evidence a conclusion is audited from: the exact request
sent to the model, its unedited reply, and the run log. That evidence used to survive
exactly one run.

`_clear_debug_dir()` did `shutil.rmtree()` at the start of every run, on a directory keyed
by pipeline filename alone. Running the same pipeline for Ruth and then for Mark therefore
deleted the entire Ruth run — reported from Ears to Hear, LLMFlow#198. Nothing warned; the
run reported success.

The fix is not to stop cleaning — a run directory *should* hold that run and nothing else,
which was #145's point. The fix is to scope the clean to one run:

* **The run key is part of the path.** CLI ``--var`` values are what distinguish one run of
  a pipeline from the next, so they name the directory: ``debug/<pipeline>/book-Ruth/``.
* **The clear targets that leaf directory**, never the parent holding sibling runs. The run
  key is emitted even when it is ``default``, precisely so the delete can never climb.

The second half of #198 is here too: debug filenames were doing a database's job. Two steps
sharing a prompt file produced the same name, a retry overwrote the attempt it retried, and
``sp tools replay`` paired requests with responses by sorting filenames. A sequence number
now makes each name unique and ordered, and :class:`DebugRecorder` writes a
``manifest.jsonl`` carrying the facts — step, attempt, model, passage, timings, and which
files belong together.
"""

import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
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

    # The run key is ALWAYS a segment, including the default. It is tempting to omit it for
    # runs with no --var, to leave those layouts untouched — but the run directory is
    # emptied at the start of a run, and without the segment that rmtree would target
    # debug/<pipeline>/, which contains the sibling run directories. One var-less run would
    # then delete every per-book trail. The segment is what keeps the delete to a leaf.
    if run_key:
        base = base / run_key
    return str(base)


def _clear_debug_dir(
    pipeline_config: Dict[str, Any],
    context: Dict[str, Any],
    dry_run: bool,
    pipeline_name: str = "pipeline",
    run_key: Optional[str] = None,
) -> None:
    """Empty **this run's** directory at the start of the run.

    A run directory should contain that run and nothing else — no leftovers from a previous
    attempt to puzzle over. That was #145's point and it still holds.

    What changed in #198 is the *scope*. The delete used to target
    ``debug/<pipeline_name>/``, shared by every run of the pipeline, so a second passage
    erased the first. It now targets ``debug/<pipeline_name>/<run_key>/``, which belongs to
    this run alone; sibling runs are untouched. `_get_debug_dir` always emits the run-key
    segment precisely so that this delete can never reach a parent holding other runs.
    """
    if dry_run:
        return
    debug_dir = Path(_get_debug_dir(pipeline_config, context, pipeline_name, run_key))
    if debug_dir.exists():
        shutil.rmtree(debug_dir)
    debug_dir.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------------------
# Run manifest (LLMFlow#198)
#
# Debug filenames used to carry the facts about a call — passage, prompt, request-or-
# response — and `sp tools replay` had to parse them back out, pairing a request with its
# response by sorting names and taking "the earliest at or after". That is a join done with
# string comparison, and it was lossy in three ways: two steps sharing a prompt file
# produced the same name, a retry overwrote the attempt it retried, and the only field that
# could establish order was present only when `passage` was absent.
#
# A sequence number makes the name unique and orders it; the manifest carries the facts.
# --------------------------------------------------------------------------------------

MANIFEST_NAME = "manifest.jsonl"


@dataclass
class DebugCall:
    """One model call, and where its evidence lives."""

    seq: int
    step: str
    attempt: int
    prompt_file: str = ""
    model: str = ""
    passage: str = ""
    iteration: str = ""
    started: str = ""
    request_path: Optional[str] = None
    response_path: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)

    @property
    def slug(self) -> str:
        parts = [f"{self.seq:04d}", _slug(self.step)]
        if self.attempt > 1:
            parts.append(f"attempt{self.attempt}")
        return "-".join(parts)


class DebugRecorder:
    """Writes a run's debug files and the manifest describing them.

    Held on ``pipeline_config["_debug_recorder"]`` so the several write sites share one
    sequence counter. When *enabled* is false every method is a no-op returning ``None``
    paths — debug capture is opt-in, and the recorder must never be able to break a run.
    """

    def __init__(self, run_dir: Any, enabled: bool = True) -> None:
        self.run_dir = Path(run_dir)
        self.enabled = enabled
        self._seq = 0
        self._attempts: Dict[str, int] = {}

    def begin(
        self,
        step: str,
        prompt_file: str = "",
        model: str = "",
        passage: str = "",
        iteration: str = "",
    ) -> DebugCall:
        """Allocate a sequence number and attempt number for a call about to be made."""
        self._seq += 1
        self._attempts[step] = self._attempts.get(step, 0) + 1
        return DebugCall(
            seq=self._seq,
            step=step or "step",
            attempt=self._attempts[step],
            prompt_file=prompt_file,
            model=model,
            passage=passage,
            iteration=iteration,
            started=datetime.now().isoformat(timespec="seconds"),
        )

    def save_request(self, call: DebugCall, content: str) -> Optional[str]:
        return self._write(call, "request", content, "txt")

    def save_response(self, call: DebugCall, content: Any) -> Optional[str]:
        """Save a response, as JSON when it is structured and text otherwise."""
        if isinstance(content, (dict, list)):
            return self._write(call, "response", json.dumps(content, indent=2), "json")
        return self._write(call, "response", str(content), "txt")

    def save_artifact(self, name: str, content: Any) -> Optional[str]:
        """Save a supplementary file that is not itself a model call.

        The responses-API path dumps the provider's raw reply alongside the step's parsed
        response. That is one call's evidence, not a second call, so it gets a file but no
        sequence number and no manifest line of its own.
        """
        if not self.enabled:
            return None
        self.run_dir.mkdir(parents=True, exist_ok=True)
        path = self.run_dir / f"{_slug(name)}.txt"
        path.write_text(str(content), encoding="utf-8")
        return str(path)

    def _write(self, call: DebugCall, kind: str, content: str, ext: str) -> Optional[str]:
        if not self.enabled:
            return None
        self.run_dir.mkdir(parents=True, exist_ok=True)
        path = self.run_dir / f"{call.slug}-{kind}.{ext}"
        path.write_text(content, encoding="utf-8")
        if kind == "request":
            call.request_path = str(path)
        else:
            call.response_path = str(path)
        return str(path)

    def finish(self, call: DebugCall, **extras: Any) -> None:
        """Append this call's line to the manifest.

        File paths are stored **relative to the run directory** so a run can be archived or
        moved without invalidating them.
        """
        if not self.enabled:
            return
        # `model` may be corrected by the caller via extras: the declared model and the one
        # actually called differ whenever a default or llm_config value fills in, and the
        # record has to name the model that answered.
        record = {
            "seq": call.seq,
            "step": call.step,
            "attempt": call.attempt,
            "prompt_file": call.prompt_file,
            "model": extras.pop("model", None) or call.model,
            "passage": call.passage,
            "iteration": call.iteration,
            "started": call.started,
            "finished": datetime.now().isoformat(timespec="seconds"),
            "status": extras.pop("status", "ok"),
            "request_file": self._relative(call.request_path),
            "response_file": self._relative(call.response_path),
        }
        record.update(extras)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with (self.run_dir / MANIFEST_NAME).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _relative(self, path: Optional[str]) -> Optional[str]:
        if not path:
            return None
        try:
            return str(Path(path).relative_to(self.run_dir))
        except ValueError:
            return str(path)


def read_manifest(run_dir: Any) -> list:
    """Read a run manifest, or return [] when there is none.

    Absence is normal, not an error: directories captured before #198 have no manifest, and
    `sp tools replay` falls back to its filename-pairing path for those.
    """
    path = Path(run_dir) / MANIFEST_NAME
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue  # a truncated final line must not make the whole run unreadable
    return out
