# Frontend Testing Strategy

## Current Problem

Frontend tests only verify that components **import**, not that they **render correctly or are visible to users**.

**What we tested:**
- ✓ Components load without syntax errors
- ✓ Backend APIs respond with 200 status

**What we didn't test:**
- ✗ Page actually displays content to users
- ✗ CSS loads and renders correctly
- ✗ No JavaScript runtime errors
- ✗ End-to-end user workflows
- ✗ Component state updates work
- ✗ User interactions (clicks, forms, navigation)

## Recommended Testing Stack

### 1. **TypeScript Migration** (Type Safety)
**Current:** Plain JavaScript (`.jsx`)
**Proposed:** TypeScript (`.tsx`)

**Benefits:**
- Catch prop type errors at compile time
- IDE autocomplete for component APIs
- Prevent runtime errors from undefined properties
- Self-documenting code

**Effort:** Medium (2-3 days to migrate existing components)

**Example:**
```typescript
interface StageCardProps {
  stage: StageConfig;
  files: FileInfo[];
  onTransition: (file: string, from: string, to: string) => void;
}

const StageCard: React.FC<StageCardProps> = ({ stage, files, onTransition }) => {
  // TypeScript ensures all props exist and have correct types
}
```

### 2. **Vitest + React Testing Library** (Unit/Component Tests)
**Status:** Already installed, but tests are too shallow

**What to add:**
- Render tests that verify actual DOM output
- User interaction tests (clicks, form submissions)
- State update tests (async data loading)
- Accessibility tests (screen readers, keyboard nav)

**Example Real Test:**
```javascript
it('displays stage cards with actual content', async () => {
  render(<ContentDashboard />);

  await waitFor(() => {
    // Verify user sees stage names
    expect(screen.getByText('generated')).toBeVisible();
    expect(screen.getByText('editing')).toBeVisible();
    expect(screen.getByText('published')).toBeVisible();
  });
});
```

### 3. **Playwright** (End-to-End Tests)
**Status:** Not installed
**Purpose:** Verify the actual user experience in a real browser

**What it catches:**
- Blank screens (our current issue)
- CSS not loading
- API integration failures
- Navigation broken
- Forms not submitting
- WebSocket disconnections

**Example E2E Test:**
```javascript
test('user can view content lifecycle dashboard', async ({ page }) => {
  await page.goto('http://localhost:5173/');

  // Should NOT see blank screen
  await expect(page.locator('h1')).toContainText('Scripture Pipelines');

  // Should see content when loaded
  await expect(page.getByText('Select a project')).toBeVisible();
});
```

**Run in CI:** Yes - Playwright has GitHub Actions integration

### 4. **ESLint + Prettier** (Code Quality)
**Status:** ESLint installed, Prettier not configured
**Purpose:** Enforce consistent code style, catch common errors

**Recommended rules:**
- `react-hooks/rules-of-hooks` - Prevent hook errors
- `react-hooks/exhaustive-deps` - Fix useEffect dependencies
- No unused variables
- Consistent naming conventions

## Implementation Plan

### Phase 1: Fix Current Tests (1 day)
- [ ] Replace import-only tests with real rendering tests
- [ ] Add visibility assertions (`toBeVisible()`)
- [ ] Mock APIs properly with realistic data
- [ ] Add async state update tests

### Phase 2: Add Playwright E2E (2-3 days)
- [ ] Install Playwright
- [ ] Write 5-10 critical path tests:
  - Homepage loads
  - Projects list appears
  - Content lifecycle dashboard renders
  - Pipeline execution works
  - File transitions work
- [ ] Add Playwright to GitHub Actions
- [ ] Configure browser matrix (Chromium, Firefox, WebKit)

### Phase 3: TypeScript Migration (3-5 days)
- [ ] Add TypeScript to build tooling
- [ ] Convert one component (start with simple ones)
- [ ] Define interfaces for all data types
- [ ] Gradually migrate remaining components
- [ ] Enable strict mode

### Phase 4: Comprehensive Coverage (ongoing)
- [ ] Test coverage target: 80%+ for components
- [ ] Accessibility testing with axe-core
- [ ] Visual regression testing (optional)
- [ ] Performance budgets (optional)

## Testing Pyramid

```
         /\
        /E2E\       Playwright (5-10 tests)
       /------\
      /  Int   \    Vitest integration (20-30 tests)
     /----------\
    /   Unit     \  Vitest unit (40-60 tests)
   /--------------\
```

## Single Command Testing

**Goal:** `pytest && npm test` gives confidence

**Pytest** (backend):
```bash
hatch run pytest tests/ -v
```

**npm test** (frontend):
```bash
cd gui/frontend
npm test              # Unit tests
npm run test:e2e      # Playwright E2E
```

**CI Integration:**
```yaml
- name: Frontend Tests
  run: |
    cd gui/frontend
    npm ci
    npm test
    npm run test:e2e
```

## Why This Matters

**Current situation:** Frontend passes tests but shows blank screen to users.

**With proper testing:**
- E2E test would fail immediately ("page is blank")
- TypeScript would catch missing CSS imports
- Real render tests would verify content appears
- CI would block merges that break the UI

## Questions to Decide

1. **TypeScript:** Migrate now or defer?
   Recommendation: **Start Phase 2 first** (Playwright), then add TypeScript gradually

2. **Test coverage target:** 80%? 90%? 70%?
   Recommendation: **75% for components**, focus on critical paths

3. **Visual regression testing:** Needed?
   Recommendation: **Not yet** - solve functional tests first

4. **Playwright browsers:** All three (Chrome/Firefox/Safari)?
   Recommendation: **Chromium + Firefox** to start

## Acceptance Criteria

This issue is done when:
- [ ] `npm test` includes real rendering tests (not just imports)
- [ ] Playwright runs 5+ E2E tests in CI
- [ ] TypeScript configured (even if migration in progress)
- [ ] Blank screen = test failure (automatic detection)
- [ ] Documentation updated with testing workflows

## Related Issues

- #103 - Content Lifecycle GUI (where blank screen was discovered)
- #104 - Testing strategy (backend API tests)
