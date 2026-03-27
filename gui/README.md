# Scripture Pipelines GUI

Web-based graphical interface for Scripture Pipelines.

## Architecture

- **Backend**: Flask + Flask-SocketIO (Python)
- **Frontend**: React + shadcn/ui + Tailwind CSS
- **Design**: Paratext 10 Studio inspired

## Features

- Project discovery via registry
- Pipeline selection and configuration
- Real-time execution with progress streaming
- Results viewer (Markdown/JSON/XML)

## Development

### Backend
```bash
cd gui/backend
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd gui/frontend
npm install
npm run dev
```

## Installation

Install with GUI dependencies:
```bash
pip install llmflow[gui]
sp gui
```
