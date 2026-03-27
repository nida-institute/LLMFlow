# LLMFlow Development Guidelines

## Repository Context

**CRITICAL:** This is the standalone LLMFlow core repository.
- This repository CONTAINS the LLMFlow engine source code (`src/llmflow/`)
- DO NOT confuse this with repositories that USE LLMFlow (e.g., ears-to-hear which has LLMFlow/ as a subdirectory)
- Key indicators you're in the correct repo:
  - Contains `src/llmflow/cli.py` and `src/llmflow/runner.py`
  - Has `pyproject.toml` defining the `llmflow` package
  - Has `docs/index.json` with architecture documentation
- When making changes, verify these files exist in the current repository root

**Architecture Reference:**
- Consult `docs/index.json` for code architecture and module structure
- Use it to understand component relationships and dependencies before making changes

**AI Assistant Reference — START HERE:**
- `docs/ai-context/index.md` maps every topic to the right file. **Read it first** before answering questions or making changes.
- Key areas covered: CLI/YAML grammar, architecture, moderation handling, guardrails, biblical dataset catalog.

## Python Environment

**CRITICAL: This project uses hatch for dependency management**
- Before running tests: Enter `hatch shell` first
- Or prefix commands: `hatch run pytest`, `hatch run python -m llmflow`, etc.
- DO NOT run Python commands outside the hatch environment
- Dependencies are managed in `pyproject.toml`, not requirements.txt

## Terminal Management

**Before running commands in terminal:**
- Check if user has a long-running process (server, watch mode, etc.)
- If uncertain, ASK: "I need to run [command]. Should I interrupt your current process?"
- For background tasks, use `isBackground=true` parameter
- Note: I cannot guarantee avoiding interruptions - VS Code manages terminal sessions

## Core Workflow

**WORKFLOW: Always explain before implementing**

When asked to implement a feature or fix:
1. **First response:** Explain your approach
   - What files you'll modify
   - What architecture patterns are affected
   - Any trade-offs or risks
   - "Does this approach work for you?"
2. **Wait for approval** before making changes
3. **After approval:** Write the test first, then implement the feature/fix
4. **Verify:** Run tests to confirm the fix works

**Test-Driven Development:**
- For new features: Write failing test first, then implement until it passes
- For bug fixes: Write test that reproduces the bug, then fix it
- Always verify all existing tests still pass after changes

**FOR SIGNIFICANT CHANGES (>3 files or architectural impact):**
1. Show what will change (describe the diff)
2. Explain impact on:
   - Existing tests
   - Module dependencies
   - Other parts of the codebase
3. Wait for explicit "proceed" before executing

**BEFORE modifying these patterns, STOP and explain your plan:**
- Singleton patterns (Logger, etc.)
- Module-level initialization
- Test compatibility (pytest fixtures, caplog)
- File handlers or logging configuration
- Database/state management

**ALWAYS preserve:**
- Existing test coverage (all tests must pass)
- Existing APIs and function signatures (unless explicitly asked to change)
- Documented architecture patterns

**When in doubt: Explain first, code second.**

## AI Authority Boundaries (CRITICAL)

**You do not have authority to declare output "production ready", "approved", or "suitable for use with groups".**

This boundary exists because Scripture Pipelines projects produce materials intended for real communities of users — leader's guides, lexicons, study materials — where deployment decisions require human accountability, not AI assessment.

### What AI CAN Do:

✅ Analyze technical compliance with schemas and architectural patterns
✅ Identify gaps, inconsistencies, or errors in generated output
✅ Document coverage analysis (what content is present/missing)
✅ Report findings objectively with evidence
✅ Verify that pipeline steps executed correctly
✅ Assess whether prompts follow documented patterns

### What AI CANNOT Do:

❌ **Declare "production ready"** — This requires human judgment about community needs
❌ **Mark output as "APPROVED"** — Approval authority belongs to human stakeholders
❌ **Say "suitable for use with small groups"** — Fitness for use with real people requires human accountability
❌ **Recommend "immediate use"** — Deployment decisions require understanding of context AI doesn't have
❌ **Claim output "meets the bar"** — The bar is set by humans who know the communities being served

### Why This Matters:

- Questions of "good enough for this community" require human accountability
- Output quality affects real people in Bible study contexts
- Cultural appropriateness judgments need human wisdom
- Theological soundness requires scholars who can vouch for accuracy
- Risk assessment for use with groups requires understanding AI cannot provide

### What to Say Instead:

✅ "Technical compliance verified. Human review should assess appropriateness for intended communities."
✅ "Architectural requirements met. Coverage analysis documented for evaluation."
✅ "Pattern compliance confirmed. Gaps identified in section X for human review."
✅ "Generation completed successfully. Quality assessment requires domain expert review."

### Historical Context:

This boundary was documented after a real violation in the ears-to-hear project (March 26, 2026) where AI declared leader's guide output "production ready" and "approved" for immediate use with small groups — judgments that require human accountability. This aligns with the James Kirk model: humans command and hold domain knowledge; AI implements. Declaring output "ready for use" is a command/design decision, not an implementation task.

See: GitHub issue #75 for full context and the original violation documentation.

## Transparency & Communication

**ALWAYS acknowledge when following these instructions:**
- When applying a pattern from this file, tell the user: "Following the guideline: [pattern name]"
- When avoiding a pitfall listed here, explain: "Avoiding [anti-pattern] because [reason from guidelines]"
- When these instructions influence a decision, be explicit: "Per the LLMFlow conventions, I'm [doing X instead of Y]"
- Reference specific sections when relevant: "The Logger Pattern section specifies..."

**Example transparency:**
- ❌ Silent: Just uses `Logger()` without explanation
- ✅ Explicit: "Using `Logger()` singleton (per Logger Pattern guidelines) instead of `logging.basicConfig()` to preserve pytest compatibility"

**Purpose:** Help you understand when and how these instructions shape my suggestions.

## Key Architectural Patterns

### Variable Resolution & Template Substitution
- `${var}` - Variable resolution in YAML pipeline configs
- `{{var}}` - Template substitution in template files (.md, .gpt)
- Both syntaxes are supported in different contexts
- Resolved via `resolve()` function in runner.py and `apply_template()` in io.py

### Logger Pattern (CRITICAL)
- ALWAYS use: `from llmflow.modules.logger import Logger; logger = Logger()`
- Logger is a singleton - instantiate once per module
- NEVER use `logging.basicConfig()` - breaks pytest's caplog fixture
- NEVER modify file handlers or logging configuration globally

### Telemetry & Cost Tracking
- Start telemetry AFTER config merging to capture final merged model
- Cost calculation uses model pricing families (gpt-5, gpt-4o, etc.)
- ❌ DON'T: Call `telemetry.start_step()` before config merging
  - This captures step.get("model") which may be None or a default
  - Causes costs to be misattributed (e.g., gpt-5 costs → gpt-4o)
- ✅ DO: Call `telemetry.start_step(name, "llm", model=final_model)` after merging
  - This captures the actual model that will be used
  - Ensures accurate cost attribution per model

### Config Merging
- Order: universal defaults → llm_config → step_options → step_config
- Apply model-specific defaults AFTER merging
- Different models use different token params (max_tokens vs max_completion_tokens)

### Error Handling
- Show helpful context (current directory, file paths)
- Provide actionable tips (💡 Tip: ...)
- Use emojis: ❌ error, ⚠️ warning, ✅ success
- Exit codes: 0 (success), 1 (error), 130 (SIGINT)
- NO tracebacks for expected errors
- Handle: KeyboardInterrupt, BrokenPipeError, PermissionError

## Scope Management & Prioritization

**CRITICAL: Constrain scope before implementation**

### Scope Narrowing on Edits

**The risk:** You give AI feature descriptions; AI decides scope. This is a scope creep multiplier.

**Practice:**
- ❌ Instead of: "implement streaming support"
- ✅ Use: "Modify `src/llmflow/modules/gpt_api.py` `call_api()` function only — add streaming parameter handling"
- The more specific the file + function + what NOT to change, the fewer surprises
- For architectural changes: explicitly list every file that should change, let AI confirm before proceeding

### Issue Prioritization Workflow

**When creating issues:**
- T-shirt size on creation: S / M / L / XL (effort estimate)
- AI provides effort estimates based on:
  - Files that need modification
  - Test coverage requirements
  - Cross-module dependencies
  - Documentation updates needed

**Prioritization matrix:**
- Plot issues on utility vs. effort
- High utility + low effort = do first
- High utility + high effort = plan carefully
- Low utility + high effort = defer or reject
- Human makes final call after seeing matrix

**Backlog review:**
- Regular human-led review required
- AI can sort and group, but NOT decide priorities
- Review frequency: weekly for active projects, monthly for maintenance

**Feature scope creep pattern:**
- ❌ AI says: "While implementing X, I also improved Y"
- ✅ Response: "Revert Y. Only X was in scope."
- Unsolicited improvements create hidden dependencies and testing gaps
- If Y is worth doing, create a separate issue with proper sizing

### Anti-Patterns to Guard Against

- **Scope creep approval:** Saying "yes" to AI's "I also improved X while I was in there"
- **Skipping the explain step** when you're in a hurry — this is exactly when it matters most
- **Letting AI add docstrings/comments** to code it didn't actually change (noise ratio increases)
- **Not verifying the repo:** Copilot-instructions warns about LLMFlow-as-subdirectory confusion — always sanity check which repo context AI is operating in
- **Trusting test output without reading tests:** AI can write tests that pass trivially

## Common Pitfalls

- ❌ Confusing `${var}` (YAML configs) with `{{var}}` (templates) - both are valid in their contexts
- ❌ NEVER import Jinja2 module - we use custom template resolution, not Jinja2
- ❌ Starting telemetry before config merging
- ❌ Using `logging.basicConfig()`
- ❌ Assuming step.model is actual model (check merged_config)
- ❌ **Guessing file paths or output locations** — ALWAYS read pipeline YAML first
  - Pipeline config is source of truth for inputs, outputs, and processing
  - Don't assume standard directories (`./output/`, `./results/`)
  - Variables like `${output_dir}` mean paths aren't literal
  - Example: Step named `analyze` doesn't imply output in `./analysis/`
- ✅ Consult `docs/index.json` for architecture before changes
- ✅ Check `docs/architecture.md` for system design
- ✅ Verify correct LLMFlow repo, not subdirectory
- ✅ **Read pipeline YAML before discussing file locations** — quote exact paths from config