"""What a run wrote, so a re-run can remove its own previous output and nothing else.

Re-running a pipeline with the same parameters used to leave the previous run's
intermediates in place, so a later reader — `/audit-output` especially — saw two runs' files
as one set and reasoned about a mixture (LLMFlow#245). Where filenames carry content rather
than parameters, a re-run that draws a boundary differently writes *new* names and the old
ones stay; nothing said which run a file came from.

`sp clean` before the run is the wrong fix twice over. It deletes the whole declared
`intermediate_file_directory`, which every parameterisation shares, so cleaning before a Mark
run destroys the 1 John intermediates — LLMFlow#198's bug moved from `debug/` into
`intermediate/`. And it breaks `--rewind-to`, which replays a step by reading the very
artifacts a pre-run clean removes.

So the run records the paths it wrote, keyed by pipeline and by the run key that already
keeps one parameterisation's debug trail apart from another's. A matching re-run deletes
exactly what that record lists. This is #198's principle — separation makes deletion safe —
without changing the directory tree: artifacts stay where the pipeline declares them, and a
run can only ever delete its own previous output.

Four rails, from the issue:

1. Intermediates only. A recorded path outside the declared `intermediate_file_directory`
   is skipped, so an implicit clean can never reach a deliverable.
2. Skipped entirely under `--rewind-to`, which consumes the files a clean would remove.
3. The run reports what it deleted.
4. A listed file already gone is not an error.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

from llmflow.modules.logger import Logger

logger = Logger()

#: Where a run's record of its own writes lives, under the declared intermediate directory.
#: Not under `debug/`: that tree is emptied by `_clear_debug_dir` at the start of every run,
#: so a manifest kept there would be destroyed before the run needing it could read it.
RUNS_DIRNAME = ".sp-runs"


def manifest_path(intermediate_dir: Path, pipeline_name: str, run_key: str) -> Path:
    """The manifest for one pipeline run under one set of `--var` values."""
    return Path(intermediate_dir) / RUNS_DIRNAME / pipeline_name / f"{run_key}.json"


def _under(path: Path, directory: Path) -> bool:
    """True when *path* is inside *directory*, both resolved."""
    try:
        path.resolve().relative_to(directory.resolve())
    except ValueError:
        return False
    return True


def read(path: Path) -> List[str]:
    """The paths a previous run recorded, or [] when there is no readable record.

    Absence is the normal case — a first run, or one whose intermediates were cleaned — and a
    damaged file must not stop a run that is only trying to tidy up after itself.
    """
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.warning(f"⚠️  Unreadable run manifest, so nothing is cleaned: {path}")
        return []
    written = data.get("written") if isinstance(data, dict) else None
    return [str(item) for item in written] if isinstance(written, list) else []


def clean_previous_run(
    manifest: Path, intermediate_dir: Path
) -> List[str]:
    """Delete the files the previous matching run recorded writing. Returns what went.

    Rail 1 filters to *intermediate_dir*, so a recorded deliverable is left alone even though
    the run wrote it; rail 4 makes a file that is already gone a non-event.
    """
    removed: List[str] = []
    for recorded in read(manifest):
        target = Path(recorded)
        if not _under(target, intermediate_dir):
            continue
        try:
            target.unlink()
        except FileNotFoundError:
            continue
        except OSError as error:
            logger.warning(f"⚠️  Could not remove {target}: {error}")
            continue
        removed.append(str(target))

    # Rail 3. A silent deletion inside a run is how #145 and #198 each went wrong.
    if removed:
        logger.info(f"🧹 Removed {len(removed)} file(s) from this run's previous output:")
        for path in removed:
            logger.info(f"   {path}")
    return removed


def write(manifest: Path, written: Iterable[str]) -> None:
    """Record the paths this run wrote.

    Every path is recorded, including those outside the intermediate directory: the manifest
    says what the run wrote, and rail 1 is applied when reading it back. Filtering here would
    make the record depend on a directory declaration that can change between runs.
    """
    manifest.parent.mkdir(parents=True, exist_ok=True)
    payload = {"written": sorted({str(path) for path in written})}
    manifest.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def is_enabled(
    pipeline_config: dict,
    *,
    no_clean: bool,
    dry_run: bool,
    rewind_to: Optional[str],
) -> bool:
    """Whether this run cleans its own previous output.

    `clean_before_run:` defaults to true; `--no-clean` overrides it per invocation. A dry run
    writes nothing so it removes nothing, and `--rewind-to` is rail 2 — it replays from the
    files a clean would take.
    """
    if no_clean or dry_run or rewind_to:
        return False
    declared = pipeline_config.get("clean_before_run")
    return True if declared is None else bool(declared)
