#!/usr/bin/env python3
"""Refresh docs/ai-context helper files for AI collaborators."""
from __future__ import annotations

import datetime as _dt
import re
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

REPO_ROOT = Path(__file__).resolve().parents[1]
AI_CONTEXT_DIR = REPO_ROOT / "docs" / "ai-context"
INDEX_PATH = AI_CONTEXT_DIR / "index.md"
OVERVIEW_PATH = AI_CONTEXT_DIR / "overview.md"
RULES_PATH = AI_CONTEXT_DIR / "rules.md"

INDEX_ENTRIES = (
    ("Installation & binaries", "INSTALL.md", "../../INSTALL.md", "Standalone executables, Gatekeeper/SmartScreen steps"),
    ("Quickstart walkthrough", "docs/tutorial.md", "../tutorial.md", "`llmflow init`, greeting pipeline, multi-step example"),
    ("Engine setup & CLI basics", "docs/getting-started.md", "../getting-started.md", "Env vars, linting, resource repo pattern"),
    ("YAML grammar & step types", "docs/llmflow-language.md", "../llmflow-language.md", "`llm` / `function` / `for-each`, variables, `append_to`"),
    ("Architecture & modules", "docs/architecture.md", "../architecture.md", "CLI, runner, linter, telemetry, plugin hooks"),
    ("Philosophy & comparisons", "docs/why-llmflow.md", "../why-llmflow.md", "When/why to use LLMFlow vs other frameworks"),
    ("AI persona & tone", "docs/ai-context/rules.md", "rules.md", "Guardrails for assistant responses"),
    ("Moderation handling", "docs/moderation-handling.md", "../moderation-handling.md", "OpenAI Responses blocks, Bible-text mitigation checklist"),
)

FOUNDATIONAL_DOCS = (
    ("INSTALL.md", "../../INSTALL.md", "how to install the prebuilt CLI on Windows/macOS/Linux."),
    ("docs/tutorial.md", "../tutorial.md", "quickstart using `llmflow init` and a two-step greeting pipeline."),
    ("docs/getting-started.md", "../getting-started.md", "engine + resource-repo workflow, env vars, linting."),
    ("docs/llmflow-language.md", "../llmflow-language.md", "YAML grammar, step types, variables, `for-each` semantics."),
    ("docs/architecture.md", "../architecture.md", "module map, runner lifecycle, plugin strategy."),
    ("docs/why-llmflow.md", "../why-llmflow.md", "motivation and comparison to LangChain/Haystack."),
    ("docs/moderation-handling.md", "../moderation-handling.md", "moderation failure diagnostics plus prompt mitigation checklist."),
)

RUNTIME_SNAPSHOT = (
    "Python 3.10+, packaged binaries via Nuitka.",
    "LLM adapters currently route through the `llm` package; future work adds MCP-aware step orchestration.",
    "Telemetry must start after config merging (per repo guidelines).",
)

DESIGN_ETHOS = (
    "Deterministic, inspectable flows (lint before run; schema + prompt contracts enforced).",
    "Model/provider agnostic configuration with per-model capability guards.",
    "Humans remain in the loop: generated outputs live in resource repos (often Obsidian vaults) and are manually curated.",
    "Documentation-first: every major behavior is described in `docs/` and mirrored here for AI assistants.",
)

RULES = (
    "**Consult the docs before guessing.** The references listed in `index.md` are authoritative for syntax, architecture, and workflows.",
    "**Respect pipeline schema.** Only use documented keys (`name`, `type`, `prompt`, `inputs`, `outputs`, `llm_options`, etc.). No inventing fields.",
    "**Preserve logging/telemetry conventions.** Always use `Logger()` from `llmflow.modules.logger` and start telemetry only after config merging, per `docs/architecture.md`.",
    "**Keep prompts and templates in sync.** Ensure every `prompt.requires` item appears in the pipeline’s `prompt.inputs`. Cite `docs/llmflow-language.md` when clarifying contracts.",
    "**Model-specific features must be justified.** For example, `response_format` is OpenAI-only (GPT-4o/4.1 families); reference capability tables when advising users.",
    "**Highlight human-in-the-loop expectations.** Remind users that outputs are edited in resource repos/Obsidian vaults; do not hand-wave manual review.",
    "**Tone:** technical clarity with interpretive awareness. Explain *why* a change matters, not just *what* to type.",
    "**When requirements conflict, ask.** Use clarifying questions rather than assuming—especially before large edits.",
    "**Cite files explicitly.** When referencing code/docs, point to `path/file` (and line numbers if known) so humans can verify quickly.",
    "**Stay within policy.** Follow repository security constraints, avoid leaking secrets, and decline harmful requests.",
)

LAST_UPDATED_SOURCES = (
    Path("INSTALL.md"),
    Path("docs/tutorial.md"),
    Path("docs/getting-started.md"),
    Path("docs/llmflow-language.md"),
    Path("docs/architecture.md"),
    Path("docs/why-llmflow.md"),
)

DATE_PATTERN = re.compile(r"_Last updated:\s*(\d{4}-\d{2}-\d{2})_")


def _git_status(paths: tuple[Path, ...]) -> str:
    args = ["status", "--porcelain", "--"] + [str(p) for p in paths]
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return ""
    return proc.stdout.strip()


def _extract_existing_date(path: Path) -> str | None:
    if not path.exists():
        return None
    match = DATE_PATTERN.search(path.read_text(encoding="utf-8"))
    if match:
        return match.group(1)
    return None


def _resolve_last_updated() -> str:
    has_changes = bool(_git_status(LAST_UPDATED_SOURCES))
    if has_changes:
        return _dt.date.today().isoformat()
    existing = _extract_existing_date(OVERVIEW_PATH)
    return existing or _dt.date.today().isoformat()


def _build_index_content() -> str:
    rows = "\n".join(
        f"| {topic} | [{link_text}]({href}) | {notes} |"
        for topic, link_text, href, notes in INDEX_ENTRIES
    )
    header = dedent(
        """\
        <!-- Generated by tools/update_ai_context.py -->
        # Document Index for AI Assistants

        Use this map to decide which reference to consult when answering questions.

        | Topic | Go To | Notes |
        | --- | --- | --- |
        """
    ).strip()
    footer = dedent(
        """\
        When an AI assistant needs more detail, direct it to the appropriate file above instead of paraphrasing from memory. This keeps answers aligned with the single source of truth.
        """
    ).strip()
    return f"{header}\n{rows}\n\n{footer}\n"


def _build_overview_content(last_updated: str) -> str:
    docs_list = "\n".join(
        f"- [{label}]({href}) – {description}"
        for label, href, description in FOUNDATIONAL_DOCS
    )
    runtime = "\n".join(f"- {line}" for line in RUNTIME_SNAPSHOT)
    ethos = "\n".join(f"{idx}. {line}" for idx, line in enumerate(DESIGN_ETHOS, start=1))
    return dedent(
        f"""\
        <!-- Generated by tools/update_ai_context.py -->
        # LLMFlow — Project Overview

        _Last updated: {last_updated}_

        LLMFlow is a declarative workflow engine for LLM-assisted scholarship and publishing. Pipelines are written in YAML, validated with strict prompt contracts, and executed via the `llmflow` CLI (standalone binaries documented in [INSTALL.md](../../INSTALL.md)).

        ## Essence
        - **Purpose:** Compose reproducible reasoning pipelines that mix LLM calls, deterministic functions, and file outputs.
        - **Philosophy:** Pipelines are narratives of thought; we keep them readable, linted, and version-controlled.
        - **Core idea:** A "flow" is an ordered list of steps, each with well-defined inputs/outputs, so humans can inspect every transformation.

        ## Foundational Docs
        {docs_list}

        ## Runtime Snapshot
        {runtime}

        ## Design Ethos
        {ethos}

        Share this overview first with AI collaborators so they understand the project’s mission and canonical references before diving into specifics.
        """
    ).strip() + "\n"


def _build_rules_content() -> str:
    rules_lines = "\n".join(f"{idx}. {text}" for idx, text in enumerate(RULES, start=1))
    return dedent(
        f"""\
        <!-- Generated by tools/update_ai_context.py -->
        # AI Assistant Rules

        These guardrails apply to any language model collaborating on LLMFlow tasks.

        {rules_lines}

        Pin these rules alongside `overview.md` and `index.md` when starting an AI session so expectations are clear from the outset.
        """
    ).strip() + "\n"


def _write_file(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_content = content if content.endswith("\n") else content + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") == new_content:
            return False
    path.write_text(new_content, encoding="utf-8")
    return True


def main() -> None:
    last_updated = _resolve_last_updated()
    updates = []
    if _write_file(INDEX_PATH, _build_index_content()):
        updates.append(str(INDEX_PATH.relative_to(REPO_ROOT)))
    if _write_file(OVERVIEW_PATH, _build_overview_content(last_updated)):
        updates.append(str(OVERVIEW_PATH.relative_to(REPO_ROOT)))
    if _write_file(RULES_PATH, _build_rules_content()):
        updates.append(str(RULES_PATH.relative_to(REPO_ROOT)))

    if updates:
        joined = ", ".join(updates)
        print(f"Updated {joined}")
    else:
        print("AI context files already up to date")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"Error while updating AI context files: {exc}", file=sys.stderr)
        sys.exit(1)
