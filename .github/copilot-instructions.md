# Architectural Constraints

**WORKFLOW: Always explain before implementing**

When asked to implement a feature or fix:
1. **First response:** Explain your approach
   - What files you'll modify
   - What architecture patterns are affected
   - Any trade-offs or risks
   - "Does this approach work for you?"
2. **Wait for approval** before making changes
3. **After approval:** Execute without asking again

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