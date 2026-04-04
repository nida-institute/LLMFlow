"""
Test that all API endpoints required by the frontend are implemented.

These tests catch regressions where frontend code calls endpoints that
don't exist in the backend, resulting in 404 errors.
"""

import pytest
from gui.backend.server import create_app


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app, socketio = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_health_endpoint_exists(client):
    """
    Frontend: App.tsx fetches /api/health on mount.

    Failure symptom: Console shows 404 for /api/health
    """
    response = client.get('/api/health')

    assert response.status_code == 200, \
        "App.tsx expects /api/health endpoint to exist"

    data = response.get_json()
    assert 'sp_cli_available' in data, \
        "Health response should include CLI availability status"


def test_projects_endpoint_exists(client):
    """Frontend: ProjectList fetches /api/projects on mount."""
    response = client.get('/api/projects')
    assert response.status_code == 200


def test_pipeline_config_endpoint_exists(client):
    """Frontend: PipelineView fetches /api/pipeline/config."""
    response = client.post('/api/pipeline/config', json={
        'pipeline_path': '/test/pipeline.yaml'
    })
    # File doesn't exist, so 404 is expected. But the endpoint should exist
    # (not return 404 for missing route). Check error message has file-related content.
    assert response.status_code in [400, 404, 500], \
        "Endpoint should exist and return error for non-existent file"

    if response.status_code == 404:
        data = response.get_json()
        assert 'not found' in data.get('error', '').lower(), \
            "404 should be for file not found, not missing endpoint"


def test_open_folder_endpoint_exists(client):
    """
    Frontend: PipelineView calls /api/open-folder when Open Output clicked.

    Failure symptom: Button click does nothing, API returns 404
    """
    response = client.post('/api/open-folder', json={
        'path': '/tmp'
    })
    # May fail with error (path validation), but should not be 404
    assert response.status_code != 404, \
        "PipelineView Open Output button calls /api/open-folder"


def test_content_lifecycle_endpoint_exists(client):
    """
    Frontend: ContentApp fetches /api/content/config.

    Failure symptom: Content Lifecycle button loads nothing, shows 404
    """
    response = client.get('/api/content/config', query_string={
        'project_path': '/test/project'
    })

    assert response.status_code == 200, \
        "ContentApp requires /api/content/config endpoint"

    # Verify response has expected structure
    data = response.get_json()
    assert data.get('success') is True, \
        "Response must have 'success': true"
    assert 'stages' in data, \
        "Response must include 'stages' array"
    assert isinstance(data['stages'], list), \
        "stages must be a list"


def test_content_all_endpoint_contract(client):
    """
    Frontend: ContentDashboard fetches /api/content/all.

    This test verifies the data contract, not just endpoint existence.
    """
    response = client.get('/api/content/all', query_string={
        'project_path': '/test/project'
    })

    assert response.status_code == 200
    data = response.get_json()

    # Verify contract matches what ContentDashboard expects
    assert data.get('success') is True, \
        "ContentDashboard checks data.success"
    assert 'stages' in data, \
        "ContentDashboard expects data.stages"
    assert isinstance(data['stages'], dict), \
        "stages should be dict with stage names as keys"

    # Verify each stage is an array
    for stage_name, files in data['stages'].items():
        assert isinstance(files, list), \
            f"Stage '{stage_name}' should be a list of files"


def test_content_status_endpoint_contract(client):
    """
    Frontend: FileStatus fetches /api/content/status with path parameter.

    This is called when user clicks a file checkbox.
    """
    # Test with non-existent file
    response = client.get('/api/content/status', query_string={
        'path': '/nonexistent/file.txt',
        'project_path': '/test/project'
    })

    # Should return 404 for missing file, but still return JSON
    assert response.status_code == 404
    data = response.get_json()
    assert 'success' in data, \
        "Even 404 should return JSON with success field"
    assert data['success'] is False, \
        "404 should have success: false"
    assert 'error' in data, \
        "Error responses should include error message"


def test_content_status_accepts_full_path_with_extension(client, tmp_path):
    """
    Regression test for Issue #110: Draft file click shows "File not Found".

    Root cause: Frontend passes full file path WITH extension (e.g., 'draft/file.md'),
    but earlier implementation expected extensionless paths.

    This test verifies the API correctly handles paths with file extensions.
    """
    import os

    # Create a test file
    test_dir = tmp_path / "content"
    test_dir.mkdir()
    test_file = test_dir / "test-file.md"
    test_file.write_text("# Test Content")

    # Frontend sends full path with extension (as of StageCard.tsx fix)
    response = client.get('/api/content/status', query_string={
        'path': str(test_file),  # Full path WITH .md extension
        'project_path': str(tmp_path)
    })

    # Should succeed (or fail for reasons OTHER than missing extension)
    # The specific response depends on content lifecycle config,
    # but it should NOT be 404 "File not found" for a file that exists
    assert response.status_code in [200, 400, 500], \
        f"API should handle full paths with extensions. " \
        f"Got {response.status_code} for existing file {test_file}"

    if response.status_code == 404:
        data = response.get_json()
        pytest.fail(
            f"Issue #110 regression: API returned 404 for existing file.\n"
            f"Path: {test_file}\n"
            f"Error: {data.get('error')}\n"
            f"This suggests the API is stripping extensions or not finding the file."
        )


def test_socketio_endpoint_exists(client):
    """Frontend: PipelineView connects to socket.io for pipeline execution."""
    # SocketIO handshake
    response = client.get('/socket.io/')

    # SocketIO may return various codes, but not 404
    assert response.status_code != 404, \
        "PipelineView requires WebSocket at /socket.io/"


def test_all_frontend_api_calls_mapped():
    """
    Comprehensive check: grep frontend code for fetch/API calls,
    verify each endpoint exists.

    This is a meta-test that would scan src/ for patterns like:
    - fetch('/api/...')
    - socket.emit('...')

    And verify server.py has corresponding @app.route() or @socketio.on()
    """
    # This would require parsing frontend code
    # For now, document the contract:

    required_http_endpoints = [
        ('/api/health', 'GET', 'App.tsx useEffect'),
        ('/api/projects', 'GET', 'ProjectList'),
        ('/api/projects/{name}/pipelines', 'GET', 'ProjectList'),
        ('/api/pipeline/config', 'POST', 'PipelineView config load'),
        ('/api/open-folder', 'POST', 'PipelineView Open Output button'),
        ('/api/content/config', 'GET', 'ContentApp lifecycle view'),
    ]

    required_socketio_events = [
        'execute_pipeline',  # PipelineView Run Pipeline button
        'status',            # Server -> Client
        'output_batch',      # Server -> Client
        'complete',          # Server -> Client
        'error',             # Server -> Client
    ]

    # TODO: Implement automated scanning
    # For now, this serves as documentation of the API contract
    pass
