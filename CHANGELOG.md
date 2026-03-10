# Changelog

## 0.1.5.01 — 2026-03-09
- Hotfix release so downstream environments pick up the new step-level retry schema and telemetry updates introduced in 0.1.5.

## 0.1.5 — 2026-03-09
- Added for-each iteration metadata (nesting level, variable label, optional `debug_label` template) to debug transcript filenames so each loop iteration writes a distinct request/response pair. (See [src/llmflow/runner.py](src/llmflow/runner.py#L43-L125) and [tests/test_debug_utilities.py](tests/test_debug_utilities.py#L62-L97).)
- Bumped the package version to 0.1.5 for downstream consumers.

## 0.1.3 — 2026-03-08
- Expanded `llmflow init` scaffolding to generate multilingual reply prompts plus tutorial, quick reference, and AI-context guardrail docs so new projects start with batteries included. (See `src/llmflow/cli_utils.py`, `docs/tutorial.md`, and `docs/ai-context/`.)
- Added OpenAI Responses API moderation detection and friendlier CLI interrupts to avoid noisy tracebacks when pipelines are blocked or stopped manually. (See `src/llmflow/utils/llm_runner.py`, `src/llmflow/exceptions.py`, and `src/llmflow/cli.py`.)
