# AI Context Discoverability: Help AI Find Project Documentation

## Problem Statement

AI assistants working on Scripture Pipeline projects often **don't know what documentation is available** in `docs/ai-context/`. This leads to:

1. **Repeated questions** about conventions already documented
2. **Inefficient context discovery** - AI doesn't know to check for BaseX examples, pipeline patterns, etc.
3. **Inconsistent behavior** - Some AI sessions find context, others don't
4. **User frustration** - "I already documented that in ai-context!"

**Example scenario:**
```
AI: "Do you have BaseX XQuery examples for syntax trees?"
User: "Yes, it's in docs/ai-context/basex-patterns.md"
AI: "Oh, I didn't know that file existed"
```

The AI can't `ls docs/ai-context/` to discover what's available, so it doesn't know what to read.

---

## Current State

**What `sp init` creates:**
```
docs/ai-context/
├── pipeline-quickref.md
├── prompt-contract.md
└── (user adds more over time)
```

**Problem:** AI doesn't know these files exist or when to read them.

---

## Proposed Solutions

### Phase 1: AI Context Index (Quick Win) ⭐

**Implementation:**
1. Add `docs/ai-context/INDEX.md` to `sp init` template
2. Update `.github/copilot-instructions.md` to reference the index
3. Add explicit instruction for AI to check index before asking user

**INDEX.md template:**
```markdown
# AI Context Files Available

This project has documentation for AI assistants in `docs/ai-context/`.

## Core Pipeline Documentation
- **pipeline-quickref.md** - YAML syntax, step types, variable resolution, for-each loops
- **prompt-contract.md** - .gpt file format, requires/provides headers, variable usage

## Data Access
- **data-sources.md** - Biblical dataset locations (BaseX collections, file paths)
- **basex-patterns.md** - XQuery examples for Lowfat syntax trees
- **duckdb-patterns.md** - SQL examples for vocabulary analysis

## Project Conventions
- **naming-conventions.md** - File naming, variable naming, step naming
- **common-patterns.md** - Recurring pipeline structures (participant tracking, discourse analysis)
- **gotchas.md** - Known issues and how to avoid them

## Testing & Quality
- **testing-patterns.md** - How to test pipelines (dry-run, rewind-to, validation)
- **linter-checks.md** - Common linter errors and fixes

---

**📌 IMPORTANT FOR AI ASSISTANTS:**

1. **Check this index FIRST** before asking user about project conventions, data locations, or pipeline syntax
2. **Read relevant files** when working on related tasks (e.g., read basex-patterns.md before writing XQuery)
3. **Suggest updates** if you discover information that should be documented here
4. **Don't guess** - if a file exists here, use it; if not, ask the user

**How to use:**
```
User: "Create a pipeline that queries Greek syntax trees"
AI: [Reads INDEX.md] → [Reads basex-patterns.md] → [Uses documented XQuery patterns]
```
```

**Updated `.github/copilot-instructions.md`:**
```markdown
## AI Context Discovery

This project has AI assistant documentation in `docs/ai-context/`.

**BEFORE asking user about project conventions, data locations, or pipeline patterns:**
1. Read `docs/ai-context/INDEX.md` to see what's documented
2. Read relevant files for your task
3. Only ask user if information is not documented

This saves time and ensures consistency with project practices.
```

**Benefits:**
- ✅ Zero-cost (just documentation)
- ✅ Works immediately (no code changes)
- ✅ AI can navigate from index to specific files
- ✅ User can customize index for their project

---

### Phase 2: CLI Command (Better)

**Implementation:**
```bash
sp context list
# Output:
# AI Context Files:
#   INDEX.md                - Master index of available context
#   pipeline-quickref.md    - YAML syntax reference
#   prompt-contract.md      - .gpt file format requirements
#   basex-patterns.md       - XQuery examples
#   data-sources.md         - Dataset locations
```

**Auto-scan and inject:**
When AI context is loaded, auto-prepend:
```
AI Context Available in docs/ai-context/:
- pipeline-quickref.md (YAML syntax)
- basex-patterns.md (XQuery examples)
- data-sources.md (dataset locations)
Read these before asking user for project conventions.
```

**Benefits:**
- ✅ Dynamic (reflects actual files)
- ✅ CLI helps users too (what context did I create?)
- ✅ Can auto-update project instructions

---

### Phase 3: Registry Integration (Best)

**Extend registry to track AI context files:**

```python
# Register AI context with metadata
registry.ai_context.register(
    file="basex-patterns.md",
    description="XQuery examples for Macula Greek Lowfat syntax trees",
    topics=["basex", "xquery", "greek", "syntax"]
)

# Query
context_files = registry.ai_context.find(topic="basex")
# Returns: [{"file": "basex-patterns.md", "description": "...", ...}]
```

**CLI:**
```bash
sp context add basex-patterns.md \
  --description "XQuery examples for syntax trees" \
  --topics basex,xquery,greek

sp context search basex
# Output: basex-patterns.md - XQuery examples for syntax trees
```

**AI integration:**
```
User: "Query Greek syntax trees"
AI: [Checks registry.ai_context.find(topic="greek,syntax")]
    → Finds basex-patterns.md
    → Reads it
    → Uses documented patterns
```

**Benefits:**
- ✅ Structured metadata (topics, descriptions)
- ✅ Searchable (find by topic, not just filename)
- ✅ Versioned (track when context was added/updated)
- ✅ Cross-project (common patterns shared in `~/.sp/ai-context/`)

---

## Implementation Plan

**Phase 1 (Immediate - ~1 hour): ✅ COMPLETE**
- [x] Create `INDEX.md` template
- [x] Add to `sp init` template generation
- [x] Update `.github/copilot-instructions.md` template
- [x] Add test: verify INDEX.md created by `sp init`
- [ ] Document in tutorial: "Check INDEX.md before asking AI questions"

**Phase 2 (v0.3.0 - ~4 hours): ✅ COMPLETE**
- [x] Implement `sp context list` command
- [x] Auto-scan `docs/ai-context/` for files
- [ ] Inject context inventory into AI system prompt (deferred - integration point TBD)

**Phase 3 (v0.4.0 - ~8 hours): ✅ COMPLETE**
- [x] Extend registry schema for AI context
- [x] Implement `AIContextRegistry` class
- [x] Add `sp context add --topics` with metadata
- [x] Implement `sp context search <topic>`
- [x] AI can query registry for relevant context

---

## Success Metrics

- **Discovery rate:** AI finds and uses documented context ≥80% of time (vs. <20% now)
- **Question reduction:** User questions about "where is X documented?" down 70%
- **Context usage:** Track which ai-context files are read most (telemetry)
- **User satisfaction:** Survey: "Does AI use your documentation effectively?"

---

## Related Issues

- #78 — Global Registry (Phase 3 builds on this)
- #76 — Pipeline GUI (could visualize available context)

---

## References

1. [GitHub Copilot instructions documentation](https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
2. [Cursor .cursorrules patterns](https://cursor.directory/)
3. Similar problem: Code documentation discoverability in large repos

---

**Labels:** `enhancement`, `ai-ux`, `documentation`, `developer-experience`
**Milestone:** Phase 1 in v0.2.2, Phase 2 in v0.3.0
**Priority:** High (directly impacts AI effectiveness)
