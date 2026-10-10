---
name: audit-code
description: |
  Audit Python plugins and infrastructure code for structural
  correctness, determinism, and architectural soundness.
  Core focus: verifying plugins are deterministic, that identifier normalization goes
  through canonical helpers (not inline reimplementations), that data contracts are
  enforced at plugin boundaries, and that local plugins don't silently reimplement
  Scripture Pipelines core utilities (which diverge from core over time as core is updated).
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

Local plugins that reimplement Scripture Pipelines core utilities are harder to maintain and less
well-tested than the core. They also silently diverge over time as core is updated — the
local version keeps the old behavior while core fixes bugs or adds edge case handling.

**Step 1: Find what the engine already does**

The surface is the `sp` command line and the pipeline language it reads — not the Python
package, which is the engine's own and carries no compatibility promise. Two documents state
the whole of it:

```bash
# Every command
cat docs/ai-context/sp/command-line.md

# Every step type, and the YAML each one takes
cat docs/llmflow-language-quickref.md
```

A plugin doing something a step type already does is the finding. A plugin importing from the
package is a finding of its own, whatever it does.

**Step 2: Check for work the language already does**

Each of these has a step type. A plugin doing it in Python is carrying code the engine
already maintains, and it drifts as the engine changes:

| What the plugin is doing | The language's answer | Signs of the hand-rolled version |
|---|---|---|
| Fetching a passage, or mapping a reference between numbering schemes | `type: scripture`, with `passage:` and `versification:` | Inline regex on book names, chapter/verse splitting, a local dict of book codes, `if book == "Mark":` chains |
| Building a filename from a reference | `${passage_info.filename_prefix}` | String zero-padding inline (`f"{chapter:03d}"`) |
| Running an XQuery | `type: basex` | `subprocess.run(["basex", ...])` directly |
| Reading a JSON, YAML, XML, CSV or TSV file | `type: load_json` and its siblings | `json.loads(open(...).read())` |
| Looping, chunking, branching, assembling a structure, writing a file | `for-each`, `window`, `if`, `json`, `save` | A Python loop over units of work, an inline template renderer |

```bash
# Reference handling done by hand
grep -n "replace.*Mark\|replace.*John\|book.*chapter\|f\".*{chapter:0\|f\".*{verse:0" plugins/*.py
grep -n "\"Genesis\"\|\"Exodus\"\|\"Matthew\"\|book_map\|book_codes" plugins/*.py

# A backend driven directly
grep -n "subprocess.*basex\|Popen.*basex" plugins/*.py

# File reading a load step already does
grep -n "json\.loads\|json\.load\b" plugins/*.py

# Reaching into the engine's package — a finding whatever it is doing
grep -nE "^[[:space:]]*(import|from)[[:space:]]+llmflow" plugins/*.py
```

**Step 3: Compare behavior against the step type**

For any reimplementation found, run the step type on the same input and compare:
- Does the local version handle the same edge cases? (empty input, malformed references,
  missing fields, a reference in another versification)
- Does it produce the same output for every input you can try?
- Has the engine changed since the local version was written? (check the CHANGELOG)

**Report format:**

```
REIMPLEMENTATION: passage prefix construction
  The language's answer: ${passage_info.filename_prefix}, from a `parse_bible_reference` step
  Local version: plugins/my_plugin.py:34 → f"{book}_{chapter:03d}_{verse:03d}"
  Risk: the engine normalizes book codes and resolves the extent against a versification.
        The local version can produce a different key for the same reference.
  Recommendation: take the value from the step's output instead.
```

Where the language genuinely has no answer, that is a gap worth reporting to the engine — not
a reason to import from the package.

**What to look for beyond the known list:**

Any plugin function that:
- Takes a reference string and returns a normalized form
- Constructs a file path from passage metadata
- Queries an external data source (BaseX, SQLite, REST)
- Parses or validates JSON/XML structure

These are all candidates for core utilities. If the function exists locally and does
general-purpose work (not project-specific logic), ask: does Scripture Pipelines core already do this?

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
[any local code duplicating Scripture Pipelines core utilities, with risk assessment]

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
