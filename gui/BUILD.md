# Building the GUI for Distribution

The Scripture Pipelines GUI is designed to be bundled into the nuitka binary for end-user distribution. This document explains the build process.

## Architecture

- **Frontend**: React 18 + Vite (development), static HTML/CSS/JS (production)
- **Backend**: Flask server that serves bundled static files and provides REST API
- **Distribution**: Single nuitka binary includes Flask + React static assets

## Build Process

### 1. Build Frontend to Static Files

```bash
cd Scripture Pipelines
python build_gui.py
```

This script:
1. Runs `npm install` in `gui/frontend/` (if needed)
2. Runs `npm run build` to create production React bundle
3. Copies built assets from `gui/frontend/dist/` to `src/llmflow/gui/static/`
4. Copies `gui/backend/server.py` to `src/llmflow/gui/server.py`

### 2. Package with hatch/pip

The built static files are included in the Python package:

```bash
pip install -e '.[gui]'
```

Or build wheel:

```bash
python -m build
```

The `pyproject.toml` configuration ensures `src/llmflow/gui/` (including static files) is bundled.

### 3. Bundle with nuitka

When building the nuitka binary:

```bash
nuitka3 --standalone --onefile \
  --include-package=llmflow.gui \
  --include-data-dir=src/llmflow/gui/static=llmflow/gui/static \
  src/llmflow/cli.py
```

The `--include-data-dir` flag ensures static assets are embedded in the binary.

## File Structure After Build

```
src/llmflow/gui/
├── __init__.py
├── server.py              # Flask server (production mode)
└── static/                # Built React app
    ├── index.html
    ├── assets/
    │   ├── index-[hash].js
    │   └── index-[hash].css
    └── ...
```

## Usage

### For End Users (nuitka binary)

```bash
sp gui
```

This:
1. Starts Flask server on localhost:5000
2. Serves bundled React app from static files
3. Opens browser automatically
4. No Python/Node environment needed!

### For Developers

**Option 1: Test bundled version**
```bash
python build_gui.py
sp gui
```

**Option 2: Development mode with hot reload**
```bash
# Terminal 1 - Backend
cd gui/backend
python app.py

# Terminal 2 - Frontend
cd gui/frontend
npm run dev
```

Visit http://localhost:5174 (frontend) which proxies API to http://localhost:5000 (backend).

## Adding to CI/CD

Add these steps to your release workflow:

```yaml
- name: Build GUI
  run: python build_gui.py

- name: Build with nuitka
  run: |
    nuitka3 --standalone --onefile \
      --include-package=llmflow.gui \
      --include-data-dir=src/llmflow/gui/static=llmflow/gui/static \
      src/llmflow/cli.py
```

## Size Impact

The bundled GUI adds approximately:
- **Flask dependencies**: ~8 MB
- **React static files**: ~2-3 MB (minified + gzipped)
- **Total**: ~10-15 MB to the nuitka binary

Users without GUI needs can simply not run `sp gui` - no extra dependencies installed.

## Troubleshooting

### Static files not found

Ensure `build_gui.py` completed successfully:
```bash
ls -la src/llmflow/gui/static/
```

Should contain `index.html` and `assets/` directory.

### Import error for server

The GUI uses optional dependencies. Ensure they're installed:
```bash
pip install 'llmflow[gui]'
```

### Nuitka missing static files

Check the nuitka command includes `--include-data-dir` flag pointing to the static directory.
