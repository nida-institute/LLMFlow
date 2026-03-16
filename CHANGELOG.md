# Changelog

## Unreleased
- Added `json_schema_validator` plugin: validates a pipeline payload against a JSON Schema file. Handles both live Python objects (fresh LLM run) and raw JSON strings/bytes loaded from disk via `--rewind-to`, fixing a crash (`'<string>' is not of type 'array'`) that made schema-validated steps unusable after rewind. (See `src/llmflow/plugins/json_schema_validator.py` and `tests/test_json_schema_validator.py`.)
- Fixed `test_parse_bible_reference.py`: bare book name (e.g. `"Psalm"`) is a valid whole-book reference returning `is_whole_book: True`; corrected incorrect `pytest.raises(ValueError)` assertion.

## 0.1.5.02 — 2026-03-10
- Added rewind-friendly checkpoints: every step with `saveas` now records its outputs to `.llmflow/rewind/` so you can rerun later steps without waiting through expensive calls. The CLI exposes `--rewind-to`, `--stop-after`, and `--rewind-dir` for precise debugging, and the linter verifies that required checkpoints and saved artifacts exist before a rewind run.

## 0.1.5.01 — 2026-03-09
- Hotfix release so downstream environments pick up the new step-level retry schema and telemetry updates introduced in 0.1.5.

## 0.1.5 — 2026-03-09
- Added for-each iteration metadata (nesting level, variable label, optional `debug_label` template) to debug transcript filenames so each loop iteration writes a distinct request/response pair. (See [src/llmflow/runner.py](src/llmflow/runner.py#L43-L125) and [tests/test_debug_utilities.py](tests/test_debug_utilities.py#L62-L97).)
- Bumped the package version to 0.1.5 for downstream consumers.

## 0.1.3 — 2026-03-08
- Expanded `llmflow init` scaffolding to generate multilingual reply prompts plus tutorial, quick reference, and AI-context guardrail docs so new projects start with batteries included. (See `src/llmflow/cli_utils.py`, `docs/tutorial.md`, and `docs/ai-context/`.)
- Added OpenAI Responses API moderation detection and friendlier CLI interrupts to avoid noisy tracebacks when pipelines are blocked or stopped manually. (See `src/llmflow/utils/llm_runner.py`, `src/llmflow/exceptions.py`, and `src/llmflow/cli.py`.)
