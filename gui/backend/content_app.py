#!/usr/bin/env python3
"""
Content Lifecycle Management GUI Backend

Flask server providing REST API for content lifecycle operations.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any

from flask import Flask, jsonify, request
from flask_cors import CORS

from llmflow.utils.content_status import get_content_status, format_status
from llmflow.utils.content_list import list_content, format_content_list
from llmflow.utils.content_diff import diff_content
from llmflow.utils.content_transition import transition_content
from llmflow.utils.content_stages_loader import get_content_stages_config

app = Flask(__name__)
CORS(app)


# =============================================================================
# Root Route
# =============================================================================

@app.route('/')
def index():
    """Root route showing API documentation."""
    return """
    <html>
    <head><title>Content Lifecycle API</title></head>
    <body style="font-family: sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
        <h1>🚀 Content Lifecycle Management API</h1>
        <p>Backend API server is running! The frontend React UI needs to be built separately.</p>

        <h2>Available API Endpoints:</h2>
        <ul>
            <li><code>GET /api/content/config</code> - Get stage configuration</li>
            <li><code>GET /api/content/stages</code> - List all stages</li>
            <li><code>GET /api/content/status?path=FILENAME</code> - Get file status</li>
            <li><code>GET /api/content/list/STAGE</code> - List files in a stage</li>
            <li><code>GET /api/content/all</code> - List files across all stages</li>
            <li><code>POST /api/content/transition</code> - Transition files between stages</li>
            <li><code>GET /api/content/diff?path=FILE&from_stage=X&to_stage=Y</code> - Compare versions</li>
            <li><code>GET /api/content/git/status</code> - Get git status</li>
            <li><code>POST /api/content/git/commit</code> - Commit changes</li>
            <li><code>POST /api/content/git/push</code> - Push to remote</li>
            <li><code>POST /api/content/git/pull</code> - Pull from remote</li>
        </ul>

        <h2>CLI Alternative:</h2>
        <p>Use the CLI commands instead:</p>
        <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
sp content status FILENAME
sp content list STAGE
sp content diff FILENAME --from-stage X --to-stage Y
sp transition FROM TO FILENAME</pre>

        <h2>Try the API:</h2>
        <p><a href="/api/content/config">View Configuration</a></p>
    </body>
    </html>
    """


# =============================================================================
# Configuration API
# =============================================================================

@app.route('/api/content/config', methods=['GET'])
def get_config():
    """Get current content stages configuration."""
    try:
        # Support project_path parameter for GUI integration
        project_path = request.args.get('project_path', None)
        content_root = request.args.get('content_root', './content')
        config_path = request.args.get('config_path', None)

        if project_path:
            # Look for config in project directory
            project_dir = Path(project_path)
            # Try these locations in order:
            # 1. project/config/content-stages.yaml
            # 2. project/content-stages.yaml
            # 3. project/.sp/content-stages.yaml
            candidates = [
                project_dir / 'config' / 'content-stages.yaml',
                project_dir / 'content-stages.yaml',
                project_dir / '.sp' / 'content-stages.yaml',
            ]
            for candidate in candidates:
                if candidate.exists():
                    config_path = candidate
                    break

        if config_path:
            config_path = Path(config_path)

        config = get_content_stages_config(config_path)

        # Convert Pydantic models to dict
        return jsonify({
            'success': True,
            'stages': [
                {
                    'name': stage.name,
                    'protected': stage.protected,
                    'immutable': stage.immutable,
                    'file_permissions': stage.file_permissions,
                    'git_tracked': stage.git_tracked,
                    'auto_create_metadata': stage.auto_create_metadata,
                }
                for stage in config.stages
            ],
            'transitions': [
                {
                    'from': trans.from_stage,
                    'to': trans.to_stage,
                    'action': trans.action,
                    'requirements': [
                        {'type': req.type, 'message': req.message}
                        for req in (trans.requirements or [])
                    ]
                }
                for trans in config.transitions
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/content/stages', methods=['GET'])
def list_stages():
    """Get list of stage names."""
    try:
        config_path = request.args.get('config_path', None)
        if config_path:
            config_path = Path(config_path)

        config = get_content_stages_config(config_path)

        stages = [
            {
                'name': stage.name,
                'protected': stage.protected,
                'immutable': stage.immutable,
            }
            for stage in config.stages
        ]

        return jsonify({'success': True, 'stages': stages})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Content Status API
# =============================================================================

@app.route('/api/content/status', methods=['GET'])
def content_status():
    """Get status of a content file across all stages."""
    try:
        path = request.args.get('path')
        content_root = request.args.get('content_root', './content')
        config_path = request.args.get('config_path', None)

        if not path:
            return jsonify({'success': False, 'error': 'Missing path parameter'}), 400

        if config_path:
            config_path = Path(config_path)

        result = get_content_status(
            path=path,
            content_root=Path(content_root),
            config_path=config_path
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/content/list/<stage>', methods=['GET'])
def list_stage_content(stage):
    """List all files in a stage."""
    try:
        content_root = request.args.get('content_root', './content')
        config_path = request.args.get('config_path', None)
        with_metadata = request.args.get('with_metadata', 'false').lower() == 'true'

        if config_path:
            config_path = Path(config_path)

        result = list_content(
            stage=stage,
            content_root=Path(content_root),
            config_path=config_path,
            with_metadata=with_metadata
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/content/all', methods=['GET'])
def list_all_content():
    """List all files across all stages."""
    try:
        content_root = request.args.get('content_root', './content')
        config_path = request.args.get('config_path', None)

        if config_path:
            config_path = Path(config_path)

        config = get_content_stages_config(config_path)

        all_files = {}
        for stage in config.stages:
            result = list_content(
                stage=stage.name,
                content_root=Path(content_root),
                config_path=config_path,
                with_metadata=True
            )
            if result['success']:
                all_files[stage.name] = result['files']

        return jsonify({'success': True, 'stages': all_files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Content Transition API
# =============================================================================

@app.route('/api/content/transition', methods=['POST'])
def transition():
    """Transition content between stages."""
    try:
        data = request.json

        from_stage = data.get('from_stage')
        to_stage = data.get('to_stage')
        path = data.get('path')
        content_root = data.get('content_root', './content')
        config_path = data.get('config_path', None)
        dry_run = data.get('dry_run', False)

        if not from_stage or not to_stage or not path:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: from_stage, to_stage, path'
            }), 400

        if config_path:
            config_path = Path(config_path)

        result = transition_content(
            from_stage=from_stage,
            to_stage=to_stage,
            path=path,
            content_root=Path(content_root),
            config_path=config_path,
            dry_run=dry_run
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Content Diff API
# =============================================================================

@app.route('/api/content/diff', methods=['GET'])
def content_diff():
    """Get diff between content versions."""
    try:
        path = request.args.get('path')
        from_stage = request.args.get('from_stage')
        to_stage = request.args.get('to_stage')
        content_root = request.args.get('content_root', './content')
        config_path = request.args.get('config_path', None)

        if not path or not from_stage or not to_stage:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: path, from_stage, to_stage'
            }), 400

        if config_path:
            config_path = Path(config_path)

        result = diff_content(
            path=path,
            from_stage=from_stage,
            to_stage=to_stage,
            content_root=Path(content_root),
            config_path=config_path,
            output_to_console=False  # Return diff lines instead
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Git Integration API
# =============================================================================

@app.route('/api/content/git/status', methods=['GET'])
def git_status():
    """Get git status for content directory."""
    try:
        content_root = request.args.get('content_root', './content')

        result = subprocess.run(
            ['git', 'status', '--porcelain', content_root],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )

        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                status = line[:2]
                file_path = line[3:]
                files.append({
                    'status': status.strip(),
                    'path': file_path
                })

        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/content/git/commit', methods=['POST'])
def git_commit():
    """Commit changes in content directory."""
    try:
        data = request.json
        message = data.get('message')
        content_root = data.get('content_root', './content')

        if not message:
            return jsonify({'success': False, 'error': 'Missing commit message'}), 400

        # Add files
        subprocess.run(
            ['git', 'add', content_root],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path.cwd()
        )

        # Commit
        result = subprocess.run(
            ['git', 'commit', '-m', message],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path.cwd()
        )

        return jsonify({'success': True, 'output': result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({'success': False, 'error': e.stderr}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/content/git/push', methods=['POST'])
def git_push():
    """Push commits to remote."""
    try:
        result = subprocess.run(
            ['git', 'push'],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path.cwd()
        )

        return jsonify({'success': True, 'output': result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({'success': False, 'error': e.stderr}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/content/git/pull', methods=['POST'])
def git_pull():
    """Pull changes from remote."""
    try:
        result = subprocess.run(
            ['git', 'pull'],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path.cwd()
        )

        return jsonify({'success': True, 'output': result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({'success': False, 'error': e.stderr}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Server Entry Point
# =============================================================================

def start_content_gui(host='127.0.0.1', port=5051, open_browser=True):
    """Start the content GUI server."""
    import webbrowser

    if open_browser:
        webbrowser.open(f'http://{host}:{port}')

    print(f"🚀 Content GUI server starting at http://{host}:{port}")
    app.run(host=host, port=port, debug=True)


if __name__ == '__main__':
    start_content_gui()
