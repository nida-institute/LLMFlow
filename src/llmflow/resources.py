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

#: One file per dataset somebody has downloaded or cloned, naming where it landed on this
#: machine. Written by `sp`, never by a project — which is what makes it the right home for the
#: one absolute path a machine needs, and why an annotation key may name a dataset instead of a
#: path. `registry.DatasetRegistry` writes the same directory.
DATASETS_DIRNAME = "datasets"

#: Where the corpora themselves go — hundreds of megabytes, and deliberately **not** hidden.
#: Configuration belongs in a dotfile; a library of texts does not, and a store nobody can see
#: is a store nobody notices duplicating itself.
DATA_DIRNAME = "resources"

#: The directory registrations lived in before #217, so `sp doctor` can carry them across.
#:
#: Deliberately only `resources`. An intermediate rename to `resources` existed for part of one
#: day and never shipped, and listing it here would collide head-on with `DATA_DIRNAME`: under
#: `$SP_HOME` the corpora now live at `resources/`, and a fallback reading that as a
#: registrations directory would try to parse a library of texts as YAML.
LEGACY_REGISTRATION_DIRNAMES = ("resources",)
LEGACY_DATA_DIRNAME = "data"

#: The catalog block listing what an entry can be read as. Named for what it describes rather
#: than for this engine: another tool reading the catalog needs the same four facts.
PROVIDES_KEY = "provides"

#: The directory this store used before #217. Read for migration, never written.
LEGACY_RESOURCES_DIRNAME = "resources"


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


#: Catalog fields rendered as elements, and therefore searchable. `contains(., "…")` is free text
#: across all of them, because XPath concatenates the text of a node's descendants.
SEARCHABLE_FIELDS = ("id", "name", "category", "description", "notes", "license", "formats")

#: A query of only these characters is a keyword rather than an XPath predicate. Precise rather
#: than a guess: no predicate is spelled without a bracket, a quote, an operator or a colon.
_KEYWORD = re.compile(r"[\w][\w.-]*\Z")


def _xpath_text(value: Any) -> str:
    """An XPath argument as a string, whether it arrived as a node set or a literal."""
    if isinstance(value, list):
        return " ".join(
            item if isinstance(item, str) else "".join(item.itertext()) for item in value
        )
    return "" if value is None else str(value)


def _lower_case(context, value) -> str:
    """XPath 2.0 `lower-case()`, which lxml's XPath 1.0 does not provide."""
    return _xpath_text(value).lower()


def _matches(context, value, pattern, flags="") -> bool:
    """XPath 2.0 `matches()`: a regular expression, not a containment test.

    Implemented with its real semantics rather than redefined as `contains`, because a standard
    function that means something else in one tool is worse than no function at all.
    """
    options = re.IGNORECASE if "i" in _xpath_text(flags) else 0
    try:
        return re.search(_xpath_text(pattern), _xpath_text(value), options) is not None
    except re.error:
        return False


def _catalog_tree():
    """The catalog as an XML tree, so a search is real XPath rather than a language of ours."""
    from lxml import etree  # type: ignore[attr-defined]

    registered = set(load_registered())
    root = etree.Element("catalog")
    for entry in catalog():
        node = etree.SubElement(root, "resource")
        for field in SEARCHABLE_FIELDS:
            value = entry.get(field)
            if isinstance(value, (list, tuple)):
                value = " ".join(str(item) for item in value)
            child = etree.SubElement(node, field)
            child.text = "" if value is None else str(value)
        node.set("readable", "true" if entry.get(PROVIDES_KEY) else "false")
        node.set("registered", "true" if entry.get("id") in registered else "false")
        node.set(
            "fetch",
            "download" if entry.get("download") else "git" if entry.get("github") else "manual",
        )
    return root


def search(query: str) -> list:
    """Catalog entries matching *query*, which is an XPath predicate over a `resource`.

    The whole catalog is searched, not the readable subset that `sp resource list` shows — which
    is the point, since a resource nobody can open yet is exactly what a reader is looking for.

    A query of bare word characters is a keyword: `discourse` means
    `contains(lower-case(.), "discourse")`, free text across every searchable field and
    case-insensitive. Anything else is evaluated as written, so the full language is available —
    `contains(category, "Treebank")`, `starts-with(id, "morphgnt")`, `@readable = "true"`, and
    boolean combinations of them. `lower-case()` and `matches()` are supplied as extension
    functions with their XPath 2.0 semantics, scoped to the query so they cannot leak into the
    XPath and XSLT plugins.
    """
    from lxml import etree  # type: ignore[attr-defined]

    text = str(query or "").strip()
    if not text:
        raise ValueError("a resource search needs a keyword or an XPath predicate.")

    predicate = (
        f'contains(lower-case(.), "{text.lower()}")' if _KEYWORD.match(text) else text
    )

    try:
        evaluate = etree.XPath(
            f"//resource[{predicate}]",
            extensions={(None, "lower-case"): _lower_case, (None, "matches"): _matches},
        )
        hits = evaluate(_catalog_tree())
    except etree.XPathError as error:
        raise ValueError(f"{query!r} is not a valid search: {error}")

    found = {node.findtext("id") for node in hits}
    return [entry for entry in catalog() if entry.get("id") in found]


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
    """The file a definition's `path` points at."""
    raw = str(definition.get("path") or "")
    if not raw:
        raise ValueError(
            f"resource definition {definition.get('id') or '(unnamed)'!r} has no `path`."
        )
    return resolve_declared_path(raw, definition)


def dataset_registration(identifier: str) -> Optional[dict]:
    """The datasets-store entry for *identifier*, or None when nothing is registered under it.

    Read-only by design: a lookup never creates the store directory. The store is write-protected
    and a missing directory is the normal case on a fresh machine, so a reader that made one would
    fail exactly where it should have answered "nothing registered".

    A value carrying a path separator is never an id, so an id can address only a file inside the
    datasets directory.
    """
    import yaml

    name = str(identifier or "")
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        return None

    path = _paths.sp_home() / DATASETS_DIRNAME / f"{name}.yaml"
    if not path.is_file():
        return None
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError):
        # One bad hand-edit should not make every annotation source unresolvable.
        return None
    return dict(loaded) if isinstance(loaded, Mapping) else None


def resolve_declared_path(value: Any, definition: Mapping[str, Any]) -> Path:
    """Where a path declared in a registration points. One resolver for every such key.

    Three forms, in this order:

    - **absolute** — honoured unchanged, because a maintainer works against their own clone.
    - **a registered dataset id, optionally with a subpath** — `levinsohn-lgntdf/LGNTDF`
      resolves under that dataset's own path, which is where the one absolute path per machine
      belongs. This is the only form that reaches a corpus outside the resource's own dataset,
      and the subpath is not a convenience: the data rarely sits at a repository root.
    - **anything else** — dataset-relative, resolved against the store.

    So nothing a person authors carries an absolute path. Where a first segment is both a
    registered id and a directory inside the resource's dataset, the id wins: a declaration beats
    a coincidence of naming.

    The dataset-relative form resolves inside whichever copy of the corpus the store holds,
    while a dataset id resolves wherever that dataset was registered — possibly a different
    clone of the same corpus. Text and annotations join on word ids, so a caller mixing the two
    forms across keys can draw them from two copies, which is a silent mismatch rather than an
    error. The engine cannot tell the difference; the choice belongs to whoever writes the
    registration.
    """
    raw = str(value or "")
    if not raw:
        raise ValueError(
            f"resource definition {definition.get('id') or '(unnamed)'!r} declares an empty path."
        )

    path = Path(raw).expanduser()
    if path.is_absolute():
        return path

    head, _, tail = raw.partition("/")
    registered = dataset_registration(head)
    if registered and registered.get("path"):
        root = Path(str(registered["path"])).expanduser()
        if not tail:
            return root
        resolved = (root / tail).resolve()
        # A subpath names a place inside the dataset. Refusing the escape keeps a registration
        # from reaching an arbitrary file through a dataset it merely names.
        if root.resolve() not in resolved.parents and resolved != root.resolve():
            raise ValueError(
                f"resource definition {definition.get('id') or '(unnamed)'!r} declares "
                f"{raw!r}, which leaves dataset {head!r} at {root}."
            )
        return resolved

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
        # The registry's own name for it — what `resource_scheme()` reads first.
        entry["versification_scheme"] = item["versification"]

    target = _write_registration(
        default_resources_dir() / f"{identifier}.yaml",
        "# Written by `sp resource add`. The path is relative to the dataset, so this file\n"
        "# means the same thing on every machine. An absolute `path:` is honoured too.\n",
        entry,
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


def _write_registration(target: Path, banner: str, entry: Mapping[str, Any]) -> Path:
    """Write one registration, unlocking the store around it.

    `~/.sp` is kept read-only, and the registrations directory inherits that mode when
    `sp doctor` moves it across, so a plain write fails with EACCES on a machine that has been
    set up — and on no machine that a test builds. The lock is restored afterwards rather than
    left off: unconditionally unlocking is what broke `install_global_skills()` silently once.
    """
    import os

    import yaml

    from llmflow.cli_utils import _lock_sp_dir, _unlock_sp_dir

    target.parent.mkdir(parents=True, exist_ok=True)
    was_locked = not os.access(target.parent, os.W_OK)
    if was_locked:
        _unlock_sp_dir(target.parent)
    try:
        target.write_text(
            banner + yaml.safe_dump(dict(entry), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    finally:
        if was_locked and target.parent.exists():
            _lock_sp_dir(target.parent)
    return target


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

    return _write_registration(
        default_resources_dir() / f"{identifier}.yaml",
        "# Written by `sp resource add --path`. The path is this machine's, deliberately:\n"
        "# it names something outside the store, so it cannot be made relative to it.\n",
        entry,
    )


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
