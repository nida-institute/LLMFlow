# Global Conventions & Skills

**Status:** Available in LLMFlow 0.2.1.07+

## Overview

LLMFlow provides a globally-shared convention for organizing `.gpt` prompt files and a read-only audit skill to check compliance. These resources are automatically installed to `~/.sp/` when you run `sp init` and are available across all LLMFlow projects.

## What's Included

### 1. Prompt Organization Convention

**Location:** `~/.sp/conventions/llmflow-prompt-organization.md`

A standard structure for transformation-heavy prompts that enforces:
- **Verifiable transformations** — explicit mapping from input fields to output fields
- **Co-located knowledge** — all rules, examples, and data sources grouped by task
- **Consistent heading hierarchy** — `#` for major sections, `##` for subsections
- **Length guidelines** — sprawl indicators with complexity categories
- **Flexible quality controls** — domain-specific naming (GUARDRAILS, EVIDENCE DOCUMENTATION REQUIREMENTS, etc.)

**Key sections:**
1. YAML Frontmatter
2. WHAT THIS PROMPT PRODUCES
3. OUTPUT FORMAT
4. [TASK 1] with Input/Transformation/Examples/Rules subsections
5. [TASK 2] (if applicable)
6. COVERAGE & QUALITY CHECKLIST
7. INPUT DATA (template variables)
8. QUALITY CONTROLS & CONSTRAINTS (or domain-specific alternative)

### 2. Audit Prompts Skill

**Location:** `~/.sp/skills/audit-prompts/SKILL.md`

A workflow skill for VS Code Copilot that audits `.gpt` files for:
- Convention compliance (section structure, heading hierarchy)
- Sprawl detection (line/header counts, complexity category)
- **Input data grounding** — verifies every output field has documented input source
- **Example diversity** — checks examples generalize across passages
- **AI-generated examples** — compares to last commit, flags new examples

**Invocation:**
```
@audit-prompts Check prompts/my-prompt.gpt
```

## Installation

### Automatic (Recommended)

Run `sp init` in any directory:

```bash
sp init
```

This automatically:
- Creates `~/.sp/conventions/` with the convention and README
- Creates `~/.sp/skills/audit-prompts/` with the skill file
- Logs what was installed

### Manual Installation

If you need to reinstall or update:

```bash
# The convention and skill are bundled with LLMFlow
# They're copied from the installed package to ~/.sp/
# Just run sp init again to update
sp init --update
```

## Using the Convention

### In New Prompts

When creating a new `.gpt` file, follow the standard structure:

```markdown
---
prompt:
  requires: [passage_ref, verses]
  optional: [perspectives]
  format: JSON
  description: Generate questions from passage
---

# WHAT THIS PROMPT PRODUCES

You are generating discussion questions...

# OUTPUT FORMAT

Output a single JSON object with...

# NOTICE QUESTIONS

## Input: Where to Find the Data
- Questions derive from `verses[].sensory_inventory[]`
- Focus on observable details

## Transformation Rules
✅ Third-person phrasing: "What does X do?"
❌ Reader-focused: "What do you notice?"

## Examples: Input → Transformation → Output
[Show complete transformations with TODOs for manual writing]

# COVERAGE & QUALITY CHECKLIST

Before returning output:
- [ ] At least 3 questions per scene
- [ ] Questions cite specific text evidence

# INPUT DATA

\`\`\`
{{verses}}
\`\`\`

# CRITICAL REMINDERS

Output ONLY the JSON object. No markdown fences.
```

### For Existing Prompts

Use the audit skill to check compliance:

```
@audit-prompts Check prompts/my-existing-prompt.gpt against the convention
```

The skill will report:
- Missing or misordered sections
- Heading hierarchy issues
- Ungrounded output fields (no documented input source)
- Example diversity problems
- AI-generated content that needs review

## Project-Specific Overrides

To customize the convention for your project, create:

**`docs/prompt-organization-convention.md`**

The audit skill checks for this file first and uses it instead of the global convention if present.

**Example override:**

```markdown
# Project-Specific Prompt Convention

This project follows the global LLMFlow convention with these additions:

## Domain-Specific Requirements

### Linguistic Analysis Prompts

Use `# EVIDENCE DOCUMENTATION REQUIREMENTS` instead of `# GUARDRAILS`.

All claims must quote source text:
- ✅ `"Vocative: 'τεκνία' (2:1) opens new unit"`
- ❌ `"Vocative at 2:1"` (missing quote)

### [Other project-specific rules]
```

## Convention Highlights

### Input Data Grounding (Critical)

**Problem:** LLMs make things up when not constrained by input data.

**Solution:** For every output field, document where to find it in the input.

**Example:**

```markdown
# DATA SOURCES

## verses (from pipeline)
- `text_evidence` → from `verses[].sensory_inventory[].description`
- `arc_drivers` → from `scenes[].structural_features[]`
```

If an output field has no documented data source, the audit skill flags it as **ungrounded** (high risk for hallucination).

### Example Diversity (Critical)

**Problem:** Using only one passage trains the LLM on specifics rather than patterns.

**Solution:** Include examples from multiple passages and narrative types.

**Example:**

```markdown
## Example 1: Confrontation (Mark 12:13-17)
[Pharisees trap]

## Example 2: Wilderness (Mark 1:1-13)
[John baptizing]

## Example 3: Teaching (Matthew 5:1-12)
[Beatitudes]
```

The audit skill checks for passage diversity and recommends adding examples from different books/types.

### AI-Generated Examples (Critical - #1 Source of Problems)

**Absolute Rule:** Nothing produced by an LLM can be used as training data in prompts.

**Why:** LLM output doesn't match user intent with sufficient precision. Examples must demonstrate the exact pattern you want, which requires human judgment.

**How the audit skill helps:**
- Compares current prompt to last commit
- Flags ANY new or modified examples
- Reports line numbers with status (new/replaced TODO/modified)
- User must review all detected changes

**What to watch for:**
- TODOs that got replaced with examples
- New example blocks that weren't there before
- Examples that contradict the prompt's own rules

## Flexible Quality Controls

The convention supports domain-specific naming for the final quality control section:

**Generic:**
- `# GUARDRAILS` — data transformation, general tasks

**Domain-Specific:**
- `# EVIDENCE DOCUMENTATION REQUIREMENTS` — scholarly/linguistic analysis
- `# VALIDATION RULES` — data processing, schema compliance
- `# COMPLIANCE REQUIREMENTS` — regulatory domains
- `# OUTPUT CONSTRAINTS` — rendering, formatting tasks

**All variants must:**
1. Appear near the end (after transformation rules)
2. Use ❌/✅ pattern to show violations and correct forms
3. Block domain-specific escape hatches (vague AI output)
4. Be verifiable (each constraint must be checkable)

## Complexity Categories

The convention provides length guidelines:

| Category | Lines | Headers | Example |
|----------|-------|---------|---------|
| Simple | < 200 | < 15 | Consolidation step |
| Medium | 200-300 | 15-25 | Enrichment step |
| Complex | 300-500 | 25-35 | Question generation |
| Very Complex | > 500 | > 35 | ⚠️ Consider splitting |

**Warning signs of sprawl:**
- More than 35 headers
- Examples scattered across multiple sections
- Difficult to find specific rules

## Best Practices

### 1. Co-locate related content

Put everything about a task in that task's section:
- Where to find the data (Input subsection)
- How to transform it (Transformation Rules)
- Examples showing the transformation
- Rules specific to this output type

**Don't** scatter rules across the file.

### 2. Write the test first (for examples)

Before writing an example:
1. Pick a passage
2. Show the actual input data
3. Demonstrate the transformation step-by-step
4. Mark sections with TODO if you'll write them manually

This ensures examples are grounded in real data.

### 3. Use TODOs for manual writing

When examples require careful human judgment:

```markdown
## Example 3: Parable (Matthew 13:1-9)

**TODO:** Add sower parable example
- Demonstrates metaphorical language handling
- Shows how to avoid over-literal interpretation
```

The audit skill tracks TODOs. If they get replaced with examples, it flags them for review (likely AI-generated).

### 4. Audit regularly

Run the audit skill:
- Before committing prompt changes
- After prompts exceed 300 lines
- When output quality degrades
- Monthly for stable prompts

### 5. Document data sources early

When creating a prompt, write the DATA SOURCES section first:
- Forces you to think about input → output mapping
- Prevents ungrounded generation later
- Makes the prompt easier to debug

## Related Documentation

- [LLMFlow Language Quickref](llmflow-language-quickref.md) — YAML syntax reference
- [Tutorial](tutorial.md) — Getting started with LLMFlow
- [AI Context Index](ai-context/index.md) — Project-specific AI guidelines

## Updating Conventions

Conventions can be updated with LLMFlow releases. To get the latest:

```bash
sp init --update
```

This regenerates files marked with `<!-- Generated by sp init -->` including global conventions and skills.

**Note:** Your project-specific overrides in `docs/prompt-organization-convention.md` are never touched.

## Contributing Improvements

Have suggestions for the convention? Open an issue or PR at:
https://github.com/nida-institute/LLMFlow/issues

The convention evolves based on real-world prompt engineering experience across multiple projects.

---

**Last Updated:** April 1, 2026
**Version:** LLMFlow 0.2.1.07+
