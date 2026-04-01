# LLMFlow Prompt Organization Convention

**Status:** ACTIVE
**Date:** March 29, 2026
**Last Updated:** April 1, 2026
**Scope:** Global convention for all LLMFlow .gpt prompt files
**Source:** Originated in nida-institute/ears-to-hear repository

> **Note:** This is the global convention used by the audit-prompts skill. Individual repositories can override by providing their own `docs/prompt-organization-convention.md`.

---

## Design Principle

**Prompts are transformations: INPUT DATA → RULES → OUTPUT DATA**

The organization should make this transformation **verifiable**: given this input, did we get this output following these rules?

This means:
1. **Input data grounding is explicit** — for every output field, we document where to find it in the input
2. **Rules are co-located** — everything about Notice questions is in the Notice section, everything about Imagine is in Imagine section
3. **Examples show complete transformations** — input → transformation steps → output (with TODOs for manual writing)
4. **Anti-patterns are concrete** — show what NOT to do with actual examples

---

## Standard Structure for Transformation-Heavy Prompts

Use this structure for prompts that transform structured JSON input into structured JSON output following complex rules (e.g., hearts-questions, bodies-questions, connecting-questions).

---

## The 8-Section Pattern

### 1. YAML Frontmatter
```yaml
---
prompt:
  requires: [passage_ref, scenes, verses]
  optional: [perspectives]
  format: JSON
  description: >-
    One-line description of what this prompt does
---
```

### 2. VARIABLES Section (if applicable)
```markdown
# VARIABLES

- `{{var1}}` — description
- `{{var2}}` — description
```

### 3. SYSTEM ROLE
```markdown
# SYSTEM ROLE

You are generating the [X] section of...
[High-level purpose and philosophy]
```

### 4. CORE PRINCIPLES
```markdown
# CORE PRINCIPLES

## Principle 1: [Name]
[Explanation with ✅/❌ examples if simple]

## Principle 2: [Name]
[Explanation]
```

### 5. EXAMPLES (Consolidated)
```markdown
# EXAMPLES

## Example 1: [Name]
**Based on this input data:**
[Show actual data structure]

**Demonstrate:**
[What this example teaches]

[Show transformation with ✅/❌]

## Example 2: [Name]
[Same pattern]

---
TODO sections for examples that need manual writing
```

### 6. DATA SOURCES
```markdown
# DATA SOURCES

## Input Source 1 (from file.json)
- **Source:** path
- **Pipeline variable:** `${var}`
- **Key fields:**
  - field1: description
  - field2: description

## Input Source 2
[Same pattern]
```

### 7. INPUT DATA (Template Variables)
```markdown
# INPUT DATA

### Source 1
\```
{{var1}}
\```

### Source 2
\```
{{var2}}
\```
```

### 8. OUTPUT SCHEMA
```markdown
# OUTPUT SCHEMA

Output a single valid JSON object. No markdown fences, no commentary before or after.

**Schema definition with example:**
\```json
{
  "field": "value"
}
\```

## Field Rules
- field1: description
- field2: description
```

**Note:** The example above shows JSON in fences for documentation purposes. In actual prompts, the "No markdown fences" instruction should appear immediately before the example, and the Guardrails section should reinforce it.

### 9. DOMAIN-SPECIFIC RULES
```markdown
# [DOMAIN] RULES

## Major Rule Category 1
[Explanation with examples]

## Major Rule Category 2
[Explanation with examples]
```

For example:
- "NOTICE VS. IMAGINE" (hearts/bodies)
- "COVERAGE & QUALITY RULES"
- "QUESTION STRUCTURE"

### 10. QUALITY CONTROLS & CONSTRAINTS

**Purpose:** Define what blocks LLM output from being valid. This section prevents common failure modes specific to your domain.

**Section naming:** Choose the term that fits your domain:
- `# GUARDRAILS` — generic (data transformation, general tasks)
- `# EVIDENCE DOCUMENTATION REQUIREMENTS` — scholarly/linguistic analysis requiring citations
- `# VALIDATION RULES` — data processing, schema compliance
- `# COMPLIANCE REQUIREMENTS` — regulatory, safety-critical domains
- `# OUTPUT CONSTRAINTS` — rendering, formatting tasks

**Required characteristics:**
1. **Appears near the end** — After transformation rules, before or alongside OUTPUT SCHEMA
2. **Uses ❌/✅ pattern** — Show violations and correct forms concretely
3. **Blocks escape hatches** — Prevent vague AI output specific to your domain
4. **Verifiable** — Each constraint must be checkable (either programmatically or by human audit)

**Generic template:**
```markdown
# GUARDRAILS  # Or domain-specific alternative from list above

## Critical Blockers

### 1. [Blocker Name]
[Explanation of why this matters]

❌ **BLOCKER:** [concrete example of violation]
✅ **CORRECT:** [concrete example of valid output]

### 2. [Blocker Name]
[Same pattern]

## Output Requirements
- Output format requirements (e.g., "JSON only, no markdown fences")
- Validation rules
- Error handling expectations
```

**Domain-specific example (linguistic analysis):**
```markdown
# EVIDENCE DOCUMENTATION REQUIREMENTS

## PROHIBITED: Vague Language Without Grounding

**DO NOT USE** these phrases without specific linguistic citations:
- ❌ "thematic shift"
- ❌ "new section"
- ❌ "rhetorical transition"

These are **escape hatches** — vague descriptions that cannot be verified.

## REQUIRED: Source Text Quoting

Every claim MUST quote Greek/Hebrew text:

**Template:** `"Feature-Type: 'source-text' (location) explanation"`

**Valid examples:**
- ✅ `"Vocative: 'τεκνία' (2:1) opens new unit"`
- ✅ `"Asyndeton: 'Θαυμάζω ὅτι' (1:6) marks abrupt shift"`

**Invalid:**
- ❌ `"Vocative at 2:1"` — missing quote
- ❌ `"New section begins"` — escape hatch phrase
```

**What stays consistent across all variants:**
- Placement near end of prompt
- ❌/✅ pattern for showing violations
- Focus on blocking vague/wrong/unverifiable output
- Concrete examples

**What becomes flexible:**
- Section name (matches domain terminology)
- Specific prohibitions (domain-specific escape hatches)
- Citation format requirements (domain-appropriate verification)

### 11. VALIDATION CHECKLIST (if needed)
```markdown
# FINAL VALIDATION CHECKLIST

Before returning output:
- [ ] Check 1
- [ ] Check 2
- [ ] Check 3
```

---

## Section Hierarchy Convention

Use consistent heading levels:
- `#` = Major sections (VARIABLES, SYSTEM ROLE, DATA SOURCES, OUTPUT SCHEMA, QUALITY CONTROLS)
- `##` = Subsections within major sections
- `###` = Fine-grained details within subsections
- Use `**bold**` for inline emphasis, not additional heading levels

**Note:** "QUALITY CONTROLS" is the generic term; use domain-specific alternatives like GUARDRAILS, EVIDENCE DOCUMENTATION REQUIREMENTS, VALIDATION RULES, etc. as appropriate.

**Avoid:**
- `####` (too granular — use bold or lists instead)
- Skipping levels (# → ### without ##)
- Mixing emoji in headers inconsistently

---

## Guideline: Examples vs. Quality Controls

**EXAMPLES section:**
- Show how to do it RIGHT
- Demonstrate transformations
- Use ✅/❌ to show good/bad
- Use actual data from representative passages
- Keep examples TOGETHER in one section for easy reference

**QUALITY CONTROLS section (GUARDRAILS, EVIDENCE REQUIREMENTS, etc.):**
- Show what BLOCKS usage
- Explain violations clearly
- Use ❌ **BLOCKER** to mark critical issues
- Keep controls TOGETHER at end of prompt

**Don't mix:** Examples scattered throughout make prompts hard to navigate.

---

## Length Guidelines

Target ranges by prompt complexity:

### Simple prompts (< 200 lines)
- Consolidation step (bookish-connecting.gpt: 122 lines)
- Perspective analysis (bookish-perspectives.gpt: 139 lines)
- Should have < 15 headers

### Medium prompts (200-300 lines)
- Enrichment step (bookish-intro.gpt: 298 lines)
- Should have 15-25 headers

### Complex prompts (300-500 lines)
- Question generation with extensive guardrails (bodies/hearts: ~500 lines)
- Should have 25-35 headers
- Consider splitting if > 500 lines or > 35 headers

### Warning signs of sprawl:
- More than 35 headers
- Long blocks of text repeated with variations
- Examples scattered across multiple sections
- Difficult to find specific rules

---

## When to Split a Prompt

Consider splitting when:
1. Prompt exceeds 500 lines
2. Two distinct sub-tasks are mixed (e.g., analysis + rendering)
3. Examples and guardrails become longer than core instructions
4. Different personas needed (e.g., analyst vs. writer)

**Don't split just because:** A 500-line prompt with clear organization is better than two 250-line prompts with duplicated context.

---

## Migration Strategy

### Phase 1: Document (CURRENT)
- Create this convention document
- Get feedback from team

### Phase 2: Pilot
- Apply to one sprawling prompt (e.g., bookish-hearts-questions.gpt)
- Verify output quality maintained
- Note any issues

### Phase 3: Rollout
- Apply gradually to other prompts
- Prioritize active prompts with known sprawl
- Skip stable prompts that don't need changes

### Phase 4: Maintain
- Use convention for all new prompts
- Update convention as patterns emerge

---

## Open Questions

1. **Should we enforce maximum line counts?** Or just use as guidelines?
2. **How do we handle legacy prompts?** Reorg only when we need to edit them?
3. **What about genre-specific variations?** (exegetical-*, narrative-*, rd-*)
4. **Examples in TODOs:** Keep TODO placeholders long-term or fill them immediately?
5. **Variable declarations:** Always in separate VARIABLES section vs. inline?

---

## Current Status: Prompts by Complexity

**Simple (< 200 lines):**
- bookish-perspectives.gpt (139 lines) ✅ Well-organized
- bookish-connecting-questions.gpt (146 lines)
- bookish-connecting.gpt (122 lines)
- bookish-scene-outline.gpt (117 lines)
- bookish-frameworks.gpt (142 lines)
- bookish-book-summary.gpt (143 lines)

**Medium (200-300 lines):**
- bookish-intro.gpt (298 lines)
- bookish-hearts.gpt (201 lines)
- bookish-scene-adjudicate.gpt (178 lines)
- bookish-bodies.gpt (152 lines)

**Complex (300-500 lines):**
- bookish-hearts-questions.gpt (503 lines) ⚠️ 33 headers - recently reorganized
- bookish-bodies-questions.gpt (499 lines) ⚠️ 20 headers - needs review

**Very Complex (> 500 lines):**
- leadersguide-summary.gpt (61K) 🚨 Outlier - investigate

---

## Comparison: Hearts vs. Bodies Organization

### Hearts (after reorg)
```
# VARIABLES
# SYSTEM ROLE
# CORE PRINCIPLE: Direct Transformation
## EXAMPLES NEEDED (6 major TODOs)
# QUESTION STRUCTURE: Open First, Then Guiding
# DATA SOURCES
## verses, scenes, perspectives
# INPUT DATA
# OUTPUT SCHEMA
## Field Rules
# NOTICE VS. IMAGINE
## Notice, Imagine, Blocker: Duplication
# COVERAGE & QUALITY RULES
## Priority, Per Scene, Quality Test, Natural English
# GUARDRAILS
## Critical Blockers (4 subsections)
## Output Requirements
## Validation Checklist
```

### Bodies (current)
```
System: [role]
## MANDATORY PATTERN: Open Question First
## FROM DATA TO QUESTIONS: Direct Transformation
### Example 1
### Example 2
[long example section]
## Data Sources
### verses, scenes, perspectives
## Input data
## Output schema
### Field rules
### Question ordering strategy
## Notice vs. Imagine
## Coverage rules
## Guardrails
### Background guardrails
### No predetermined conclusions
```

**Key differences:**
- Hearts uses `#` for major sections, Bodies uses `##`
- Hearts has VARIABLES section, Bodies doesn't (but could use it)
- Hearts consolidates EXAMPLES separately, Bodies intersperses them
- Hearts has explicit CORE PRINCIPLE section
- Bodies has "System:" prefix that Hearts removed

**Recommendation:** Align Bodies to Hearts structure pattern.
