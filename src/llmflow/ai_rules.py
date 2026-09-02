"""The single source for this project's AI assistant rules.

`data/ai-rules.yaml` holds the rules; nothing else does. Two renderers read this module:

- `llmflow.cli_utils.AI_RULES_DOC` — what `sp init` writes into a new project
- `tools/update_ai_context.py` — this repository's own `docs/ai-context/rules.md`

Before 2026-08-21 each of those held its own hand-written list — 17 rules in the tool, a
different 12 in `cli_utils` — so which rules a project was held to depended on which
generator last ran, and `sp doctor` would replace one set with the other without saying
which text it considered authoritative. The two documents keep their own framing (title,
preamble, generated-by marker); only the rules are shared, because only the rules are the
same thing said twice.

Captain, 2026-08-21: *"why have multiple generators at all? single source of truth …"*
"""

from __future__ import annotations

import importlib.resources
from functools import lru_cache
from pathlib import Path

import yaml

DATA_FILENAME = "ai-rules.yaml"


def rules_path() -> Path:
    """Locate the rules file whether running from an installed wheel or a dev checkout.

    Mirrors `file_catalog.catalog_path()`, which solves the same problem for the file
    catalog. Keeping the two resolutions identical means a packaging change that breaks one
    breaks both visibly, rather than leaving this one silently falling back to a path that
    does not exist in a wheel.
    """
    try:
        ref = importlib.resources.files("llmflow").joinpath(f"data/{DATA_FILENAME}")
        path = Path(str(ref))
        if path.exists():
            return path
    except Exception:
        pass
    return Path(__file__).parent.parent.parent / "data" / DATA_FILENAME


@lru_cache(maxsize=1)
def entries() -> tuple[dict, ...]:
    """Every rule as recorded: `id`, `rule`, and an optional `note`.

    Order is significant for reading — related rules sit together — but it is not an identity.
    `id` is the citation, because collapsing or adding a rule reorders everything after it.
    """
    path = rules_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"AI rules not found at {path}. This file is the only place the project's AI "
            "rules are written; without it neither `sp init` nor this repository's own "
            "context can be generated."
        )
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    found = loaded.get("rules") or ()
    if not found:
        raise ValueError(f"{path} declares no rules")
    return tuple(found)


def rules() -> tuple[str, ...]:
    """Just the instructions, in order."""
    return tuple(entry["rule"] for entry in entries())


#: The `enforcement` value for a rule no test can catch.
JUDGMENT = "judgment"

#: Heading above the rules a test can catch, and above those it cannot.
CHECKED_HEADING = "## Rules a test can catch"
JUDGMENT_HEADING = "## Rules no test can catch — these are the ones to carry"

JUDGMENT_PREAMBLE = (
    "A breach of every rule above either fails a test today or could. These cannot be "
    "checked by any test, so they hold only while they are actually in attention — which "
    "makes them the short list worth re-reading, and the only one a reader has to carry."
)


def _rendered(entry: dict) -> list[str]:
    lines = [f"- `{entry['id']}` — {entry['rule']}"]
    note = (entry.get("note") or "").strip()
    if note:
        lines.append(f"  - _{note}_")
    return lines


def render_rules() -> str:
    """The rules as markdown, grouped by whether a test can catch a breach.

    Rules a test can catch come first, then the `judgment` rules under their own heading.
    The split is read from each entry's `enforcement` field, so nothing holds a second list
    of which rules are checkable — a rule gaining a guard moves group by one edit to the
    data.

    Within each group the recorded order is kept: it groups related rules for reading. The
    id leads and no number is emitted, so the only handle a reader can take hold of is the
    stable one.

    A note carries provenance or detail that would otherwise compete with the imperative —
    the versification specification, or why a rule was moved out of a skill. Keeping it
    beneath the sentence rather than inside it is the point: the rule stays an instruction.
    """
    checked, judgment = [], []
    for entry in entries():
        (judgment if entry.get("enforcement") == JUDGMENT else checked).extend(_rendered(entry))

    if not judgment:
        return "\n".join(checked)

    return "\n".join(
        [CHECKED_HEADING, "", *checked, "", JUDGMENT_HEADING, "", JUDGMENT_PREAMBLE, "", *judgment]
    )
