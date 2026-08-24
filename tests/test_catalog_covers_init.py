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

#: The eight files that used to sit here — the four hello-world examples and the four audit
#: documents — were ruled on 2026-08-24 (Q3-Q6 of
#: `project/plans/plan-init-doctor-unification.md`) and are now catalogued. The list itself is
#: gone rather than left empty: rule `one-design` says the superseded path goes, and an empty
#: allowlist is an invitation to refill it. An uncatalogued file now fails this suite loudly,
#: which is the behaviour the list was suppressing.


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
    assert path in _catalog_paths(), (
        f"`sp init` writes {path} but `data/file-catalog.yaml` does not list it.\n"
        f"   Consequence: `sp doctor` cannot see, check, or restore it — only "
        f"`sp init --update` will ever refresh it.\n"
        f"   Fix: add an entry with the policy the write site actually implements "
        f"(`generated` if there is an `elif update and _is_generated` branch, "
        f"`create-once` if the file is only written when absent)."
    )


def test_the_catalog_names_no_path_sp_init_stopped_writing():
    """The converse guard: a catalogued project path that `sp init` no longer writes.

    Replaces `test_awaiting_list_is_not_stale`, which policed the allowlist that Q3-Q6
    retired. Only project-scoped `constant` entries are checked — those are the ones this
    file's parser can see; templates and `~/.sp` entries are covered by the sync record and
    by `sp doctor`'s own group checks.
    """
    import yaml

    data = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    written = set(_written_paths())
    constant_project_paths = {
        f["path"] for f in data.get("files", [])
        if f.get("scope") == "project" and f.get("source") == "constant"
    }
    # The three assistant files are written by `_upsert_delimited_block`, not by a
    # `<var>_path.write_text(CONSTANT)` call, so this parser cannot see them. Their `block:`
    # field is what identifies them. `.github/copilot-instructions.md` joined them on
    # 2026-08-24 (Q2) and no longer needs naming as a special case.
    block_written = {
        f["path"] for f in data.get("files", []) if f.get("block")
    }
    orphans = constant_project_paths - written - block_written
    assert not orphans, (
        "The catalog claims these project files but `sp init` writes none of them:\n   "
        + "\n   ".join(sorted(orphans))
        + "\n   Either sp stopped writing them — remove the entry — or the write site moved "
        "and this parser can no longer see it."
    )
