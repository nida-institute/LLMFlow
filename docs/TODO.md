# TODO

## Fastest Path to Next Public Release

1. **Stabilize main**
   - Ensure no failing tests (`hatch run pytest`).
   - Resolve open TODOs tied to step-level retry and debug logging before tagging.
2. **Versioning + changelog**
   - Update `pyproject.toml` with the next patch (0.1.x → 0.1.x+1).
   - Append a matching entry to `CHANGELOG.md` summarizing user-facing fixes.
3. **Package build + smoke tests**
   - Inside `hatch shell`: `hatch build` to produce wheel + sdist.
   - Install the wheel into a clean venv and run `llmflow --help` plus a sample pipeline (e.g., `pipelines/hello-llmflow.yaml`).
4. **Publish + tag**
   - `hatch publish` (requires `POETRY_PYPI_TOKEN` or `PYPI_API_TOKEN`).
   - `git tag v0.1.x && git push origin main --tags`.
5. **Notify downstream repos**
   - Update dependent projects’ `pyproject.toml` / `requirements.txt` to reference the new version.

## Rewind: for-each inner step support

**Context:** `--rewind-to` currently raises a `StepRewindError` for any step that
declares `append_to`. This is overly strict. When each for-each iteration saves
to a **unique per-iteration path** (e.g.
`outputs/scenes/${item.reference}_scenes.json`) every artifact is preserved and
replayable; the replayed content simply needs to be re-appended to the
`append_to` list rather than stored to a single output variable.

**Plan:**
1. In `StepRewindManager.replay_step`, remove the blanket `append_to` guard.
2. After loading the artifact content, append it to `context[step["append_to"]]`
   (initialising the list if absent) instead of assigning to `context[target_output]`.
3. Validate that the `saveas` path contains at least one loop-scoped variable
   reference (warn if it doesn't — same path every iteration means only the last
   artifact survives).
4. Add a lint check: if a for-each inner step declares both `append_to` and
   `saveas`, ensure the saveas path differs per iteration (heuristic: path must
   reference the `item_var` or a dot-path of it).
5. Add integration tests using a fixture pipeline where a for-each loop writes
   per-item JSON files, then verify `--rewind-to` replays all iterations
   correctly and final `append_to` list length matches.

**Do not start** until the current rewind fix (no-saveas steps + dynamic paths)
is merged and stable.

---

## Runner Refactor Plan

Goal: make `src/llmflow/runner.py` maintainable by extracting focused modules while preserving current behavior.

1. **Step execution core**
   - Move `_execute_step_with_retry`, `_snapshot_retry_targets`, `_restore_retry_targets`, and the step dispatch logic into `llmflow/steps/executor.py`.
   - Expose a small interface (`execute_step(step, context, pipeline_config) -> after_action`).
2. **For-each + control-flow utilities**
   - Extract `run_for_each_step`, `run_if_step`, and related helpers into `llmflow/steps/control_flow.py`.
   - Keep recursion + context propagation isolated for easier testing.
3. **Debug artifacts + logging**
   - Relocate `build_debug_filename`, `_format_iteration_fragment`, and any debug save helpers into `llmflow/steps/debug.py`.
   - Provide integration points so future UI/CLI hooks can reuse them.
4. **Runner thin layer**
   - Leave `run_pipeline()` responsible for parsing YAML, linting, telemetry, and calling the executor.
   - Ensure telemetry, logger configuration, and CLI signals still originate from a single location.

Sequencing: tackle Step Executor extraction first (highest change velocity), follow with control-flow split, then logging helpers. After each move, rerun the full test suite and update imports accordingly. This staged approach minimizes regressions while chipping away at the monolith.

## Repository Cleanup Plan

Keep LLMFlow focused on the core engine plus a handful of well-documented samples; migrate other domain-specific assets to their project repos.

1. **Inventory & tag content**
   - Audit `docs/`, `pipelines/`, and `prompts/` to tag each file with its owning project (semdom, storytelling, etc.).
   - Identify 3–5 “core” examples that best illustrate the engine (e.g., hello-world, JSON response, visual commentary).
2. **Create destination repos**
   - For each domain (semdom lexicon, storytelling dictionary, etc.), confirm or create dedicated repos and document the new home for their pipelines/prompts.
3. **Migrate content**
   - Move tagged files into their respective repos, preserving history via `git mv` + subtree or by copying with clear attribution.
   - Update those repos to reference LLMFlow as a dependency (pyproject/requirements) rather than bundling engine code.
4. **Curate remaining examples**
   - Keep only the selected core pipelines/prompts here, each with a short README snippet explaining what it demonstrates.
   - Update `docs/getting-started.md` and `docs/llmflow-language.md` to reference the curated set and link out to external project repos for advanced scenarios.
