"""The established order for a transformation prompt's sections, read from its declaration.

`data/prompt-structure.yaml` is the order. This module reads it and renders the one block
that every shipped document carries, so no document restates the order in prose of its own.

The declaration's own comments carry why it is data; `CHANGELOG.md` and
`project/plans/design-one-prompt-order.md` carry the reasoning and the ruling.
"""

from __future__ import annotations

import importlib.resources
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

__all__ = [
    "Position",
    "conditions",
    "declaration_path",
    "positions",
    "refused",
    "render_markdown",
    "task_subsections",
]


@dataclass(frozen=True)
class Position:
    """One position in the order.

    `headings` is empty where the position is not a heading: frontmatter, and the task band,
    whose headings are whatever matches no other production (C5).
    """

    n: int
    id: str
    headings: tuple[str, ...]
    required: bool
    condition: Optional[str]


def declaration_path() -> Path:
    """Locate prompt-structure.yaml from an installed wheel or a dev checkout.

    Mirrors `file_catalog.catalog_path()`.
    """
    try:
        ref = importlib.resources.files("llmflow").joinpath("data/prompt-structure.yaml")
        path = Path(str(ref))
        if path.exists():
            return path
    except Exception:
        pass
    return Path(__file__).parent.parent.parent / "data" / "prompt-structure.yaml"


def _load() -> dict[str, Any]:
    path = declaration_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"prompt structure declaration not found at {path}. It states the section order "
            "every transformation prompt follows; without it nothing can check one."
        )
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def positions() -> tuple[Position, ...]:
    """Every position, in order."""
    return tuple(
        Position(
            n=int(spec["n"]),
            id=str(spec["id"]),
            headings=tuple(str(h) for h in spec.get("headings") or ()),
            required=bool(spec.get("required")),
            condition=spec.get("condition"),
        )
        for spec in _load().get("positions", [])
    )


def task_subsections() -> tuple[str, ...]:
    """The four subsections required in every task section."""
    return tuple(str(s) for s in _load().get("task_subsections", []))


def conditions() -> dict[str, str]:
    """C1-C5 — what the grammar cannot express, each checkable."""
    return {str(k): str(v) for k, v in (_load().get("conditions") or {}).items()}


def refused() -> dict[str, str]:
    """Headings the grammar does not admit, each with what to write instead."""
    return {str(k): str(v) for k, v in (_load().get("refused") or {}).items()}


def render_markdown() -> str:
    """The block every shipped document carries verbatim.

    Rendered rather than written out, so a document cannot disagree with the declaration.
    """
    lines = [
        "<!-- Rendered from data/prompt-structure.yaml. Do not hand-edit: the declaration is",
        "     the order, and an edit here is lost the next time it is rendered. -->",
        "",
        "| # | section | heading | required |",
        "| --- | --- | --- | --- |",
    ]
    for position in positions():
        if position.headings:
            heading = " or ".join(f"`{h}`" for h in position.headings)
        elif position.id == "frontmatter":
            heading = "_YAML frontmatter_"
        else:
            heading = "_one or more task sections — C5_"
        obligation = "required" if position.required else f"conditional — {position.condition}"
        lines.append(f"| {position.n} | `{position.id}` | {heading} | {obligation} |")

    lines += [
        "",
        "**Conditional is not discretionary.** A position is omitted only when its side",
        "condition forbids writing it, never because writing it was work.",
        "",
        "Every task section at position 9 carries all four of these, in this order:",
        "",
    ]
    lines += [f"- `{subsection}`" for subsection in task_subsections()]
    lines += ["", "| | side condition |", "| --- | --- |"]
    lines += [f"| {name} | {text} |" for name, text in sorted(conditions().items())]
    lines += [
        "",
        "These headings are refused, with what to write instead:",
        "",
        "| heading | instead |",
        "| --- | --- |",
    ]
    lines += [f"| `{name}` | {text} |" for name, text in sorted(refused().items())]
    return "\n".join(lines) + "\n"
