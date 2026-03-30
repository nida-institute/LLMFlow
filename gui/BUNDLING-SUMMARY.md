# GUI Bundling Implementation - Summary

## What Changed

Restructured the Scripture Pipelines GUI for bundled distribution with the nuitka `sp` binary.

## Files Created/Modified

### New Files
1. **`build_gui.py`** - Build script that compiles React to static files and copies to package
2. **`gui/backend/server.py`** - Production Flask server that serves bundled static files
3. **`gui/BUILD.md`** - Comprehensive build documentation
4. **`test_gui_bundle.py`** - Test suite for verifying bundle correctness
5. **`src/llmflow/gui/__init__.py`** - Package marker for GUI module

### Modified Files
1. **`src/llmflow/cli.py`**
   - Added `gui` subcommand with `--host`, `--port`, `--no-browser` options
   - Handler imports and calls `llmflow.gui.server.start_server()`

2. **`src/llmflow/gui_launcher.py`**
   - Simplified to call `llmflow.gui.server.start_server()`
   - Removed development-mode subprocess approach

3. **`gui/frontend/vite.config.js`**
   - Added production build configuration
   - Configured output directory and minification
   - Added WebSocket proxy for socket.io

4. **`pyproject.toml`**
   - Updated force-include to bundle `src/llmflow/gui/` (including static assets)

5. **`gui/README.md`**
   - Added end-user instructions
   - Added build/distribution section
   - Clarified development vs production workflows

## Architecture

### Development Mode (Hot Reload)
- Backend: `python gui/backend/app.py` (Flask dev server)
- Frontend: `npm run dev` (Vite dev server on port 5174)
- Frontend proxies API requests to backend

### Production Mode (Bundled)
- `python build_gui.py` builds React to `src/llmflow/gui/static/`
- `sp gui` starts Flask serving static files + REST API
- All runs from single server on port 5000
- Browser auto-opens to http://localhost:5000

### Nuitka Bundle
- Include `llmflow.gui` package
- Include `src/llmflow/gui/static/` as data directory
- Flask + React assets embedded in binary
- No external Python/Node needed!

## Usage

### For End Users
```bash
sp gui
```

### For Developers

**Test production build:**
```bash
python build_gui.py
sp gui
```

**Development with hot reload:**
```bash
# Terminal 1
cd gui/backend && python app.py

# Terminal 2
cd gui/frontend && npm run dev
# Visit http://localhost:5174
```

## Size Impact

Adds ~10-15 MB to nuitka binary:
- Flask dependencies: ~8 MB
- React minified assets: ~2-3 MB

Optional install - CLI-only users unaffected.

## Nuitka Build Command

```bash
nuitka3 --standalone --onefile \
  --include-package=llmflow.gui \
  --include-data-dir=src/llmflow/gui/static=llmflow/gui/static \
  src/llmflow/cli.py
```

## Testing

Run test suite:
```bash
python test_gui_bundle.py
```

Verifies:
- ✅ `build_gui.py` completes successfully
- ✅ Static files created in correct location
- ✅ `llmflow.gui.server` module imports
- ✅ `sp gui` command available and works

## Next Steps for Production

1. Add `python build_gui.py` to CI/CD before nuitka build
2. Update release workflow with nuitka data directory flags
3. Test bundled binary on clean systems
4. Document GUI in main README and release notes

## Benefits

✅ Single binary distribution (no external runtimes)
✅ Professional UI without complexity for users
✅ Developers can still use hot reload
✅ Optional feature - doesn't affect CLI users
✅ Leverages registry system (no manual project configuration)
