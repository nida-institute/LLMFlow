"""Guardrail: in prose the product is **Scripture Pipelines**, never LLMFlow.

`project/plans/design-vocabulary.md` is in force and rules three things:

  | Scripture Pipelines | the product / project name — use in prose |
  | llmflow             | the Python package and import namespace *only*. Not a product name |
  | LLMFlow             | **deprecated** as a product name; superseded by Scripture Pipelines |

That ruling existed and was being violated in 43 markdown files, which is what this test now
prevents. It is scoped to prose — `.md` — because the same string is legitimate in four other
roles, and a test that failed on those would be turned off rather than obeyed:

  1. **URLs and repository slugs** — `github.com/nida-institute/LLMFlow`. Real addresses.
  2. **Filesystem paths** — `~/github/nida-institute/LLMFlow`, and `ears-to-hear/LLMFlow`, which
     is a consumer repo's documented project root.
  3. **Identifiers** — `_LLMFlowLoader`, and the `llmflow` import namespace, which
     `design-vocabulary.md` explicitly keeps.
  4. **Quotations** — what a person said keeps its words, per rule `one-design`.

Renaming the repository itself is tracked separately in #209; until that lands, categories 1
and 2 are correct as they stand and this test must tolerate them.
"""
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TERM = "LLMFlow"

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "dist",
             "build", ".ruff_cache", ".mypy_cache", "outputs", "tmp", ".hatch"}

#: Files that keep the deprecated name, each for a stated reason.
EXEMPT = {
    # A record of what shipped in past releases. Rewriting it would make it wrong.
    "CHANGELOG.md",
    # The declaration itself — it has to name the term it deprecates.
    "project/plans/design-vocabulary.md",
    # This test names the term in order to forbid it.
    "tests/test_product_name_in_prose.py",
}

#: A line quoting someone. `*"` is this project's house style for quoting the Captain.
QUOTE_LINE = re.compile(r'^\s*(>|=>)|Captain[,:]|\*"')


def _is_legitimate(line: str, start: int) -> bool:
    """True when this occurrence is a URL, a path, or part of an identifier."""
    before = line[start - 1] if start > 0 else " "
    after = line[start + len(TERM)] if start + len(TERM) < len(line) else " "
    if before in "/-" or after == "/":
        return True
    if after.isalnum() or after == "_":
        return True
    if before.isalnum() or before == "_":
        return True
    return False


def _prose_files() -> list[Path]:
    found = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".md"):
                found.append(Path(dirpath) / name)
    return sorted(found)


def _violations() -> list[str]:
    hits = []
    for path in _prose_files():
        rel = str(path.relative_to(REPO_ROOT))
        if rel in EXEMPT:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if TERM not in line or QUOTE_LINE.search(line):
                continue
            for m in re.finditer(TERM, line):
                if not _is_legitimate(line, m.start()):
                    hits.append(f"{rel}:{n}: {line.strip()[:100]}")
                    break
    return hits


def test_prose_uses_the_ruled_product_name():
    hits = _violations()
    assert not hits, (
        "`design-vocabulary.md` deprecates LLMFlow as a product name; prose says "
        "Scripture Pipelines.\n     " + "\n     ".join(hits) + "\n"
        "   `llmflow` stays as the import namespace, and URLs and paths stay until #209 "
        "renames the repository. If a line is a quotation or a record, add its file to "
        "EXEMPT with the reason rather than rewriting it."
    )


def test_the_generated_context_files_are_covered():
    """`docs/ai-context/` and `CLAUDE.md` are checked by the test above, not exempted.

    They carried 11 occurrences until 2026-08-24 and were swept at the Captain's authorization,
    the four generated files by fixing their sources — `tools/update_ai_context.py` and the
    `cli_utils` constants — and regenerating. A pending-exemption mechanism existed here while
    that work was outstanding; it was deleted once empty, per rule `one-design`.
    """
    checked = {str(p.relative_to(REPO_ROOT)) for p in _prose_files()} - EXEMPT
    assert any(p.startswith("docs/ai-context/") for p in checked)

    # `CLAUDE.md` is gitignored, so it is present in a working tree and absent from a clean
    # checkout. Asserting it exists made this test unpassable in CI; asserting it is not
    # exempted keeps the coverage the test is for.
    if (REPO_ROOT / "CLAUDE.md").exists():
        assert "CLAUDE.md" in checked
    else:
        assert "CLAUDE.md" not in EXEMPT
