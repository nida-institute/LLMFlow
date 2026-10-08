# SP Pipeline Debugging

Project-neutral debugging practices for any `sp` pipeline. Applies to every SP
project on this machine.

**Source:** generalized from `nida-institute/ears-to-hear` `docs/architecture/debugging.md`.

---

## Debug request/response dumps

Setting `linter_config.log_level: debug` at the pipeline level makes every
`type: llm` step write its rendered request and raw response to disk. This is
the switch — there is **no `--debug` flag and no environment variable**.

```yaml
linter_config:
  log_level: debug
```

Then run normally:

```bash
sp run --pipeline pipelines/<name>.yaml
```

- **Location:** `<intermediate_file_directory>/debug/<pipeline_name>/<run_key>/`
  when the pipeline declares `intermediate_file_directory` (resolved through
  `${...}`), otherwise `outputs/debug/<pipeline_name>/<run_key>/`.
  `<pipeline_name>` is the pipeline YAML file stem (e.g. `build-book.yaml` →
  `build-book`). `<run_key>` names the run from its `--var` values, sorted —
  `book-Ruth` — or is `default` when there are none.
- **Filenames:** `<seq>-<step>[-attempt<n>]-request.txt` and
  `<seq>-<step>[-attempt<n>]-response.(txt|json)` — e.g.
  `0001-segment_book-request.txt`, `0002-analyze-attempt2-request.txt`. The
  sequence number orders the calls in a run; the attempt suffix appears from a
  step's second call onward, so a retry never overwrites what it retried. A
  response is `.json` when structured, `.txt` otherwise.
- **`manifest.jsonl`:** one line per model call — step, attempt, the model
  actually called, passage, timings, token counts, cost, and the request and
  response file names. Read the pairing from here rather than from filenames.
- **Cleared per run:** this run's directory is emptied at the start of the run
  (skipped on `--dry-run`). Runs with other `--var` values keep theirs.
- **Cleanup:** `sp clean --debug-only` deletes just the debug directory;
  `sp clean --intermediate-only` preserves it.

These dumps show exactly what instructions and context tokens the model saw —
start here whenever output ignores instructions.

## When LLM output ignores instructions

1. **Confirm the JSON contract first.** Validate the pipeline with
   `sp lint --pipeline pipelines/<name>.yaml` so every downstream consumer sees
   the same keys. If a prompt references a renamed field, fix the producing step
   before retrying the LLM call.
2. **Audit prompt cognitive load.** If completions wander, open the `.gpt`
   template and look for giant bullet lists or requirements buried under
   unrelated context. Split into smaller helper prompts; prefer passing a single
   summary over pasting entire arrays when only one item is being regenerated.
3. **Check chain-of-thought scaffolding.** Prompts that expect phased reasoning
   (analysis → synthesis) need the template to keep asking for the intermediate
   segments; when the model jumps straight to a final answer, that reminder is
   usually missing.
4. **Compare against reference output.** Use prior good dumps or fixture files to
   see what "good" looks like; drift shows up as missing blocks or inconsistent
   fields.

## Inspecting inputs and outputs

- **Debug dumps** (above) show the exact rendered request and raw response for a
  step.
- **`llmflow.log`** — every run writes a log file. When `intermediate_file_directory`
  is declared it is redirected to
  `<intermediate_file_directory>/debug/<pipeline_name>/<run_key>/llmflow.log`; otherwise it
  is `llmflow.log` in the working directory. It records timestamps, step names,
  models, and validation warnings. Ask for its tail when a run fails on another
  machine.
- **Intermediate files** — every step writes its payload under
  `<intermediate_file_directory>/`. Open these to tell whether the model produced
  the wrong data or a later structuring step mangled it.
- **Trace step inputs** — function steps that take `input_path` arguments can be
  pretty-printed with `jq` before they feed a prompt.

## Validation checklist

1. **Contract lint** — `sp lint --pipeline pipelines/<name>.yaml` verifies each
   step's `.gpt` template matches the pipeline-supplied vars.
2. **Dry run** — `sp run --pipeline pipelines/<name>.yaml --dry-run` ensures all
   I/O paths resolve before spending tokens.
3. **Debug dump review** — set `log_level: debug` and inspect the request and
   response files for the failing step; `manifest.jsonl` says which they are.
