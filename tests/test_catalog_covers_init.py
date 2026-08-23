"""Guardrail: every file `sp init` writes into a project must appear in the catalog.

Why this exists. `data/file-catalog.yaml` is the single source for two derived things —
the generated `.gitignore` (D9) and `sp doctor`'s ownership boundary (D10). A file that
`sp init` writes but the catalog does not list is therefore invisible to `doctor`: it
cannot be checked or restored, and only `sp init --update` will ever refresh it.

That is not hypothetical. `docs/llmflow-language-quickref.md` was absent from the
catalog, so when `c1647af` fixed the window-cursor example inside `LANGUAGE_QUICKREF_DOC`
— an example that had already cost real content in a consumer repo — `sp doctor` could
not push the fix out. Reported from `nida-institute/discourse-flow`, 2026-08-22.

The check is static: it reads `cli_utils.py` for `<path>.write_text(<CONSTANT>)` and
resolves the path variable. That is brittle against a refactor of how those paths are
built, and deliberately so — it fails loudly rather than silently passing, which is the
failure mode it exists to prevent. A behavioural alternative (run `sp init` into a
temporary tree and diff) is not used here because `sp init` also writes to the real
`~/.sp` (#207).
"""
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_UTILS = REPO_ROOT / "src" / "llmflow" / "cli_utils.py"
CATALOG = REPO_ROOT / "data" / "file-catalog.yaml"

#: How `sp init` builds its directories, from cli_utils.py.
DIRS = {
    "base_dir": "",
    "prompts_dir": "prompts",
    "pipelines_dir": "pipelines",
    "docs_dir": "docs",
    "ai_context_dir": "docs/ai-context",
    "docs_audits_dir": "docs/audits",
    "project_dir": "project",
    "audits_dir": "project/audits",
    "plans_dir": "project/plans",
}

#: Written by `sp init`, not yet in the catalog, awaiting the Captain's ruling on policy.
#: Entries come off this list as he rules; the list is not a licence to add new ones.
AWAITING_CATALOG_RULING = {
    "prompts/hello.gpt",
    "prompts/reply.gpt",
    "pipelines/hello-llmflow.yaml",
    "pipelines/hello.yaml",
    "project/audits/README.md",
    "docs/audits/INDEX.md",
    "docs/audits/audit-passage.md",
    "docs/audits/audit-leadersguide.md",
}


def _written_paths() -> dict[str, str]:
    """Repo-relative path -> the constant `sp init` writes into it."""
    src = CLI_UTILS.read_text(encoding="utf-8")
    assigns = dict(re.findall(r"^\s+(\w+_path)\s*=\s*(\w+_dir)\s*/\s*\"([^\"]+)\"", src, re.M)
                   and [] or [])  # placeholder, replaced below
    assigns = {}
    for var, dirvar, leaf in re.findall(
        r"^\s+(\w+_path)\s*=\s*(\w+_dir)\s*/\s*\"([^\"]+)\"", src, re.M
    ):
        if dirvar in DIRS:
            prefix = DIRS[dirvar]
            assigns[var] = f"{prefix}/{leaf}" if prefix else leaf
    out = {}
    for var, const in re.findall(r"(\w+_path)\.write_text\((\w+)", src):
        if var in assigns:
            out[assigns[var]] = const
    return out


def _catalog_paths() -> set[str]:
    data = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    return {f["path"] for f in data.get("files", [])}


def test_init_writes_something():
    written = _written_paths()
    assert len(written) >= 10, f"only resolved {len(written)} written paths — parser likely broken"


@pytest.mark.parametrize("path", sorted(_written_paths()), ids=lambda p: p)
def test_written_file_is_in_the_catalog(path):
    if path in AWAITING_CATALOG_RULING:
        pytest.skip("written by sp init; catalog policy awaiting the Captain's ruling")
    assert path in _catalog_paths(), (
        f"`sp init` writes {path} but `data/file-catalog.yaml` does not list it.\n"
        f"   Consequence: `sp doctor` cannot see, check, or restore it — only "
        f"`sp init --update` will ever refresh it.\n"
        f"   Fix: add an entry with the policy the write site actually implements "
        f"(`generated` if there is an `elif update and _is_generated` branch, "
        f"`create-once` if the file is only written when absent)."
    )


def test_awaiting_list_is_not_stale():
    """Anything on the awaiting list must still be written by `sp init`."""
    written = set(_written_paths())
    stale = AWAITING_CATALOG_RULING - written
    assert not stale, f"AWAITING_CATALOG_RULING names paths sp init no longer writes: {sorted(stale)}"
