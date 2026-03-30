# Scripture Pipelines GUI - Quick Start

## What You Have

A **working GUI MVP** with:
- ✅ Flask backend with REST API
- ✅ Project discovery via registry (`sp registry list`)
- ✅ Pipeline selection and configuration
- ✅ Pipeline execution with output display
- ✅ React frontend with Paratext 10-inspired design

## Quick Test

### 1. Start the Backend

```bash
cd gui/backend
pip install -r requirements.txt
python app.py
```

Backend runs on **http://localhost:5000**

Test it:
```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/projects
```

### 2. Start the Frontend (in a new terminal)

```bash
cd gui/frontend
npm install
npm run dev
```

Frontend runs on **http://localhost:5173**

Open in browser: **http://localhost:5173**

## What Works Now

1. **Project Discovery**: Auto-loads all registered projects from `sp registry list`
2. **Pipeline Selection**: Click a project → see its pipelines
3. **Configuration Form**: Auto-generates input fields from pipeline variables
4. **Execution**: Click "Run Pipeline" → see stdout/stderr
5. **Paratext Design**: Clean, professional UI matching Paratext 10 Studio

## Next Steps (Optional Enhancements)

- **WebSocket streaming**: Real-time progress updates (backend code already there)
- **Results viewer**: Better rendering for Markdown/JSON/XML
- **Error handling**: More detailed error messages
- **Output files**: Detect and display generated files
- **History**: Track past pipeline runs

## Install as  Package Feature

```bash
# Install GUI dependencies
pip install llmflow[gui]

# Launch GUI
sp-gui
```

The `sp-gui` command starts the backend on port 5000. Frontend must be run separately (or built and bundled with backend).

## Architecture

```
gui/
├── backend/        Flask REST API + WebSocket
│   ├── app.py      Main server (270 lines)
│   └── requirements.txt
└── frontend/       React + Tailwind + shadcn/ui
    ├── src/
    │   ├── App.jsx                Main layout
    │   ├── components/
    │   │   ├── ProjectList.jsx    Sidebar with projects/pipelines
    │   │   └── PipelineView.jsx   Config form + execution + output
    │   └── index.css              Paratext color scheme
    └── package.json
```

## API Endpoints

- `GET /api/health` - Check if sp CLI is available
- `GET /api/projects` - List all registered projects
- `GET /api/projects/<name>/pipelines` - Get pipelines for a project
- `POST /api/execute` - Execute a pipeline (blocking)
- WebSocket: `execute_pipeline` - Execute with streaming output

## Estimated Completion

- **Backend**: 80% complete (needs WebSocket integration)
- **Frontend**: 60% complete (needs results viewer, better error handling)
- **Overall MVP**: **~1 more day of work** to polish

This MVP took ~2 hours to build thanks to the registry infrastructure!
