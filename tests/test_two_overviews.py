"""Guardrail: `overview.md` was two different documents sharing one path (#210).

Measured 2026-08-24, before the split:

| written by | opens with | reader |
|---|---|---|
| `cli_utils.AI_OVERVIEW_DOC` (902 chars) | "This repository contains Scripture Pipelines pipelines, prompts, and outputs" | a consumer project |
| `tools/update_ai_context.py` (1,151 chars) | "Scripture Pipelines is a declarative workflow engine…" + Essence, Philosophy | this engine repository |

`data/file-catalog.yaml` can name only one owner per path and named the first, so `sp doctor`
run in this repository would have replaced the engine overview with a project's. That is the
hazard `project/HANDOFF.md` records as "do not run sp doctor from this repository" — not
staleness, but one filename serving two readers.

The Captain, 2026-08-24: *"project facing should be project-overview.md"*, then *"alternatively,\nwe could have directories for sp vs. project context"* and *"take sp space as the template …\nmirror project structure after that"*. The prefix form lasted an hour; the layout is now\n`docs/ai-context/sp/` and `docs/ai-context/project/`, each carrying index, overview and rules.

`rules.md` needed no split: it is single-sourced from `data/ai-rules.yaml`, so both sides render
the same text. `github-workflow.md` is a different defect, covered by the last test here.
"""
from pathlib import Path

from llmflow import file_catalog as fc

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CONTEXT = REPO_ROOT / "docs" / "ai-context" / "sp"

PROJECT_OVERVIEW = "docs/ai-context/project/overview.md"


def _by_path() -> dict[str, fc.Entry]:
    return {e.path: e for e in fc.entries()}


def test_the_ambiguous_path_is_gone_from_the_catalog():
    assert "docs/ai-context/overview.md" not in _by_path(), (
        "docs/ai-context/overview.md still has a catalog row. One path cannot own two "
        f"documents; the project's is {PROJECT_OVERVIEW} and this engine's is sp/overview.md."
    )


def test_the_project_overview_is_catalogued():
    entry = _by_path().get(PROJECT_OVERVIEW)
    assert entry is not None, f"{PROJECT_OVERVIEW} has no catalog row"
    assert entry.purpose, "it is a document a reader chooses, so it needs a purpose for sp-index"


def test_this_repository_has_its_own_overview_under_its_own_name():
    assert (AI_CONTEXT / "overview.md").is_file(), (
        "this repository's engine overview is missing; it was renamed from overview.md"
    )
    assert not (AI_CONTEXT.parent / "overview.md").exists(), (
        "docs/ai-context/overview.md still exists here — the ambiguous name is the bug"
    )


def test_this_repository_does_not_ship_a_project_overview_to_itself():
    """This repo is sp. A document saying 'this repository contains pipelines' is false here."""
    assert not (AI_CONTEXT.parent / "project-overview.md").exists(), (
        "this repository is the engine, not a consumer project; it has no project overview, "
        "for the same reason it has no project.md"
    )


def test_nothing_still_points_at_the_ambiguous_name():
    from llmflow import cli_utils

    offenders = []
    for name in dir(cli_utils):
        if name.isupper() and isinstance(getattr(cli_utils, name, None), str):
            if "ai-context/overview.md" in getattr(cli_utils, name):
                offenders.append(f"cli_utils.{name}")
    # The generator writes `AI_CONTEXT_DIR / "overview.md"`, which is correct now that
    # AI_CONTEXT_DIR is `docs/ai-context/sp` — the directory carries the ownership, so the
    # filename does not need to. What would be wrong is the generator writing into the flat
    # directory again.
    tool = (REPO_ROOT / "tools" / "update_ai_context.py").read_text(encoding="utf-8")
    if 'AI_CONTEXT_DIR = REPO_ROOT / "docs" / "ai-context"\n' in tool:
        offenders.append("tools/update_ai_context.py writes into the flat directory")
    assert not offenders, (
        "these still name the retired `overview.md`:\n     " + "\n     ".join(offenders)
    )


def test_the_authority_rules_are_not_duplicated_into_github_workflow():
    """The other half of #210, and a different defect.

    This repository's `github-workflow.md` carried an "AI GitHub Authority — Hard Boundaries"
    section restating `disciplines/github-authority.md`. That is not two audiences; it is one
    audience with a local copy of a discipline. Measured 2026-08-24: those rules existed in
    four places — the shipped discipline, `~/.sp/user-context/github-authority.md` (a longer
    variant, the Captain's and not sp's), this addendum, and the shipped constant that lacks
    the section. The discipline is authoritative; the copy goes.
    """
    local = (AI_CONTEXT / "github-workflow.md").read_text(encoding="utf-8")
    assert "AI GitHub Authority — Hard Boundaries" not in local, (
        "github-workflow.md restates disciplines/github-authority.md. Point at the discipline "
        "instead of copying it — a copy drifts, and this one already had."
    )
