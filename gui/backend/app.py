#!/usr/bin/env python3
"""
Scripture Pipelines GUI Backend

Flask server providing REST API and WebSocket for pipeline execution.
"""

import os
import json
import subprocess
import yaml
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


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
        projects = json.loads(result.stdout)
        return jsonify({'projects': projects})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e), 'stderr': e.stderr}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<project_name>/pipelines', methods=['GET'])
def get_project_pipelines(project_name):
    """Get all pipelines for a specific project."""
    try:
        # First get project info to get path
        result = subprocess.run(
            ['sp', 'registry', 'info', 'project', project_name],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse output to get path (simple parsing)
        project_path = None
        for line in result.stdout.split('\n'):
            if 'path:' in line.lower():
                project_path = line.split(':', 1)[1].strip()
                break

        if not project_path:
            return jsonify({'error': 'Could not find project path'}), 404

        # Scan for pipeline files
        pipelines_dir = Path(project_path) / 'pipelines'
        if not pipelines_dir.exists():
            return jsonify({'pipelines': []})

        pipelines = []
        for yaml_file in pipelines_dir.glob('*.yaml'):
            try:
                with open(yaml_file, 'r') as f:
                    config = yaml.safe_load(f)
                    pipelines.append({
                        'name': yaml_file.stem,
                        'file': yaml_file.name,
                        'path': str(yaml_file),
                        'description': config.get('description', ''),
                        'variables': config.get('variables', {})
                    })
            except Exception as e:
                print(f"Error reading {yaml_file}: {e}")
                continue

        return jsonify({'pipelines': pipelines})

    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e), 'stderr': e.stderr}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Pipeline Execution API
# =============================================================================

@app.route('/api/execute', methods=['POST'])
def execute_pipeline():
    """Execute a pipeline with given parameters."""
    data = request.json
    pipeline_path = data.get('pipeline_path')
    variables = data.get('variables', {})

    if not pipeline_path:
        return jsonify({'error': 'pipeline_path is required'}), 400

    try:
        # Build command
        cmd = ['sp', 'run', '--pipeline', pipeline_path]

        # Add variables
        for key, value in variables.items():
            cmd.extend(['--var', f'{key}={value}'])

        # Execute (non-blocking for now - TODO: use WebSocket for streaming)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(pipeline_path).parent.parent
        )

        return jsonify({
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# WebSocket for Real-time Pipeline Execution
# =============================================================================

@socketio.on('execute_pipeline')
def handle_execute_pipeline(data):
    """Execute pipeline with real-time progress updates via WebSocket."""
    pipeline_path = data.get('pipeline_path')
    variables = data.get('variables', {})

    if not pipeline_path:
        emit('error', {'message': 'pipeline_path is required'})
        return

    try:
        # Build command
        cmd = ['sp', 'run', '--pipeline', pipeline_path]
        for key, value in variables.items():
            cmd.extend(['--var', f'{key}={value}'])

        # Start process
        emit('status', {'message': 'Starting pipeline...', 'status': 'running'})

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(pipeline_path).parent.parent,
            bufsize=1
        )

        # Stream output
        for line in process.stdout:
            emit('output', {'line': line.rstrip()})

        # Wait for completion
        process.wait()

        if process.returncode == 0:
            emit('complete', {'message': 'Pipeline completed successfully'})
        else:
            stderr = process.stderr.read()
            emit('error', {'message': f'Pipeline failed: {stderr}'})

    except Exception as e:
        emit('error', {'message': str(e)})


# =============================================================================
# Health Check
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Check if sp CLI is available
        result = subprocess.run(
            ['sp', '--version'],
            capture_output=True,
            text=True
        )
        sp_available = result.returncode == 0
    except FileNotFoundError:
        sp_available = False

    return jsonify({
        'status': 'ok',
        'sp_cli_available': sp_available
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Scripture Pipelines GUI Backend")
    print(f"📡 Starting server on http://localhost:{port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
