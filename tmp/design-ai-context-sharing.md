# Design: AI Context Sharing Across Tools and Projects

**Status:** Draft for discussion
**Date:** April 5, 2026
**Context:** Multiple AI coding assistants (GitHub Copilot, Claude Code, Cursor, etc.) need project context, but each has different mechanisms

---

## Problem Statement

LLMFlow currently uses multiple mechanisms for AI context:

1. **`.github/copilot-instructions.md`** — GitHub Copilot-specific, in-repo, version controlled
2. **`CLAUDE.md`** — Claude Code (claude.ai/code)-specific, in-repo, version controlled
3. **`/memories/repo/`** — VS Code Copilot workspace memory, external storage, NOT version controlled
4. **`docs/ai-context/`** — Architecture documentation intended for AI consumption
5. **`project/TODO.md`** — Active work tracking, in-repo, version controlled

**The challenge:** Projects using Scripture Pipelines span multiple organizations (nida-institute, SIL International, translation orgs). Developers may use different AI tools. How do we share verified facts, patterns, and pitfalls effectively?

---

## Current State Analysis

### What Works Well

**In-Repository Files (copilot-instructions.md, CLAUDE.md)**

✅ **Pros:**
- Version controlled — changes tracked, reviewable via PRs
- Portable — works on any machine, any clone of the repo
- Shareable — all collaborators see the same context
- Discoverable — visible in file tree, searchable
- Tool-specific — can optimize for each AI's capabilities

✅ **Current effective uses:**
- Communication protocols (Captain Kirk model)
- Error analysis templates
- Architecture patterns (Logger singleton, config merging)
- Common pitfalls with ❌/✅ examples
- Workflow requirements (explain-before-implementing)

❌ **Limitations:**
- Duplication — copilot-instructions.md and CLAUDE.md overlap ~70%
- Maintenance burden — update both files for consistency
- Tool fragmentation — what about Cursor? Aider? Future tools?
- Size constraints — these files can get large (copilot-instructions.md is 340+ lines)

**External Memory (/memories/repo/, /memories/session/)**

✅ **Pros:**
- Persistent across sessions
- Quick to update during active work
- Good for session-specific notes (session memory)
- Can capture lessons learned in real-time

❌ **Cons:**
- **NOT version controlled** — changes don't go through PR review
- **NOT portable** — local machine only, doesn't travel with git clone
- **NOT shareable** — other developers can't see these insights
- **Storage location unclear** — external VS Code workspace directory
- **Discovery problem** — can't browse in normal file tree

❌ **Current evidence of problems:**
- `/memories/repo/pypi-status.md` contains critical fact (LLMFlow not registered on PyPI)
- `/memories/repo/nuitka-build-verification.md` has mandatory verification commands
- **Neither is visible to other developers or in other environments**

**Documentation Directory (docs/ai-context/)**

✅ **Pros:**
- Version controlled and shareable
- Tool-agnostic — any AI can read markdown
- Can be comprehensive without file size concerns
- Natural home for architectural knowledge

✅ **Current effective uses:**
- `index.md` — topic map pointing to right files
- `cli-grammar.md` — YAML pipeline grammar
- `gui-architecture.md` — dual-location setup pitfalls

❌ **Limitations:**
- Not automatically loaded by AI tools (some support @-mentions, some don't)
- Requires AI to actively search/read
- Separation from execution context (copilot-instructions loaded automatically)

**Active Work Tracking (project/TODO.md)**

✅ **Pros:**
- Version controlled and shareable
- Shows what's in progress (prevent duplicate work)
- Identifies areas in flux (don't refactor code being rewritten)
- Links to GitHub issues (permanent decisions)
- Convention documented: "Active work here, permanent decisions in issues"

✅ **Current effective uses:**
- Monday priorities — what to focus on next
- Workshop readiness tracking
- Backlog visibility
- Naming conventions (e.g., `--update` flag pattern)

✅ **Value for AI:**
- **Avoid duplicate work:** "GUI Content Lifecycle fix is already queued"
- **Focus problems:** "Don't refactor PyPI publication code until credentials are in place"
- **Understand constraints:** "Naming convention locked: --update is a flag, not a subcommand"
- **Priority awareness:** AI suggestions can align with current priorities

❌ **Limitations:**
- Not linked from copilot-instructions.md or CLAUDE.md
- AI may not check TODO.md before suggesting features
- Gets stale if not maintained
- Unclear when items graduate to issues vs. stay in TODO

❌ **Missing use case from today's session:**
- Error Analysis Protocol document would benefit from TODO.md note: "Windows install script verification failing, see v0.2.1.16 investigation"
- Could prevent AI from claiming releases succeeded while verification failures are being debugged

**GitHub Issues & Project Boards**

✅ **Pros:**
- Permanent decision record — discussions preserved, decisions linked
- Cross-project visibility — org-level board tracks multiple repos
- Priority signaling — board columns show "In Progress" vs "Backlog"
- Stakeholder communication — external collaborators can participate
- Searchable history — past decisions documented with rationale
- Labels and milestones — categorization and planning metadata

✅ **Current effective uses:**
- Issue #32 — Workshop readiness tracking with checklist
- Issue #11 — Conditionals and switches feature discussion
- Project board — https://github.com/orgs/nida-institute/projects/13
- Convention: "Active work in TODO.md, permanent decisions in issues"

✅ **Value for AI:**
- **Understand priorities:** Board columns show what's actively being worked on
- **Avoid duplicate suggestions:** Check if feature already has issue before proposing
- **Link to decisions:** "As discussed in #11, conditionals use `when:` syntax"
- **Cross-project context:** Org board shows work across all nida-institute repos
- **Historical rationale:** Why was X rejected? Check closed issues
- **Focus on what matters:** Board "In Progress" column = highest priority

✅ **Value for human-AI-human communication:**
- **Async collaboration:** Issue discussion thread captures multi-day decisions
- **Between projects:** Ears-to-hear references LLMFlow issues for shared patterns
- **Knowledge transfer:** New collaborators read issue history for context
- **Consensus building:** Multiple stakeholders comment on design decisions
- **Audit trail:** When did we decide X? Who advocated for Y?

❌ **Limitations:**
- Not loaded automatically into AI context (requires explicit tool calls or @-mentions)
- API rate limits — can't crawl all issues on every prompt
- Stale metadata — labels/milestones require maintenance
- Discoverability — AI may not know issue #32 exists unless told
- Fragmentation — some context in issues, some in TODO.md, some in copilot-instructions

❌ **Integration gap:**
- copilot-instructions.md doesn't mention checking issues/board before suggesting features
- No link from TODO.md to project board (should be in header)
- AI doesn't reliably check board status before claiming "nothing blocking X"
- Cross-repo context: nida-institute org board not referenced in any repo's AI instructions

❌ **Today's evidence of integration failure:**
- AI claimed v0.2.1.16 "build succeeded" without knowing Windows verification was failing
- If TODO.md had "🔥 Active: Debug Windows install script verification failure #116" (hypothetical issue), AI would have additional context
- Project board "In Progress" column would signal "releases are currently problematic, verify carefully"

---

## Design Goals

1. **Portability:** Context should travel with the repository (git clone works everywhere)
2. **Shareability:** All team members see the same verified facts
3. **Version Control:** Changes reviewable, mistakes revertable
4. **Tool Agnostic:** Support Copilot, Claude, Cursor, Aider, future tools
5. **Minimal Duplication:** Single source of truth where possible
6. **Discoverable:** Easy to find, browse, update
7. **Structured:** Machine-readable where appropriate (JSON, YAML frontmatter)
8. **Maintainable:** Don't create update burden
9. **Issues/Boards Integration:** AI should check GitHub issues and project boards for priorities, active work, and permanent decisions before making suggestions
10. **Cross-Project Coordination:** Enable context sharing across multiple repos in nida-institute organization

---

## Proposed Architecture

### Tier 0: GitHub Issues & Project Boards (Source of Truth for Decisions & Priorities)

**Location:** GitHub.com (nida-institute organization)

**Purpose:** Permanent decision record, priority signaling, cross-project coordination

**Key Resources:**
- **Issues:** Permanent decisions, feature discussions, bug tracking
- **Project Board:** https://github.com/orgs/nida-institute/projects/13
- **Labels:** Bug, enhancement, documentation, workshop-blocking, etc.
- **Milestones:** Workshop 2026, v1.0, etc.

**AI Integration Points:**
- Check project board "In Progress" column before suggesting new work
- Search issues for prior discussion before proposing features
- Link to issues when referencing decisions ("As per #32...")
- Note when issue is blocked to avoid suggesting dependent work

**Documentation Requirements:**
- copilot-instructions.md should reference project board URL
- TODO.md should link to board and explain convention (active work vs permanent decisions)
- When AI tools support it, check board status before claiming "nothing blocking X"

**Cross-Project Value:**
- Org-level board shows work across all nida-institute repos
- Ears-to-hear can reference LLMFlow issues for shared patterns
- Design decisions made visible to all projects

**Limitation acknowledged:**
- Not all AI tools have GitHub integration yet
- Manual: AI must be told issue numbers or board status
- Future: Tools like GitHub Copilot may auto-check board state

### Tier 1: Universal In-Repo Context (Tool-Agnostic)

**Location:** `docs/ai-context/`

**Purpose:** Comprehensive project knowledge accessible to any AI tool

**Structure:**
```
docs/ai-context/
  index.md              # Topic map with @-mention paths
  patterns.md           # Architectural patterns (Logger, config merging, etc.)
  pitfalls.md           # Common mistakes with examples
  verification.md       # Build/release verification requirements
  pypi-status.md        # Publication status facts
  workflows.md          # Required workflows (TDD, explain-first, etc.)
  error-analysis.md     # Diagnostic framework
```

**Frontmatter for machine-readability:**
```markdown
---
type: ai-context
category: patterns
last-verified: 2026-04-05
---
```

**Reference in tool-specific files:**
```markdown
# GitHub Copilot Instructions

For comprehensive context, see:
- Architecture patterns: docs/ai-context/patterns.md
- Common pitfalls: docs/ai-context/pitfalls.md
- Build verification: docs/ai-context/verification.md
```

✅ **Benefits:**
- Version controlled, portable, shareable
- Works with any AI tool (Claude, Cursor, Copilot, Aider)
- Can be comprehensive without size limits
- Natural home for long-form knowledge

### Tier 2: Tool-Specific Instructions (Optimized, In-Repo)

**Location:** `.github/copilot-instructions.md`, `CLAUDE.md`, `CURSOR.md`, etc.

**Purpose:** Tool-specific optimizations, integration points, communication protocols

**Content:**
- Communication style (Captain Kirk model, pronouns, etc.)
- Tool-specific features (how to use that tool's strengths)
- References to docs/ai-context/ for deep dives
- Quick-reference pitfalls (top 5-10 most critical)

**Size target:** Keep under 200 lines, link to docs/ai-context/ for details

**Example structure:**
```markdown
# GitHub Copilot Instructions

## Communication Protocol
[Captain Kirk model, Error Analysis Protocol]

## Key Patterns
See docs/ai-context/patterns.md for full details:
- Logger: Singleton pattern, never use logging.basicConfig()
- Config merging: universal → llm_config → step_options → step_config
- [5-6 more critical patterns]

## Top Pitfalls
See docs/ai-context/pitfalls.md for comprehensive list:
❌ Building packages ≠ ready to publish to PyPI
❌ Individual build jobs ≠ entire workflow success
❌ Starting telemetry before config merging
[3-4 more]

## Workflows
See docs/ai-context/workflows.md for rationale:
1. Explain approach before implementing
2. Write test first, then implement
3. Verify with mandatory commands before claiming success

## Tool-Specific Features
[GitHub Copilot Chat slash commands, skills, etc.]
```

✅ **Benefits:**
- Optimized for each tool's capabilities
- DRY principle: details in docs/ai-context/, references here
- Smaller files easier to maintain
- Still version controlled and shareable

### Tier 3: Session Memory (Ephemeral, External)

**Location:** `/memories/session/` (VS Code workspace storage)

**Purpose:** Active work notes, current session context, temporary findings

**Use cases:**
- "Currently debugging X, don't touch files Y and Z"
- "Tried approach A, failed because B, now trying C"
- Session handoff notes
- In-progress discoveries not yet verified

**Lifecycle:**
- Created during active work
- Reviewed at session end
- Promoted to docs/ai-context/ if verified and valuable
- Deleted if ephemeral

✅ **Benefits:**
- Fast to create during flow
- No PR friction for temporary notes
- Clears automatically (session-scoped)

❌ **Rules:**
- NEVER put verified facts here (use docs/ai-context/)
- NEVER rely on persistence across machines
- Review and promote or delete before ending work

### Tier 4: User Memory (Personal, External)

**Location:** `/memories/` (VS Code user storage, all workspaces)

**Purpose:** Personal preferences, cross-project patterns, individual working style

**Use cases:**
- "Address user as Captain"
- "User prefers TDD approach"
- "Never use heredoc syntax in terminals"
- Cross-repo patterns (all nida-institute projects)

**Scope:** Single user, all projects

✅ **Benefits:**
- Travels across projects
- Personal customization
- No repo clutter

❌ **Rules:**
- NEVER put project-specific facts here
- Use for personal preferences only

---

## Migration Strategy

### Immediate (Today)

1. **Migrate critical /memories/repo/ files to docs/ai-context/**
   - `/memories/repo/pypi-status.md` → `docs/ai-context/pypi-status.md`
   - `/memories/repo/nuitka-build-verification.md` → `docs/ai-context/verification.md`
   - `/memories/repo/llmflow-docs-gaps.md` → Keep as roadmap, reference in docs/TODO.md

2. **Update copilot-instructions.md and CLAUDE.md**
   - Add references to docs/ai-context/ files
   - Keep communication protocols and top pitfalls inline
   - Link to docs/ai-context/ for comprehensive lists

3. **Create docs/ai-context/index.md update**
   - Add rows for new context files
   - Make it the single entry point for AI context discovery

### Near-term (This Week)

4. **Extract common content to docs/ai-context/patterns.md**
   - Logger pattern
   - Config merging order
   - Telemetry timing
   - Variable resolution (${var} vs {{var}})

5. **Extract pitfalls to docs/ai-context/pitfalls.md**
   - All ❌/✅ examples
   - Keep top 5-10 in tool-specific files
   - Link to comprehensive list

6. **Create docs/ai-context/workflows.md**
   - Explain-before-implementing
   - TDD requirements
   - Scope narrowing practices
   - Verification requirements

### Medium-term (Next Sprint)

7. **Add YAML frontmatter to ai-context files**
   - `type: ai-context`
   - `category: patterns|pitfalls|workflows|verification`
   - `last-verified: <date>`
   - Enables tooling/automation

8. **Create validation script**
   - Check copilot-instructions.md + CLAUDE.md references point to existing files
   - Validate frontmatter syntax
   - Flag outdated last-verified dates

9. **Document for other nida-institute projects**
   - Template structure in docs/ai-context/
   - Copy ai-context/ directory to other repos
   - Customize per project

---

## Multi-Tool Support Pattern

### For New AI Tools (Cursor, Aider, etc.)

**When supporting a new tool:**

1. Create tool-specific file in repo root: `CURSOR.md`, `AIDER.md`, etc.
2. Follow Tier 2 structure: communication + references
3. Optimize for tool's specific features
4. Share 90% of context via docs/ai-context/ references

**Example CURSOR.md:**
```markdown
# Cursor AI Instructions

See comprehensive context in docs/ai-context/:
- Architecture: docs/ai-context/patterns.md
- Pitfalls: docs/ai-context/pitfalls.md
- Workflows: docs/ai-context/workflows.md

## Cursor-Specific Optimizations
[Features specific to Cursor: multi-file editing, etc.]

## Communication Protocol
[Captain Kirk model]
```

---

## Questions for Discussion

1. **Size limits:** Should we enforce max size on tool-specific files? (Suggested: 200 lines, rest in docs/ai-context/)

2. **Duplication policy:** Is 10% duplication acceptable for critical pitfalls (in both tool file + docs/ai-context/)? Or strict DRY?

3. **Frontmatter format:** JSON vs YAML vs custom? What fields required?

4. **Validation enforcement:** CI check for broken references? Or just make-work?

5. **Other projects:** Should nida-institute have org-level ai-context/ that all repos inherit? Or per-repo only?

6. **Memory cleanup:** Should we delete /memories/repo/ content once migrated? Or keep as backup?

7. **User memory migration:** Move cross-project patterns (Captain Kirk, heredoc ban) to org-level docs?

---

## Recommendation Summary

**DO:**
- ✅ Migrate verified facts from /memories/repo/ to docs/ai-context/ (version controlled)
- ✅ Keep tool-specific files small, reference comprehensive context
- ✅ Use docs/ai-context/ as single source of truth for patterns/pitfalls
- ✅ Session memory for temporary notes only, promote to docs when verified
- ✅ Support multiple AI tools via consistent reference structure

**DON'T:**
- ❌ Put verified facts in /memories/repo/ (not shareable)
- ❌ Duplicate entire pattern descriptions in multiple tool files
- ❌ Let tool-specific files exceed ~200 lines
- ❌ Mix project facts with personal preferences

**PRINCIPLE:**
Optimize for **shareability** and **verification** over **convenience**. External memory is fast to update but invisible to teammates. In-repo context is slightly slower to update (requires commit) but ensures everyone has the same verified truth.

---

## Cognitive Overload Analysis

**Question: Is this architecture too complex? Will it overwhelm AI systems?**

### The Complexity Is Already Here

This design doesn't CREATE complexity—it DOCUMENTS existing reality:
- copilot-instructions.md already exists (340+ lines)
- CLAUDE.md already exists (~180 lines, 70% overlap with above)
- docs/ai-context/ already exists (5 files)
- /memories/repo/ exists but hidden
- TODO.md exists
- GitHub issues exist
- Project board exists

**Current state:** All these sources exist but AI doesn't know they exist or how to navigate between them.

**Proposed state:** Tool-specific files act as navigation hub, explicit references create discoverability.

### Navigation Hub Pattern (Reduces Cognitive Load)

**Key insight:** AI doesn't load ALL context simultaneously. It follows references on demand.

**Execution model:**
1. AI reads copilot-instructions.md (automatically loaded)
2. Sees reference: "Architecture patterns: docs/ai-context/patterns.md"
3. If needed for current task, reads that file
4. If not needed, ignores it

**This is LESS cognitive load than:**
- Having all patterns duplicated inline in copilot-instructions.md (information density problem)
- Not knowing comprehensive patterns exist at all (AI invents conflicting approaches)
- Searching blindly across repo without navigation structure

### Current Cognitive Overload Symptoms (Evidence-Based)

**Today's session demonstrated actual overload:**
1. AI claimed "build succeeded" - didn't know about verification requirements
2. AI claimed "ready for PyPI" - didn't know project isn't registered
3. AI missed that Windows verification was failing - no TODO.md check
4. AI gave anthropomorphic responses - optimization for wrong objective

**Root cause:** Not too much context, but WRONG context priorities:
- Build verification commands weren't in AI's active context
- PyPI status wasn't in AI's active context
- Current work status (TODO.md, project board) wasn't checked
- Error analysis protocol didn't exist yet

**The fix:** Ensure CRITICAL context is in tool-specific files (tier 2), details in tier 1.

### Tiered Loading Strategy (How AI Actually Uses This)

**Tier 0 (GitHub Issues/Board):** Pull on demand
- "Is feature X already requested?" → Search issues
- "What's blocking?" → Check board "In Progress" column
- NOT: Load all 50 issues into context

**Tier 1 (docs/ai-context/):** Pull when tool file references it
- copilot-instructions: "See docs/ai-context/verification.md for build checks"
- AI reads verification.md ONLY when doing release work
- NOT: Load all docs/ai-context/ files for every prompt

**Tier 2 (Tool-specific files):** Always loaded
- Keep under 200 lines
- Top 5-10 critical patterns/pitfalls inline
- Reference tier 1 for comprehensive details

**Tier 3 (Session memory):** Ephemeral, small
- Current work notes
- Cleared between sessions

**Tier 4 (User memory):** Personal preferences
- Loaded automatically but minimal size

### Comparison to Human Working Memory

**Humans navigate similar complexity:**
- Don't memorize all patterns - reference architecture docs when needed
- Don't memorize all issues - search when relevant
- Keep TODO list in front (tier 2 equivalent)
- Deep dive into specific docs only when task requires it

**AI should work similarly:**
- Navigation structure (tier 2) always loaded
- Deep context (tier 1) pulled on demand
- GitHub data (tier 0) queried when relevant
- Session notes (tier 3) for active work only

### Validation Checkpoints

**To ensure we DON'T create overload:**

1. **Size limits enforced:**
   - Tool-specific files: 200 lines max
   - Force DRY via references, not duplication

2. **Pull model, not push:**
   - AI doesn't auto-load all docs/ai-context/
   - Explicit references in tool files guide when to pull

3. **Hierarchy clarity:**
   - Each tier has clear purpose
   - No ambiguity about which source is authoritative

4. **Incremental adoption:**
   - Start with pypi-status.md and verification.md
   - Add patterns.md and pitfalls.md next
   - Measure if AI actually uses them before adding more

5. **Real-world testing:**
   - Does AI still miss critical context?
   - Does AI get confused about conflicting sources?
   - Does AI spend excessive time searching?

### Warning Signs to Monitor

**If this design creates overload, we'll see:**
- ❌ AI frequently says "I don't know where to find X" despite clear references
- ❌ AI contradicts docs/ai-context/ content (didn't actually read it)
- ❌ AI takes longer to respond (processing too much context)
- ❌ AI gets confused between tool-specific file and docs/ai-context/

**If design is working well, we'll see:**
- ✅ AI references specific docs when relevant ("Per docs/ai-context/verification.md...")
- ✅ AI checks TODO.md before suggesting new features
- ✅ AI catches mistakes earlier (knows about verification requirements)
- ✅ Less time correcting AI mistakes (gets it right first time)

### Recommendation: Start Small, Validate, Expand

**Phase 1 (This week):**
- Migrate /memories/repo/ to docs/ai-context/ (3 files)
- Add references to tool-specific files
- Measure: Does AI actually use verification.md and pypi-status.md?

**Phase 2 (Next week, if Phase 1 works):**
- Extract patterns.md from copilot-instructions.md
- Slim down copilot-instructions.md to <200 lines
- Measure: Does AI still catch pattern violations?

**Phase 3 (Following week, if Phase 2 works):**
- Extract pitfalls.md with comprehensive list
- Keep top 5-10 in tool files
- Measure: Does AI miss common pitfalls more or less?

**Abort criteria:**
- If AI starts missing critical context more often
- If responses get slower without quality improvement
- If AI shows confusion between sources

**Success criteria:**
- Fewer "you just lied to me" corrections needed
- AI proactively checks verification requirements
- Cross-project context actually used (ears-to-hear references LLMFlow patterns)

---

## Next Steps

1. Review this design with user
2. Execute Immediate migration (today)
3. Create docs/ai-context/ files with frontmatter
4. Update tool-specific files to reference new structure
5. Document pattern for other nida-institute projects
6. Share migration approach via Balisage paper update
