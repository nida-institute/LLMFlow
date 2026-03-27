#!/usr/bin/env python3
"""
Scripture Pipelines GUI Server (Production)

Flask server that serves bundled static frontend and provides REST API.
This version is designed to be bundled with nuitka.
"""

import os
import sys
import json
import subprocess
import threading
import webbrowser
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit


def create_app():
    """Create and configure the Flask application."""

    # Get static files directory (bundled with package)
    if getattr(sys, 'frozen', False):
        # Running in nuitka bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development
        base_path = Path(__file__).parent

    static_folder = base_path / "static"

    app = Flask(__name__,
                static_folder=str(static_folder),
                static_url_path='')

    CORS(app)
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

    # =============================================================================
    # Static File Serving
    # =============================================================================

    @app.route('/')
    def serve_index():
        """Serve the React app index.html."""
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        """Serve static files (JS, CSS, etc.)."""
        if (Path(app.static_folder) / path).exists():
            return send_from_directory(app.static_folder, path)
        else:
            # For client-side routing, return index.html
            return send_from_directory(app.static_folder, 'index.html')

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

            data = request.json
            pipeline_path = data.get('pipeline_path')

            if not pipeline_path:
                return jsonify({'error': 'pipeline_path required'}), 400

            if not Path(pipeline_path).exists():
                return jsonify({'error': 'Pipeline file not found'}), 404

            with open(pipeline_path, 'r') as f:
                config = yaml.safe_load(f)

            return jsonify(config)

        except Exception as e:
            return jsonify({'error': str(e)}), 500


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

            # Log execution details for debugging
            print(f"DEBUG: Executing from cwd={cwd}")
            print(f"DEBUG: Command: {' '.join(cmd)}")

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
        try:
            pipeline_path = data.get('pipeline_path')
            variables = data.get('variables', {})
            project_path = data.get('project_path')

            if not pipeline_path:
                emit('error', {'message': 'pipeline_path required'})
                return

            emit('status', {'message': 'Starting pipeline...', 'stage': 'init'})

            # Determine working directory and pipeline path
            if project_path and Path(project_path).exists():
                cwd = project_path
                pipeline_file = Path(pipeline_path)
                if pipeline_file.is_absolute():
                    try:
                        pipeline_rel = pipeline_file.relative_to(project_path)
                        pipeline_arg = str(pipeline_rel)
                    except ValueError:
                        pipeline_arg = str(pipeline_path)
                else:
                    pipeline_arg = str(pipeline_path)
            else:
                cwd = None
                pipeline_arg = str(pipeline_path)

            # Build command
            cmd = ['sp', 'run', '--pipeline', pipeline_arg]
            for key, value in variables.items():
                cmd.extend(['--var', f'{key}={value}'])

            # Execute with streaming output
            import os
            import time
            import select
            import sys
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,
                cwd=cwd,
                env=env
            )

            # Stream output with throttling and heartbeat
            buffer = []
            last_emit = time.time()
            last_heartbeat = time.time()
            EMIT_INTERVAL = 0.5  # Send batches every 0.5 second
            HEARTBEAT_INTERVAL = 2.0  # Show "still running" every 2 seconds
            CHECK_INTERVAL = 0.2  # Check for output every 0.2 seconds

            while True:
                now = time.time()
                
                # Check if there's data to read (non-blocking)
                ready = select.select([process.stdout], [], [], CHECK_INTERVAL)[0]
                if ready:
                    line = process.stdout.readline()
                    if line:
                        buffer.append(line.rstrip())
                        # Reset heartbeat timer when we get output
                        last_heartbeat = now
                
                # Check if process finished
                if process.poll() is not None:
                    break
                
                # Emit buffer if interval passed or buffer is large
                if buffer and ((now - last_emit >= EMIT_INTERVAL) or len(buffer) >= 30):
                    emit('output_batch', {'lines': buffer})
                    buffer = []
                    last_emit = now
                    last_heartbeat = now
                
                # Send heartbeat if no activity for a while
                if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                    emit('heartbeat', {'message': '⏳ Pipeline is running...'})
                    last_heartbeat = now
                    socketio.sleep(0)  # Yield to process other events

            process.wait()

            # Send completion
            emit('complete', {
                'success': process.returncode == 0,
                'exit_code': process.returncode
            })

        except Exception as e:
            emit('error', {'message': str(e)})


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
