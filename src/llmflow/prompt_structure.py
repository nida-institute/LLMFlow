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
    "Finding",
    "Position",
    "binds",
    "check",
    "conditions",
    "declaration_path",
    "declares_a_header",
    "positions",
    "refused",
    "render_markdown",
    "render_sequence",
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


def binds() -> str:
    """Which prompts the grammar binds, in the declaration's own words."""
    return str(_load().get("binds") or "").strip()


@dataclass(frozen=True)
class Finding:
    """One thing wrong with a prompt: where it is, and what to write instead.

    A finding is one line, and `check` returns only the first one, so a prompt broken in several
    ways costs its reader one line rather than a cascade.
    """

    line: int
    message: str


def declares_a_header(text: str) -> bool:
    """Whether *text* opens with a header fence, which is what the grammar binds.

    The **first line**, not a fence anywhere. An unanchored match reads a markdown horizontal
    rule as frontmatter — `prompts/sikkemese/typology-checking.gpt` has one — and an unanchored
    HTML-comment form reads an ordinary body comment as a header, which three prompts in a
    consumer repository carry. Both are silent false positives that would hold an unbound prompt
    to the grammar.

    Presence is all the binding rule needs; parsing a header stays `linter.parse_prompt_header`'s
    job, and a test holds the two to the same answer on every prompt this repository ships.
    """
    first, _, _ = text.partition("\n")
    return first.strip() == "---"


def _top_level_headings(text: str) -> list[tuple[int, str]]:
    return [(number, line.strip()) for number, line in enumerate(text.splitlines(), start=1) if line.startswith("# ")]


def _heading_positions() -> dict[str, Position]:
    return {heading: position for position in positions() for heading in position.headings}


def check(text: str) -> Optional[Finding]:
    """The first way *text* departs from the grammar, or None where it conforms.

    Returns None for a prompt the grammar does not bind — see `binds()`. Only what the grammar
    can decide is checked: a heading's name, the order, a required section's absence, and a task
    section's subsections. C2 and C4 turn on what a section *means* rather than what it says, so
    nothing here reports them; a warning that cannot be trusted teaches a reader to skip warnings.
    """
    if not declares_a_header(text):
        return None

    headings = _top_level_headings(text)
    admitted = _heading_positions()
    refusals = refused()
    highest = 0
    seen: set[str] = set()

    in_reference = False
    for number, heading in headings:
        if heading in refusals:
            return Finding(number, f"{heading!r} is not in the grammar — {refusals[heading]}")
        position = admitted.get(heading)
        if position is None:
            # Past the extension point an unrecognised heading is extension content, not a task.
            # Before it, C5 makes it a task section. Reading extension material as a task is what
            # produced the wrong diagnosis this position exists to end: "missing four subsections"
            # about a table of labels.
            if in_reference:
                continue
            finding = _check_task_section(text, number, heading)
            if finding is not None:
                return finding
            continue
        if position.id == "reference":
            in_reference = True
        if position.n < highest:
            return Finding(
                number,
                f"{heading!r} is position {position.n} and follows position {highest}; the order is fixed",
            )
        highest = max(highest, position.n)
        seen.add(position.id)

    for position in positions():
        if not position.required or not position.headings or position.id in seen:
            continue
        wanted = " or ".join(repr(h) for h in position.headings)
        return Finding(
            len(text.splitlines()),
            f"{wanted} is required at position {position.n} and is absent",
        )
    return None


def _check_task_section(text: str, start: int, heading: str) -> Optional[Finding]:
    """A heading matching no other production is a task section (C5), and carries all four.

    The subsections are read from the declaration, so adding or renaming one needs no change
    here.
    """
    lines = text.splitlines()
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("# "):
            break
        body.append(line)
    for subsection in task_subsections():
        if not any(line.strip() == subsection for line in body):
            return Finding(
                start,
                f"task section {heading!r} does not carry "
                f"{subsection.lstrip('#').strip()!r}, which every task section requires",
            )
    return None


def render_sequence() -> str:
    """The required order, for a terminal.

    Printed once per lint run at the first finding, so a reader who has just been told their
    prompt is wrong can see what right looks like without opening a document.
    """
    lines = ["The required order:"]
    for position in positions():
        if position.headings:
            heading = " | ".join(position.headings)
        elif position.id == "frontmatter":
            heading = "YAML frontmatter"
        else:
            heading = "one or more task sections"
        obligation = "" if position.required else f"  (conditional — {position.condition})"
        lines.append(f"  {position.n:>2}. {position.id:<16} {heading}{obligation}")
    lines.append("")
    lines.append("Every task section carries, in this order:")
    lines += [f"      {subsection}" for subsection in task_subsections()]
    return "\n".join(lines)


def render_markdown() -> str:
    """The block every shipped document carries verbatim.

    Rendered rather than written out, so a document cannot disagree with the declaration.
    """
    lines = [
        "<!-- Rendered from data/prompt-structure.yaml. Do not hand-edit: the declaration is",
        "     the order, and an edit here is lost the next time it is rendered. -->",
        "",
        "**What the grammar binds.** " + " ".join(binds().split()),
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
