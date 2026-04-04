## Additional LLMFlow Practice: GUI Dual-Location Architecture

Since paratext-copilot includes a GUI component, here's another discipline we've formalized in LLMFlow:

### The Dual-Location Pattern

**Problem:** Need both development flexibility (hot reload) AND production simplicity (single bundled package).

**Solution:** Maintain GUI code in two locations:
- **Development:** `gui/backend/` - edit here, run dev servers
- **Production:** `src/paratext_copilot/gui/` (or equivalent) - synced by build script

### Why This Matters

1. **Development flexibility:** Hot reload, separate frontend/backend servers
2. **Production simplicity:** Single `paratext-copilot gui` command serves bundled static files
3. **Binary compatibility:** Packages/Nuitka bundles need all files under `src/`

### Workflow: Edit → Test → Sync → Verify

**ALWAYS follow this sequence:**

1. **Edit** in `gui/backend/`:
   - `gui/backend/server.py` - Flask routes
   - `gui/backend/executor.py` - Backend logic

2. **Test development version:**
   ```bash
   pytest tests/test_gui_api_contract.py
   ```
   (Tests import `from gui.backend.server`)

3. **Sync to production:**
   ```bash
   python build_gui.py
   ```
   This copies:
   - `gui/backend/*.py` → `src/paratext_copilot/gui/`
   - `gui/frontend/dist/` → `src/paratext_copilot/gui/static/`

4. **Test production version:**
   ```bash
   pytest tests/test_gui_server_pkg.py
   ```
   (Tests import `from paratext_copilot.gui.server`)

5. **Verify with GUI:**
   ```bash
   paratext-copilot gui
   ```

### Common Pitfalls

❌ **NEVER** edit `src/*/gui/` directly - overwritten by build script
❌ **NEVER** forget to run `build_gui.py` before testing with production command
❌ **NEVER** test only one version - always test BOTH dev and production

✅ **ALWAYS** edit in `gui/backend/`
✅ **ALWAYS** run build script before release
✅ **ALWAYS** run both test suites to catch sync drift

### Testing Strategy

- `test_gui_api_contract.py` - tests development version (hot reload)
- `test_gui_server_pkg.py` - tests production version (detects drift)

**Why two test suites?** Development imports from `gui.backend`, production imports from `paratext_copilot.gui`. Testing both prevents the "works in dev, breaks in production" problem.

### Real LLMFlow Example

We caught this bug during v0.2.1.14 release:
1. Edited `gui/backend/server.py`, tests passed
2. Forgot to run `build_gui.py`
3. `sp gui` had 404 errors (missing new endpoints)
4. Production tests failed → caught the issue before release

**Fix:** Run `build_gui.py`, re-test, commit both locations.

### Minimum Testing Standards for GUI Applications

**Reality check:** Even with LLMFlow's testing infrastructure, we still catch bugs in production. Here's what we've learned about minimum viable testing.

#### Backend Testing (Flask + pytest)

**Complexity:** Low | **Value:** Critical | **Time:** Minutes to set up

**Minimum required tests:**

1. **API Contract Tests** (`test_gui_api_contract.py`)
   - Every endpoint the frontend calls MUST have a test
   - Prevents 404 errors when frontend makes requests
   - LLMFlow example: 15+ contract tests catch missing endpoints

   ```python
   def test_health_endpoint_exists(client):
       """Frontend App.tsx fetches /api/health on mount"""
       response = client.get('/api/health')
       assert response.status_code == 200
   ```

2. **Security Tests** (`test_gui_server_security.py`)
   - File extension validation (reject .py, .sh, accept .yaml)
   - Path traversal prevention
   - CORS configuration (not wildcard `*`)
   - LLMFlow mistake: Initially allowed arbitrary file extensions

   ```python
   def test_rejects_python_file(client, tmp_path):
       bad_file = tmp_path / "exploit.py"
       resp = client.post('/api/pipeline/config',
                         json={'pipeline_path': str(bad_file)})
       assert resp.status_code == 400
   ```

3. **Production Package Tests** (`test_gui_server_pkg.py`)
   - Import from `paratext_copilot.gui.server` (not `gui.backend`)
   - Ensures production version has same endpoints as dev
   - Catches sync drift from forgetting `build_gui.py`

   ```python
   # CRITICAL: Test production import path
   from paratext_copilot.gui.server import create_app

   def test_endpoint_exists(client):
       response = client.get('/api/health')
       assert response.status_code == 200
   ```

**Tools:**
- **pytest + Flask test client** - Built-in, no dependencies
- **pytest-cov** - Coverage reporting (aim for >80% backend)

**LLMFlow coverage:** 50+ backend tests, but still missing:
- WebSocket reconnection logic
- Pipeline cancellation edge cases
- Concurrent execution handling

#### Frontend Testing (React + Vitest)

**Complexity:** Medium-High | **Value:** Variable | **Time:** Hours to set up properly

**Testing tool options:**

| Tool | Setup (LLM-assisted) | Ongoing Burden | Value | LLMFlow Use |
|------|---------------------|----------------|-------|-------------|
| **Vitest + Testing Library** | 1-2 hours | Low (stable tests) | High | ✅ Primary |
| **Playwright** | 4-8 hours | High (flaky, debugging) | Very High | ❌ Not yet |
| **Cypress** | 4-8 hours | High (flaky, debugging) | Very High | ❌ Not yet |
| **Manual testing** | 0 hours | Very High (repetitive) | Low | ⚠️ Fallback |

**"Complexity" in the LLM era = ongoing human burden, not initial code writing**

Even with an LLM generating Playwright tests for you:
- ✅ LLM **CAN** write initial test code in minutes
- ✅ LLM **CAN** set up basic browser automation
- ❌ LLM **CANNOT** fix flaky tests (timing issues, race conditions)
- ❌ LLM **CANNOT** debug why tests pass locally but fail in CI
- ❌ LLM **CANNOT** maintain tests as UI changes (you review every change)
- ❌ LLM **CANNOT** manage ChromeDriver versions / browser compatibility
- ❌ LLM **CANNOT** determine if test failure is real bug or test issue

**Playwright/Cypress "high complexity" means:**
- Initial setup: 4-8 hours (install browsers, configure CI, write first tests)
- **Ongoing maintenance: 1-2 hours/week** (fix flaky tests, update selectors, debug CI failures)
- **Debugging time: 30 min - 2 hours per failure** (understand what broke, real bug vs test issue)

**Vitest "medium complexity" means:**
- Initial setup: 1-2 hours (already have Node.js, just add testing-library)
- Ongoing maintenance: 15-30 min/week (mostly stable, mocks easier to maintain)
- Debugging time: 5-15 min per failure (stack traces clear, failures reproducible)

**Why we haven't adopted Playwright despite LLM assistance:**
1. **Maintenance burden** - Even with LLM-written tests, humans debug failures
2. **Flakiness** - E2E tests fail randomly, requires constant attention
3. **CI complexity** - Browser automation in GitHub Actions has quirks
4. **Diminishing returns** - Current approach catches most bugs for less effort

**When Playwright IS worth it (even with maintenance burden):**
- Users report frequent critical bugs that unit tests miss
- Team >3 people (maintenance burden shared)
- GUI is primary interface (not CLI fallback)
- Budget for 5-10 hours/month maintaining E2E tests

**Minimum required tests:**

1. **Component Rendering** (`App.test.tsx`, `components.test.tsx`)
   - Does the app load without crashing?
   - Are critical UI elements present?
   - LLMFlow gap: Tests pass in dev, fail in CI (environment issues)

   ```typescript
   it('renders the app title', async () => {
     render(<App />);
     expect(screen.getByText('Scripture Pipelines')).toBeInTheDocument();
   });
   ```

2. **API Integration** (`integration.test.tsx`)
   - Mock fetch calls
   - Verify frontend calls correct endpoints
   - Check error handling when API fails

   ```typescript
   global.fetch = vi.fn();
   global.fetch.mockImplementation((url) => {
     if (url.includes('/api/health')) {
       return Promise.resolve({
         ok: true,
         json: () => Promise.resolve({ status: 'ok' })
       });
     }
   });
   ```

3. **User Interactions** (`PipelineView.buttons.test.tsx`)
   - Button clicks trigger expected actions
   - Form submissions work
   - File selection works
   - LLMFlow gap: WebSocket mock failures in CI

   ```typescript
   it('calls execute API when Run clicked', async () => {
     render(<PipelineView />);
     const runButton = screen.getByRole('button', { name: /run/i });
     await userEvent.click(runButton);
     expect(mockExecuteAPI).toHaveBeenCalled();
   });
   ```

**Known testing gaps in LLMFlow (honest assessment):**

❌ **No E2E tests** - Don't test actual Flask ↔ React communication
❌ **Mock-heavy** - Tests use mocks, not real WebSocket connections
❌ **Environment brittleness** - Pass locally, fail in CI (DOM setup issues)
❌ **No visual regression** - UI breaks don't get caught
❌ **Limited error state coverage** - Happy path mostly tested

**Why we haven't fixed these yet:**
- E2E testing (Playwright/Cypress) adds significant complexity
- Setting up requires ChromeDriver, browser automation
- Test maintenance burden increases dramatically
- Current approach catches ~70% of bugs, diminishing returns

**When to invest in E2E:**
- ✅ If users report frequent GUI bugs
- ✅ If team size >3 (maintenance burden shared)
- ✅ If GUI is primary interface (not CLI fallback)
- ❌ If GUI is secondary tool (LLMFlow case)
- ❌ If team is 1-2 people (ROI too low)

#### What We Still Miss (LLMFlow Reality Check)

**Bugs that escaped our testing:**

1. **WebSocket reconnection failures** - No tests for network interruption
2. **File system race conditions** - Pipeline writes file, GUI reads before write completes
3. **CORS in production** - Different behavior in bundled vs dev server
4. **Memory leaks** - Long-running GUI sessions slow down
5. **Mobile/responsive** - Never tested on small screens

**Why these escaped:**
- Not enough integration testing (mocks hide real behavior)
- CI environment different from user environments
- Time constraints (shipping features vs perfect tests)

#### Recommended Minimum for paratext-copilot

**Start here (1-2 days setup):**
1. ✅ Backend contract tests (every API endpoint)
2. ✅ Backend security tests (file validation)
3. ✅ Production package tests (import from correct location)
4. ✅ Basic frontend render tests (app doesn't crash)

**Add later if needed (1-2 weeks setup):**
5. ⚠️ E2E tests with Playwright (if GUI bugs frequent)
6. ⚠️ Visual regression tests (if UI breaks often)
7. ⚠️ Performance tests (if users report slowness)

**Skip these (not worth it):**
8. ❌ 100% code coverage (diminishing returns after 80%)
9. ❌ Unit testing every React component (integration tests better)
10. ❌ Testing third-party libraries (trust but verify at boundaries)

#### Testing Commands Checklist

```bash
# Backend only (fast)
pytest tests/test_gui*.py -v

# Backend with coverage
pytest tests/test_gui*.py --cov=gui/backend --cov=src/*/gui

# Frontend only
cd gui/frontend && npm test

# Frontend watch mode (during development)
cd gui/frontend && npm run test

# Everything before release
pytest tests/test_gui*.py && cd gui/frontend && npm run test:run
```

### Resources

- LLMFlow GUI architecture docs: https://github.com/nida-institute/LLMFlow/blob/main/docs/ai-context/gui-architecture.md
- Example build script: https://github.com/nida-institute/LLMFlow/blob/main/build_gui.py
- Backend test examples: https://github.com/nida-institute/LLMFlow/tree/main/tests
- Frontend test examples: https://github.com/nida-institute/LLMFlow/tree/main/gui/frontend/src/test

### Discussion Questions

1. Does paratext-copilot use this pattern already?
2. Do we have both dev and production test suites?
3. What's our current test coverage percentage?
4. Have users reported GUI-specific bugs?
5. Should we invest in E2E testing or stick with contract/integration tests?
6. Should we document this in CONTRIBUTING.md?
