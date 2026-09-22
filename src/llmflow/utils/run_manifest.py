"""What a run wrote, so a re-run can remove its own previous output and nothing else.

A run records every path it writes in `<intermediate_file_directory>/.sp-runs/<pipeline>/<run
key>.json`. A re-run whose pipeline and run key match deletes exactly what that record lists,
then writes a fresh one.

Four rails: only paths under the declared `intermediate_file_directory` are removed; the clean
is skipped under `--rewind-to`; every deletion is reported; a listed file already gone is not
an error.

Why it works this way, and what was rejected: LLMFlow#245.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

from llmflow.modules.logger import Logger

logger = Logger()

#: Where a run's record of its own writes lives, under the declared intermediate directory.
#: It must stay outside `debug/`, which `_clear_debug_dir` empties at the start of every run.
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

    # Rail 3: every deletion is reported.
    if removed:
        logger.info(f"🧹 Removed {len(removed)} file(s) from this run's previous output:")
        for path in removed:
            logger.info(f"   {path}")
    return removed


def write(manifest: Path, written: Iterable[str]) -> None:
    """Record the paths this run wrote.

    Every path is recorded, including those outside the intermediate directory; rail 1 is
    applied when the record is read back rather than when it is written.
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
