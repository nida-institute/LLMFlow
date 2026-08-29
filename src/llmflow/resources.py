"""What resources exist, how to open one, and which of them this machine has (#217).

Three questions with three different owners, and the defect this module exists for was answering
them in one place or in none.

- **What exists, and how do I get it** is the public catalog, `resources.json`, maintained in
  `nida-institute/awesome-biblical-data` and vendored here so nothing needs a network.
- **How is it opened** is the `provides` block on a catalog entry: which file inside the
  download, which backend reads that shape, which versification its references are in. Facts
  about how the resource is *built*, which change only when it is restructured.
- **What this machine has** is `~/.sp/resources/` — one file per resource somebody chose to
  register, holding a dataset-relative path so the file means the same thing on every machine.

**State is deliberately absent.** Which books have been reviewed, what is superseded, what is
usable — that changes whenever a maintainer works, and a copy here would eventually tell a
consumer that a reviewed file is unreviewed, authoritatively and wrongly. Where a resource
declares its own state, its entry points at the manifest and the reader goes there.
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional
from urllib.parse import urlparse

from llmflow import paths as _paths
from llmflow.modules.logger import Logger

logger = Logger()

#: The vendored copy of the public catalog.
CATALOG_FILENAME = "resources.json"

#: One file per registration, inside the store beside the rest of the configuration. Small,
#: hand-editable, and yours: which texts *this machine* has been told it may read.
RESOURCES_DIRNAME = "registrations"

#: Where the corpora themselves go — hundreds of megabytes, and deliberately **not** hidden.
#: Configuration belongs in a dotfile; a library of texts does not, and a store nobody can see
#: is a store nobody notices duplicating itself.
DATA_DIRNAME = "resources"

#: The directory registrations lived in before #217, so `sp doctor` can carry them across.
#:
#: Deliberately only `editions`. An intermediate rename to `resources` existed for part of one
#: day and never shipped, and listing it here would collide head-on with `DATA_DIRNAME`: under
#: `$SP_HOME` the corpora now live at `resources/`, and a fallback reading that as a
#: registrations directory would try to parse a library of texts as YAML.
LEGACY_REGISTRATION_DIRNAMES = ("editions",)
LEGACY_DATA_DIRNAME = "data"

#: The catalog block listing what an entry can be read as. Named for what it describes rather
#: than for this engine: another tool reading the catalog needs the same four facts.
PROVIDES_KEY = "provides"

#: The directory this store used before #217. Read for migration, never written.
LEGACY_RESOURCES_DIRNAME = "editions"


def catalog_path() -> Path:
    """The vendored catalog, whether running from a wheel or a dev checkout."""
    import importlib.resources

    try:
        ref = importlib.resources.files("llmflow").joinpath(f"data/{CATALOG_FILENAME}")
        path = Path(str(ref))
        if path.exists():
            return path
    except Exception:
        pass
    return Path(__file__).resolve().parent.parent.parent / "data" / CATALOG_FILENAME


@lru_cache(maxsize=1)
def catalog() -> tuple:
    """Every catalog entry. Absence is a packaging fault, not a user error."""
    path = catalog_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"resource catalog not found at {path}. It declares every resource sp knows how to "
            f"open; without it `sp resource` cannot tell what exists."
        )
    entries = json.loads(path.read_text(encoding="utf-8"))
    return tuple(entries)


def _safe(segment: str) -> str:
    """One path segment, with anything that could leave the directory removed."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", segment).strip("-.")
    return cleaned or "unnamed"


def dataset_dir(entry: Mapping[str, Any]) -> str:
    """Where a catalog entry unpacks, relative to the store's data directory.

    Two segments, always: **where it came from, then which thing it is.** A directory listing
    then says who published what, and two contributors cannot collide.

    - In git: `Clear-Bible/macula-greek`, from the source URL rather than the catalog id. An id
      is a label someone chose and may rename; the repository path is the resource's identity.
    - Downloaded from a site: `https-tyndaleopenresources.com/tyndale_open-studynotes` — the
      scheme and host, then the downloaded file's name without its extension.
    - Neither: the catalog id, which is all there is.
    """
    github = str(entry.get("github") or "").rstrip("/")
    if github:
        parts = [p for p in github.split("/") if p]
        if len(parts) >= 2:
            return f"{_safe(parts[-2])}/{_safe(parts[-1])}"

    identifier = str(entry.get("id") or "")
    source = str(entry.get("download") or entry.get("url") or "")
    if source:
        parsed = urlparse(source)
        host = f"{parsed.scheme}-{parsed.netloc}" if parsed.scheme else parsed.netloc
        name = PurePosixPath(parsed.path).name
        # Only a `download` names a file; a bare site URL does not, and the id is the better name.
        stem = PurePosixPath(name).stem if entry.get("download") and name else identifier
        if host:
            return f"{_safe(host)}/{_safe(stem or identifier)}"

    return _safe(identifier) if identifier else ""


def readable() -> dict:
    """`{id: item}` for everything the catalog says can be opened.

    An entry with no `provides` block is a resource sp has no reader for — ACAI is entity
    annotation, MARBLE a domain index — and asking for one by name is an error rather than an
    empty result. Each item carries the dataset that provides it, because one download may carry
    several readable texts, and the licence, so a later reader sees the terms without coming back
    here.
    """
    out: dict = {}
    for entry in catalog():
        for item in entry.get(PROVIDES_KEY) or []:
            if not isinstance(item, Mapping) or not item.get("id"):
                continue
            merged = dict(item)
            merged["dataset"] = dataset_dir(entry)
            merged["source_id"] = entry.get("id")
            merged.setdefault("license", entry.get("license"))
            # Where to get it, carried so a fetcher needs the item and not the whole catalog.
            for field in ("github", "download"):
                if entry.get(field):
                    merged.setdefault(field, entry[field])
            out[str(item["id"])] = merged
    return out


def default_resources_dir() -> Path:
    """The `resources` directory inside the store."""
    return _paths.sp_home() / RESOURCES_DIRNAME


def legacy_resources_dirs() -> tuple:
    """Where registrations lived before #217, so `sp doctor` can carry them across."""
    return tuple(_paths.sp_home() / name for name in LEGACY_REGISTRATION_DIRNAMES)


def data_dir() -> Path:
    """Where the corpora live.

    Visible by default — `~/sp/resources/` — because a library of texts is not configuration
    and a hidden one duplicates itself unnoticed. `$SP_HOME` keeps everything together when it
    is set, which is what a container and the test suite want; `$LLMFLOW_DATA_DIR` overrides
    both, and `sp doctor` reports either redirection so one machine's several copies are visible.
    """
    override = os.environ.get("LLMFLOW_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if os.environ.get(_paths.SP_HOME_ENV):
        return _paths.sp_home() / DATA_DIRNAME
    return Path.home() / "sp" / DATA_DIRNAME


def legacy_data_dir() -> Path:
    """`~/.sp/data`, where corpora lived before they were made visible."""
    return _paths.sp_home() / LEGACY_DATA_DIRNAME


def resolve_path(definition: Mapping[str, Any]) -> Path:
    """The file a definition points at.

    A dataset-relative path is resolved against the store, so the registration is the same on
    every machine. An absolute path is honoured unchanged and wins over any `dataset`: a
    maintainer works against their own clone, and that is the whole reason absolute paths stay
    supported.
    """
    raw = str(definition.get("path") or "")
    if not raw:
        raise ValueError(
            f"resource definition {definition.get('id') or '(unnamed)'!r} has no `path`."
        )
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    dataset = definition.get("dataset")
    if dataset:
        return data_dir() / str(dataset) / raw
    return path


def load_registered(directory: Any = None) -> dict:
    """Every registration this machine holds. Absence is normal; a fresh machine has none.

    A malformed file is skipped rather than allowed to make every resource unreadable — one bad
    hand-edit should not take the whole store down with it.
    """
    import yaml

    root = Path(directory) if directory is not None else default_resources_dir()

    if directory is None and not root.is_dir():
        for legacy in legacy_resources_dirs():
            if not legacy.is_dir():
                continue
            # A migration with a stated end: `sp doctor` moves the directory, and this branch
            # goes with the release after the one that introduced it. Reading it meanwhile
            # keeps an upgraded machine working instead of failing every pipeline at once.
            logger.warning(
                f"Reading registrations from {legacy} — that directory was renamed to "
                f"{root.name!r} in #217. Run `sp doctor` to move it; this fallback will be "
                f"removed."
            )
            root = legacy
            break

    if not root.is_dir():
        return {}
    out: dict = {}
    for path in sorted(root.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue  # a broken file hides itself, not its neighbours
        if not isinstance(data, Mapping):
            continue
        name = data.get("id") or path.stem
        out[str(name)] = dict(data)
    return out


#: What a registration records. `path` stays relative and `dataset` says what it is relative to,
#: so the file is identical on every machine; the rest is copied from the catalog so a reader
#: sees the terms and the numbering without going back to it.
REGISTERED_FIELDS = ("name", "language", "canon", "kind", "path", "license")


def register(identifier: str, download: bool = True) -> Path:
    """Write this machine's registration for one catalog resource, and return its path.

    Downloading is the default because `sp resource add X` is a request to make X usable, and a
    registration pointing at data that is not there reproduces the failure #217 reports: a
    command reports success and the pipeline fails later. `download=False` is for a metered
    connection or an offline setup, and says plainly that the resource will not resolve yet.
    """
    item = readable().get(identifier)
    if item is None:
        known = ", ".join(sorted(readable())) or "(none)"
        raise KeyError(
            f"The catalog has no readable resource {identifier!r}. It knows: {known}. "
            f"A resource of your own is registered from its path instead."
        )

    if download and not resolve_path(item).exists():
        from llmflow.download_data import fetch

        fetch(item)

    entry: dict = {"id": identifier, "dataset": item.get("dataset")}
    for field in REGISTERED_FIELDS:
        if item.get(field):
            entry[field] = item[field]
    if item.get("versification"):
        # The registry's own name for it — what `edition_scheme()` reads first.
        entry["versification_scheme"] = item["versification"]

    directory = default_resources_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{identifier}.yaml"

    import yaml

    target.write_text(
        "# Written by `sp resource add`. The path is relative to the dataset, so this file\n"
        "# means the same thing on every machine. An absolute `path:` is honoured too.\n"
        + yaml.safe_dump(entry, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    if not resolve_path(entry).exists():
        logger.warning(
            f"{identifier} is registered, but its data is not on this machine yet. "
            f"Fetch it with `sp resource add {identifier}` (without --no-download)."
        )
    return target


#: Written beside a fetched resource, recording what was fetched. A directory named
#: `Clear-Bible/macula-hebrew` says which resource it holds and says nothing about *which copy*
#: — two machines, or one machine six months apart, differ invisibly without this (#201).
VERSION_FILENAME = ".sp-resource.json"


def installed_version(directory: Any) -> Optional[dict]:
    """What was fetched into *directory*, or None if nothing recorded it.

    None is the honest answer for data placed by hand or fetched by an older release. Doctor
    reports it as unknown rather than inventing a version.
    """
    path = Path(directory) / VERSION_FILENAME
    if not path.is_file():
        return None
    try:
        recorded = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return recorded if isinstance(recorded, dict) else None


def record_version(directory: Any, **fields: Any) -> Path:
    """Write the record of what was just fetched."""
    path = Path(directory) / VERSION_FILENAME
    path.write_text(json.dumps(fields, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def register_local(
    identifier: str,
    path: Any,
    kind: Optional[str] = None,
    versification: Optional[str] = None,
    name: Optional[str] = None,
) -> Path:
    """Register something this machine already has, by its path.

    The catalog cannot describe a resource that is not public, and it does not need to: access
    to a Paratext project is a right its owner has already established, and a repository of
    your own is your responsibility. So the engine records what it is told and gates nothing on
    licence.

    A Paratext project identifies itself — `Settings.xml` names the versification and the
    directory is the project — so almost nothing has to be typed. Anything else must say what
    kind it is, because guessing a reader from a file extension is how the wrong text gets read.
    """
    target_path = Path(str(path)).expanduser()
    if not target_path.exists():
        raise FileNotFoundError(f"Nothing to register at {target_path}.")

    entry: dict = {"id": identifier, "name": name or identifier}
    settings = target_path / "Settings.xml"

    if settings.is_file():
        from llmflow.utils import scripture as _scripture

        entry["kind"] = "usfm"
        entry["base_dir"] = str(target_path.parent)
        entry["project"] = target_path.name
        scheme = versification or _scripture._paratext_scheme(
            {"base_dir": str(target_path.parent), "project": target_path.name}
        )
        if scheme:
            entry["versification_scheme"] = scheme
    else:
        if not kind:
            raise ValueError(
                f"Registering {target_path} needs a `kind` — tsv, tei or usfm. Only a Paratext "
                f"project can say what it is on its own, by its Settings.xml."
            )
        entry["kind"] = str(kind).lower()
        if entry["kind"] == "usfm":
            entry["base_dir"] = str(target_path.parent)
            entry["project"] = target_path.name
        else:
            entry["path"] = str(target_path)
        if versification:
            entry["versification_scheme"] = versification

    directory = default_resources_dir()
    directory.mkdir(parents=True, exist_ok=True)
    written = directory / f"{identifier}.yaml"

    import yaml

    written.write_text(
        "# Written by `sp resource add --path`. The path is this machine's, deliberately:\n"
        "# it names something outside the store, so it cannot be made relative to it.\n"
        + yaml.safe_dump(entry, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return written


def report() -> list:
    """One row per readable resource: what it is, where it comes from, and its status."""
    registered = load_registered()
    rows = []
    for identifier, item in sorted(readable().items()):
        rows.append(
            {
                "id": identifier,
                "name": item.get("name") or identifier,
                "kind": item.get("kind"),
                "dataset": item.get("dataset"),
                "license": item.get("license"),
                "status": status(identifier, registered=registered),
            }
        )
    return rows


def status(identifier: str, registered: Optional[Mapping[str, Any]] = None) -> str:
    """`registered`, `available` or `absent` for one catalog id.

    `available` means the data is on this machine and nothing has chosen to use it — the state a
    fresh machine reaches after `sp download-data` and the one `sp doctor` reports with a remedy.
    """
    known = dict(registered) if registered is not None else load_registered()
    if identifier in known:
        return "registered"
    item = readable().get(identifier)
    if item is None:
        return "absent"
    try:
        return "available" if resolve_path(item).exists() else "absent"
    except ValueError:
        return "absent"
