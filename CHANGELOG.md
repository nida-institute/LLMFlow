# Changelog

## Unreleased

## 0.2.1.13 — 2026-04-02

### New Features

- **File-based schema loading** — Support `schema_file` in `response_format` config to load JSON schemas from external files instead of inline definitions. This keeps pipeline YAML cleaner and enables schema reuse across pipelines. Example:
  ```yaml
  response_format:
    type: json_schema
    json_schema:
      name: discourse_analysis
      strict: true
      schema_file: schemas/discourse_analysis.json
  ```
- Schema files use standard JSON Schema format and are loaded relative to the current directory.

### Changed

- Added `_load_schema_from_file()` helper to load and parse JSON schemas
- Added `_expand_response_format_schema()` to detect and expand `schema_file` references before calling OpenAI API
- Both inline `schema` and file-based `schema_file` approaches are supported

### Test Coverage

- Added `tests/test_schema_file.py` with 12 comprehensive tests:
  - Schema file loading (valid/invalid/missing files)
  - Response format expansion (inline schemas preserved, schema_file expanded)
  - Integration tests with real OpenAI API
  - Mocked unit tests for parameter passing
  - Error handling for missing/malformed schema files
- Full test suite: **1763 tests passing** (12 new tests added)

### Documentation

- Updated `docs/llmflow-language.md` with file-based schema examples
- Added example pipeline: `pipelines/discourse-analysis-schema-file.yaml`
- Created `schemas/discourse_analysis.json` as reference schema

## 0.2.1.12 — 2026-04-02

### New Features

- **Direct OpenAI Client for Structured Outputs** — LLMFlow now automatically uses OpenAI's client directly when `response_format` is present in step config, bypassing Simon Willison's `llm` package (which may not pass the parameter through). This ensures 100% compatibility with OpenAI's structured outputs feature (`json_schema` mode). No configuration changes needed — works transparently for all pipelines using `response_format`.

### Changed

- **call_llm() detects response_format** — When `response_format` is in config and model is from OpenAI families (gpt-4, gpt-5), automatically routes to `_call_openai_with_response_format()` which uses OpenAI client directly. Falls back to `llm` package for other models/parameters.

### Test Coverage

- **Integration tests for response_format** — Added `tests/test_response_format_integration.py` with 7 tests covering:
  - Basic json_object mode
  - json_schema with simple schema (strict mode, additionalProperties: false)
  - Nested arrays and objects (book segmentation pattern)
  - Prevention of hallucinated fields (strict mode enforcement)
  - Reliability testing (10 iterations, 100% success rate expected)
  - Edge cases: strings with quotes, apostrophes, both
- Tests are SKIPPED unless `OPENAI_API_KEY` is set (to avoid charges during normal test runs).
- Run with: `OPENAI_API_KEY=your-key pytest tests/test_response_format_integration.py -v`

### Documentation

- Updated `docs/llmflow-language.md` — Added note that LLMFlow automatically uses OpenAI client when response_format is present (removes uncertainty about `llm` package support).

## 0.2.1.11 — 2026-04-02

### New Features

- **Structured Outputs Documentation** — Comprehensive documentation for `response_format` with `json_schema` mode guarantees 100% valid JSON from LLM responses. Added to `docs/llmflow-language.md` with full examples showing schema definition, model requirements, and migration path. Eliminates 40-60% intermittent JSON parse failure rate observed in production. (Issue #95)

- **AI Context for JSON Reliability** — Created `docs/ai-context/json-reliability.md` as mandatory reading for AI assistants working with JSON pipelines. Documents the problem (missing commas, unescaped quotes, variable error positions), solution (structured outputs), migration path, and common pitfalls. Referenced prominently in `docs/ai-context/index.md`.

- **JSON Schema Example Pipeline** — Added `pipelines/json-schema-example.yaml` demonstrating three production-ready patterns: (1) nested arrays with complex objects, (2) multi-level required fields, (3) strict mode with `additionalProperties: false`. Includes inline documentation of all schema features.

### Changed

- **audit-prompts Skill Now Audits Pipelines** — Extended `/audit-prompts` skill to check pipeline YAML files for missing `response_format` on JSON steps. New Step 9 detects: (1) JSON steps without `response_format` (legacy/unreliable), (2) steps using `json_object` vs `json_schema` mode, (3) model compatibility (gpt-4o-2024-08-06+ required), (4) project-wide adoption stats. Reports risk level and provides migration code snippets. Skill now applies to `**/*.gpt` AND `**/*.yaml` files.

- **Documented response_format in Language Spec** — Added `response_format` to optional fields for `type: llm` steps in `docs/llmflow-language.md` with cross-reference to new "Structured JSON Output" section. Section includes comparison table (with vs without structured outputs), model requirements, and Gemini alternative syntax.

### Documentation

- **Structured JSON Output section in llmflow-language.md** — 80+ line section with: (1) complete yaml example, (2) results comparison table, (3) key requirements (model, strict mode, additionalProperties), (4) when to use which mode, (5) Gemini alternative. Positioned immediately after `type: llm` field documentation for visibility.

- **Issue #95 comment** — Posted comprehensive solution guide to https://github.com/nida-institute/LLMFlow/issues/95 with migration instructions for discourse-flow project, cost/benefit analysis, and testing checklist.

### Bug Fixes

None (documentation and tooling release only).

## 0.2.1.10 — 2026-04-02

### New Features

- **JSON Output Format Validation in audit-prompts skill** — Added Step 8 to check JSON-producing
  prompts for common formatting issues that cause intermittent parse failures. Detects: (1) code
  fences in OUTPUT SCHEMA sections (confuses LLM into markdown mode), (2) missing JSON formatting
  rules (escaping guidance, structural requirements), (3) incorrect escaping examples (apostrophe
  escaping that's wrong in JSON), (4) inconsistency across multiple JSON prompts in same project.
  Reports risk level and provides specific line numbers with fix recommendations. Based on real
  production failures in discourse-flow where 2 of 8 books failed with delimiter/comma errors due
  to missing formatting guidance. (Issue #94)

## 0.2.1.09 — 2026-04-02

### Changed

- **GUI dependencies now included by default** — Flask, Flask-SocketIO, Flask-CORS, and
  python-socketio moved from optional `[gui]` extra to main dependencies. Since `sp gui`
  is a first-class subcommand of the main `sp` CLI, its dependencies should work out of
  the box without requiring `pip install llmflow[gui]`.

## 0.2.1.08 — 2026-03-30

### New Features

- **Global Prompt Organization Convention** — `sp init` now automatically installs a
  standard organization pattern for `.gpt` prompt files to `~/.sp/conventions/`.
  The convention enforces verifiable transformations (explicit input → output mapping),
  co-located knowledge (rules/examples/data sources grouped by task), consistent heading
  hierarchy, and flexible quality controls with domain-specific naming (GUARDRAILS,
  EVIDENCE DOCUMENTATION REQUIREMENTS, etc.). Projects can override with local
  `docs/prompt-organization-convention.md`. (Issue #93)

- **Audit Prompts Skill** — VS Code Copilot skill installed to `~/.sp/skills/audit-prompts/`
  by `sp init`. Audits `.gpt` files for convention compliance, sprawl detection, and
  three CRITICAL checks: (1) input data grounding (verifies every output field has
  documented input source to prevent hallucination), (2) example diversity (ensures
  examples generalize across passages, not hardcoded to single case), (3) AI-generated
  examples (compares to last commit, flags ANY new examples — #1 source of problems).
  Read-only skill that reports findings with line numbers without modifying files.
  (Issue #93)

- **Automatic editable install in hatch environment** — Added `post-install-commands`
  to `pyproject.toml` so `hatch shell` or `hatch run` automatically installs the package
  in editable mode. The `sp` command is now immediately available for development work
  without manual `pip install -e .` step. (Issue #94)

### Documentation

- Added `docs/global-conventions.md` — comprehensive guide to the prompt organization
  convention and audit skill, including usage examples, best practices, complexity
  categories, project-specific overrides, and critical checks explanation.
- Updated `README.md` — added "Global Conventions & Skills" section with quick usage.

### Bug fixes

- **Telemetry was silently reporting $0.00 / 0 tokens** on every pipeline run.
  Root cause: `response.usage` in `llm_runner.py` was being read as a property but
  the `llm` package exposes it as a method; changed to `response.usage()`.
- **Registry YAML wrote ASCII-escaped Unicode** (`\u05e9` instead of `שׁ`) when
  storing project descriptions containing Hebrew or Greek. Fixed all four
  `yaml.safe_dump` call sites in `registry.py` with `allow_unicode=True` and
  `encoding='utf-8'`.
- **DuckDB `acai_entities` table failed to create** because `references` is a SQL
  reserved word. Column now quoted as `"references"` in `bible_data.py`.
- **DuckDB integration tests were unconditionally skipped** (`skipif(True, ...)`).
  Skip condition replaced with `importlib.util.find_spec("duckdb") is None` so they
  run automatically when DuckDB is installed.

### Type safety — Pyright now reports 0 errors (was 149 across 18 files)

Key fixes across the codebase:
- `modules/logger.py`: added `ClassVar[Optional["Logger"]]` annotation to `_instance`
  and explicit `-> "Logger"` return type on `__new__` so callers see a non-optional type.
- `cli.py`: moved `Logger` import and initialization to module top level, eliminating
  the `logger: None | Logger` union that propagated 22 errors through the module.
- `runner.py`: `resolve()` return values cast to `str` at call sites; `run_llm_step`
  return type widened to `Any` (was `str`, which broke JSON step results);
  `apply_output_template` defined (was called but missing).
- `gui/server.py`: `sys._MEIPASS` accessed via `getattr` instead of direct attribute
  (not in type stubs); `app.static_folder` captured in a typed local variable to
  survive closure narrowing; `room=` → `to=` (Flask-SocketIO API).
- `utils/io.py`: `raise UnicodeDecodeError(msg)` → `raise ValueError(msg)`
  (constructor requires 5 positional arguments).
- `utils/guards.py`: keyword dict comprehension filtered with `if kw.arg is not None`
  to eliminate `str | None` key type.
- Additional fixes in `exceptions.py`, `bible_data.py`, `cli_utils.py`, `linter.py`,
  `rewind.py`, `xml.py`, `xpath.py`, `data.py`, `pipeline_schema.py`, `llm_runner.py`.

### Test coverage

- **Unicode output** (`tests/test_unicode_output.py`, 8 tests): verifies that
  `save_content_to_file` in JSON and text formats, and `ProjectRegistry.register()`,
  write literal Unicode rather than `\uXXXX` escape sequences. Sentinel string is
  `שָׁלוֹם` (shalom with niqquud) plus `בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים` (Genesis 1:1
  with niqquud and cantillation marks — tifha, munah, atnah).
- **Hebrew collation — DuckDB** (2 tests added to `TestDuckDBIntegration`):
  - `COLLATE he` sorts `גָּדוֹל / אֱלֹהִים / בָּרָא` into correct aleph-bet order
    despite attached niqquud.
  - `שָׁלוֹם` (with niqquud) and `שלום` (bare) both sort before `תּוֹרָה`, confirming
    the base consonant — not the niqquud — is the primary sort key.
- **Hebrew collation — BaseX** (2 tests added to `TestBasexIntegration`, run with
  `BASEX_INTEGRATION_TESTS=1`):
  - `fn:sort` with `UCA?lang=he` collation produces aleph-bet order for niqquud-bearing words.
  - `fn:compare("שָׁלוֹם", "שלום", "UCA?lang=he;strength=primary")` returns `0`,
    confirming niqquud are transparent at primary collation strength (essential for
    searching pointed text without knowing whether sources include niqquud).
- `pytest.ini`: fixed section header (`[tool:pytest]` → `[pytest]`); registered
  `duckdb` mark to silence `PytestUnknownMarkWarning`.

### GUI executor refactor

- Extracted `PipelineExecutor` class into a standalone module
  (`src/llmflow/gui/executor.py`) with a parallel copy in `gui/backend/executor.py`.
  Separates testable execution logic from Flask/SocketIO wiring.
- New test files: `tests/test_gui_executor.py` (418 lines),
  `tests/test_gui_server_security.py` (178 lines).

## 0.2.1.07 — 2026-03-27

### GUI Bundling for Nuitka Distribution
- **Restructured GUI for single-binary distribution**: React frontend now builds to static files that are bundled into the nuitka `sp` binary.
- **New production server** (`gui/backend/server.py`): Flask server that serves bundled static React files + REST API in a single process.
- **Build script** (`build_gui.py`): Automates `npm build` → copy to `src/llmflow/gui/static/` → ready for nuitka bundling.
- **CLI command updates**:
  - Added `sp gui` command with `--host`, `--port`, `--no-browser` options.
  - GUI server auto-opens browser and provides clean shutdown on Ctrl+C.
- **Updated `sp-gui` launcher**: Simplified to call bundled server module.
- **Package structure**: GUI static files included via `pyproject.toml` force-include directive.
- **Documentation**:
  - [gui/BUILD.md](gui/BUILD.md): Complete build process documentation.
  - [gui/README.md](gui/README.md): Updated with end-user vs developer workflows.
  - [gui/BUNDLING-SUMMARY.md](gui/BUNDLING-SUMMARY.md): Implementation summary.
- **Test suite** (`test_gui_bundle.py`): Verifies build, static files, imports, and CLI command.
- **Size impact**: Adds ~10-15 MB to binary (Flask ~8MB + React static ~2-3MB). Optional feature - CLI-only users unaffected.
- **Nuitka integration**: Documented `--include-data-dir` flags for embedding static assets.
- **No Python/Node environment needed by end users** - just run `sp gui` from the compiled binary!

## 0.2.1.06 — 2026-03-27

### Global Registry System (Issue #78)
- Added `~/.sp/` global registry for tracking projects, datasets, and databases across the filesystem.
- Implemented `Registry` class with three sub-registries: `ProjectRegistry`, `DatasetRegistry`, `DatabaseRegistry`.
- Added `AIContextRegistry` for tracking AI context files with topics and searchable metadata.
- CLI commands: `sp registry list/info/status/context` for managing global resources.
- Auto-discovery script: `discover_and_register.py` successfully registered 12 projects and 24 datasets from local directories.
- Registry respects `SP_REGISTRY_PATH` environment variable (defaults to `~/.sp/`).
- YAML-based storage for human-readable configuration and easy Git tracking.
- 40 comprehensive tests added in `tests/test_registry.py`; all tests passing.
- Closes issue #78.

### AI Context Discoverability (Issue #79)
**Phase 1: Comprehensive AI Context Index**
- Enhanced `sp init` to create comprehensive `docs/ai-context/index.md` (100+ lines) with:
  - Explicit "Check this FIRST" instruction for AI assistants.
  - Complete list of core files and suggested context files (basex-patterns.md, duckdb-patterns.md, etc.).
  - Usage examples for both AI assistants and project maintainers.
  - Integration guidance for registry system.
- Updated `.github/copilot-instructions.md` template to emphasize checking index.md as second read (after TODO.md).
- Templates marked with `<!-- Generated by sp init -->` for `--update` support.

**Phase 2: CLI Discovery Commands**
- Added `sp context list` command: scans `docs/ai-context/` and displays files with auto-extracted descriptions.
- Implemented context file discovery in `src/llmflow/context.py` (~165 lines):
  - `list_context_files()` - directory scanning and metadata extraction.
  - `extract_description()` - intelligent markdown parsing for descriptions.
  - `format_context_list()` - formatted terminal output.
  - `generate_context_inventory()` - prepared for future AI prompt injection.
- 14 comprehensive tests in `tests/test_context.py`; all tests passing.

**Phase 3: Registry Integration with Topics**
- Extended `AIContextRegistry` with searchable topic-based metadata.
- Added `sp context add <file> --description "..." --topics "basex,xquery,greek"` - register context files with rich metadata.
- Added `sp context search <topics>` - find relevant context across all projects by topic.
- Context files stored in `~/.sp/ai-context/*.yaml` with structured metadata (file, project, description, topics, path, created timestamp).
- Cross-project search enables discovering patterns from any registered project.
- 10 AIContextRegistry tests added to `tests/test_registry.py`.
- Closes issue #79.

### DuckDB Analytics Step Type
- Added `type: duckdb` step: query CSV/Parquet/JSON files with SQL and return results in multiple formats.
- Supports `query:` (inline SQL with `${variable}` substitution) or `query_file:` (path to `.sql` file).
- Output formats: `records` (list of dicts), `dict` (single record), `json` (JSON string), `dataframe` (pandas DataFrame).
- Variable substitution in queries: `SELECT * FROM '${input_file}' WHERE book = '${book}'`.
- Added dependency: `duckdb>=1.0.0` and `pandas>=1.3.0` in `pyproject.toml`.
- 18 comprehensive tests in `tests/test_duckdb_step.py` covering query execution, formats, errors, and integration.
- Design document: `docs/duckdb-analytics-design.md` with rationale and examples.
- Use case document: `docs/xquery-greek-analytics.md` with 10 Greek NT analysis patterns using XQuery+DuckDB.

### Bible Data Access Utilities
- Added `src/llmflow/utils/bible_data.py` with `BibleDataRegistry` for discovering biblical datasets.
- Maps resource IDs (acai, macula-hebrew, macula-greek, sblgnt) to filesystem paths.
- High-level APIs: `load_acai_entity()`, `get_entities_for_passage()`, `parse_reference_to_verse_range()`.
- Supports multiple organizations: checks `~/github/BibleAquifer/` and `~/github/Clear/` automatically.
- Custom base path support with proper isolation (fixes test_custom_base_path).
- XQuery integration: `to_basex_verse_range()` converts human references to BaseX verse IDs.
- DuckDB integration helpers included for loading biblical datasets into DuckDB.
- 27 tests in `tests/test_bible_data.py`; all tests passing.

### Collaboration Principles Documentation
- Added `docs/collaboration-principles.md`: structured framework for AI-human collaboration on Scripture Pipelines.
- Documents five key principles: Common Language, Defined Authority, Testable Claims, Incremental Progress, Explicit Context.
- Includes anti-patterns, implementation guidelines, and measurement criteria.
- Provides practical examples of effective collaboration patterns.

### Test Suite
- **1593 tests passing** (81 new tests added across registry, context, duckdb, and bible_data modules).
- Zero test regressions - all existing functionality preserved.
- Comprehensive TDD workflow: tests written first, implementation followed, all tests passing.

## 0.2.1.05 — 2026-03-25

### Paratext project metadata access
- Added `load_project_file(base_dir, project_name, file)` function to load Paratext project metadata files (Scripture Burrito `metadata.json`, Paratext `Settings.xml`, `BiblicalTerms.xml`, etc.). Auto-detects format by extension: `.json` → dict, `.xml` → lxml Element.
- Added `xpath_text(element, path)` helper function for extracting text values from XML elements via XPath queries.
- Scripture Burrito metadata supports direct dict access in templates: `${burrito.languages[0].name.en}`, `${burrito.identification.name.en}`.
- Paratext XML requires extraction via `xpath_text()` before passing to LLM templates (cannot serialize `_Element` objects directly).
- 9 tests added in `tests/test_paratext_metadata.py`; all 1225 tests passing.
- **Design rationale (eager evaluation):** USFM files are parsed upfront to protect against network mount disconnects during long-running LLM steps. Once `load_usfm_book(format="usj")` returns a dict, the pipeline is independent of filesystem I/O.
- Created example repository: https://github.com/nida-institute/paratext-pipelines with backtranslation and multi-project comparison pipelines.
- Closes issue #73.

### Audit checklists in `sp init`
- Added `docs/audits/` directory created by `sp init` with audit procedure checklists (version-controlled).
- Added `docs/audits/INDEX.md` dispatch table mapping artifact types to checklist files.
- Added `docs/audits/audit-passage.md` (40-line checklist for passage outputs) and `docs/audits/audit-leadersguide.md` (45-line checklist for leader's guides).
- All checklists follow pattern: 20-60 lines, checkbox format only, STOP conditions in bold, no prose.
- Templates marked with `<!-- Generated by sp init -->` for `--update` support.
- `project/audits/` directory remains for audit findings (gitignored, not version-controlled).
- 3 tests added in `tests/test_init.py`.
- Implementation complete for issue #72 (documentation pending).

### AI context documentation
- Added `docs/ai-context/paratext-schemas.md` with comprehensive schema reference for Scripture Burrito and Paratext XML metadata files.
- Documents Scripture Burrito structure: `languages`, `identification`, `agencies`, `copyright` fields with access paths.
- Documents Paratext Settings.xml elements: `LanguageName`, `LanguageIsoCode`, `Versification`, `IsRTL`, etc. with XPath queries.
- Provides guidance on choosing between Scripture Burrito vs Settings.xml for different metadata needs.
- Includes structure overview for `BiblicalTerms.xml` and `BookNames.xml`.
- Updated `docs/ai-context/data-sources.md` to reference the new schema file.

## 0.2.1.02 — 2026-03-20
- Renamed product to **Scripture Pipelines** and CLI binary to `sp` throughout install scripts (`install.sh`, `install.ps1`), `README.md`, `INSTALL.md`, and all docs. Asset names updated to `sp-macos`, `sp-linux`, `sp-windows.exe`. CI workflow asset labels updated to match. `PROJECT_TODO` tutorial backlog in `cli_utils.py` expanded to 8 steps mirroring `sp init` tutorial issues; 5 new tests added to `TestProjectTodoTutorial`.

## 0.2.1.01 — 2026-03-20
- Added `type: basex` step: runs XQuery against a local BaseX database and stores the result in pipeline context. Accepts `database:` (any existing BaseX DB name), `query:` (inline XQuery string) or `query_file:` (path to `.xq` file), `params:` (dict resolved from context and substituted into the query via `{key}` placeholders), and `timeout:` (default 120 s). Built-in error handling for missing `basex` binary, non-zero exit, and timeout. Linter validates required fields and allows all basex-specific keys. (See `src/llmflow/plugins/basex.py`, `src/llmflow/runner.py`, and `tests/test_basex.py`; closes nida-institute/LLMFlow#49.)

## 0.1.5.07 — 2026-03-18

### `llmflow init` scaffolding expanded
- Added `docs/vscode.md`: recommended VS Code settings with privacy/convenience explanation table for AI-assisted pipeline work. Regenerated by `init --update`.
- Added `project/TODO.md`: Active/Backlog/Done task tracking file. Created once on first `init`, never overwritten (designed to be hand-edited). Convention: link GitHub Issues with `→ #N`.
- Added `project/audits/README.md`: naming conventions and guidelines for QA reports and output review notes. Regenerated by `init --update`.

### AI context docs improved
- `AI_RULES_DOC` (→ `docs/ai-context/rules.md`) gains two new rules:
  - Rule 8: read `project/TODO.md` at session start; update Active/Done sections; link issues by number.
  - Rule 9: do not create GitHub Issues — flag the need and let the human open them.
- `AI_INDEX_DOC` (→ `docs/ai-context/index.md`) now points AI assistants to `project/TODO.md` as the first thing to read each session.

### Prompt contract enforcement tightened
- `HELLO_PROMPT` and `HELLO_REPLY_PROMPT` now include proper `requires:` frontmatter so the linter can validate the hello-world pipeline contracts.
- `LANGUAGE_QUICKREF_DOC` gains §6 "Prompt file format" showing the full `---requires:/optional:---` pattern with example.
- `AI_RULES_DOC` rule 7 (declare prompt contracts) was already present; now backed by tests.
- `validate_step_prompt_contract()` in `linter.py`: when a step provides inputs but the `.gpt` header has no `requires:` key, now emits a `❌` error instead of silently treating it as "no requirements". Previously this produced only a ⚠️ warning on "unexpected inputs", which never failed lint. (4 new tests in `TestMissingRequiresIsError`.)

### INSTALL.md
- Mac install instructions now use `~/bin` (no `sudo` or admin rights needed).
- New §3 "Install the `llm` package and models": `llm keys set openai`, Anthropic/Gemini plugin examples, `llm models` verification.
- Windows section rewritten with step-by-step PATH setup, SmartScreen clearing, and persistent API key via PowerShell.

## 0.1.5.06 — 2026-03-18
- Fixed `rewind.py` `replay_step()`: replayed artifacts are now JSON-parsed before being stored in context, so downstream steps receive a `list`/`dict` the same as from a live run. Plain-text artifacts fall back to `str` as before. Steps declaring `output_type: json` emit a warning if their artifact cannot be parsed. (4 new tests in `TestReplayStepJsonParsing`.)

## 0.1.5.05 — 2026-03-17
- Implemented `[*]` wildcard in `get_from_context()`: `${list[*].field}` and deep paths like `${list[*].a[0].b}` now fan out over the list, apply the remaining path to each element, and return a flat list. Missing fields or out-of-bounds indices produce `None` slots; an empty source list produces `[]`. Previously the expression resolved silently to `None`. (6 new tests in `TestStarWildcardResolution`, including `pericope_results[*].segments[0].boundary_signals` deep-path coverage.)
- Added `llmflow init --update`: regenerates files carrying the `<!-- Generated by llmflow init -->` marker (quickref, ai-context docs, tutorial) while leaving hand-edited files untouched. (2 new tests in `test_init.py`.)
- Updated `LANGUAGE_QUICKREF_DOC` (emitted by `init`) to include `type: if`, step-level `condition:`, and the `${list[*].field}` array mapping syntax.
- Documented `condition:` step-level skip guard and `type: if` block in `docs/llmflow-language.md` — both were fully implemented in the runner but absent from the language spec.
- Added `docs/ai-context/data-shapes.md`: canonical shapes for engine-owned artifacts (`passage_info`, `scene_list` items), `[*]` semantics with Python-equivalent mental model, and a clarifying note that consumer-project artifacts are not defined in this repo.

## 0.1.5.04 — 2026-03-16
- Implemented `[*]` wildcard in `get_from_context()`: `${list[*].field}` and deep paths like `${list[*].a[0].b}` now fan out over the list, apply the remaining path to each element, and return a flat list. Missing fields or out-of-bounds indices produce `None` slots; an empty source list produces `[]`. Previously the expression resolved silently to `None`. (6 new tests in `TestStarWildcardResolution`, including `pericope_results[*].segments[0].boundary_signals` deep-path coverage.)
- Documented `condition:` step-level skip guard and `type: if` block in `docs/llmflow-language.md` — both were fully implemented in the runner but absent from the language spec.
- Added `docs/ai-context/data-shapes.md`: canonical shapes for engine-owned artifacts (`passage_info`, `scene_list` items), `[*]` semantics with Python-equivalent mental model, and a clarifying note that consumer-project artifacts (`pericope_package`, `book_flow_json`, etc.) are not defined in this repo.

## 0.1.5.04 — 2026-03-16
- Added `--version` flag to the CLI (`llmflow --version`). The existing `version` subcommand is unchanged. The flag is what CI binary smoke tests call and what users expect from a standard Unix tool. Fixes CI Run #15 failure where `$BIN --version` exited with code 2 because argparse didn't recognise it.

## 0.1.5.03 — 2026-03-16
- Added `json_schema_validator` plugin: validates a pipeline payload against a JSON Schema file. Handles both live Python objects (fresh LLM run) and raw JSON strings/bytes loaded from disk via `--rewind-to`, fixing a crash (`'<string>' is not of type 'array'`) that made schema-validated steps unusable after rewind. (See `src/llmflow/plugins/json_schema_validator.py` and `tests/test_json_schema_validator.py`.)
- Added binary smoke tests to `build-release.yml`: each platform build now runs `--version`, `lint`, and `--dry-run` against the Nuitka binary before uploading, catching packaging failures before they reach GitHub Releases. Added `tests/fixtures/smoke.yaml` as the no-API-key test fixture.
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
