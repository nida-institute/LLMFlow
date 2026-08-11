# Content Lifecycle GUI - Testing Strategy

**Status**: Partially Implemented
**Last Updated**: April 3, 2026

## Overview

The Content Lifecycle Management system has **core logic fully tested** (64 passing tests) but **GUI-specific testing is minimal**. This document outlines the complete testing strategy.

---

## Current Test Coverage ✅

### Python Core Logic (100% — 64 tests)

All core functionality is tested through pytest:

**File**: `tests/test_content_stages.py` (18 tests)
- ✅ Pydantic schema validation
- ✅ Config file loading and search
- ✅ Default configuration fallback
- ✅ Stage and transition validation

**File**: `tests/test_content_transition.py` (10 tests)
- ✅ File transitions (copy/move)
- ✅ Metadata creation and updates
- ✅ Permission application
- ✅ Requirement checking

**File**: `tests/test_sentinel_permissions.py` (7 tests)
- ✅ Sentinel file creation (.sp-permissions)
- ✅ Git clone detection
- ✅ Permission reapplication after clone
- ✅ Immutable sentinel behavior

**File**: `tests/test_content_status.py` (10 tests)
- ✅ Status reporting across stages
- ✅ Authoritative version detection
- ✅ Next action suggestions

**File**: `tests/test_content_list.py` (10 tests)
- ✅ File listing per stage
- ✅ Metadata inclusion
- ✅ Summary statistics

**File**: `tests/test_content_diff.py` (9 tests)
- ✅ Unified diff generation
- ✅ Identical file detection
- ✅ Cross-stage comparison

**Run with**: `hatch run pytest tests/test_content_*.py -v`

---

## Missing Test Coverage ⏳

### 1. Flask Backend API (0 tests)

**File to Create**: `tests/test_content_api.py`

**Endpoints to Test**:
- GET `/api/content/config` — Configuration retrieval
- GET `/api/content/stages` — Stage list
- GET `/api/content/status?path=X` — File status
- GET `/api/content/list?stage=X` — List files in stage
- GET `/api/content/all` — All files across stages
- POST `/api/content/transition` — Execute transition
- GET `/api/content/diff?path=X&from_stage=A&to_stage=B` — Compare versions
- GET `/api/content/git/status` — Git status
- POST `/api/content/git/commit` — Commit changes
- POST `/api/content/git/push` — Push to remote
- POST `/api/content/git/pull` — Pull from remote

**Pattern to Follow**: `tests/test_gui_server_pkg.py`

```python
import pytest
pytest.importorskip("flask", reason="GUI tests require: pip install llmflow[gui]")

@pytest.fixture
def content_client(tmp_path):
    """Flask test client for content lifecycle API."""
    # Set up test config-stages.yaml
    # Import and start content_app
    # Return Flask test client
    pass

class TestContentConfigEndpoint:
    def test_returns_valid_config(self, content_client):
        resp = content_client.get('/api/content/config')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'stages' in data
        assert len(data['stages']) >= 3

class TestContentTransitionEndpoint:
    def test_transitions_file_between_stages(self, content_client, tmp_path):
        # Create test file in 'generated' stage
        # POST transition to 'editing'
        # Verify file moved and metadata created
        pass

    def test_rejects_invalid_transition(self, content_client):
        resp = content_client.post('/api/content/transition',
            json={'from_stage': 'editing', 'to_stage': 'generated', 'path': 'test.md'})
        assert resp.status_code == 400
```

**Estimated Time**: 2-3 hours to implement comprehensive Flask API tests

---

### 2. Frontend Build Validation (Not in CI)

**Current State**: Frontend builds during release (`build-release.yml`) but NOT during regular CI

**Problem**: PR merges could break the frontend build, only discovered at release time

**Solution**: Add frontend build to `.github/workflows/test.yml`

```yaml
jobs:
  test:
    # ... existing Python tests ...

  test-frontend:
    name: Test Frontend Build
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: gui/frontend/package-lock.json

    - name: Install dependencies
      run: |
        cd gui/frontend
        npm ci

    - name: Lint frontend
      run: |
        cd gui/frontend
        npm run lint

    - name: Build frontend
      run: |
        cd gui/frontend
        npm run build

    - name: Verify build artifacts
      run: |
        test -d gui/frontend/dist
        test -f gui/frontend/dist/index.html
        test -f gui/frontend/dist/content.html
```

**Benefits**:
- ✅ Catch build failures before merge
- ✅ Validate ESLint rules
- ✅ Ensure all imports resolve
- ✅ No broken React components

**Estimated Time**: 15 minutes to add to CI, ~2 min per CI run

---

### 3. React Component Tests (Optional)

**Status**: Not implemented, not required for production

**If Desired**: Use Jest + React Testing Library

**Setup** (in `gui/frontend/`):
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom jest jest-environment-jsdom
```

**Add to `package.json`**:
```json
"scripts": {
  "test": "jest"
}
```

**Example Test** (`src/components/__tests__/StageCard.test.jsx`):
```javascript
import { render, screen } from '@testing-library/react';
import StageCard from '../StageCard';

test('renders stage name', () => {
  const stage = { name: 'editing', protected: true, file_permissions: '644' };
  render(<StageCard stage={stage} files={[]} />);
  expect(screen.getByText('editing')).toBeInTheDocument();
});
```

**Recommendation**: Defer until needed. Core logic is well-tested; React is straightforward.

**Estimated Time**: 1-2 days for full component test suite

---

### 4. End-to-End Tests (Optional)

**Status**: Not implemented, optional for future

**Tool**: Playwright (not currently used anywhere in LLMFlow — this would be a new addition)

**What to Test**:
- Full workflow: Dashboard → Select file → View status → Diff → Transition
- Git panel operations
- Error states (backend down, invalid config)

**Example**:
```javascript
test('transitions file through stages', async ({ page }) => {
  await page.goto('http://localhost:5173/content.html');
  await page.click('text=generated');
  await page.click('text=hello.md');
  await page.click('button:has-text("Send to editing")');
  await expect(page.locator('text=Successfully transitioned')).toBeVisible();
});
```

**Recommendation**: Not needed now. Flask + unit tests provide sufficient coverage.

**Estimated Time**: 2-3 days for full E2E suite

---

## Recommended Immediate Actions

### Priority 1: Add Frontend Build to CI (15 min)
**Impact**: Prevents build breaks from reaching `dev` branch
**File**: `.github/workflows/test.yml`
**See**: Section 2 above

### Priority 2: Flask API Tests (2-3 hours)
**Impact**: Validates all 11 API endpoints work correctly
**File**: `tests/test_content_api.py`
**See**: Section 1 above

### Priority 3: Document Testing Standards (30 min)
**Impact**: Future contributors know how to test GUI features
**File**: This document + `TESTING.md` reference

---

## CI Test Matrix

**Current** (what runs on every push/PR):
```
✅ Python Core Logic (64 tests)
   - Schema validation
   - Transition logic
   - Sentinel permissions
   - Status/list/diff
❌ Flask API Endpoints (0 tests) — MISSING
❌ Frontend Build (npm run build) — MISSING
❌ React Component Tests (0 tests) — OPTIONAL
❌ E2E Tests (0 tests) — OPTIONAL
```

**Recommended** (minimal but robust):
```
✅ Python Core Logic (64 tests)
✅ Flask API Endpoints (11 endpoint tests) — ADD THIS
✅ Frontend Build Validation — ADD THIS
⏳ React Component Tests — OPTIONAL
⏳ E2E Tests — OPTIONAL
```

**Gold Standard** (comprehensive, future):
```
✅ Python Core Logic
✅ Flask API Endpoints
✅ Frontend Build + Lint
✅ React Component Tests (Jest + RTL)
✅ E2E Tests (Playwright)
✅ Visual Regression Tests (Percy/Chromatic)
```

---

## How Build Success is Ensured

### During Development (Local)
```bash
# Backend tests (run these before committing)
hatch run pytest tests/test_content_*.py -v

# Frontend build (verify it works)
cd gui/frontend
npm run build

# Frontend lint (fix issues)
npm run lint
```

### During CI (GitHub Actions)
**Current**: Only Python tests run
**Recommended**: Python tests + Frontend build + Flask API tests

### During Release (Tags like v0.2.2)
**Current** (in `build-release.yml`):
1. ✅ Python tests pass (required)
2. ✅ Frontend builds successfully (`python build_gui.py`)
3. ✅ GUI static files included in Nuitka bundle
4. ✅ Smoke tests run (binary works)

**This works, but frontend issues could slip into dev branch.**

---

## Implementation Plan

### Week 1: Critical Path
- [ ] Add frontend build to `.github/workflows/test.yml`
- [ ] Implement basic Flask API tests in `tests/test_content_api.py`
- [ ] Verify CI passes with new tests

### Week 2-3: Optional Enhancements
- [ ] Add React component tests if team wants them
- [ ] Set up Playwright for E2E (if desired)
- [ ] Visual regression testing (if needed for design QA)

### Ongoing: Maintenance
- [ ] Add API tests for new endpoints
- [ ] Update build validation if frontend dependencies change
- [ ] Review test coverage quarterly

---

## Summary

**Current Status**:
- ✅ Core logic: Excellent (64 tests)
- ⚠️ API endpoints: Zero coverage (manual testing only)
- ⚠️ Frontend build: Tested at release, not in CI
- ❌ E2E: None (acceptable for now)

**Minimum Viable Testing** (2-4 hours to implement):
1. Flask API endpoint tests (following existing GUI test pattern)
2. Frontend build in CI (prevents broken builds in dev)

**Gold Standard** (optional, 1-2 weeks):
3. React component tests with Jest + RTL
4. Playwright E2E tests
5. Visual regression with Percy/Chromatic

**Recommendation**: Do Priority 1 and 2 now. Defer Priority 3 until GUI complexity increases or team requests it.

---

## Files Referenced

- `.github/workflows/test.yml` — Python test CI
- `.github/workflows/build-release.yml` — Frontend build CI (releases only)
- `tests/test_gui_server_pkg.py` — Pattern to follow for Flask tests
- `tests/test_content_*.py` — Existing core logic tests (64 tests)
- `gui/frontend/package.json` — Frontend build scripts
- `gui/backend/content_app.py` — Flask API to test
