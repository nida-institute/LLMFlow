# GUI Architecture

## Dual-Location Design

The Scripture Pipelines GUI uses a **two-location architecture** to support both development and production workflows:

- **Development:** `gui/backend/` - edit code here, run dev servers
- **Production:** `src/llmflow/gui/` - synced by build script, bundled in package

### Why Two Locations?

1. **Development flexibility:** Hot reload, separate frontend/backend servers
2. **Production simplicity:** Single `sp gui` command serves bundled static files
3. **Nuitka compatibility:** Package must include all files under `src/llmflow/`

## Critical Workflow: Edit → Test → Sync → Verify

**ALWAYS follow this sequence when modifying GUI code:**

1. **Edit** in `gui/backend/`:
   - `gui/backend/server.py` - Flask routes, SocketIO handlers
   - `gui/backend/executor.py` - Pipeline execution logic

2. **Test development version:**
   ```bash
   hatch run pytest tests/test_gui_api_contract.py
   ```
   (Tests import `from gui.backend.server`)

3. **Sync to production:**
   ```bash
   python build_gui.py
   ```
   This copies:
   - `gui/backend/server.py` → `src/llmflow/gui/server.py`
   - `gui/backend/executor.py` → `src/llmflow/gui/executor.py`
   - `gui/frontend/dist/` → `src/llmflow/gui/static/`

4. **Test production version:**
   ```bash
   hatch run pytest tests/test_gui_server_pkg.py
   ```
   (Tests import `from llmflow.gui.server`)

5. **Verify with GUI:**
   ```bash
   sp gui
   ```

## Files Managed by build_gui.py

| File | Source | Destination | Purpose |
|------|--------|-------------|---------|
| `server.py` | `gui/backend/` | `src/llmflow/gui/` | Flask routes, SocketIO |
| `executor.py` | `gui/backend/` | `src/llmflow/gui/` | Pipeline execution |
| `static/*` | `gui/frontend/dist/` | `src/llmflow/gui/static/` | React frontend |

**Production runtime imports:** `from llmflow.gui.server import create_app`

## Dev-Only Files (NOT Synced to Production)

- `gui/backend/app.py` - Development server with hot reload
- `gui/backend/content_app.py` - Standalone content lifecycle API server

These files live only in `gui/backend/` and are NOT copied to `src/llmflow/gui/`.

## Common Pitfalls

### ❌ Editing src/llmflow/gui/ Directly

**NEVER** edit files in `src/llmflow/gui/` directly - they will be overwritten by `build_gui.py`.

**ALWAYS** edit in `gui/backend/`, then run the build script.

### ❌ Forgetting to Run build_gui.py

**Symptom:** Tests pass but production GUI has errors (404s, missing features)

**Cause:** You edited `gui/backend/server.py`, tests passed (they use dev version), but forgot to sync to `src/llmflow/gui/server.py` (production).

**Fix:** Run `python build_gui.py` before testing with `sp gui`

### ❌ Testing Only One Version

**Problem:** Tests import from `gui.backend` but production imports from `llmflow.gui`

**Solution:** Always run BOTH test suites:
- `test_gui_api_contract.py` - tests development version
- `test_gui_server_pkg.py` - tests production version (prevents drift)

## Frontend Development

### Quick Iteration (Hot Reload)

```bash
# Terminal 1 - Backend
cd gui/backend
python app.py

# Terminal 2 - Frontend
cd gui/frontend
npm run dev
```

Frontend proxies API calls to `localhost:5000`, React dev server runs on `localhost:5173` with hot reload.

### Production Build

```bash
cd gui/frontend
npm run build
```

Creates optimized bundle in `gui/frontend/dist/`. Build script copies this to `src/llmflow/gui/static/`.

## Testing Strategy

### test_gui_api_contract.py
- **Imports:** `from gui.backend.server import create_app`
- **Purpose:** Verify development version endpoints work
- **Run during:** Active GUI development

### test_gui_server_pkg.py
- **Imports:** `from llmflow.gui.server import create_app`
- **Purpose:** Verify production version has same endpoints as dev
- **Run before:** Releases, after running build_gui.py
- **Detects:** Sync drift between gui/backend and src/llmflow/gui

## Port Management

- **Default:** 5000
- **Dynamic:** `find_free_port()` if 5000 is occupied
- **CORS:** Regex pattern `r"http://localhost:\d+"` allows any port
- **Frontend config:** `vite.config.ts` proxies to backend port

## Nuitka Bundling

When building the standalone binary:

```bash
nuitka3 --standalone --onefile \
  --include-package=llmflow.gui \
  --include-data-dir=src/llmflow/gui/static=llmflow/gui/static \
  src/llmflow/cli.py
```

The `--include-data-dir` flag ensures static assets are embedded in the binary.

## Historical Notes

**March 2026:** Discovered duplicate server files caused production bugs (#107 follow-up). Tests imported dev version, production used outdated version. Root cause: Missing `build_gui.py` step in workflow. Added `test_gui_server_pkg.py` to catch future drift.
