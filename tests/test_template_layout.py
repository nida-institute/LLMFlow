"""Guardrail: `templates/` holds two roots, each a picture of its destination.

Ruled 2026-08-25, recorded in `project/plans/design-shipping-the-audit-method.md` Q1. The
Captain: *"is it better if our internal directory structure looks more like what we create in a
project directory structure?"* — yes, and *"one pass."*

Before: three flattened prefixes, `sp-disciplines/`, `sp-skills/`, `sp-root/`, each named for a
subdirectory of `~/.sp`. That works only while every template lands in the machine store. Project
templates land in ten different directories and collide on two basenames — `overview.md` and
`rules.md` each belong to both `docs/ai-context/sp/` and `docs/ai-context/project/` — so a flat
scheme would need filename prefixes, which `8d8ac2a` replaced with directories.

After: two roots that mirror where their contents go.

    templates/sp/       -> ~/.sp/
    templates/project/  -> <project>/

The gain is that `templates/project/` reads as "this is what `sp init` creates" without consulting
the catalog, and a template at the wrong path is visible on sight instead of only when a test
fails.
"""
from pathlib import Path

from llmflow import file_catalog as fc

TEMPLATES = Path(fc.__file__).resolve().parent / "templates"

#: The prefixes this layout replaces. Named so the failure message can say what to do.
RETIRED = ("sp-disciplines", "sp-skills", "sp-root")


def test_the_flattened_prefixes_are_gone():
    surviving = [d for d in RETIRED if (TEMPLATES / d).exists()]
    assert not surviving, (
        f"Retired template directories still present: {surviving}. They move under "
        "templates/sp/ — sp-disciplines -> sp/disciplines, sp-skills -> sp/skills, "
        "sp-root/* -> sp/*."
    )


def test_templates_holds_only_destination_roots():
    """Two roots and nothing else. A loose file or a third directory means something landed
    without a declared destination."""
    present = sorted(p.name for p in TEMPLATES.iterdir() if not p.name.startswith("."))
    assert present == ["project", "sp"] or present == ["sp"], (
        f"templates/ contains {present}. It should hold `sp/` (and `project/` once project "
        "templates exist) and nothing else — each a mirror of where its contents go."
    )


def test_the_sp_tree_mirrors_the_machine_store():
    sp = TEMPLATES / "sp"
    assert (sp / "disciplines").is_dir(), "templates/sp/disciplines/ is missing"
    assert (sp / "skills").is_dir(), "templates/sp/skills/ is missing"
    assert (sp / "drift-patterns.md").is_file(), (
        "templates/sp/drift-patterns.md is missing — sp-root held it, and `~/.sp/` is where it "
        "lands, so it belongs at the root of the sp mirror."
    )


def test_every_group_glob_resolves_to_something():
    """A renamed directory with an un-renamed glob ships nothing, silently. The groups expand
    against the filesystem, so an empty expansion is not an error — it is an absence."""
    empty = [
        g["templates"]
        for g in (fc._load().get("groups") or [])
        if not list(TEMPLATES.glob(g["templates"]))
    ]
    assert not empty, f"Group globs matching no files: {empty}"


# ---------------------------------------------------------------------------
# Project-scoped templates (#214)
#
# `templates/project/` mirrors a project's own tree, so a template and the copy in *this*
# repository sit at the same relative path. That is the `data/ai-rules.yaml` pattern — one
# source, a generated copy here like everyone else's — and it is sound only while the copy is
# actually regenerated. `sp doctor` cannot run in this repository yet, so nothing regenerates
# it automatically, and this repository has form: `docs/tutorial.md` drifted from TUTORIAL_DOC
# to say `output/` where the constant says `outputs/`, and stayed that way.
# ---------------------------------------------------------------------------

PROJECT_TEMPLATES = TEMPLATES / "project"


def test_project_templates_mirror_their_destination():
    """The template's path under `templates/project/` is the destination path. Identity, so a
    template filed in the wrong place is visible without consulting the catalog.

    **`block` entries are exempt, and must be.** Such a template holds a block that sp inserts
    into a file it does not own, and one block serves several destinations — the same pointer
    goes into `.cursorrules`, `.windsurfrules` and `.github/copilot-instructions.md`. Mirroring
    would demand three identical files, reintroducing exactly the triplication that naming them
    for the block avoids."""
    wrong = [
        f"{e.template} should be project/{e.path}"
        for e in fc.entries()
        if e.scope is fc.Scope.PROJECT
        and e.source is fc.Source.TEMPLATE
        and not e.block  # a block template is named for its block, not its destination
        and e.template != f"project/{e.path}"
    ]
    assert not wrong, "Project templates not mirroring their destination:\n  " + "\n  ".join(wrong)


def test_this_repository_matches_its_own_templates():
    """A template and this repository's copy of it must be byte-identical.

    Turns "remember to run `sp doctor`" into a red test. Without it the two drift silently and
    the second copy becomes a second source, which is the whole defect the template form exists
    to remove.

    `create-once` entries are excluded, and the exclusion is the point rather than a loophole:
    sp writes such a file if it is absent and never touches it again, so this repository's copy
    is *meant* to have diverged. Its `project/TODO.md` is 247 lines against a 23-line template.
    Comparing those would assert that nobody may use the file sp created for them.
    """
    drifted = []
    for e in fc.entries():
        if e.scope is not fc.Scope.PROJECT or e.source is not fc.Source.TEMPLATE:
            continue
        if e.policy is fc.Policy.CREATE_ONCE:
            continue
        if e.block:
            # sp owns a block of this file, not the file. The copy here legitimately carries
            # the project's own content below the block, so byte-equality is the wrong test —
            # `test_every_sp_block_carries_the_same_warning` covers what is shared.
            continue
        shipped = fc.shipped_content(e)
        local = Path(fc.__file__).resolve().parent.parent.parent / e.path
        if shipped is None or not local.is_file():
            continue
        if local.read_text(encoding="utf-8") != shipped:
            drifted.append(e.path)
    assert not drifted, (
        f"This repository's copy differs from the shipped template: {drifted}. "
        "The template is the source; regenerate the copy rather than editing it."
    )


def test_every_sp_block_carries_the_same_warning():
    """The warning heading every sp-owned block must be one text, not four near-copies.

    It used to be guaranteed by construction — `SP_BLOCK_WARNING + \"\"\"...\"\"\"` in Python. The
    blocks are now templates, so the prose lives in a file an editor can open, and this test
    takes over the guarantee the concatenation used to give for free.
    """
    from llmflow.cli_utils import SP_BLOCK_WARNING, template_text

    blocks = ["project/claude-md-block.md", "project/assistant-rules-pointer.md"]
    for name in blocks:
        text = template_text(name)
        assert text.startswith(SP_BLOCK_WARNING), (
            f"{name} does not open with the shared warning. Every file sp writes into but does "
            f"not own must carry the same notice, or a reader learns the rules from whichever "
            f"copy they happened to open."
        )


def test_the_warning_template_matches_the_constant():
    """`sp-block-warning.md` exists so the warning is editable; it must not drift from the code."""
    from llmflow.cli_utils import SP_BLOCK_WARNING, template_text

    assert template_text("project/sp-block-warning.md") == SP_BLOCK_WARNING
