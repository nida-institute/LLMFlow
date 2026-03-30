#!/bin/bash
# Close resolved issues with descriptive comments

close() {
  gh issue close "$1" --repo nida-institute/LLMFlow --comment "$2"
  echo "Closed #$1"
}

close 67 "Implemented as \`sp update-ai-context\` in v0.2.1.03. The command dynamically loads \`tools/update_ai_context.py\` and regenerates all files under \`docs/ai-context/\`. Wired into \`cli.py\` alongside the other subcommands."

close 65 "Implemented in \`src/llmflow/utils/data.py\`. Available built-in helpers: \`load_text_file(path)\`, \`load_json_file(path)\`, \`load_csv_file(path)\`, \`load_tsv_file(path)\`. All are usable in pipeline \`function:\` steps via the built-in function registry. Covered by \`tests/test_data_utilities.py\` and \`tests/test_load_json_file.py\`."

close 64 "Duplicate of #65 — implemented in \`src/llmflow/utils/data.py\`. See #65 for details."

close 63 "Fixed. \`resolve()\` now recursively expands \`\${vars}\` that appear mid-string in a variable value (e.g. \`prefix_\${name}_suffix\`). Max depth is 10 to prevent infinite loops. Covered by the full \`TestResolveMidStringNested\` test class in \`tests/test_variable_resolution.py\` (7 tests)."

close 55 "Fixed in the \`save_content_to_file()\` path for \`.md\` outputs. Markdown normalization (via \`clean_markdown()\`) is applied when saving \`.md\` files, including trailing newline normalization. Regression test \`test_saveas_markdown_extension\` in \`tests/test_saveas.py\` ensures this stays correct."

close 28 "\`sp init\` is fully implemented in \`src/llmflow/cli_utils.py\`. Running \`sp init\` in a new directory creates: \`pipelines/\`, \`prompts/\`, \`outputs/\`, a starter \`hello.yaml\` pipeline, a \`hello.gpt\` prompt, and a \`README.md\`. The \`--update\` flag regenerates marked files without overwriting hand-edited ones. Covered by \`tests/test_init.py\`."

close 26 "Verse reference parser implemented in \`src/llmflow/utils/\` (parse_bible_reference). Supports full book names, abbreviations, chapter:verse ranges, multi-chapter ranges, zero-padded book numbers, and Unicode. Full test coverage in \`tests/test_parse_bible_reference.py\` (40+ test cases)."

close 11 "Conditionals implemented via \`type: if\` step with \`condition:\` field supporting \`\${var}\` and \`{{expr}}\` evaluation, plus \`true_steps:\` / \`false_steps:\` branches. Also supports \`condition_on:\` for checking a named step's output. See \`docs/llmflow-language.md\` for full syntax. Covered by \`tests/test_conditional.py\` and \`tests/test_condition_on_steps.py\`."

close 8 "Checkpointing implemented via \`--rewind-to <step-name>\` and \`--stop-after <step-name>\` CLI flags. Steps with \`saveas:\` write artifacts to disk; on rewind, those artifacts are replayed from disk without re-running the LLM. JSON artifacts are parsed back to their original types. The linter validates that referenced saveas artifacts exist before a rewind run. Full coverage in \`tests/test_rewind.py\`."

echo "All done."
