"""Guardrail: two indexes, and the sp half is derived rather than authored.

Ruled 2026-08-24 (Q1 of `project/plans/plan-init-doctor-unification.md`). `docs/ai-context/`
used to hold one `index.md` that claimed to be the whole map — *"READ THIS FIRST — maps all
available context"* — with open-ended sections. A consumer repo added its own entry documents
to it, exactly as the file invited, and `sp doctor` overwrote them because the catalog marked
the path `policy: generated`.

The split, in the Captain's words: *"let's use two indexes."*

- **`docs/ai-context/project/index.md`** — `create-once`. The project's map, opened first,
  free to name a HANDOFF, design documents with their warnings, a field reference. sp cannot
  generate it: *"we can't know what files a project has created in advance."*
- **`docs/ai-context/sp/index.md`** — `generated`, and **derived from the catalog** rather
  than held in a constant. Each catalogued document carries a `purpose:`; the index is
  rendered from those. A hand-kept second list is what `file_catalog.py` blames for three
  conventions going unshipped for months, so the index that lists sp's documents is not
  allowed to be one.

The derivable half is derived; the un-derivable half is authored. One file could not be both,
which is the argument for two.
"""
import re
from pathlib import Path

import yaml

from llmflow import file_catalog as fc

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG = REPO_ROOT / "data" / "file-catalog.yaml"

PROJECT_INDEX = "docs/ai-context/project/index.md"
SP_INDEX = "docs/ai-context/sp/index.md"


def _entries_by_path() -> dict[str, fc.Entry]:
    return {e.path: e for e in fc.entries()}


def test_the_old_single_index_is_gone_from_the_catalog():
    assert "docs/ai-context/index.md" not in _entries_by_path(), (
        "docs/ai-context/index.md still has a catalog row. The split replaces it with "
        f"{PROJECT_INDEX} (create-once) and {SP_INDEX} (generated, derived)."
    )


def test_the_project_index_is_the_projects_own():
    entry = _entries_by_path().get(PROJECT_INDEX)
    assert entry is not None, f"{PROJECT_INDEX} has no catalog row"
    assert entry.policy is fc.Policy.CREATE_ONCE, (
        f"{PROJECT_INDEX} must be create-once — sp writes a starter once and never again. "
        "It cannot be generated: only the project knows what files it has."
    )


def test_the_sp_index_is_generated_and_derived():
    entry = _entries_by_path().get(SP_INDEX)
    assert entry is not None, f"{SP_INDEX} has no catalog row"
    assert entry.policy is fc.Policy.GENERATED, f"{SP_INDEX} must be generated — sp owns it"
    assert entry.source is fc.Source.DERIVED, (
        f"{SP_INDEX} must have source: derived. A `constant` would be a second hand-kept "
        "list of sp's own documents, which is the failure file_catalog.py exists to prevent."
    )


def test_the_catalog_carries_purpose_for_its_documents():
    """Semantics, not only shape — rule `design-is-declarative`."""
    documented = fc.documents()
    assert len(documented) >= 6, (
        f"only {len(documented)} catalogue entries carry a `purpose:`; the sp index is "
        "rendered from them, so an empty index means the field was never filled in"
    )
    for entry in documented:
        assert entry.purpose and entry.purpose.strip(), f"{entry.path} has an empty purpose"


def test_the_sp_index_renders_every_documented_entry():
    rendered = fc.render_sp_index()
    for entry in fc.documents():
        assert entry.path in rendered, (
            f"{entry.path} carries a purpose but does not appear in the rendered sp index"
        )
    assert SP_INDEX not in rendered or rendered.count(SP_INDEX) >= 0  # self-listing is fine


def test_nothing_shipped_still_points_at_the_old_index():
    """A pointer to a file that no longer exists sends every reader nowhere."""
    from llmflow import cli_utils

    offenders = []
    for name in dir(cli_utils):
        if not name.isupper():
            continue
        value = getattr(cli_utils, name, None)
        if isinstance(value, str) and "ai-context/index.md" in value:
            offenders.append(f"cli_utils.{name}")

    rules = yaml.safe_load((REPO_ROOT / "data" / "ai-rules.yaml").read_text(encoding="utf-8"))
    for rule in rules.get("rules", []):
        blob = f"{rule.get('rule', '')} {rule.get('note', '')}"
        if re.search(r"(?<!project-)(?<!sp-)(?<!project/)(?<!sp/)\bindex\.md", blob):
            offenders.append(f"ai-rules.yaml:{rule['id']}")

    # The `load-context` skill is exempt, deliberately and with an end condition. It reads all
    # three names because a project created before 2026-08-24 still has the single `index.md`
    # and that is the file to read there — rule `one-design`: "Where an older path must
    # survive, name who depends on it and when it ends." Who depends on it: every project
    # scaffolded before the split. When it ends: when those projects have a `project-index.md`,
    # at which point the third `cat` comes out of the skill and this exemption goes with it.
    # (The layout moved from `project-index.md` to `project/index.md` the same day; the skill
    # reads both new paths plus the pre-split name.)
    skill = REPO_ROOT / "src/llmflow/templates/sp-skills/load-context/SKILL.md"
    if skill.is_file():
        text = skill.read_text(encoding="utf-8")
        assert "pre-split single index" in text, (
            "the skill reads the retired `index.md`; that is allowed only while the line says "
            "who depends on it and when it ends"
        )

    assert not offenders, (
        "These still name the retired `index.md`:\n     " + "\n     ".join(offenders) + "\n"
        "   'Start here' pointers go to project/index.md; references to sp's own reference "
        "map go to sp/index.md. The two are not interchangeable."
    )


def test_this_repository_lives_under_the_design():
    """This repo is sp, so it has an sp index and no project index (it has no project.md)."""
    assert (REPO_ROOT / "docs" / "ai-context" / "sp" / "index.md").is_file(), (
        "this repository's own docs/ai-context/sp/index.md is missing — shipping the design "
        "without living under it is how the two-audiences bug happened in the first place"
    )
    assert not (REPO_ROOT / "docs" / "ai-context" / "index.md").exists(), (
        "docs/ai-context/index.md still exists here; it moved to sp/index.md"
    )
