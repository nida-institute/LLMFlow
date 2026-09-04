"""Fetching a catalog resource onto this machine.

What exists and where to get it is the public catalog's job (`llmflow.resources`); this module
only does the fetching. It used to carry its own four-entry `CATALOG`, which was a smaller,
drifting copy of the public one — its `berean-usx` entry pointed at a repository that 404s, and
its dataset names disagreed with the catalog's ids. One declaration now, read by both (#217).

There is no `sp download-data` command any more. Fetching happens as part of `sp resource add`,
or on its own for a resource nothing can yet read — ACAI and the CNTR transcriptions are in the
catalog and have no reader, so they are fetched and used directly.
"""

from __future__ import annotations

import hashlib
import shutil
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping

from llmflow.modules.logger import Logger

logger = Logger()

AWESOME_BIBLICAL_DATA_URL = "https://github.com/nida-institute/awesome-biblical-data"


def get_default_data_dir() -> Path:
    """Where corpora live — one answer, owned by `llmflow.resources`.

    This module used to compute it separately, and kept answering `~/.sp/data` after the
    corpora moved somewhere visible. A real `sp resource add` then unpacked into a directory
    the reader never looks at — and, because `~/.sp` is deliberately read-only, could not even
    create it. Two encodings of one fact, agreeing until they silently did not.
    """
    from llmflow import resources as _resources

    return _resources.data_dir()


def _archive_url(source: Mapping[str, Any]) -> str:
    """Where to fetch from: a repository's default-branch zip, or a named download."""
    github = str(source.get("github") or "").rstrip("/")
    if github:
        branch = str(source.get("branch") or "main")
        return f"{github}/archive/refs/heads/{branch}.zip"
    download = str(source.get("download") or "")
    if download:
        return download
    raise ValueError(
        f"Resource {source.get('id') or '(unnamed)'!r} says neither `github` nor `download`, "
        f"so there is nowhere to fetch it from."
    )


def fetch(source: Mapping[str, Any], dest: Path | None = None) -> Path:
    """Download *source* into the store and return the directory it landed in.

    Present data is left alone: a fetch is skipped rather than repeated, so `sp resource add`
    on a machine that already has the download costs nothing.
    """
    from llmflow import resources as _resources

    dataset = str(source.get("dataset") or _resources.dataset_dir(source))
    if not dataset:
        raise ValueError("Cannot work out where to unpack this resource.")

    target = Path(dest) if dest else get_default_data_dir() / dataset
    if target.exists():
        logger.info(f"✅ Already downloaded: {target}")
        return target

    url = _archive_url(source)
    label = source.get("name") or source.get("id") or dataset
    logger.info(f"📥 Downloading {label} from {url}")
    logger.info(f"   Destination: {target}")

    request = urllib.request.Request(url, headers={"User-Agent": "llmflow/sp"})
    with urllib.request.urlopen(request) as response:
        data = response.read()

    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise RuntimeError(
            f"Cannot create {target}: {error}. Resources live outside the read-only store; if "
            f"this path is inside `~/.sp`, LLMFLOW_DATA_DIR or SP_HOME is redirecting it — "
            f"`sp doctor` reports both."
        )

    try:
        if zipfile.is_zipfile(BytesIO(data)):
            _unpack(data, target, strip=_github_prefix(source))
        else:
            (target / Path(urllib.parse.urlparse(url).path).name).write_bytes(data)
    except Exception:
        shutil.rmtree(target, ignore_errors=True)
        raise

    # Record what was fetched. A directory name says which resource this is; it says nothing
    # about which copy, and that is how two machines drift without either noticing (#201).
    _resources.record_version(
        target,
        id=source.get("id") or source.get("source_id"),
        source=url,
        branch=str(source.get("branch") or "main") if source.get("github") else None,
        sha256=hashlib.sha256(data).hexdigest(),
        bytes=len(data),
        fetched=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )

    logger.info(f"✅ Downloaded to {target}")
    return target


def _github_prefix(source: Mapping[str, Any]) -> str:
    """GitHub wraps an archive in `<repo>-<branch>/`; a plain download has no such wrapper."""
    github = str(source.get("github") or "").rstrip("/")
    if not github:
        return ""
    branch = str(source.get("branch") or "main")
    return f"{github.split('/')[-1]}-{branch}/"


def _unpack(data: bytes, dest: Path, strip: str = "") -> None:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        for member in archive.infolist():
            name = member.filename
            if strip:
                if not name.startswith(strip):
                    continue
                name = name[len(strip):]
            if not name or name.startswith("/") or ".." in name:
                continue  # never let an archive write outside its own directory
            member.filename = name
            archive.extract(member, dest)
