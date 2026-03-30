# Scripture Pipelines GUI

Web-based graphical interface for Scripture Pipelines.

## Architecture

- **Backend**: Flask + Flask-SocketIO (Python)
- **Frontend**: React + shadcn/ui + Tailwind CSS
- **Design**: Paratext 10 Studio inspired
- **Distribution**: Bundled into nuitka binary (no Node/Python needed for end users!)

## Features

- Project discovery via registry
- Pipeline selection and configuration
- Real-time execution with progress streaming
- Results viewer (Markdown/JSON/XML)

## For End Users

If you have the `sp` binary installed, simply run:

```bash
sp gui
```

This will:
1. Start the GUI server on http://localhost:5000
2. Automatically open your browser
3. No Python or Node.js installation needed!

To stop: Press `Ctrl+C` in the terminal.

## For Developers

### Quick Test (Production Build)

Build and test the bundled version:

```bash
# From LLMFlow root directory
python build_gui.py
sp gui
```

### Development Mode (Hot Reload)

**Terminal 1 - Backend:**
```bash
cd gui/backend
pip install -r requirements.txt
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd gui/frontend
npm install
npm run dev
```

Visit http://localhost:5174 - the frontend will proxy API requests to the Flask backend.

### Building for Distribution

See [BUILD.md](BUILD.md) for complete build documentation.

**Quick summary:**
```bash
# Build frontend and copy to package
python build_gui.py

# Test bundled version
sp gui

# Include in nuitka build
nuitka3 --standalone --onefile \
  --include-package=llmflow.gui \
  --include-data-dir=src/llmflow/gui/static=llmflow/gui/static \
  src/llmflow/cli.py
```

## Size Impact

The GUI adds ~10-15 MB to the nuitka binary:
- Flask dependencies: ~8 MB
- React static files: ~2-3 MB (minified)

Users who don't need the GUI are not impacted - the dependencies are optional.

## Installation (Optional GUI Dependencies)

For development or if GUI not bundled in your binary:
```bash
pip install llmflow[gui]
```
