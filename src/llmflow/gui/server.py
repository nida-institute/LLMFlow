#!/usr/bin/env python3
"""
Scripture Pipelines GUI Server (Production)

Flask server that serves bundled static frontend and provides REST API.
This version is designed to be bundled with nuitka.
"""

import logging
import sys
import json
import subprocess
import threading
import webbrowser
import uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room

logger = logging.getLogger(__name__)

# Allowed origins for CORS — localhost only; this server is designed for local use
_CORS_ORIGINS = [
    "http://localhost:5000",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

_PIPELINE_EXTENSIONS = {".yaml", ".yml"}

# Import testable execution logic
from .executor import PipelineExecutor


def create_app():
    """Create and configure the Flask application."""

    # Get static files directory (bundled with package)
    if getattr(sys, 'frozen', False):
        # Running in nuitka bundle
        base_path = Path(getattr(sys, '_MEIPASS', str(Path(__file__).parent)))
    else:
        # Running in development
        base_path = Path(__file__).parent

    static_folder = base_path / "static"

    app = Flask(__name__,
                static_folder=str(static_folder),
                static_url_path='')
    assert app.static_folder is not None, "Flask static_folder must be set"
    _static_folder: str = app.static_folder

    CORS(app, origins=_CORS_ORIGINS)
    socketio = SocketIO(app, cors_allowed_origins=_CORS_ORIGINS, async_mode='threading')

    # =============================================================================
    # Static File Serving
    # =============================================================================

    @app.route('/')
    def serve_index():
        """Serve the React app index.html."""
        return send_from_directory(_static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        """Serve static files (JS, CSS, etc.)."""
        if (Path(_static_folder) / path).exists():
            return send_from_directory(_static_folder, path)
        else:
            # For client-side routing, return index.html
            return send_from_directory(_static_folder, 'index.html')

    # =============================================================================
    # Registry API - Project Discovery
    # =============================================================================

    @app.route('/api/projects', methods=['GET'])
    def get_projects():
        """Get all registered projects from sp registry."""
        try:
            result = subprocess.run(
                ['sp', 'registry', 'list', 'projects', '--json'],
                capture_output=True,
                text=True,
                check=True
            )
            # sp registry returns {"projects": [...]} - return as-is
            data = json.loads(result.stdout)
            return jsonify(data)
        except subprocess.CalledProcessError as e:
            return jsonify({'error': str(e), 'stderr': e.stderr}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500


    @app.route('/api/projects/<project_name>/pipelines', methods=['GET'])
    def get_project_pipelines(project_name):
        """Get all pipelines for a specific project."""
        try:
            # Get project info to get path
            result = subprocess.run(
                ['sp', 'registry', 'info', 'project', project_name],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse output for path
            project_path = None
            for line in result.stdout.splitlines():
                if line.startswith('path'):
                    project_path = line.split(':', 1)[1].strip()
                    break

            if not project_path:
                return jsonify({'error': 'Project path not found'}), 404

            # Find pipelines directory - check multiple possible locations
            pipelines_dir = None
            possible_dirs = [
                Path(project_path) / 'pipelines',
                Path(project_path) / 'LLMFlow' / 'pipelines',
            ]

            for possible_dir in possible_dirs:
                if possible_dir.exists():
                    pipelines_dir = possible_dir
                    break

            if not pipelines_dir:
                return jsonify({'pipelines': []})

            # List YAML files
            pipelines = []
            for pattern in ['*.yaml', '*.yml']:
                for yaml_file in pipelines_dir.rglob(pattern):
                    relative_path = yaml_file.relative_to(pipelines_dir)
                    pipelines.append({
                        'name': yaml_file.stem,
                        'path': str(relative_path),
                        'full_path': str(yaml_file)
                    })

            return jsonify({'pipelines': sorted(pipelines, key=lambda x: x['name'])})

        except subprocess.CalledProcessError as e:
            return jsonify({'error': str(e), 'stderr': e.stderr}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500


    @app.route('/api/pipeline/config', methods=['POST'])
    def get_pipeline_config():
        """Load pipeline YAML configuration."""
        try:
            import yaml

            data = request.get_json(silent=True)
            if not data or not isinstance(data, dict):
                return jsonify({'error': 'JSON body required'}), 400

            pipeline_path = data.get('pipeline_path')
            if not pipeline_path:
                return jsonify({'error': 'pipeline_path required'}), 400

            path = Path(pipeline_path).resolve()
            if path.suffix not in _PIPELINE_EXTENSIONS:
                return jsonify({'error': 'Invalid pipeline file'}), 400
            if not path.is_file():
                return jsonify({'error': 'Pipeline file not found'}), 404

            with open(path, 'r') as f:
                config = yaml.safe_load(f)

            return jsonify(config)

        except Exception as e:
            logger.error("Error loading pipeline config: %s", e)
            return jsonify({'error': 'Failed to load pipeline configuration'}), 500


    # =============================================================================
    # Pipeline Execution API
    # =============================================================================

    @app.route('/api/execute', methods=['POST'])
    def execute_pipeline():
        """Execute a pipeline (simple version without streaming)."""
        try:
            data = request.json
            pipeline_path = data.get('pipeline_path')
            variables = data.get('variables', {})
            project_path = data.get('project_path')

            if not pipeline_path:
                return jsonify({'error': 'pipeline_path required'}), 400

            pipeline_resolved = Path(pipeline_path).resolve()
            if pipeline_resolved.suffix not in _PIPELINE_EXTENSIONS:
                return jsonify({'error': 'Invalid pipeline file'}), 400

            # Determine working directory and pipeline path
            if project_path and Path(project_path).exists():
                # Run from project directory
                cwd = project_path
                # Make pipeline path relative to project directory
                pipeline_file = Path(pipeline_path)
                if pipeline_file.is_absolute():
                    try:
                        pipeline_rel = pipeline_file.relative_to(project_path)
                        pipeline_arg = str(pipeline_rel)
                    except ValueError:
                        # Not relative to project, use absolute
                        pipeline_arg = str(pipeline_path)
                else:
                    pipeline_arg = str(pipeline_path)
            else:
                # Fallback: use absolute path and current directory
                cwd = None
                pipeline_arg = str(pipeline_path)

            # Build sp run command
            cmd = ['sp', 'run', '--pipeline', pipeline_arg]

            for key, value in variables.items():
                cmd.extend(['--var', f'{key}={value}'])

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd
            )

            return jsonify({
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_code': result.returncode
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500


    # =============================================================================
    # WebSocket - Real-time Pipeline Execution
    # =============================================================================

    @socketio.on('execute_pipeline')
    def handle_execute_pipeline(data):
        """Execute pipeline with real-time output streaming via WebSocket."""
        execution_id = data.get('execution_id')

        try:
            pipeline_path = data.get('pipeline_path')
            variables = data.get('variables', {})
            project_path = data.get('project_path')

            if not pipeline_path:
                emit('error', {'message': 'pipeline_path required'})
                return

            if Path(pipeline_path).resolve().suffix not in _PIPELINE_EXTENSIONS:
                emit('error', {'message': 'Invalid pipeline file'})
                return

            if not execution_id:
                emit('error', {'message': 'execution_id required'})
                return

            # Join this execution's room
            join_room(execution_id)

            # Create emit callback that routes to the execution's room
            def emit_to_room(event_type, data):
                emit(event_type, data, to=execution_id)
                socketio.sleep(0)  # Yield to process other events

            # Execute pipeline using testable executor
            executor = PipelineExecutor(
                pipeline_path=pipeline_path,
                project_path=project_path,
                variables=variables,
                execution_id=execution_id,
                emit_callback=emit_to_room
            )

            result = executor.execute()

            # Send completion
            emit('complete', {
                'success': result['success'],
                'exit_code': result['exit_code'],
                'created_files': result['created_files'],
                'telemetry': result['telemetry']
            }, to=execution_id)

        except Exception as e:
            emit('error', {'message': str(e)}, to=execution_id if execution_id else None)


    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        emit('status', {'message': 'Connected to Scripture Pipelines server'})


    return app, socketio


def start_server(host='127.0.0.1', port=5000, open_browser=True):
    """Start the GUI server and optionally open browser."""
    app, socketio = create_app()

    url = f"http://{host}:{port}"
    print(f"\n")
    print(f"{'='*60}")
    print(f"Scripture Pipelines GUI")
    print(f"{'='*60}")
    print(f"\n  🌐 Server running at: {url}")
    print(f"\n  Press Ctrl+C to stop the server")
    print(f"{'='*60}\n")

    if open_browser:
        # Open browser after a short delay
        def open_in_browser():
            import time
            time.sleep(1.5)
            webbrowser.open(url)

        threading.Thread(target=open_in_browser, daemon=True).start()

    try:
        socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down GUI server...")


if __name__ == '__main__':
    import sys
    start_server()
