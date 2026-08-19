"""Loader for the managed-file catalog (#204, plan D7).

**The catalog itself is data, not code** — it lives in `data/file-catalog.yaml`, which is
where its comments, its policies and its field documentation belong. This module only
reads that file and answers questions about it.

Two things are derived from the catalog rather than maintained beside it:

- **the generated `.gitignore`** (D9) — from each entry's `committed` field
- **`sp doctor`'s ownership boundary** (D10) — from each entry's `policy` field

Deriving both is what stops them disagreeing with each other, which is the same principle
the Captain stated for D10: one authoritative place per fact.

Not catalogued by design: `~/.sp/user-context/`. Those files grant an AI standing access
to a machine, and only the machine's owner can grant that (D6). Cataloguing them would
invite `sp` to manage them.

Unrelated to `llmflow.catalog`, which describes the public API's *methods* (#187).
"""

from __future__ import annotations

import enum
import importlib.resources
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml


class Policy(enum.Enum):
    """What `sp` is permitted to do to a file. Values match the catalog's `policy` field."""

    GENERATED = "generated"
    """sp owns the content. Restored when missing or when it has diverged (D10)."""

    CREATE_ONCE = "create-once"
    """sp writes it when absent and never touches it again."""

    USER_OWNED = "user-owned"
    """sp never writes it."""


class Scope(enum.Enum):
    PROJECT = "project"
    SP_HOME = "sp-home"


class Source(enum.Enum):
    TEMPLATE = "template"
    """A file shipped under `llmflow/templates/`."""

    CONSTANT = "constant"
    """A string constant in `cli_utils`."""

    SP_HOME = "sp-home"
    """Copied out of `~/.sp/` — the project skills of D1-A′."""

    NONE = "none"
    """sp writes no content; the entry exists so the path is not lost sight of."""


@dataclass(frozen=True)
class Entry:
    """One managed path.

    `path` is relative to the entry's scope root — the project directory for
    `Scope.PROJECT`, `~/.sp` for `Scope.SP_HOME`.
    """

    path: str
    policy: Policy
    scope: Scope
    source: Source
    committed: bool
    template: Optional[str] = None
    constant: Optional[str] = None
    block: Optional[str] = None
    """Delimiter name when sp owns only a block of the file, not the whole of it.

    `.cursorrules` and `.windsurfrules` are written with `_upsert_delimited_block`, so a
    project may keep its own rules around sp's block. Ownership stops at the delimiters:
    comparing or restoring the whole file would discard the project's content.
    """


def _templates_dir() -> Path:
    import llmflow

    return Path(llmflow.__file__).parent / "templates"


def catalog_path() -> Path:
    """Locate file-catalog.yaml whether running from an installed wheel or a dev checkout.

    Mirrors how `data/models.json` is resolved in `modules/telemetry.py`.
    """
    try:
        ref = importlib.resources.files("llmflow").joinpath("data/file-catalog.yaml")
        path = Path(str(ref))
        if path.exists():
            return path
    except Exception:
        pass
    return Path(__file__).parent.parent.parent / "data" / "file-catalog.yaml"


def _load() -> dict[str, Any]:
    path = catalog_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"file catalog not found at {path}. It declares every file sp init manages; "
            "without it sp cannot tell which files it owns."
        )
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _entry_from(spec: dict[str, Any], path: str, template: Optional[str]) -> Entry:
    return Entry(
        path=path,
        policy=Policy(spec["policy"]),
        scope=Scope(spec["scope"]),
        source=Source(spec["source"]),
        committed=bool(spec["committed"]),
        template=template,
        constant=spec.get("constant"),
        block=spec.get("block"),
    )


def _expand_group(spec: dict[str, Any]) -> list[Entry]:
    """Expand a group against what the package actually ships.

    Groups exist so that adding a template requires no edit to the catalog. A second
    hand-kept list is how three conventions went unshipped for months (#204, #181).
    """
    matches = sorted(_templates_dir().glob(spec["templates"]))
    requires = spec.get("requires")
    if requires:
        matches = [p for p in matches if (p / requires).exists()]

    found: list[Entry] = []
    for match in matches:
        template = str(match.relative_to(_templates_dir()))
        found.append(
            _entry_from(
                spec,
                path=spec["path"].format(name=match.name),
                template=template if spec["source"] == Source.TEMPLATE.value else None,
            )
        )
    return found


def entries() -> tuple[Entry, ...]:
    """Every path `sp init` writes or places, with its ownership policy."""
    data = _load()
    found: list[Entry] = []

    for group in data.get("groups", []):
        found.extend(_expand_group(group))

    for spec in data.get("files", []):
        found.append(_entry_from(spec, path=spec["path"], template=spec.get("template")))

    return tuple(found)


def managed_by_doctor() -> tuple[Entry, ...]:
    """Entries `sp doctor` restores when they are missing or have diverged (D10).

    Everything else — `project.md`, `CLAUDE.md`, anything under `user-context/` — is
    outside sp's ownership and is never written by a repair pass.
    """
    return tuple(e for e in entries() if e.policy is Policy.GENERATED)


def project_gitignore_lines() -> list[str]:
    """The ignore list, derived from the catalog (D9).

    Every project-scoped entry that is not committed becomes a line. Nothing that *is*
    committed can appear, which is what stops a generated `.gitignore` from hiding
    `.claude/skills/` — the mistake that leaves a clone with no slash commands.
    """
    lines: list[str] = []
    for entry in entries():
        if entry.scope is not Scope.PROJECT or entry.committed:
            continue
        if entry.path not in lines:
            lines.append(entry.path)
    return lines


def shipped_path(entry: Entry) -> Optional[Path]:
    """The packaged file or directory backing `entry`, if it has one.

    Skills are directories — the whole tree is the unit, not a single file — so this is
    the resolver that works for both.
    """
    if entry.source is Source.TEMPLATE and entry.template:
        path = _templates_dir() / entry.template
        return path if path.exists() else None
    return None


def shipped_content(entry: Entry) -> Optional[str]:
    """The text `entry` should hold, or None when it is not a single-file entry.

    Returns None for directory entries (skills) and for entries whose content sp does
    not own. Callers comparing content must handle directories separately.
    """
    if entry.source is Source.TEMPLATE:
        path = shipped_path(entry)
        if path is not None and path.is_file():
            return path.read_text(encoding="utf-8")
        return None
    if entry.source is Source.CONSTANT and entry.constant:
        from llmflow import cli_utils

        return getattr(cli_utils, entry.constant, None)
    return None
