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

- **Location:** `<intermediate_file_directory>/debug/<pipeline_name>/` when the
  pipeline declares `intermediate_file_directory` (resolved through `${...}`),
  otherwise `outputs/debug/<pipeline_name>/`. `<pipeline_name>` is the pipeline
  YAML file stem (e.g. `build-book.yaml` → `build-book`).
- **Filenames:** `<passage>_<prompt_stem>_request.txt` and
  `<passage>_<prompt_stem>_response.txt`. `<passage>` comes from the step's
  `passage` / `Citation` context (sanitized); when absent a timestamp is used.
  Inside `for-each` loops, iteration tokens are appended. Plain text, not JSON.
- **Cleared per run:** the pipeline's debug subdirectory is wiped at the start of
  every run (skipped on `--dry-run`), so dumps reflect the latest run only.
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
  `<intermediate_file_directory>/debug/<pipeline_name>/llmflow.log`; otherwise it
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
3. **Debug dump review** — set `log_level: debug` and inspect the request/response
   `.txt` files for the failing step.
