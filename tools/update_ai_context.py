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
    ("Python API — drive the engine in-process", "docs/python-api.md", "../python-api.md", "`import llmflow`: `load_pipeline(...)` then `.resolve()` / `.lint()` / `.run()` / `.schemas()` / `.saveas()`; `call_llm(prompt, config)` for direct model access; `PIPELINE_SCHEMA` + `api_catalog()` are the machine-readable syntax↔API map. Prefer this over re-parsing pipeline YAML or shelling out to `sp` (#175)"),
    ("AI persona & tone", "docs/ai-context/rules.md", "rules.md", "Guardrails for assistant responses"),
    ("Moderation handling", "docs/moderation-handling.md", "../moderation-handling.md", "OpenAI Responses blocks, Bible-text mitigation checklist"),
    ("Versification systems", "Copenhagen Alliance Versification spec", "https://github.com/Copenhagen-Alliance/versification-specification", "Canonical spec for mapping between verse systems (KJV, LXX, Vulgate, etc.); derived from Paratext .vrs files, which are semantically compatible; use for any cross-versification pipeline work"),
)

FOUNDATIONAL_DOCS = (
    ("INSTALL.md", "../../INSTALL.md", "how to install the prebuilt CLI on Windows/macOS/Linux."),
    ("docs/tutorial.md", "../tutorial.md", "quickstart using `llmflow init` and a two-step greeting pipeline."),
    ("docs/getting-started.md", "../getting-started.md", "engine + resource-repo workflow, env vars, linting."),
    ("docs/llmflow-language.md", "../llmflow-language.md", "YAML grammar, step types, variables, `for-each` semantics."),
    ("docs/architecture.md", "../architecture.md", "module map, runner lifecycle, plugin strategy."),
    ("docs/why-llmflow.md", "../why-llmflow.md", "motivation and comparison to LangChain/Haystack."),
    ("docs/python-api.md", "../python-api.md", "the public Python API — `load_pipeline`, the `Pipeline` methods, and `call_llm` for direct model access."),
    ("docs/moderation-handling.md", "../moderation-handling.md", "moderation failure diagnostics plus prompt mitigation checklist."),
)

RUNTIME_SNAPSHOT = (
    "Python 3.10+, packaged binaries via Nuitka.",
    "LLM adapters currently route through the `llm` package; future work adds MCP-aware step orchestration.",
    "Telemetry must start after config merging (per repo guidelines).",
)

# (flag, description)
CLI_FLAGS = (
    ("--pipeline PATH", "Path to the pipeline YAML (required)"),
    ("--var KEY=VALUE", "Set a pipeline variable; repeatable"),
    ("--dry-run", "Parse and validate without making LLM calls"),
    ("--skip-lint", "Skip linting before execution"),
    ("-v / --verbose", "Verbose logging"),
    ("--log PATH", "Write logs to this file (default: `llmflow.log` in cwd)"),
    ("--rewind-to STEP", "Replay checkpointed steps up to and including STEP, then continue"),
    ("--stop-after STEP", "Stop execution after STEP completes"),
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
    "**Project boards use four columns.** All GitHub project boards for this organisation must have exactly these columns in order: Backlog → Todo → Doing → Done. Do not suggest or create boards with different column names or structures.",
    "**Verses are milestones, not units.** In all Scripture pipeline designs, treat verse references as location markers only — never as the basis for structural or semantic decisions. Do not divide scenes, passages, or content blocks by verse count (e.g., 'group into 3-verse units'). Pericope boundaries, scene structure, and semantic cohesion must be determined by narrative/discourse analysis, not by verse numbers. For cross-versification work (mapping between KJV, LXX, Vulgate, etc.) use the Copenhagen Alliance Versification specification (see `index.md` → 'Versification systems'). Paratext `.vrs` files are semantically compatible with the Copenhagen spec (Copenhagen is derived from them) and can be used interchangeably for versification mapping.",
    "**File organisation.** Plans go in `project/plans/` (design-*.md, plan-*.md). Audits go in `project/audits/`. Use `tmp/` only for truly throwaway files (temp scripts, issue drafts before posting to GitHub). Never place design docs or plans in `tmp/` or the repo root.",
    "**Authorization workflow (mandatory).** Before editing any file: (1) state the authorization — GH issue, explicit Captain instruction, or audit finding, quoted exactly; (2) declare scope — every file that will change and what specifically will change in each; (3) list what will NOT change; (4) ask the Captain whether a plan file in `project/plans/`, a GH issue, or neither is needed — always ask, never decide alone; (5) wait for explicit Captain sign-off; (6) before touching implementation files, write the failing test first if the change is testable — if not testable, state explicitly why. Invoke with `/authorize`.",
    "**Plans before implementation.** Non-trivial features or changes require either a plan file in `project/plans/` or a GH issue before any code is written. Either must be reviewed and approved by the Captain. Implementation that begins without an approved plan or issue is unauthorized.",
    "**Audits are diagnostic, not mandatory gates.** Running `/audit-prompts` or `/audit-pipeline` is a tool for understanding what needs to change — it often produces the plan or GH issues that then authorize implementation. Audits are not required before every edit; they are invoked when the Captain wants a systematic assessment before deciding what to do.",
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
    flag_rows = "\n        ".join(f"| `{flag}` | {desc} |" for flag, desc in CLI_FLAGS)
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

        ## `llmflow run` Flag Reference

        | Flag | Description |
        |------|-------------|
        {flag_rows}

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
