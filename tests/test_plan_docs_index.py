"""Guardrail: design and plan documents must declare their status and be indexed.

Why this exists: `project/plans/` holds 25+ documents at different stages — some
authoritative, some implemented-and-historical, some proposed and never built. A reader
(or an LLM) facing an undifferentiated directory cannot tell which is which, and a
document whose issue is never named can be stranded without anyone noticing. That
happened to `design-scripture-editions.md`, which existed only on a local tag while
`project/TODO.md` pointed at it.

Three checks:
  1. Every document declares a parseable status.
  2. Every document names its issue, or is listed in NO_ISSUE_YET below.
  3. `project/plans/README.md` matches what the generator would produce.

Convention: rule `file-organisation` — plans in `project/plans/`, named `design-*.md` or `plan-*.md`.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

# `tools/` is not a package and the generator is deliberately outside the installed
# package, so it is loaded by path rather than imported.
_TOOL = Path(__file__).resolve().parent.parent / "tools" / "update_plans_index.py"
_spec = importlib.util.spec_from_file_location("update_plans_index", _TOOL)
update_plans_index = importlib.util.module_from_spec(_spec)
# Registered before exec: @dataclass resolves its own module via sys.modules.
sys.modules[_spec.name] = update_plans_index
_spec.loader.exec_module(update_plans_index)

PLANS_DIR = update_plans_index.PLANS_DIR
parse_doc = update_plans_index.parse_doc
render_index = update_plans_index.render_index

DOCS = sorted(p for p in PLANS_DIR.glob("*.md") if p.name != "README.md")

#: Documents that predate the issue-linking convention. Entries come off this list as
#: the Captain assigns an issue to each; the list is not a licence to add new ones.
NO_ISSUE_YET = {
    "design-ai-drift-control.md",
    "design-clean-command.md",
    "design-format-keyword-split.md",
    "design-loader-steps.md",
    "design-pipeline-schema.md",
    "design-prompt-mixins.md",
    "design-vocabulary.md",
    "plan-ai-rules-single-source.md",
    "plan-migrate-pipeline-directories.md",
    "plan-scripture-pipelines-articles.md",
    "plan-verse-range-set-ops.md",
    "usfm-support.md",
}

#: Filenames predating rule `file-organisation`'s `design-*` / `plan-*` convention. Renaming a document
#: the Captain wrote is his call, not the suite's, so it is recorded rather than failed.
NAMING_EXCEPTIONS = {"usfm-support.md"}


def test_documents_exist():
    assert DOCS, f"no plan documents found under {PLANS_DIR}"


@pytest.mark.parametrize("path", DOCS, ids=lambda p: p.name)
def test_document_declares_status(path):
    doc = parse_doc(path)
    assert doc.status, (
        f"{path.name} has no parseable status line.\n"
        f"   Add a line beginning '**Status:**' or '## Status:' near the top, saying "
        f"where the document stands — approved, proposed, implemented-historical, or not built."
    )


@pytest.mark.parametrize("path", DOCS, ids=lambda p: p.name)
def test_document_names_its_issue(path):
    doc = parse_doc(path)
    if path.name in NO_ISSUE_YET:
        pytest.skip("predates the issue-linking convention; awaiting an issue assignment")
    assert doc.issues, (
        f"{path.name} names no issue. Reference it as '#NNN' so the document and the "
        f"work it specifies can be found from each other."
    )


@pytest.mark.parametrize("path", DOCS, ids=lambda p: p.name)
def test_document_follows_naming_convention(path):
    if path.name in NAMING_EXCEPTIONS:
        pytest.skip("predates rule `file-organisation`'s naming convention; renaming is the Captain's call")
    assert path.name.startswith(("design-", "plan-")), (
        f"{path.name} does not follow rule `file-organisation` — plans are named 'design-*.md' or 'plan-*.md'."
    )


def test_index_is_current():
    index = PLANS_DIR / "README.md"
    assert index.exists(), (
        "project/plans/README.md is missing. Regenerate it:\n"
        "   hatch run python tools/update_plans_index.py"
    )
    expected = render_index(DOCS)
    actual = index.read_text(encoding="utf-8")
    assert actual == expected, (
        "project/plans/README.md is out of date with the documents in this directory.\n"
        "   Regenerate it: hatch run python tools/update_plans_index.py"
    )
