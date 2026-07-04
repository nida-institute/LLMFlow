---
name: audit-code
description: |
  **WORKFLOW SKILL** — Audit Python plugins and infrastructure code for structural
  correctness, determinism, and architectural soundness.
  Core focus: verifying plugins are deterministic, that identifier normalization goes
  through canonical helpers (not inline reimplementations), that data contracts are
  enforced at plugin boundaries, and that local plugins don't silently reimplement
  LLMFlow core utilities (which diverge from core over time as core is updated).
  DO NOT USE FOR: pipeline YAML structure, identifier lifecycle across pipeline stages,
  JSON schema coverage, prompt field contracts — use audit-pipeline for those.
  DO NOT USE FOR: modifying code; running pipelines.
toolRestrictions:
  forbidden:
    - replace_string_in_file
    - multi_replace_string_in_file
  reasoning: "Read-only audit skill unless user explicitly requests changes."
---

# Audit Code Skill

## Core Principle: My Findings Require Human Review

Report specific evidence for every finding. Flag uncertainty explicitly. Do not
declare code "correct" or "ready" — that judgment belongs to the human who
understands the full pipeline lifecycle.

---

## Scope

This skill audits **Python plugin code**. For pipeline YAML structure, identifier
lifecycle across stages, JSON schema coverage, and prompt field contracts, use
`/audit-pipeline` instead.

---

## What to Audit

### Python plugins (`plugins/*.py`)

**Identifier normalization:**
- [ ] Normalization functions exist and are called consistently — not reimplemented inline
- [ ] If a plugin constructs a key (passage ref, scene ID, lemma), it calls the same
  helper as every other plugin that constructs that key
  ```bash
  grep -rn "scene_id\|passage_key\|normalize" plugins/
  ```
- [ ] No string manipulation of passage references inline (e.g., `.replace(" ", "_").lower()`)
  without going through the canonical normalizer

**Data contract:**
- [ ] Each plugin's `run()` function returns the fields the pipeline YAML declares in `outputs:`
- [ ] Required input fields are validated at the top — missing fields raise clearly, not silently
- [ ] `.get("field", default)` defaults are correct — no `{}` default for an array field,
  no `[]` default for a dict field

**Determinism:**
- [ ] No calls to `random`, `datetime.now()`, or anything that changes between runs
  (unless explicitly documented as intentional)
- [ ] File reads use explicit paths, not glob patterns that could match different files

**Error handling:**
- [ ] No bare `except:` or `except Exception: pass` — failures should surface clearly
  ```bash
  grep -n "except:\|except Exception\|: pass" plugins/*.py
  ```

---

### Core Reimplementation Check

Local plugins that reimplement LLMFlow core utilities are harder to maintain and less
well-tested than the core. They also silently diverge over time as core is updated — the
local version keeps the old behavior while core fixes bugs or adds edge case handling.

**Step 1: Find the LLMFlow core API surface**

```bash
# Installed package (what the project actually runs against)
python -c "import llmflow; print(llmflow.__file__)"

# Engine source repo (if available locally)
ls ~/github/nida-institute/LLMFlow/src/llmflow/

# List all public functions in core utilities
grep -n "^def \|^class " ~/github/nida-institute/LLMFlow/src/llmflow/*.py | grep -v "test_\|_private"
```

**Step 2: Check for reimplemented core utilities in local plugins**

Known core utilities that get reimplemented locally — check for each:

| Core utility | What it does | Local reimplementation signs |
|---|---|---|
| `parse_bible_reference()` | Normalizes reference strings to stable keys | Inline regex on book names, chapter/verse splitting |
| `normalize_book_code()` | Maps book names/abbreviations to canonical codes | Local dict of book names, `if book == "Mark":` chains |
| `format_passage_prefix()` | Builds the `BBBCCCVVV-BBBCCCVVV` filename prefix | String zero-padding inline (`f"{chapter:03d}"`) |
| BaseX query helpers | Runs XQuery, parses results | `subprocess.run(["basex", ...])` directly |
| JSON load/save with error handling | Safe read/write with schema validation | `json.loads(open(...).read())` without validation |

```bash
# Passage reference construction (should use parse_bible_reference)
grep -n "replace.*Mark\|replace.*John\|book.*chapter\|f\".*{chapter:0\|f\".*{verse:0" plugins/*.py

# Book name mapping (should use normalize_book_code or equivalent)
grep -n "\"Genesis\"\|\"Exodus\"\|\"Matthew\"\|book_map\|book_codes" plugins/*.py

# Direct BaseX subprocess calls (should use core helper)
grep -n "subprocess.*basex\|Popen.*basex" plugins/*.py

# Raw JSON without validation (should use core safe-load)
grep -n "json\.loads\|json\.load\b" plugins/*.py
```

**Step 3: Compare behavior against core**

For any reimplementation found, open both versions and check:
- Does the local version handle the same edge cases as core? (empty input, malformed
  references, missing fields)
- Does the local version produce identical output format for all inputs?
- Has core been updated since the local version was written? (check git log on the engine)

**Report format:**

```
REIMPLEMENTATION: passage prefix construction
  Core utility: llmflow.utils.format_passage_prefix()
  Local version: plugins/my_plugin.py:34 → f"{book}_{chapter:03d}_{verse:03d}"
  Risk: Core handles book code normalization and edge cases. Local version may
        produce different keys for the same reference under some inputs.
  Recommendation: Replace with core utility call.
```

**What to look for beyond the known list:**

Any plugin function that:
- Takes a reference string and returns a normalized form
- Constructs a file path from passage metadata
- Queries an external data source (BaseX, SQLite, REST)
- Parses or validates JSON/XML structure

These are all candidates for core utilities. If the function exists locally and does
general-purpose work (not project-specific logic), ask: does LLMFlow core already do this?

---

### General red flags

```bash
# Inline string normalization (should be in a function)
grep -n '\.lower()\|\.replace(" ", "_")\|\.strip()' plugins/*.py

# Silent failures — bare except or pass
grep -n "except:\|except Exception\|: pass" plugins/*.py

# Raw JSON without validation
grep -n "json\.loads\|json\.load\b" plugins/*.py

# Direct subprocess to external tools (should use core helpers)
grep -n "subprocess\.\|Popen(" plugins/*.py
```

---

## Report Format

```markdown
# Code Audit: {target}
**Date:** {date}
**Files examined:** [list]

## Plugin Findings
[findings with file:line references]

## Core Reimplementations
[any local code duplicating LLMFlow core utilities, with risk assessment]

## Red Flags
[specific grep results that need human review]

## Summary
**Blockers:** [silent failure risks, incorrect defaults, identifier mismatches inside plugins]
**Items for human review:** [judgment calls]
```

---

## Related Skills

- `/audit-pipeline` — Audits pipeline YAML contracts: identifier lifecycle across stages,
  field contract between prompts and schemas, schema coverage, plugin/schema sync.
  Run this for pipeline-level concerns; run `/audit-code` for plugin internals.
- `/audit-prompts` — Audits prompt structure, conventions, and structural forcing.
- `/audit-output` — Audits pipeline output quality (content, not contracts).
