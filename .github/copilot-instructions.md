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

## Common Pitfalls

- ❌ Confusing `${var}` (YAML configs) with `{{var}}` (templates) - both are valid in their contexts
- ❌ NEVER import Jinja2 module - we use custom template resolution, not Jinja2
- ❌ Starting telemetry before config merging
- ❌ Using `logging.basicConfig()`
- ❌ Assuming step.model is actual model (check merged_config)
- ✅ Consult `docs/index.json` for architecture before changes
- ✅ Check `docs/architecture.md` for system design
- ✅ Verify correct LLMFlow repo, not subdirectory