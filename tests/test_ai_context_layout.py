"""Guardrail: every ai-context document is on the side that owns it, and its index names it.

Ruled 2026-08-25, recorded in `project/plans/design-ai-context-layout.md`.

`8d8ac2a` created the two halves — *"everything under `sp/` is regenerated, everything under
`project/` is created once and never touched again"* — and then moved this repository's eleven
context documents into `sp/` wholesale, leaving seven hand-authored files in the directory that
means "regenerated" and no `project/` directory at all.

Three rulings from the Captain hold these tests up:

- **R1** — *"the index file in each needs to reference all the files that are needed, typically
  all files in that directory."*
- **R2**, as revised by **R10** — the split of the seven: `gui-architecture.md`,
  `data-sources.md`, `paratext-schemas.md` and `data-shapes.md` are the project's. Of the rest
  only `audits-pattern.md` survives on the sp side: `json-reliability.md` is deleted (R10, its
  content already in `docs/llmflow-language.md`) and `README.md` is folded into `sp/overview.md`
  (Q2, *"Fold it in"*).
- **R3** — *"we cannot know what files a project might want in advance."* The project half is
  authored, so no file under `project/` may be `policy: generated`.

The sp half is checked against the catalog rather than against a list here: a second list in a
test is the same defect as a second list in `tools/update_ai_context.py`, which R4 rejects.
"""
from pathlib import Path

from llmflow import file_catalog as fc

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CONTEXT = REPO_ROOT / "docs" / "ai-context"
SP_DIR = AI_CONTEXT / "sp"
PROJECT_DIR = AI_CONTEXT / "project"

#: R2, the Captain's ruling. Named here because a *placement* ruling has nowhere else to live —
#: the catalog records what sp ships, not which half a project's own documents belong to.
PROJECT_HALF = {
    "gui-architecture.md",
    "data-sources.md",
    "paratext-schemas.md",
    "data-shapes.md",
}


def _md_names(directory: Path) -> set[str]:
    return {p.name for p in directory.glob("*.md")} if directory.is_dir() else set()


def _catalogued_under(prefix: str) -> set[str]:
    return {
        e.path.split("/")[-1] for e in fc.entries() if e.path.startswith(prefix)
    }


def test_project_half_directory_exists():
    assert PROJECT_DIR.is_dir(), (
        "docs/ai-context/project/ does not exist. The repository that defines the two-half "
        "layout does not yet live under it."
    )


def test_r2_documents_are_on_the_project_side():
    misplaced = PROJECT_HALF & _md_names(SP_DIR)
    assert not misplaced, (
        f"R2 places these on the project side, but they are still in sp/: {sorted(misplaced)}. "
        "sp/ means regenerated; these are hand-authored project documents."
    )


def test_readme_was_folded_into_sp_overview():
    assert not (SP_DIR / "README.md").exists(), (
        "docs/ai-context/sp/README.md still exists. Q2 ruled 'Fold it in' — its content belongs "
        "in sp/overview.md."
    )


def test_every_file_in_sp_is_catalogued():
    """R1 and R4 together: the sp index is rendered from the catalog, so an uncatalogued file
    in `sp/` can never appear in it."""
    uncatalogued = _md_names(SP_DIR) - _catalogued_under("docs/ai-context/sp/")
    assert not uncatalogued, (
        f"Files in docs/ai-context/sp/ with no catalog entry: {sorted(uncatalogued)}. "
        "sp/index.md is derived from the catalog, so these are unreachable from it."
    )


def test_no_generated_file_on_the_project_side():
    """R3: the project half is authored. `sp` creates it once and does not own the content."""
    generated = [
        e.path
        for e in fc.entries()
        if e.path.startswith("docs/ai-context/project/")
        and e.policy is fc.Policy.GENERATED
    ]
    assert not generated, (
        f"policy: generated on the project side: {generated}. Under R3 the project half is "
        "authored — sp cannot know what a project has."
    )


def test_each_index_references_every_file_beside_it():
    """R1, enforced. The index is the only thing standing between a topic document and
    invisibility: `project.md` went unread for want of a row naming it."""
    failures = []
    for directory in (SP_DIR, PROJECT_DIR):
        index = directory / "index.md"
        if not index.is_dir() and not index.exists():
            failures.append(f"{index.relative_to(REPO_ROOT)} does not exist")
            continue
        text = index.read_text(encoding="utf-8")
        for name in sorted(_md_names(directory) - {"index.md"}):
            if name not in text:
                failures.append(f"{index.relative_to(REPO_ROOT)} does not reference {name}")
    assert not failures, "R1 violations:\n  " + "\n  ".join(failures)


# ---------------------------------------------------------------------------
# The shipped load-context skill (step 5)
#
# #204's acceptance criterion is that a cloned project runs `/load-context` cleanly. Its
# recorded failure was HTTP 400 with no body, traced to a skill reading a file a fresh machine
# cannot have: an unguarded `cat` on a missing path emits an error, and an empty content block
# is the bodyless 400. So every read the skill performs must be guarded.
# ---------------------------------------------------------------------------

SKILL = (
    REPO_ROOT / "src" / "llmflow" / "templates" / "sp" / "skills" / "load-context" / "SKILL.md"
)

#: The standard set (R5), on both halves, plus the pre-split flat names. A project has whichever
#: layout it has, so the skill reads all three spellings of each and skips what is absent.
TRIO = ("index.md", "overview.md", "rules.md")


def test_skill_reads_the_trio_on_both_halves():
    text = SKILL.read_text(encoding="utf-8")
    missing = [
        f"docs/ai-context/{half}/{name}"
        for half in ("sp", "project")
        for name in TRIO
        if f"docs/ai-context/{half}/{name}" not in text
    ]
    assert not missing, (
        f"load-context does not read: {missing}. R5 makes the trio the standard set and the "
        "layout mirrors it, so each half's map, self-description and constraints are all read."
    )


def test_every_read_in_the_skill_is_guarded():
    unguarded = [
        line.strip()
        for line in SKILL.read_text(encoding="utf-8").splitlines()
        if line.startswith("cat ") and "2>/dev/null" not in line
    ]
    assert not unguarded, (
        "Unguarded reads in load-context:\n  " + "\n  ".join(unguarded) + "\n"
        "A missing file must be skipped in silence — an empty content block is #204's "
        "bodyless HTTP 400."
    )


# ---------------------------------------------------------------------------
# What the rendered index says (R7, and step 6)
#
# `design-vocabulary.md` is "Draft, but in force… authoritative for user-facing text", and the
# index is rendered into every project — so the strings below are user-facing, not internal.
# The product is Scripture Pipelines; LLMFlow is deprecated as a product name and survives only
# as the Python import namespace and the repository URL.
# ---------------------------------------------------------------------------


def test_rendered_index_names_no_path_that_does_not_exist():
    """`SP_INDEX_HEADER` pointed readers at `project-index.md` for a day — a filename introduced
    and retired the same evening — so every project's index sent them to nothing."""
    rendered = fc.render_sp_index()
    assert "project-index.md" not in rendered, (
        "The rendered index still names `project-index.md`. The project's map is "
        "`docs/ai-context/project/index.md`."
    )
    assert "sp-index.md" not in rendered, (
        "The rendered index still names `sp-index.md`, also retired by the directory split."
    )


def test_rendered_index_uses_the_authorised_product_name():
    """R7. `engine` is not a ruled term in `design-vocabulary.md`; Scripture Pipelines is."""
    rendered = fc.render_sp_index()
    assert "Engine reference" not in rendered, (
        "The rendered index still carries the heading 'Engine reference, canonical'. R7 names it "
        "'Scripture Pipelines documentation'."
    )
    assert "## Scripture Pipelines documentation" in rendered


def test_index_never_links_a_document_it_also_ships():
    """R11. A project that receives `docs/tutorial.md` as a file does not also need a link to
    the copy on the web — and showing both made one document look like two, nine lines apart
    in the same rendered file. Documents sp does *not* write are the only ones worth linking.
    """
    rendered = fc.render_sp_index()
    shipped = {e.path for e in fc.documents() if e.scope is fc.Scope.PROJECT}
    both = sorted(p for p in shipped if f"/blob/main/{p})" in rendered)
    assert not both, (
        f"The rendered index lists these as files and also links them upstream: {both}. "
        "A reader cannot tell the two apart, and the linked copy is not the one their `sp` "
        "version matches."
    )


def test_no_create_once_file_on_the_sp_side():
    """The mirror of `test_no_generated_file_on_the_project_side`, and the other half of what
    makes ownership structural rather than a convention a filename can misstate.

    `8d8ac2a`: *"everything under `sp/` is regenerated, everything under `project/` is created
    once and never touched again."* A create-once file in `sp/` would be the first exception,
    and the cost is measured — `docs/audits/audit-passage.md` is create-once, and its four
    consumer copies are byte-identical to each other while differing from this repository's by
    53 lines. The constant improved after they were seeded; none of them received it. Correct
    for a project's own criteria, wrong for method (Captain, 2026-08-25: "generated").
    """
    create_once = [
        e.path
        for e in fc.entries()
        if e.path.startswith("docs/ai-context/sp/")
        and e.policy is not fc.Policy.GENERATED
    ]
    assert not create_once, (
        f"Not `policy: generated` on the sp side: {create_once}. sp/ means sp owns the content "
        "and `sp doctor` repairs it; a project's own documents belong in docs/ai-context/project/."
    )
