#!/usr/bin/env python3
"""
Scripture Pipelines GUI Server (Production)

Flask server that serves bundled static frontend and provides REST API.
This version is designed to be bundled with nuitka.
"""

import json
import logging
import platform
import socket
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room

logger = logging.getLogger(__name__)

# CORS configuration — localhost only; this server is designed for local use
# Use regex patterns to accept any port on localhost (for dynamic port selection)
_CORS_ORIGINS = [
    r"http://localhost:\d+",   # Any port on localhost
    r"http://127\.0\.0\.1:\d+", # Any port on 127.0.0.1
]

_PIPELINE_EXTENSIONS = {".yaml", ".yml"}

# Import testable execution logic
try:
    from .executor import PipelineExecutor
except ImportError:
    from executor import PipelineExecutor  # type: ignore[import-not-found]


def create_app():
    """Create and configure the Flask application."""

    # Get static files directory (bundled with package)
    if getattr(sys, 'frozen', False):
        # Running in nuitka bundle
        base_path = Path(getattr(sys, '_MEIPASS', __file__))
    else:
        # Running in development
        base_path = Path(__file__).parent

    static_folder = base_path / "static"

    app = Flask(__name__,
                static_folder=str(static_folder),
                static_url_path='')

    # CORS: Accept any localhost port (for dynamic port selection)
    CORS(app, origins=_CORS_ORIGINS, supports_credentials=True)

    # SocketIO CORS: Use '*' for local-only server (safe since we bind to localhost)
    socketio = SocketIO(
        app,
        cors_allowed_origins='*',  # Local development only - server binds to 127.0.0.1
        async_mode='threading'
    )

    # =============================================================================
    # Static File Serving
    # =============================================================================

    @app.route('/')
    def serve_index():
        """Serve the React app index.html."""
        if app.static_folder is None:
            return "Static folder not configured", 500
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        """Serve static files (JS, CSS, etc.)."""
        if app.static_folder is None:
            return "Static folder not configured", 500
        if (Path(app.static_folder) / path).exists():
            return send_from_directory(app.static_folder, path)
        else:
            # For client-side routing, return index.html
            return send_from_directory(app.static_folder, 'index.html')

    # =============================================================================
    # Health Check
    # =============================================================================

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Check if sp CLI is available."""
        try:
            result = subprocess.run(
                ['sp', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            sp_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            sp_available = False

        return jsonify({
            'sp_cli_available': sp_available,
            'status': 'ok'
        })

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


    @app.route('/api/content/config', methods=['GET'])
    def get_content_config():
        """Get content lifecycle configuration for a project."""
        project_path = request.args.get('project_path')

        if not project_path:
            return jsonify({'error': 'project_path parameter required'}), 400

        try:
            project_path_obj = Path(project_path)

            # Look for content lifecycle config in common locations
            possible_configs = [
                project_path_obj / 'content-lifecycle.yaml',
                project_path_obj / 'LLMFlow' / 'content-lifecycle.yaml',
                project_path_obj / 'config' / 'content-lifecycle.yaml',
            ]

            for config_path in possible_configs:
                if config_path.exists():
                    # TODO: Parse YAML and return actual stages
                    # For now, return a valid but minimal response
                    return jsonify({
                        'success': True,
                        'config_path': str(config_path),
                        'stages': [
                            {'name': 'draft', 'label': 'Draft'},
                            {'name': 'review', 'label': 'Review'},
                            {'name': 'approved', 'label': 'Approved'},
                        ],
                        'project_path': str(project_path)
                    })

            # No config found - return default stages
            return jsonify({
                'success': True,
                'config_path': None,
                'stages': [
                    {'name': 'draft', 'label': 'Draft'},
                    {'name': 'review', 'label': 'Review'},
                    {'name': 'approved', 'label': 'Approved'},
                ],
                'project_path': str(project_path),
                'message': 'Using default stages (no config file found)'
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500


    @app.route('/api/content/all', methods=['GET'])
    def get_content_all():
        """Get all files across all content lifecycle stages."""
        project_path = request.args.get('project_path')

        try:
            stages_data = {
                'draft': [],
                'review': [],
                'approved': []
            }

            if project_path:
                project_path_obj = Path(project_path)

                # Look for output directories
                output_dirs = [
                    project_path_obj / 'outputs',
                    project_path_obj / 'output',
                    project_path_obj / 'results',
                    project_path_obj / 'artifacts',
                ]

                # Find all files in output directories
                for output_dir in output_dirs:
                    if output_dir.exists() and output_dir.is_dir():
                        # Recursively find all files
                        for file_path in output_dir.rglob('*'):
                            if file_path.is_file():
                                # Get relative path from project root
                                try:
                                    rel_path = file_path.relative_to(project_path_obj)

                                    # Determine stage based on directory structure or file naming
                                    # For now, put everything in draft
                                    # TODO: Implement actual stage detection
                                    stages_data['draft'].append({
                                        'path': str(rel_path),
                                        'name': file_path.name,
                                        'size': file_path.stat().st_size,
                                        'modified': file_path.stat().st_mtime
                                    })
                                except ValueError:
                                    # File is outside project root, skip
                                    continue

            return jsonify({
                'success': True,
                'stages': stages_data,
                'total_files': sum(len(files) for files in stages_data.values())
            })

        except Exception as e:
            logger.error("Error loading content files: %s", e)
            return jsonify({
                'success': False,
                'error': str(e),
                'stages': {
                    'draft': [],
                    'review': [],
                    'approved': []
                }
            }), 500


    @app.route('/api/content/status', methods=['GET'])
    def get_content_status():
        """Get detailed status for a specific file."""
        file_path = request.args.get('path')
        project_path = request.args.get('project_path')

        if not file_path:
            return jsonify({'error': 'path parameter required'}), 400

        try:
            # If project_path provided, resolve relative to it
            if project_path:
                full_path = Path(project_path) / file_path
            else:
                full_path = Path(file_path)

            if not full_path.exists():
                return jsonify({
                    'success': False,
                    'error': 'File not found'
                }), 404

            # Get file info
            stat = full_path.stat()

            return jsonify({
                'success': True,
                'path': file_path,
                'full_path': str(full_path),
                'name': full_path.name,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'current_stage': 'draft',  # TODO: Determine actual stage
                'history': [],  # TODO: Get transition history
                'metadata': {}  # TODO: Read file metadata
            })

        except Exception as e:
            logger.error("Error loading file status: %s", e)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


    @app.route('/api/content/transition', methods=['POST'])
    def content_transition():
        """Transition a file from one stage to another."""
        data = request.json

        # TODO: Implement actual file transition logic
        return jsonify({
            'success': False,
            'error': 'Content lifecycle transitions not yet implemented'
        }), 501


    # =============================================================================
    # File System Operations
    # =============================================================================

    @app.route('/api/open-folder', methods=['POST'])
    def open_folder():
        """Open a folder in the system file manager."""
        data = request.json
        folder_path = data.get('path')

        if not folder_path:
            return jsonify({'error': 'path is required'}), 400

        try:
            # Resolve to absolute path
            abs_path = Path(folder_path).resolve()

            # Verify it exists and is a directory
            if not abs_path.exists():
                return jsonify({'error': f'Path does not exist: {abs_path}'}), 404

            if not abs_path.is_dir():
                return jsonify({'error': f'Path is not a directory: {abs_path}'}), 400

            # Open with platform-specific command
            system = platform.system()
            if system == 'Darwin':  # macOS
                subprocess.run(['open', str(abs_path)], check=True)
            elif system == 'Windows':
                subprocess.run(['explorer', str(abs_path)], check=True)
            else:  # Linux and others
                subprocess.run(['xdg-open', str(abs_path)], check=True)

            return jsonify({'success': True, 'path': str(abs_path)})

        except subprocess.CalledProcessError as e:
            return jsonify({'error': f'Failed to open folder: {e}'}), 500
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
                'telemetry': result['telemetry'],
                'output_dir': result.get('output_dir')
            }, to=execution_id)

        except Exception as e:
            emit('error', {'message': str(e)}, to=execution_id if execution_id else None)


    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        emit('status', {'message': 'Connected to Scripture Pipelines server'})


    return app, socketio


def find_free_port(start_port=5000, max_attempts=100):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")


def start_server(host='127.0.0.1', port=None, open_browser=True):
    """Start the GUI server and optionally open browser."""
    app, socketio = create_app()

    # Find a free port if not specified
    if port is None:
        port = find_free_port()

    url = f"http://{host}:{port}"
    print("\n")
    print(f"{'='*60}")
    print("Scripture Pipelines GUI")
    print(f"{'='*60}")
    print(f"\n  🌐 Server running at: {url}")
    print("\n  Press Ctrl+C to stop the server")
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
