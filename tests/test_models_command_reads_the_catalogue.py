"""`sp models` reports the model data this project maintains, not a list beside it.

The failure: `data/models.json` was updated to a current roster — `gpt-5`, `claude-4-*`,
`gemini-2.5-*` — while `sp models` printed a literal dict in `setup_command.py` whose newest
entry was `gpt-4o`. The two had drifted so far they barely overlapped: the printed list offered
`o3` and `gemini-2.0-flash`, which the data file does not contain, and never mentioned any model
from the current generation, which it does.

Nobody is at fault twice over here — the list lives in a *setup* module, so a person updating
model data has no reason to look at it. That is the shape this project has hit repeatedly, and
the CHANGELOG already records it: "a second hardcoded list is how three disciplines went
unshipped for months". `test_catalog.py::test_disciplines_derive_from_shipped_templates` is the
same guard for a different list.

The provider keys had drifted too — the code said `gemini` where the data says `google`, so that
whole provider would silently print nothing the moment the display was derived rather than typed.

What this cannot check is whether the data file itself is current; that is what
`sp models --update` and the age warning are for. It checks only that there is one list.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _catalogue() -> dict:
    return json.loads((REPO_ROOT / "data" / "models.json").read_text(encoding="utf-8"))["models"]


def test_every_displayed_model_is_in_the_catalogue():
    from llmflow.setup_command import provider_models

    known = set(_catalogue())
    shown = {name for names in provider_models().values() for name in names}

    assert shown, "no models displayed at all"
    assert shown <= known, f"displayed but absent from data/models.json: {sorted(shown - known)}"


def test_every_provider_in_the_catalogue_is_displayed():
    """A `catalog` name that does not match the data prints an empty section and says nothing.

    `key` and `catalog` differ on purpose — the `llm` keystore calls Google's provider `gemini`
    and `data/models.json` calls it `google` — so this checks the one that addresses the data.
    """
    from llmflow.setup_command import PROVIDERS, provider_models

    in_data = {entry.get("provider") for entry in _catalogue().values()}
    roster = provider_models()
    displayed = {
        p.get("catalog", p["key"]) for p in PROVIDERS if roster.get(p.get("catalog", p["key"]))
    }

    assert in_data <= displayed, (
        f"providers in the data that `sp models` shows nothing for: {sorted(in_data - displayed)}"
    )


def test_the_current_generation_is_reachable():
    """The concrete regression: a reader picking from this list got a two-generation-old model."""
    from llmflow.setup_command import provider_models

    shown = {name for names in provider_models().values() for name in names}
    catalogued = set(_catalogue())

    for recent in ("gpt-5", "claude-4-sonnet", "gemini-2.5-pro"):
        if recent in catalogued:
            assert recent in shown, f"{recent} is in data/models.json but `sp models` hides it"


def test_no_model_is_listed_twice():
    from llmflow.setup_command import provider_models

    flat = [name for names in provider_models().values() for name in names]
    assert len(flat) == len(set(flat)), "a model appears under more than one provider"


# ---------------------------------------------------------------------------
# The retired command name, wherever a user can read it
# ---------------------------------------------------------------------------

SUBCOMMANDS = (
    "setup", "init", "run", "lint", "doctor", "models", "resource", "dataset", "clean", "tools",
)

SOURCES = sorted((REPO_ROOT / "src" / "llmflow").rglob("*.py"))


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.name)
def test_nothing_tells_a_user_to_run_a_command_that_does_not_exist(path: Path):
    """The binary is `sp`. `llmflow setup` is not a command and never was on this CLI.

    `sp models` printed "(no key — run `llmflow setup`)" to anyone without a Gemini key, and the
    setup banner announced itself the same way. A reader who follows that gets
    `command not found`, and has no way to know the instruction was simply stale.
    """
    offences = [
        f"{path.relative_to(REPO_ROOT)}:{number}: {line.strip()[:100]}"
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        for verb in SUBCOMMANDS
        if f"llmflow {verb}" in line
    ]
    assert not offences, (
        "the CLI is `sp`; these name a command that does not exist:\n  " + "\n  ".join(offences)
    )
