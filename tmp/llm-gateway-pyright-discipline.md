## Additional LLMFlow Practice: Pyright Type Checking Integration

Since llm-gateway is a Python project, here's another discipline we've integrated in LLMFlow:

### Pyright Type Checking via pytest

**Problem:** Type checking tools often run separately from tests, making them easy to skip or ignore.

**Solution:** Integrate Pyright into pytest suite so type errors fail the test run.

### Implementation Pattern

**1. Configuration** (`pyrightconfig.json`):
```json
{
  "include": ["src", "tests"],
  "pythonVersion": "3.13",
  "typeCheckingMode": "standard"
}
```

**Why "standard" (not "basic")?**
- **"basic" is too permissive** - misses common bugs like Optional misuse, missing return types
- **"standard" catches real issues** - undefined names, type mismatches, missing attributes
- **"strict" is overkill** - requires annotations everywhere, even for obvious types
- **"standard" is the sweet spot** - productive without being pedantic

**DO NOT use "basic" mode.** It's essentially type checking theater - looks like you're checking types but misses too much to be useful.

**2. Test Integration** (`tests/test_types.py`):
```python
import subprocess
import sys
from pathlib import Path

def test_pyright_type_checking():
    """Validate type hints with Pyright"""
    result = subprocess.run(
        ["pyright"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )
    
    # Fail test if Pyright finds errors
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        pytest.fail("Pyright type checking failed")
```

**3. CI Integration** (`.github/workflows/test.yml`):
```yaml
- name: Type-check Python with Pyright
  run: hatch run pytest tests/test_types.py -v

- name: Run backend tests
  run: hatch run pytest tests/ -q --tb=short
```

### Why This Matters

1. **Type errors = test failures** - Can't merge with type issues
2. **Catches bugs early** - Type mismatches found before runtime
3. **No separate step** - Developers already run `pytest`, don't need to remember `pyright`
4. **CI enforcement** - Type checking fails the PR CI, blocking merge

### Benefits We've Seen

**Caught during v0.2.1.14:**
- 127 type errors initially (inherited codebase)
- Fixed incrementally over 2 weeks
- Now: **0 errors**, enforced by CI
- Prevented 3 bugs from reaching production (caught by type checker)

**Examples:**
1. Function expected `str`, received `Optional[str]` → added null check
2. Dictionary key typo → Pyright caught undefined key access
3. Wrong return type annotation → fixed before runtime error

### Integration with Development Workflow

**Local development:**
```bash
# Run all tests (includes type checking)
hatch run pytest

# Run ONLY type checking (faster for type-only fixes)
hatch run pytest tests/test_types.py -v

# Skip type checking during rapid iteration
hatch run pytest tests/ --ignore=tests/test_types.py
```

**PR CI:**
- Type checking MUST pass for merge
- Shown separately in CI status checks
- Fast feedback (~10 seconds for LLMFlow)

### Don't Silence Your Critics

**CRITICAL ANTI-PATTERN:** Filtering or suppressing type errors instead of fixing them.

Type checking is like having a knowledgeable colleague review your code. When they point out issues, the wrong response is to tell them to be quiet. The right response is to listen and fix the problems.

**Common ways developers silence the critic:**
- ❌ Adding `# type: ignore` everywhere
- ❌ Changing `typeCheckingMode` from "standard" to "basic"
- ❌ Excluding entire directories from checking
- ❌ Setting up `.pyrightignore` files
- ❌ Making the test always pass (`assert True`)
- ❌ Catching and suppressing the error in test_types.py

**Why this is destructive:**
1. Type errors often indicate real bugs waiting to happen
2. Suppression creates technical debt that compounds over time
3. New developers inherit a codebase where type hints lie
4. You lose the safety net that type checking provides

**When suppression is acceptable:**
- ✅ Third-party library has wrong/missing type stubs (document in comment)
- ✅ Complex generic type that Pyright can't infer (with detailed explanation)
- ✅ Temporary suppression during gradual migration (with TODO and issue number)

**Example of wrong vs. right approach:**

```python
# WRONG: Silencing the critic
def get_user(user_id: str) -> dict:  # type: ignore
    return database.query(user_id)  # Returns Optional[dict]

# RIGHT: Listening to the critic
def get_user(user_id: str) -> Optional[dict]:
    return database.query(user_id)  # Pyright happy, caller knows to check None
```

**Tell your LLM coding assistant:**
> "When Pyright reports errors, fix the actual problem. Don't suppress the error unless you can explain why suppression is the only option. Type checking is feedback, not an obstacle."

### Common Pitfalls

❌ **NEVER** use `# type: ignore` without explanation comment
❌ **NEVER** set typeCheckingMode to "basic" to "make errors go away"
❌ **NEVER** skip type checking in CI to "unblock" a release
❌ **NEVER** exclude directories just because they have many errors

✅ **ALWAYS** fix type errors properly (null checks, type narrowing, etc.)
✅ **ALWAYS** document `# type: ignore` with reason (e.g., third-party library issue)
✅ **ALWAYS** run type checker locally before pushing
✅ **ALWAYS** treat type errors as bugs to fix, not warnings to suppress

### Gradual Adoption Strategy

**If you have existing type errors:**

1. **Baseline:** Add `test_types.py` but allow failure initially
2. **Exclude:** Start with `"exclude": ["tests"]` - check only src/
3. **Incremental:** Fix one module at a time, remove from exclude list
4. **Enforce:** When clean, make test required for CI pass

**LLMFlow path:**
- Week 1: 127 errors, test not required
- Week 2: Fixed 80%, required for new code only
- Week 3: Fixed remaining 20%, required for all code
- Now: 0 errors, enforced

### Resources

- Pyright documentation: https://github.com/microsoft/pyright
- LLMFlow pyrightconfig.json: https://github.com/nida-institute/LLMFlow/blob/main/pyrightconfig.json
- LLMFlow test_types.py: https://github.com/nida-institute/LLMFlow/blob/main/tests/test_types.py
- Type checking guide: https://typing.readthedocs.io/

### PyYAML Type Stubs (CRITICAL for llm-gateway)

**Problem:** PyYAML doesn't ship with type stubs, causing Pyright to treat all yaml.load() returns as `Unknown`.

**Solution:** Install types-PyYAML

```bash
pip install types-PyYAML
```

**Why this matters for llm-gateway:**
- YAML parsing is core functionality
- Without type stubs, you lose type safety at the YAML boundary
- `config = yaml.safe_load(...)` becomes `Unknown`, defeating the purpose of type checking

**With types-PyYAML installed:**
```python
import yaml
from typing import Any

# Pyright knows this returns Any (not Unknown)
config: dict[str, Any] = yaml.safe_load(file)  # ✅ Type-safe

# Can narrow further with validation
if "api_key" in config and isinstance(config["api_key"], str):
    api_key: str = config["api_key"]  # ✅ Pyright knows it's str
```

**LLMFlow experience:**
- Initially had `Unknown` types everywhere after YAML parsing
- Added `types-PyYAML` → immediately caught 15+ type errors
- Example: Passing `config.get("timeout")` (could be `None`) to function expecting `int`

### Discussion Questions

1. Does llm-gateway currently use type hints?
2. What's the current type error count (if any)?
3. Does the project use yaml.safe_load()? (If yes, install types-PyYAML)
4. Should we integrate with pytest or run separately in CI?

### Recommended Starting Point

```bash
# 1. Install pyright and type stubs
pip install pyright types-PyYAML

# 2. Create pyrightconfig.json
echo '{
  "include": ["src"],
  "pythonVersion": "3.11",
  "typeCheckingMode": "standard"
}' > pyrightconfig.json

# 3. Check current state
pyright

# 4. Assess error count:
#    - If manageable (<50): Fix them all, then enforce
#    - If many (50-200): Use gradual adoption (fix module by module)
#    - If overwhelming (>200): Consider excluding tests/ initially

# 5. Once clean, integrate with pytest + CI
```

**Important:** Start with "standard" mode from day one. Don't use "basic" as a stepping stone - it teaches bad habits and misses too many real bugs.
