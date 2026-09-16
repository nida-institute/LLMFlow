"""Guardrail: this engine says "analysis" for a claim made about a text.

"Annotation" described how such a claim is delivered rather than what it is, and a term naming
the representation is a term a reader has to translate. The two words meant one thing until
they were separated; this test keeps them separated, because nothing else will remember.

The word still appears where it belongs to somebody else — a source format's element name, a
third-party dataset's title, a vendored catalog — and in the rule that retires it, which has to
name it. Those are listed below with the reason, and the list is the record of where the
boundary runs.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SCANNED = ("src/llmflow", "data")

#: Built bundles carry the word from libraries nobody here wrote.
EXEMPT_DIRS = ("src/llmflow/gui/static",)

#: `from __future__ import annotations` is Python's own, and says nothing about texts.
FUTURE_IMPORT = "import annotations"

WORD = re.compile(r"[Aa]nnotation")

#: Where the word may still appear — because it is somebody else's, or because the text has to
#: name the term it retires. Each entry says which, since an allowlist without a reason becomes
#: a place to hide a new violation.
ALLOWED = {
    "data/ai-rules.yaml":
        "The rule that retires the word has to name it, and its note records what was renamed.",
    "src/llmflow/utils/discourse.py":
        "Levinsohn's own element and type name. In those files `annotations` means free-text "
        "notes in English, which is a different thing from an analysis. Fixed by the source.",
    "src/llmflow/plugins/xml_entry_to_base_json.py":
        "An output key in the lexicon base-JSON schema, read downstream. Renaming it would "
        "change a published field name.",
    "src/llmflow/utils/bible_data.py":
        "ACAI's own description of itself — a third-party dataset's title.",
    "data/resources.json":
        "Vendored from awesome-biblical-data. An edit here is reverted by the next sync, and "
        "the strings are other people's descriptions of their own datasets.",
}


def offences() -> list[str]:
    found = []
    for directory in SCANNED:
        for path in sorted((REPO_ROOT / directory).rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(REPO_ROOT).as_posix()
            if relative.startswith(EXEMPT_DIRS) or relative in ALLOWED:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if FUTURE_IMPORT in line:
                    continue
                if WORD.search(line):
                    found.append(f"{relative}:{number}: {line.strip()[:100]}")
    return found


def test_the_engine_says_analysis_not_annotation():
    assert not offences(), (
        "This engine says `analysis` for a claim made about a text. If the word belongs to a "
        "source format, a dataset or a vendored file, add the file to ALLOWED with the reason "
        "rather than renaming somebody else's field.\n  " + "\n  ".join(offences())
    )


def test_the_boundary_list_names_only_files_that_exist():
    """An entry for a deleted file is a licence nobody is using and a reason nobody can check."""
    missing = sorted(name for name in ALLOWED if not (REPO_ROOT / name).is_file())
    assert not missing, f"ALLOWED names files that are gone: {missing}"


def test_every_listed_file_still_uses_the_word():
    """A file that has come clean leaves the list, so it cannot go stale the other way."""
    clean = sorted(
        name
        for name in ALLOWED
        if (REPO_ROOT / name).is_file()
        and not any(
            WORD.search(line)
            for line in (REPO_ROOT / name).read_text(encoding="utf-8").splitlines()
            if FUTURE_IMPORT not in line
        )
    )
    assert not clean, f"no longer uses the word — delete from ALLOWED: {clean}"
