---
name: audit-prompts
description: |
  **WORKFLOW SKILL** — Audit LLMFlow prompt files (.gpt) AND pipeline files (.yaml) for organization, sprawl, convention compliance, and CRITICAL: input data grounding, example diversity, AI-generated examples, JSON output format, and structured outputs usage.
  USE FOR: checking prompt structure; identifying sprawl (line count, header count); validating section hierarchy;
  comparing against prompt-organization-convention.md; finding scattered examples; detecting inconsistent heading levels;
  auditing pipelines for missing response_format on JSON steps.
  CRITICAL CHECKS: (0) guardrail integrity — detect removed/weakened MANDATORY/MUST/REQUIRED constraints since last commit (silent failure mode that causes known bad outputs);
  (1) verifying every output field has documented input data source (no making things up);
  (2) ensuring examples generalize across passages (not hardcoded to single case);
  (3) detecting ANY new examples since last commit (#1 source of problems - AI creates examples that don't match intent);
  (4) validating JSON output format mechanics (code fences, formatting rules, escaping examples, consistency);
  (5) detecting JSON steps without response_format (guarantees valid JSON, eliminates 40-60% failure rate).
  DO NOT USE FOR: testing prompt output quality; debugging LLM responses; modifying prompt content (use other tools).
  INVOKES: file_search, read_file, grep_search for pattern analysis; git show for version comparison; reports findings with specific line numbers.
applyTo:
  - "**/*.gpt"
  - "**/*.yaml"
toolRestrictions:
  forbidden:
    - replace_string_in_file
    - multi_replace_string_in_file
    - create_file
  reasoning: "This is a read-only audit skill. It identifies issues but does not make changes. User decides whether/how to fix."
---

# Audit Prompts Skill

## Purpose

Audit LLMFlow `.gpt` prompt files for:
1. **Sprawl detection** — line counts, header counts, complexity indicators
2. **Convention compliance** — comparing against `docs/prompt-organization-convention.md`
3. **Section hierarchy** — checking heading level consistency
4. **Example organization** — finding scattered vs. consolidated examples
5. **TODOs** — tracking placeholder sections
6. **🚨 Input data grounding (CRITICAL)** — verifying every output field has documented input source (prevents "making things up")
7. **🚨 Example diversity (CRITICAL)** — ensuring examples generalize across passages (not hardcoded to single case)
8. **🚨 Guardrail integrity (CRITICAL)** — detecting removed or weakened MANDATORY/MUST/REQUIRED constraints since last commit (the silent failure mode — removed guardrails cause known bad output patterns without obvious signal)
9. **🚨 AI-generated examples (CRITICAL - #1 SOURCE OF PROBLEMS)** — detecting ANY new examples since last commit (AI creates examples that don't match user intent)
10. **🚨 JSON output format (CRITICAL - for JSON prompts)** — code fences, formatting rules, escaping guidance, consistency (prevents intermittent parse failures)
11. **🚨 Structured outputs usage (CRITICAL - for pipelines)** — detecting JSON steps without `response_format` (guarantees valid JSON, eliminates 40-60% failure rate)

## Core Principle: No LLM-Generated Training Data

**ABSOLUTE RULE:** Nothing produced by an LLM can ever be used as training data (examples) in prompts. Period.

**Why this matters:**
- LLM output doesn't match user intent with sufficient precision
- AI-generated examples encode subtle patterns the AI already knows, not what you're trying to teach
- Examples must demonstrate the exact pattern you want, which requires human judgment
- Using LLM output as training creates circular reasoning and drift from intent

**What this means for audits:**
- Any new examples since last commit are SUSPECT until proven human-written
- At best, AI can propose examples for user approval (never auto-merged)
- Often, user must write examples themselves to ensure quality
- TODOs that get replaced with examples warrant extra scrutiny

**During audits:**
1. Always compare current version to last commit
2. Flag ANY new or modified examples
3. Report them with suspicion: "likely AI-generated, needs user review"
4. Never assume new examples are correct

## When to Invoke

Use this skill when:
- User asks to "audit prompts" or "check prompt organization"
- User wants to know if a prompt follows conventions
- User is considering reorganizing a prompt and wants current state
- User asks "is [prompt] organized like [other prompt]?"
- User requests comparison of multiple prompts

## Workflow

### Step 1: Load Convention

Read the prompt organization convention to understand the standard organization pattern.

**Convention location (check in order):**
1. `~/.sp/disciplines/llmflow-prompt-organization.md` (global default)
2. `docs/prompt-organization-convention.md` (repo-specific override)

Use global convention by default; use local version if project has customized standards.

**Task-focused structure (for transformation prompts):**
1. **YAML Frontmatter** — requires, optional, format, description
2. **# WHAT THIS PROMPT PRODUCES** — purpose, philosophy, model explanation
3. **# OUTPUT FORMAT** — JSON schema with wording guidelines
4. **# [TASK 1 NAME]** — First major task (e.g., NOTICE QUESTIONS, ANALYSIS, etc.)
   - ## Input: Where to Find the Data
   - ## Transformation Rules (with ✅/❌ examples)
   - ## Examples: Input → Transformation → Output (with TODOs for manual writing)
   - ## Rules Specific to This Output Type
5. **# [TASK 2 NAME]** — Second major task (if applicable)
   - (same subsection pattern)
6. **# COVERAGE & QUALITY CHECKLIST** — pre-submission verification
7. **# INPUT DATA** — template variables ({{scenes}}, {{verses}}, etc.)
8. **# CRITICAL REMINDERS** — final guardrails

**Key principle:** Everything about a task is co-located in that task's section (data sources, rules, examples). Don't scatter rules across the file.

**Heading hierarchy:**
- `#` for major sections (tasks, checklist, input data)
- `##` for subsections within tasks
- `###` for fine details if needed

**Length guidelines:**
- Simple: < 200 lines, < 15 headers
- Medium: 200-300 lines, 15-25 headers
- Complex: 300-500 lines, 25-35 headers
- Warning signs: > 500 lines, > 35 headers

### Step 2: Analyze Target Prompt(s)

For each prompt file:

**Basic metrics:**
```bash
wc -l [prompt].gpt              # Line count
grep -c "^#" [prompt].gpt       # Header count
grep -c "TODO:" [prompt].gpt    # TODO count
```

**Section structure:**
```bash
grep -n "^#" [prompt].gpt       # All headers with line numbers
```

**Heading level patterns:**
```bash
grep "^####" [prompt].gpt       # Check for over-granular headings
```

**Example organization:**
```bash
grep -n -B2 -A2 "^.*Example:" [prompt].gpt | head -50
# Are examples consolidated or scattered?
```

**YAML frontmatter:**
```bash
head -15 [prompt].gpt | grep "^---"
```

### Step 3: Check Convention Compliance

Compare against standard structure:
1. ✅ Has YAML frontmatter?
2. ✅ Has "WHAT THIS PROMPT PRODUCES" section?
3. ✅ Has "OUTPUT FORMAT" with wording guidelines?
4. ✅ Major tasks organized with:
   - Input: Where to Find the Data
   - Transformation Rules (with examples)
   - Examples: Input → Transformation → Output
   - Rules specific to this output type
5. ✅ Has "COVERAGE & QUALITY CHECKLIST"?
6. ✅ Has "INPUT DATA" section with template variables?
7. ✅ Has "CRITICAL REMINDERS" final guardrails?
8. ✅ Heading hierarchy consistent? (# for major tasks, ## for subsections)
9. ✅ Data sources, rules, and examples co-located within each task section? (not scattered)

### Step 4: Identify Sprawl Indicators

**Red flags:**
- Line count > 500
- Header count > 35
- Examples appear in 3+ different sections
- Repeated guardrail text with variations
- Multiple `###` or `####` subsections for same concept
- Long prose blocks (> 50 lines) without structure

**Yellow flags:**
- Line count 400-500
- Header count 30-35
- Examples in 2+ sections
- Inconsistent heading levels (mixing `##` and `#` for major sections)

### Step 5: Check Input Data Grounding (CRITICAL)

**Purpose:** Verify the prompt doesn't let the LLM make things up. For every output field the LLM is asked to produce, check that the prompt explicitly tells it where to find that data in the input.

**Check DATA SOURCES section:**
```bash
# Find DATA SOURCES section
grep -n -A 50 "^# DATA SOURCES" [prompt].gpt

# Look for explicit field mappings like:
# - `heart_movements[]` → `.character`, `.treasure_verb`, etc.
# - `sensory_inventory[]` → `.modality`, `.description`
# - `structural_features[]` → narrative patterns
```

**Verify for each output field:**
1. Read OUTPUT SCHEMA section - list all fields the LLM must produce
2. For each field, find where DATA SOURCES or INPUT DATA tells the LLM where to get it
3. Flag any output field that has no documented data source

**Red flags:**
- Output field with no corresponding input data source
- Generic instructions like "identify the key themes" without pointing to specific input fields
- "Use your knowledge of..." or "Based on typical patterns..." (making things up)
- Missing DATA SOURCES section entirely

**What to report:**
- List of output fields without clear input data sources (with line numbers)
- Sections that ask for content without grounding in input data
- Grade: Full grounding / Partial grounding / Ungrounded

### Step 6: Check Example Diversity (CRITICAL)

**Purpose:** Examples must generalize across passages, not hardcode to a single case. Using only one passage trains the LLM on specifics rather than patterns.

**Scan EXAMPLES section:**
```bash
# Find all passage references in examples
grep -n "Mark [0-9]" [prompt].gpt
grep -n "MRK [0-9]" [prompt].gpt
grep -n "John [0-9]" [prompt].gpt
# ... etc for other books
```

**Check for:**
1. How many distinct passages are referenced in examples?
2. Are examples all from the same chapter or passage?
3. Do examples show the same pattern across different narrative types?

**Red flags:**
- All examples from Mark 12:13-17 (or any single passage)
- Examples from only one book or narrative type
- No variety in scenario types (all confrontation, all teaching, etc.)

**Yellow flags:**
- Examples from 2 passages but both similar types
- One good example set but others need diversity

**What to report:**
- List of passage references found in examples (with line numbers)
- Count of distinct passages used
- Assessment: Good diversity / Limited diversity / Single-passage examples
- Recommend adding examples from different passage types

### Step 6.5: Guardrail Integrity Check (CRITICAL)

**Purpose:** Detect removed or weakened guardrails — the silent failure mode where a critical constraint disappears without touching the examples.

**What counts as a guardrail:**
- Sections titled GUARDRAILS, CRITICAL REMINDERS, Critical Blockers
- Any paragraph containing: MANDATORY, MUST, REQUIRED, "Do not", "Never", "FORBIDDEN"
- Coverage rules like "every scene must have at least N questions"
- Output requirements list items with mandatory language

**Process:**

1. **Get last committed version:**
   ```bash
   git show HEAD:prompts/[prompt].gpt > /tmp/last-committed.gpt
   # or: git show main:prompts/[prompt].gpt > /tmp/last-committed.gpt
   ```

2. **Extract guardrail content from both versions:**
   ```bash
   # All lines with mandatory/prohibition language
   grep -n "MANDATORY\|MUST\|REQUIRED\|FORBIDDEN\|Do not\|Never\|must have\|must include\|every scene\|at least" [prompt].gpt > /tmp/current-guardrails.txt
   grep -n "MANDATORY\|MUST\|REQUIRED\|FORBIDDEN\|Do not\|Never\|must have\|must include\|every scene\|at least" /tmp/last-committed.gpt > /tmp/committed-guardrails.txt
   ```

3. **Diff section content:**
   ```bash
   # Check specific guardrail sections
   awk '/^# GUARDRAILS/,/^# [A-Z]/' [prompt].gpt > /tmp/current-guardrail-section.txt
   awk '/^# GUARDRAILS/,/^# [A-Z]/' /tmp/last-committed.gpt > /tmp/committed-guardrail-section.txt
   diff /tmp/committed-guardrail-section.txt /tmp/current-guardrail-section.txt

   # Same for CRITICAL REMINDERS
   awk '/^# CRITICAL REMINDERS/,/^# [A-Z]/' [prompt].gpt > /tmp/current-reminders.txt
   awk '/^# CRITICAL REMINDERS/,/^# [A-Z]/' /tmp/last-committed.gpt > /tmp/committed-reminders.txt
   diff /tmp/committed-reminders.txt /tmp/current-reminders.txt
   ```

4. **Flag any removal or softening:**
   - Line present in committed version, absent in current = REMOVED guardrail
   - "MUST" changed to "should" = WEAKENED guardrail
   - "REQUIRED" removed = WEAKENED guardrail
   - Count of numbered reminders decreased = item removed

**What to report:**
```markdown
## 🚨 GUARDRAIL INTEGRITY CHECK

**GUARDRAILS section:** [Unchanged | Changed — see below]
**CRITICAL REMINDERS section:** [Unchanged | Changed — see below]

### Removed guardrails:
🚨 **Line 47 (committed) — REMOVED in current version:**
> "every scene in `{{passage_ref}}` must have at least 1 Imagine question"
**Risk:** Model treats Imagine generation as optional. Confirmed output impact: Mark 13 _hearts.json had 0 Imagine items.

### Weakened guardrails:
⚠️  **Line 89 — language softened:**
> Committed: "Output MUST include coverage for all scenes"
> Current: "Output should include coverage for all scenes"
**Risk:** "Should" is advisory; model may skip scenes under token pressure.

### Added guardrails:
✅ Line 612: New reminder — "every scene must have at least 2 questions" (appears intentional addition)
```

**Critical rule:** A removed guardrail is always CRITICAL severity — these are the constraints that prevent known failure modes. If guardrail was removed AND bad output was observed, report the confirmed causal link.

### Step 7: Detect AI-Generated Examples (CRITICAL - #1 SOURCE OF PROBLEMS)

**Purpose:** LLMs create examples that don't match user intent and obscure understanding. Any new examples since last commit must be surfaced.

**Core Principle:** Nothing produced by an LLM can ever be used as training data in prompts. At best, AI can propose examples for user approval. Often, the user must write examples themselves. See "Core Principle: No LLM-Generated Training Data" above.

**Process:**
1. **Get last committed version of the prompt:**
   ```bash
   git show main:[relative-path-to-prompt].gpt > /tmp/last-committed.gpt
   # If that fails, try HEAD or dev
   ```

2. **Extract examples from both versions:**
   ```bash
   # Current version
   grep -n "^.*\(Example\|✅\|❌\|TODO\)" [prompt].gpt > /tmp/current-examples.txt

   # Last committed version
   grep -n "^.*\(Example\|✅\|❌\|TODO\)" /tmp/last-committed.gpt > /tmp/committed-examples.txt
   ```

3. **Compare line-by-line:**
   - Look for new example blocks (✅/❌ pairs)
   - Look for removed TODOs that now have examples
   - Look for changed example text

4. **Flag suspected AI additions:**
   - New examples that weren't in last commit
   - TODOs replaced by examples
   - Examples that don't match the documentation style

**What to report:**
```markdown
## ⚠️ NEW EXAMPLES DETECTED SINCE LAST COMMIT

**Lines 45-52: New Notice example added**
```
✅ "What does John eat in the wilderness?" (third person)
❌ "What might the crowd have thought..." (speculation)
```
**Status:** Not in last commit - likely AI-generated
**Action needed:** Review whether this matches intended pattern

**Lines 103-110: TODO replaced with example**
```
**TODO:** Add example for Jesus' response
[NOW REPLACED WITH:]
✅ "What does Jesus say?" (correct)
❌ "What do you notice about Jesus?" (reader-focused - wrong)
```
**Status:** Example may not match TODO intent
**Action needed:** Verify this is what you wanted
```

**Red flags:**
- 3+ new examples added
- Examples appear in sections that previously had TODOs
- Example content uses vague language ("something important", "key themes")
- Examples contradict the prompt's own rules

**Critical rule:** If ANY new examples are detected, they must be explicitly listed in the audit report with:
- Exact line numbers
- The example text
- Status (new/replaced TODO/modified)
- Warning that user must verify

### Step 8: Check JSON Output Format (CRITICAL - for JSON Prompts Only)

**Purpose:** Verify prompts that produce JSON have explicit formatting rules to prevent intermittent parse errors (delimiter issues, unescaped quotes, malformed structure).

**When to run this check:**
- Prompt frontmatter has `format: json`, OR
- OUTPUT SCHEMA section contains JSON structure (detect via `{` or `[` after header), OR
- Pipeline config specifies `output_type: json` for this step

**Skip if:** Prompt produces plain text, markdown, or other non-JSON formats

#### Check 1: Code Fences in OUTPUT SCHEMA ❌

**Problem:** Code fences (` ```json ``` `) confuse the LLM into treating output as markdown-embedded JSON rather than pure JSON.

**Detection:**
```bash
# Find OUTPUT SCHEMA section, check next 100 lines for code fences
awk '/^# OUTPUT SCHEMA/,/^# [A-Z]/' [prompt].gpt | grep -n '```json'
```

**Red flag:** Any ` ```json ``` ` wrapper in OUTPUT SCHEMA section
**Fix recommendation:** Remove fences from OUTPUT SCHEMA; examples can keep them

#### Check 2: Explicit JSON Formatting Rules ✅

**Problem:** Missing formatting guidance leads to intermittent parse failures (unescaped quotes, trailing commas, delimiter errors).

**Detection:**
```bash
# Look for formatting requirements near OUTPUT SCHEMA
grep -A 30 "^# OUTPUT SCHEMA" [prompt].gpt | \
  grep -c "CRITICAL.*JSON\|JSON Formatting Requirements\|Return valid JSON"
```

**Must include:**
- "Return valid JSON only. No markdown, no code fences, no commentary"
- Escape double quotes inside strings: `\"He said \\\"yes\\\"\"`
- Apostrophes in strings need no escaping: `\"Jesus' disciples\"`
- Commas between array elements and object properties
- No trailing commas
- No comments

**Red flag:** No formatting rules section before/after OUTPUT SCHEMA
**Yellow flag:** Formatting rules present but incomplete (missing escaping guidance)

**Standard template to recommend:**
```markdown
CRITICAL: Return valid JSON only. No markdown, no code fences, no commentary.

JSON Formatting Requirements:
- Use double quotes for all keys and string values
- Escape double quotes inside strings: "He said \\"yes\\""
- Apostrophes in strings need no escaping: "Jesus' disciples"
- Commas between array elements and object properties
- No trailing commas
- No comments
```

#### Check 3: Incorrect Escaping Examples ❌

**Problem:** Examples showing apostrophe escaping (wrong in double-quoted JSON strings) teach the LLM incorrect patterns.

**Detection:**
```bash
# Look for incorrect apostrophe escaping in examples
grep -n "\\\\\\\\'\\|\\\\\"" [prompt].gpt | \
  grep -v "He said\\\\\|she said\\\\\|they said"
# Matches patterns like "Jesus\\'" or "John\\'s"
```

**Wrong:** `"Jesus\\' instructions"` or `"John\\'s identity"`
**Right:** `"Jesus' disciples"` and `"John\\\"s identity"` (only inner quotes need escaping)

**Red flag:** Examples showing apostrophe escaping in JSON strings
**Fix recommendation:** Replace with correct examples showing only double-quote escaping

#### Check 4: Consistency Across JSON Prompts

**Problem:** If project has multiple JSON-producing prompts, formatting guidance should be word-for-word identical to avoid confusion.

**Detection:**
```bash
# Extract formatting rules from all .gpt files in project
for f in prompts/*.gpt; do
  if grep -q "^# OUTPUT SCHEMA" "$f" && grep -q "{\\|\\[" "$f"; then
    echo "=== $f ==="
    awk '/JSON Formatting Requirements/,/^$/' "$f" || \
    awk '/CRITICAL.*Return valid JSON/,/^$/' "$f"
  fi
done
```

**Check:**
1. Count JSON-producing prompts in project
2. Extract formatting rules from each
3. Compare for consistency

**Red flag:** Different wording, different rules, or some prompts missing rules entirely
**Yellow flag:** Rules present but vary slightly in coverage

**What to report:**
```markdown
**JSON Prompts in this project:**
- segment-book.gpt: ❌ No formatting rules (4 code fences detected)
- segments.gpt: ⚠️  Has formatting rules BUT 4 code fences in OUTPUT SCHEMA
- subdivide-pericope.gpt: ❌ No formatting rules
- generate-context.gpt: ✅ Complete formatting rules, no code fences
- summarize.gpt: ❌ No formatting rules

**Consistency:** 1 of 5 prompts has correct guidance
**Risk:** HIGH (4 prompts missing critical formatting rules)
```

#### Real-World Impact Example

**Observed failures** (from discourse-flow):
```
Mark segmentation: JSON parse failed: Expecting ',' delimiter at position 9450
John segment generation: JSON parse failed: Expecting ',' delimiter at position 2722
6 other books succeeded with identical prompts (intermittent failures)
```

**Root causes found:**
- All 5 prompts had ` ```json ``` ` code fences in OUTPUT SCHEMA
- Only 1 of 5 had formatting rules (and example was wrong)
- Intermittent because LLM sometimes follows fences literally, sometimes ignores them

**After fixes:**
- Removed all code fences from OUTPUT SCHEMA sections
- Added identical formatting rules to all 5 prompts
- Mark and John runs succeeded on retry

An audit with this check would have flagged:
```
⚠️  segment-book.gpt: 4 code fences, 0 formatting rules
⚠️  segments.gpt: 4 code fences, incorrect apostrophe example
⚠️  5 of 5 JSON prompts inconsistent
Risk Level: HIGH (intermittent JSON parse failures likely)
```

### Step 9: Check Pipeline Structured Outputs Usage (CRITICAL - for Pipeline YAML Files)

**Purpose:** Detect JSON-producing steps without `response_format`, which causes 40-60% intermittent failure rates. Using `response_format` with `json_schema` guarantees 100% valid JSON from the LLM.

**When to run this check:**
- User asks to audit a pipeline file (`.yaml`)
- User mentions JSON parse failures or reliability issues
- Audit is run on a directory containing both prompts and pipelines

**Skip if:** Auditing only `.gpt` files, no pipeline context

#### Check 1: Find JSON-Producing Steps

**Detection:**
```bash
# Find all LLM steps with output_type: json
grep -n "output_type: json" [pipeline].yaml
```

**For each match**, extract the step name and check if `response_format` is present in that step's config.

#### Check 2: Verify response_format Usage

For each JSON step found in Check 1:

**Check A: Has response_format parameter?**
```bash
# Get line number of output_type: json
json_line=$(grep -n "output_type: json" [pipeline].yaml | cut -d: -f1 | head -1)

# Check if response_format appears within next 20 lines (same step)
awk "NR==$json_line,NR==$json_line+20" [pipeline].yaml | grep -q "response_format:"
```

**Check B: Uses json_schema mode (not just json_object)?**
```bash
# If response_format found, verify it uses json_schema (structured mode)
awk "NR==$json_line,NR==$json_line+30" [pipeline].yaml | grep -A 2 "response_format:" | grep -q "type: json_schema"
```

**Check C: Model supports structured outputs?**
```bash
# Extract model from step or global llm_config
model=$(awk "NR==$json_line,NR==$json_line+20" [pipeline].yaml | grep "model:" | head -1 | awk '{print $2}')

# Verify model is gpt-4o-2024-08-06 or later (not gpt-4.1)
echo "$model" | grep -qE "gpt-4o-2024-08-06|gpt-4o-mini-2024"
```

#### What to Report

**For steps WITHOUT response_format:**
```markdown
🚨 **MISSING STRUCTURED OUTPUTS**

**Step:** `segment_chunk` (line 45)
**Problem:** Uses `output_type: json` without `response_format`
**Risk:** 40-60% intermittent JSON parse failures (missing commas, unescaped quotes)
**Impact:** Wasted retries (3 attempts × cost), unpredictable failures

**Recommended fix:**
```yaml
- name: segment_chunk
  type: llm
  model: gpt-4o-2024-08-06  # MUST be 2024-08-06 or later
  output_type: json
  response_format:
    type: json_schema
    json_schema:
      name: book_segmentation
      strict: true
      schema:
        type: object
        properties:
          book: {type: string}
          pericopes:
            type: array
            items:
              type: object
              properties:
                title: {type: string}
                passage: {type: string}
              required: ["title", "passage"]
              additionalProperties: false
        required: ["book", "pericopes"]
        additionalProperties: false
```

**Benefits:**
- ✅ 100% valid JSON (no parse errors)
- ✅ No retry waste
- ✅ Guaranteed schema compliance
- ✅ Eliminates manual JSON formatting rules in prompts
```

**For steps WITH response_format but using json_object mode:**
```markdown
⚠️  **BASIC JSON MODE (Not Structured)**

**Step:** `analyze_text` (line 123)
**Current:** Uses `response_format: {type: json_object}`
**Problem:** Forces JSON output but NO schema enforcement
**Risk:** LLM can add unexpected fields, miss required fields

**Recommendation:** Upgrade to `json_schema` mode for production use
```

**For steps WITH json_schema but incorrect model:**
```markdown
❌ **WRONG MODEL FOR STRUCTURED OUTPUTS**

**Step:** `extract_data` (line 200)
**Model:** `gpt-4.1`
**Problem:** GPT-4.1 uses Responses API (different structured output mechanism)
**Fix:** Change to `gpt-4o-2024-08-06` or later
```

#### Summary Stats

Report project-wide JSON reliability status:

```markdown
**Pipeline JSON Reliability Audit**

**JSON-producing steps:** 5
**Using structured outputs (`json_schema`):** 1 (20%)
**Using basic JSON mode (`json_object`):** 1 (20%)
**NO `response_format` (legacy/unreliable):** 3 (60%)

**Steps needing upgrade:**
1. Line 45: `segment_chunk` — add `response_format` + schema
2. Line 89: `generate_details` — add `response_format` + schema
3. Line 134: `create_summary` — add `response_format` + schema

**Risk Level:** HIGH
- 3 of 5 JSON steps rely on prompt-based formatting (40-60% failure rate observed)
- Estimated retry waste: ~$150-200 per failed run (from issue #95)
- Recommendation: Implement structured outputs on all JSON steps

**Documentation:** See docs/llmflow-language.md "Structured JSON Output" section
```

### Step 10: Generate Report

Provide:

**Summary:**
- Prompt name and size (lines, headers, TODOs)
- Complexity category (Simple/Medium/Complex/Very Complex)
- Overall assessment (Well-organized / Needs attention / Sprawling)

**Convention Compliance:**
- Checklist of standard sections (present/missing/wrong order)
- Heading hierarchy issues (specific line numbers)
- Task section organization (data sources, rules, examples co-located or scattered?)

**Input Data Grounding:** (CRITICAL)
- For each output field, verify DATA SOURCES specifies where to find it
- Flag any fields where LLM must "make things up"
- Grade: Full grounding / Partial grounding / Ungrounded

**Example Diversity:** (CRITICAL)
- Count distinct passages referenced in examples
- Check for variety across narrative types
- Grade: Good diversity / Limited diversity / Single-passage examples

**AI-Generated Examples:** (CRITICAL - #1 SOURCE OF PROBLEMS)
- Compare with last committed version
- List ANY new or modified examples with line numbers
- Flag replaced TODOs or new example blocks
- User MUST review all detected changes

**JSON Output Format:** (CRITICAL - for JSON prompts only)
- Code fences in OUTPUT SCHEMA sections
- Explicit JSON formatting rules present/missing
- Incorrect escaping examples (apostrophe escaping)
- Consistency across multiple JSON prompts in project
- Risk Level: Low / Medium / High / CRITICAL

**Pipeline Structured Outputs:** (CRITICAL - for pipeline YAML files)
- JSON steps without `response_format` (legacy/unreliable approach)
- JSON steps using `json_object` vs `json_schema` mode
- Model compatibility (requires gpt-4o-2024-08-06+, not gpt-4.1)
- Project-wide adoption stats (% using structured outputs)
- Risk Level: Low / Medium / High / CRITICAL

**Specific Findings:**
- List issues with line numbers
- Compare to similar prompts if requested
- Suggest priority improvements

**Example Output Format:**
```
## Audit: bookish-bodies-questions.gpt

**Metrics:**
- Lines: 499 (Complex range)
- Headers: 20 (within Complex range)
- TODOs: 0

**Convention Compliance:**
✅ Has YAML frontmatter (lines 1-13)
✅ Has WHAT THIS PROMPT PRODUCES (line 17-30)
✅ Has OUTPUT FORMAT (line 32-107)
✅ Major tasks organized:
   - NOTICE QUESTIONS (line 111) ✅ has Input/Transformation/Examples subsections
   - IMAGINE QUESTIONS (line 346) ✅ has Input/Transformation/Examples subsections
✅ Has COVERAGE & QUALITY CHECKLIST (line 516)
✅ Has INPUT DATA (line 553)
✅ Has CRITICAL REMINDERS (line 572)
⚠️  Task sections could consolidate rules better (some rules scattered in examples)
✅ Heading hierarchy consistent: # for major sections, ## for subsections

**Input Data Grounding:**
✅ OUTPUT SCHEMA fields mapped to DATA SOURCES
   - `question` → generated from text evidence
   - `perspective_actor` → from perspectives input
   - `grounding_type` → from sensory_inventory.modality
   - `text_evidence` → from verses.sensory_inventory[]
   - `arc_drivers` → from scenes.structural_features[]
⚠️  Missing explicit source for `arc_drivers` field (line 242)
   - Prompt says "why this detail matters" but doesn't point to specific input field
   - RISK: LLM may fabricate narrative significance
**Grade:** Partial grounding (1 field unmapped)

**Example Diversity:**
✅ Examples from multiple passages:
   - Mark 12:13-17 (Pharisees trap) - lines 55-90
   - Mark 1:1-13 (John baptizing) - lines 292-310, 363-375
📊 2 distinct passages, both from Mark (confrontation + wilderness)
⚠️  Could benefit from: teaching passage, healing, parable
**Grade:** Limited diversity (2 passages, same book)

**⚠️  AI-GENERATED EXAMPLES DETECTED:**

🚨 **Lines 292-300: New Notice examples (NOT in last commit)**
```
✅ "What does John eat in the wilderness?" (third person)
✅ "What do the people do as they come to the river?" (third person)
❌ "What do you notice happening at the river?" (addresses participant with "you")
❌ "What might the crowd have thought about John's clothing?" (modal verb speculation)
```
**Status:** These 4 examples were NOT in committed version
**Problem:** Example 1 "What does John eat?" asks about observable detail (Bodies)
          but the question is too specific - may not generalize to other passages
**Action:** USER MUST REVIEW - do these match Bodies question principles?

🚨 **Lines 363-375: Background rules example changed**
```
[COMMITTED VERSION - line 363:]
❌ "Background tells the answer" → ✅ "Background provides context"

[CURRENT VERSION - lines 363-375:]
❌ BLOCKER: Background: "Locusts and wild honey were wilderness foods..."
   Question: "What does John eat?"
✅ CORRECT: Background: "Camel hair clothing marked ascetics..."
   Questions: "What does clothing signal?" / "How does appearance connect?"
```
**Status:** Entirely new example content
**Problem:** The ✅ "correct" example asks about SIGNALING and CONNECTING - these are
          Hearts questions (meaning/significance), NOT Bodies questions (observables)
**CRITICAL:** This example CONTRADICTS the prompt's own Bodies definition
**Action:** USER MUST REVIEW IMMEDIATELY - this teaches the wrong pattern

**Summary:** 2 new example blocks detected totaling 12 example items
**Risk Level:** HIGH - one example contradicts core prompt principles

**JSON Output Format:** (segment-book.gpt produces JSON)
⚠️  **Code fences in OUTPUT SCHEMA (lines 42, 98, 105, 112)**
```
Found 4 instances of ```json``` wrapper in OUTPUT SCHEMA section:
- Line 42: ```json wrapped around full schema
- Lines 98, 105, 112: individual field schemas wrapped
```
**Problem:** Confuses LLM into markdown mode → intermittent JSON parse failures
**Recommendation:** Remove all code fences from OUTPUT SCHEMA section

❌ **No JSON formatting rules**
```
OUTPUT SCHEMA section (lines 32-115) has no CRITICAL formatting guidance
Missing required rules:
- "Return valid JSON only. No markdown, no code fences"
- Escape double quotes: "He said \\"yes\\""
- Apostrophes need no escaping: "Jesus' disciples"
- No trailing commas
```
**Risk:** Intermittent delimiter errors, unescaped quotes, malformed JSON
**Observed:** Mark segmentation failed with "Expecting ',' delimiter at position 9450"

⚠️  **Inconsistent with other JSON prompts in project**
```
JSON prompts in discourse-flow:
- segment-book.gpt: ❌ No formatting rules (4 code fences)
- segments.gpt: ⚠️  Has rules BUT 4 code fences remain
- subdivide-pericope.gpt: ❌ No formatting rules
- generate-details.gpt: ❌ No formatting rules
- context-summary.gpt: ❌ No formatting rules
```
**Consistency:** 0 of 5 prompts have correct guidance (1 has partial rules)
**Recommendation:** Add identical JSON Formatting Requirements section to all 5 prompts

**Risk Level:** HIGH
- Intermittent parse failures observed in production (Mark, John)
- 4 of 5 prompts completely missing formatting guidance
- Code fences present in all OUTPUT SCHEMA sections
- Risk of wasted compute on retry attempts (3x before failure)

**Sprawl Indicators:**
- Yellow flag: Near 500-line threshold
- Yellow flag: Examples in 2 sections (lines 47-90 and later inline)

**Comparison to bookish-hearts-questions.gpt:**
- Hearts: 603 lines, follows task-focused organization pattern
- Bodies: 499 lines, similar structure but some differences
- Both use # for major task sections (NOTICE, IMAGINE)
- Both co-locate data sources, rules, examples within task sections
- Hearts has more complete subsection structure (Input/Transformation/Examples clearly labeled)

**Recommendations:**
1. 🚨 URGENT: Review AI-generated examples (lines 292-300, 363-375) - one contradicts principles
2. Map `arc_drivers` field to specific input data source (currently ungrounded)
3. Add examples from non-Mark passages (teaching, healing, parable types)
4. Consider consolidating scattered rule statements into Transformation Rules subsections
5. Verify all task sections follow Input→Transformation→Examples→Rules pattern

**Priority:** HIGH (example contradiction + ungrounded field)
```

## Comparison Mode

When user asks to compare multiple prompts:
1. Run same analysis on each
2. Create comparison table showing:
   - Lines, headers, TODOs
   - Section structure differences
   - Heading level patterns
   - Example organization approach
3. Identify which follows convention best
4. Suggest which to use as template for others

## Output

Provide structured report with:
- Clear sections (Summary, Compliance, Findings, Recommendations)
- Specific line numbers for all issues
- Priority assessment (Low/Medium/High)
- Actionable next steps

**Don't:**
- Make changes to files (read-only audit)
- Rewrite sections (suggest, don't implement)
- Create new files except for audit reports if explicitly requested

## Example Invocations

**Single prompt audit:**
```
User: "Audit bookish-bodies-questions.gpt"
Agent: [Runs workflow, generates report above]
```

**Convention check:**
```
User: "Does bookish-intro.gpt follow the prompt convention?"
Agent: [Loads convention, checks compliance, reports findings]
```

**Comparison:**
```
User: "Is bodies organized the same way as hearts?"
Agent: [Compares both, highlights differences, suggests alignment]
```

**Bulk audit:**
```
User: "Which bookish-*.gpt prompts need reorganization?"
Agent: [Scans all, categorizes by compliance level, priorities for reorg]
```

## Success Criteria

A successful audit:
1. Reads convention document first
2. Provides specific line numbers for findings
3. Explains WHY something is an issue (based on convention)
4. Gives clear priority guidance
5. Suggests concrete next steps
6. Does NOT make changes (respects read-only nature)

## Edge Cases

**Very large prompts (> 1000 lines):**
- Note as extreme outlier
- Suggest considering split into sub-prompts
- Example: leadersguide-summary.gpt (61K lines)

**Legacy prompts (exegetical-*, narrative-*, rd-*):**
- Note they may have genre-specific structure needs
- Compare within their family (all exegetical-* together)
- Be lenient about strict convention compliance

**Actively changing prompts:**
- Note any TODOs as "work in progress"
- Check if recent commits show reorganization effort

## Related Documents

- `docs/prompt-organization-convention.md` — The convention definition
- `docs/safe-llm-change-workflow.md` — Process for modifying prompts safely
- `.github/copilot-instructions.md` — General codebase guidelines

## Notes

This is a **workflow skill** that coordinates multiple tools to perform analysis. It does NOT:
- Modify prompts (use other tools for that)
- Test prompt output quality (that's a different audit)
- Debug LLM behavior (use prompt audit results to inform debugging)

The goal is visibility: show the user where prompts stand relative to conventions, not to fix them automatically.
