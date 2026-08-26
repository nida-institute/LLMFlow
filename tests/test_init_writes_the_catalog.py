"""Guardrail: every project file the catalog declares is one `sp init` actually writes.

`test_catalog_covers_init.py` checks the other direction — every file `sp init` writes must be
catalogued — and was built after `docs/llmflow-language-quickref.md` was written but uncatalogued,
so `sp doctor` could not push a fix out to a consumer repository.

**This is the mirror failure, and it happened on 2026-08-25.** `docs/ai-context/sp/audits-pattern.md`
was catalogued with a `purpose:`, rendered into `sp/index.md`, and repairable by `sp doctor` — and
`sp init` never created it, so no project received it. The existing guard could not see it: it
parses `cli_utils.py` for `<path>.write_text(<CONSTANT>)`, so it can only find documents that
already have a hand-written writer block. A template-sourced document has neither.

The check is behavioural rather than static, because a catalog-driven writer has no per-path
write to parse.

`HOME` is redirected at the process level, which the older init tests do not do — they register
their pytest temp directory in the real `~/.sp/projects/` (#207).
"""
from pathlib import Path

import pytest

from llmflow import file_catalog as fc
from llmflow.cli_utils import init_project


def _expected_paths() -> list[str]:
    """Project files sp is responsible for creating outright.

    Excluded, each because something else owns the write:
      - `block:` entries — `_configure_ai_assistants` upserts a block into a file it does not own
      - `source: sp-home` — `.claude/skills/`, copied by `_install_claude_skills`
      - `source: none` — no content to write (`llmflow.log`, `outputs/`)
    """
    return sorted(
        e.path
        for e in fc.entries()
        if e.scope is fc.Scope.PROJECT
        and not e.block
        and e.source not in (fc.Source.SP_HOME, fc.Source.NONE)
    )


@pytest.fixture
def project(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("SP_HOME", str(home / ".sp"))
    base = tmp_path / "project"
    base.mkdir()
    init_project(base)
    return base


def test_init_writes_every_catalogued_project_file(project):
    missing = [p for p in _expected_paths() if not (project / p).exists()]
    assert not missing, (
        "Catalogued but never written by `sp init`:\n  " + "\n  ".join(missing) + "\n"
        "A file the catalog declares and the writer does not create reaches no project, "
        "however well `sp doctor` could repair it."
    )


def test_written_content_matches_what_the_catalog_ships(project):
    """Written once, from the catalog's own resolver — so a document cannot be created from
    one source and repaired from another."""
    wrong = []
    for e in fc.entries():
        if e.path not in _expected_paths():
            continue
        target = project / e.path
        shipped = fc.shipped_content(e)
        if shipped is None or not target.is_file():
            continue
        if target.read_text(encoding="utf-8") != shipped:
            wrong.append(e.path)
    assert not wrong, (
        "Written content differs from `shipped_content`:\n  " + "\n  ".join(wrong) + "\n"
        "`sp init` and `sp doctor` must agree on what a document contains."
    )


def test_init_writes_nothing_the_catalog_does_not_declare(project):
    """The converse direction, and the reason `test_catalog_covers_init.py` existed.

    That file checked it by parsing `cli_utils.py` for `<path>.write_text(<CONSTANT>)`. The
    catalog-driven writer has no such lines, and its own docstring said it would *"fail loudly
    rather than silently passing"* against exactly this refactor. It also recorded why it was
    static: *"a behavioural alternative (run `sp init` into a temporary tree and diff) is not
    used here because `sp init` also writes to the real `~/.sp` (#207)."* The fixture above
    redirects `HOME`, so that objection is gone and the behavioural check replaces it.

    The original failure this guards against: `docs/llmflow-language-quickref.md` was written
    but uncatalogued, so when `c1647af` fixed a window-cursor example inside it — an example
    that had already cost real content in a consumer repo — `sp doctor` had no way to push the
    fix out.
    """
    catalogued = {e.path for e in fc.entries() if e.scope is fc.Scope.PROJECT}
    catalogued |= {e.path.rstrip("/") for e in fc.entries() if e.scope is fc.Scope.PROJECT}

    #: Written by `sp init` and legitimately absent from the catalog.
    #: `.gitignore` is *derived from* the catalog (D9), so cataloguing it would be circular.
    expected_extra = {".gitignore"}

    found = {
        str(p.relative_to(project))
        for p in project.rglob("*")
        if p.is_file()
    }
    # Skill trees are catalogued by their directory, not file by file.
    found = {p for p in found if not p.startswith(".claude/skills/")}

    uncatalogued = sorted(found - catalogued - expected_extra)
    assert not uncatalogued, (
        "Written by `sp init` but absent from data/file-catalog.yaml:\n  "
        + "\n  ".join(uncatalogued)
        + "\nAn uncatalogued file is invisible to `sp doctor` — it cannot be checked or "
          "restored, and only `sp init --update` will ever refresh it."
    )
