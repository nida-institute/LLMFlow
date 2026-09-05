"""Read a role map and check what the engine can check without knowing whose data it is.

A role map sits beside a schema and declares which of its fields are `evidence` — copied from the
input so the model attends to it before deciding — and which are `content`, the thing the pipeline
exists to produce. `supports` states which evidence backs which claim, and `identifies` names the
field an array is keyed by.

Two checks, and the useful thing about both is that they need no run:

1. **the order rule** — a supporting path must precede the path it supports in schema property
   order, because that is the order the model generates in. A copy written *after* the claim it is
   meant to force cannot force anything.
2. **structural validity** — every declared path exists in the schema, and no path is declared
   twice.

Both report. Neither judges: severity belongs to the pipeline, which knows what a failure costs.
Occupancy, legitimate emptiness and audience are all absent by ruling, each needing a judgment
about somebody else's data.

`sp` defines two role words and does not reject a third. A project may declare a role of its own —
a field consumed by a later step and seen by no reader, say — and these checks do not touch it.

Design: `project/plans/design-declaring-field-roles.md`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

#: The two the engine defines. A map may use others; nothing here refuses them.
ROLES = ("evidence", "content")

#: `a[]` — one array step of a path. `a[].b` is `properties.a.items.properties.b`.
ARRAY_STEP = re.compile(r"^(?P<name>[^\[\]]+)\[\]$")

#: An indented key, for finding a path declared twice. YAML keeps the last of two identical keys
#: silently, so duplicates are found in the text rather than in the parse.
BLOCK_KEY = re.compile(r"^(?P<indent> +)(?P<key>[^\s:#][^:]*?):(?:\s|$)")

#: An unindented key — `fields:`, `supports:` — which bounds the blocks above.
TOP_KEY = re.compile(r"^(?P<key>[^\s:#][^:]*?):(?:\s|$)")


@dataclass(frozen=True)
class RoleMap:
    """One schema's declaration: what each field is for, and what supports what."""

    schema: str
    fields: Mapping[str, tuple] = field(default_factory=dict)
    supports: Mapping[str, tuple] = field(default_factory=dict)
    identifies: Mapping[str, str] = field(default_factory=dict)
    #: Paths that appear more than once in a block, in declaration order.
    duplicates: tuple = ()
    #: Fields whose roles were written as a scalar rather than a list.
    scalar_roles: tuple = ()


def _duplicate_keys(text: str) -> tuple:
    """Keys repeated within one block, which the parser would silently collapse to the last.

    Grouped by the enclosing top-level section as well as by indentation: the same path may
    legitimately appear once under `fields` and once under `supports`, which is the common case
    — a field with a role that also names what supports it.
    """
    seen: dict[tuple, set] = {}
    repeated: list[str] = []
    section = ""

    for line in text.splitlines():
        top = TOP_KEY.match(line)
        if top:
            section = top.group("key").strip()
            continue
        match = BLOCK_KEY.match(line)
        if not match:
            continue
        key = match.group("key").strip().strip("\"'")
        block = seen.setdefault((section, len(match.group("indent"))), set())
        if key in block and key not in repeated:
            repeated.append(key)
        block.add(key)

    return tuple(repeated)


def load_role_map(path: Any) -> RoleMap:
    """Read a `.roles.yaml`, refusing the one YAML trap this syntax walks into.

    A path used as a *value* has to be quoted: inside a flow sequence the `[` of `[]` opens a
    nested sequence, so `a[].v: [a[].s]` fails. As a key it is fine, because YAML reads a plain
    scalar up to the colon. The parser's own message is about flow sequences and says nothing
    about what to do, so this one is caught and rewritten.
    """
    import yaml

    text = Path(path).read_text(encoding="utf-8")
    try:
        loaded = yaml.safe_load(text) or {}
    except yaml.YAMLError as error:
        if "flow sequence" in str(error):
            raise ValueError(
                f"{path}: quote paths used as values — `a[].v: [\"a[].s\"]`, or write the list in "
                f"block style. Unquoted, the `[` of `[]` opens a nested flow sequence. As a key a "
                f"path needs no quotes.\n  {error}"
            ) from error
        raise ValueError(f"{path}: {error}") from error

    if not isinstance(loaded, Mapping):
        raise ValueError(f"{path}: a role map is a mapping, not {type(loaded).__name__}.")

    scalar_roles = tuple(
        name
        for name, roles in (loaded.get("fields") or {}).items()
        if not isinstance(roles, (list, tuple))
    )

    return RoleMap(
        schema=str(loaded.get("schema") or ""),
        fields={
            name: tuple(roles) if isinstance(roles, (list, tuple)) else (roles,)
            for name, roles in (loaded.get("fields") or {}).items()
        },
        supports={
            name: tuple(paths) if isinstance(paths, (list, tuple)) else (paths,)
            for name, paths in (loaded.get("supports") or {}).items()
        },
        identifies=dict(loaded.get("identifies") or {}),
        duplicates=_duplicate_keys(text),
        scalar_roles=scalar_roles,
    )


def _properties(node: Any) -> Mapping[str, Any]:
    return node.get("properties") or {} if isinstance(node, Mapping) else {}


def resolve_path(path: str, schema: Mapping[str, Any]) -> Optional[list]:
    """Each segment's position among its siblings, or None where the path is not in *schema*.

    `a[].b` walks `properties.a`, then `items`, then `properties.b`. The positions are what the
    order rule compares: a JSON object's property order is its declaration order, which is the
    order a model generates in.
    """
    node: Any = schema
    positions: list[int] = []

    for segment in path.split("."):
        array = ARRAY_STEP.match(segment)
        name = array.group("name") if array else segment
        siblings = _properties(node)
        if name not in siblings:
            return None
        positions.append(list(siblings).index(name))
        node = siblings[name]
        if array:
            node = node.get("items") if isinstance(node, Mapping) else None
            if not isinstance(node, Mapping):
                return None

    return positions


def validate_structure(roles: RoleMap, schema: Mapping[str, Any]) -> list:
    """Findings about the declaration itself, in reading order. Empty when it is sound.

    A `supports` path must exist in the **schema**, not in `fields` — deliberately. What the
    engine needs to know about a field it orders is its position, not what to call it.
    """
    findings: list[str] = []

    for name in roles.duplicates:
        findings.append(f"`{name}` is declared twice; YAML keeps only the last of the two.")

    for name in roles.scalar_roles:
        findings.append(
            f"`{name}` gives its roles as a scalar; write a list, since a field can hold more "
            f"than one role."
        )

    for group, paths in (("fields", roles.fields), ("supports", roles.supports)):
        for path in paths:
            if resolve_path(path, schema) is None:
                findings.append(f"`{path}` in `{group}` is not a path in the schema.")

    for supported, supporting in roles.supports.items():
        for path in supporting:
            if resolve_path(path, schema) is None:
                findings.append(
                    f"`{path}`, declared as supporting `{supported}`, is not a path in the schema."
                )

    for path in roles.identifies:
        if resolve_path(path, schema) is None:
            findings.append(f"`{path}` in `identifies` is not a path in the schema.")

    return findings


def check_order(roles: RoleMap, schema: Mapping[str, Any]) -> list:
    """Findings where evidence is generated after the claim it supports. Empty when order holds.

    Two paths are compared at the first segment where they diverge, because that is the point at
    which the model writes one before the other. `a[].signal` before `a[].verdict` is compared
    inside the item; `a` before `is_boundary` is compared at the top.
    """
    findings: list[str] = []

    for supported, supporting_paths in roles.supports.items():
        supported_at = resolve_path(supported, schema)
        if supported_at is None:
            findings.append(
                f"`{supported}` in `supports` is not a path in the schema, so its order cannot "
                f"be checked."
            )
            continue

        for path in supporting_paths:
            supporting_at = resolve_path(path, schema)
            if supporting_at is None:
                findings.append(
                    f"`{path}`, declared as supporting `{supported}`, is not a path in the "
                    f"schema, so its order cannot be checked."
                )
                continue

            if not _precedes(supporting_at, supported_at):
                findings.append(
                    f"`{path}` is generated after `{supported}`, which it is declared to "
                    f"support. A model writes properties in schema order, so evidence that "
                    f"follows its claim cannot have forced it — move it earlier in the schema."
                )

    return findings


def _precedes(supporting: Sequence[int], supported: Sequence[int]) -> bool:
    """Whether *supporting* is generated before *supported*, comparing where they diverge.

    Equal prefixes mean the two sit in the same object, so the next position decides. Where one
    path is a prefix of the other — an array and a field inside it — the container is generated
    first by definition, and that counts as preceding.
    """
    for a, b in zip(supporting, supported):
        if a != b:
            return a < b
    return len(supporting) <= len(supported)
