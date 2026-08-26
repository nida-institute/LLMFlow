"""Guardrail: a docstring says what the code does, and carries no provenance.

Reported by `docstrings-say-what-not-why` in `data/ai-rules.yaml`, which is the rule this
file enforces and the place its reasoning lives.
"""
from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCANNED = ("src/llmflow", "tests", "tools")

#: Shipped documentation, not code.
EXEMPT_DIRS = ("src/llmflow/templates",)

#: Guards that must name the patterns in order to forbid them.
EXEMPT_FILES = (
    "tests/test_docstrings_say_what_not_why.py",
    "tests/test_changelog_is_not_a_transcript.py",
)

FORBIDDEN = {
    "a date": re.compile(r"\b20\d\d-\d\d-\d\d\b"),
    # Hex-alphabet, and mixed — otherwise every long run of digits is a commit.
    "a commit hash": re.compile(
        r"\b(?=[0-9a-f]{7,40}\b)(?=[0-9a-f]{0,39}[0-9])(?=[0-9a-f]{0,39}[a-f])[0-9a-f]{7,40}\b"
    ),
    "a quoted ruling": re.compile(r"\bCaptain\b"),
}

#: The backlog: files written before the rule existed. An entry is a licence to keep
#: existing offences, never to add one — `test_the_backlog_only_shrinks` fails when a
#: listed file comes clean, so the entry must be deleted as part of cleaning the file.
NOT_YET_CLEAN = frozenset({
    "src/llmflow/ai_rules.py",
    "src/llmflow/cli.py",
    "src/llmflow/cli_utils.py",
    "src/llmflow/doctor.py",
    "src/llmflow/file_catalog.py",
    "src/llmflow/gui/executor.py",
    "src/llmflow/gui/server.py",
    "src/llmflow/modules/telemetry.py",
    "src/llmflow/paths.py",
    "src/llmflow/steps/window.py",
    "src/llmflow/tools/replay.py",
    "src/llmflow/utils/context.py",
    "src/llmflow/utils/io.py",
    "src/llmflow/utils/linter.py",
    "tests/conftest.py",
    "tests/test_ai_context_layout.py",
    "tests/test_ai_rules_single_source.py",
    "tests/test_catalog.py",
    "tests/test_commit_ready_gate.py",
    "tests/test_doctor.py",
    "tests/test_doctor_help_is_honest.py",
    "tests/test_global_disciplines.py",
    "tests/test_gui_pipelines_dir_discovery.py",
    "tests/test_helm_sync.py",
    "tests/test_init.py",
    "tests/test_init_is_idempotent.py",
    "tests/test_init_noninteractive.py",
    "tests/test_init_writes_the_catalog.py",
    "tests/test_lazy_plugin_discovery.py",
    "tests/test_plan_docs_index.py",
    "tests/test_portable_skills.py",
    "tests/test_product_name_in_prose.py",
    "tests/test_pytest_writes_inside_the_repository.py",
    "tests/test_schema_covers_runner_keys.py",
    "tests/test_schema_preflight.py",
    "tests/test_scripture_step.py",
    "tests/test_shortname_is_helm.py",
    "tests/test_sp_block_is_first_and_warned.py",
    "tests/test_sp_home_is_relocatable.py",
    "tests/test_template_layout.py",
    "tests/test_two_indexes.py",
    "tests/test_two_overviews.py",
    "tests/test_unresolved_path_guard.py",
    "tests/test_window_cursor_guidance.py",
    "tests/test_window_lint_context.py",
    "tests/test_window_literal_fields.py",
    "tools/sync_helm.py",
    "tools/update_ai_context.py",
})


def scanned_files() -> list[Path]:
    found = []
    for directory in SCANNED:
        for path in sorted((REPO_ROOT / directory).rglob("*.py")):
            relative = path.relative_to(REPO_ROOT).as_posix()
            if relative not in EXEMPT_FILES and not relative.startswith(EXEMPT_DIRS):
                found.append(path)
    return found


def prose_of(path: Path) -> list[tuple[int, str]]:
    """Every docstring and comment in *path*, as (line number, text)."""
    source = path.read_text(encoding="utf-8")
    prose = []

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            text = ast.get_docstring(node, clean=False)
            if text:
                prose.append((getattr(node, "lineno", 1), text))

    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            prose.append((token.start[0], token.string))

    return prose


def offences_in(path: Path) -> list[str]:
    """One line per forbidden span, quoting the span rather than the docstring it sits in."""
    found = []
    for line, text in prose_of(path):
        for kind, pattern in FORBIDDEN.items():
            for match in pattern.finditer(text):
                # The line the span is on, not the line the docstring opens on.
                offset = text.count("\n", 0, match.start())
                context = text.splitlines()[offset].strip()
                found.append(
                    f"{path.relative_to(REPO_ROOT)}:{line + offset}: {kind} "
                    f"({match.group()!r}) — {context[:100]}"
                )
    return found


@pytest.mark.parametrize(
    "path", [p for p in scanned_files() if p.relative_to(REPO_ROOT).as_posix() not in NOT_YET_CLEAN],
    ids=lambda p: p.name,
)
def test_prose_carries_no_provenance(path: Path):
    assert not offences_in(path), (
        "A docstring says what the code does. Dates, hashes, rulings and issue numbers are "
        "provenance: they belong in git history, the issue tracker, project/plans/ and the AI "
        "context, all of which stay current while a docstring does not.\n  "
        + "\n  ".join(offences_in(path))
    )


def test_the_backlog_only_shrinks():
    """A file that has come clean must leave `NOT_YET_CLEAN`, so the list cannot go stale."""
    clean = sorted(
        name for name in NOT_YET_CLEAN
        if (REPO_ROOT / name).is_file() and not offences_in(REPO_ROOT / name)
    )
    assert not clean, "Now clean — delete from NOT_YET_CLEAN:\n  " + "\n  ".join(clean)


def test_the_backlog_names_only_files_that_exist():
    assert not sorted(n for n in NOT_YET_CLEAN if not (REPO_ROOT / n).is_file())
