"""
Integration tests for GUI button state management.

These tests verify that buttons enable/disable correctly based on state,
and that they call the right APIs when clicked.

NO STUBS - these use real Flask app, real SocketIO, real file system.
"""

import pytest
import tempfile
import time
from pathlib import Path
from gui.backend.server import create_app
from gui.backend.executor import PipelineExecutor


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app, socketio = create_app()
    app.config['TESTING'] = True
    return app, socketio


@pytest.fixture
def client(app):
    """Create test client."""
    flask_app, _ = app
    return flask_app.test_client()


@pytest.fixture
def temp_project():
    """Create a temporary project with a simple pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create a minimal working pipeline
        pipeline_yaml = project_path / "test.yaml"
        pipeline_yaml.write_text("""
steps:
  - name: test_step
    run: echo "test output"
""")

        # Create outputs directory
        outputs_dir = project_path / "outputs"
        outputs_dir.mkdir()

        yield {
            'path': str(project_path),
            'pipeline': str(pipeline_yaml),
            'outputs': str(outputs_dir)
        }


def test_pipeline_execution_returns_output_dir(temp_project):
    """
    Verify that executor actually returns output_dir.

    This is what enables the Open Output button.
    Frontend checks: if (data.output_dir) { setOutputDir(...) }
    """
    executor = PipelineExecutor(
        pipeline_path=temp_project['pipeline'],
        project_path=temp_project['path'],
        variables={},
        execution_id='test-123',
        emit_callback=lambda *args: None
    )

    result = executor.execute()

    # These are the fields frontend expects from 'complete' event
    assert 'output_dir' in result, \
        "Frontend needs output_dir to enable Open Output button"
    assert result['output_dir'] is not None
    assert result['output_dir'] == temp_project['path'], \
        f"Expected output_dir to be project path"

    # Verify other required fields
    assert 'success' in result
    assert 'exit_code' in result
    assert 'created_files' in result
    assert 'telemetry' in result


def test_websocket_complete_event_includes_output_dir(app, temp_project):
    """
    Integration test: Verify WebSocket 'complete' event includes output_dir.

    This tests the full flow:
    1. Client emits 'execute_pipeline'
    2. Server executes pipeline
    3. Server emits 'complete' with output_dir

    NO MOCKS - uses real SocketIO test client.
    """
    flask_app, socketio = app

    # Create WebSocket test client
    client = socketio.test_client(flask_app, flask_test_client=flask_app.test_client())

    assert client.is_connected(), "WebSocket should connect"

    # Emit execute_pipeline event
    client.emit('execute_pipeline', {
        'execution_id': 'test-123',
        'pipeline_path': temp_project['pipeline'],
        'project_path': temp_project['path'],
        'variables': {}
    })

    # Wait for pipeline execution to complete (async in background thread)
    time.sleep(2)

    # Get all received messages
    received = client.get_received()

    # Find completion event
    complete_events = [msg for msg in received if msg.get('name') == 'complete']

    assert len(complete_events) > 0, \
        f"Should receive 'complete' event. Got: {[m.get('name') for m in received]}"

    complete_data = complete_events[0]['args'][0]

    # Verify frontend contract
    assert 'output_dir' in complete_data, \
        "Frontend expects output_dir in complete event to enable Open Output button"
    assert complete_data['output_dir'] is not None
    assert 'success' in complete_data
    assert 'exit_code' in complete_data

    client.disconnect()


def test_content_status_requires_project_path_parameter(client, temp_project):
    """
    FileStatus calls /api/content/status with path parameter.

    Bug: Frontend wasn't passing project_path, causing 404.
    This test verifies endpoint needs it and works with it.
    """
    # Create a test file
    test_file = Path(temp_project['outputs']) / 'test.txt'
    test_file.write_text('test content')

    relative_path = str(test_file.relative_to(temp_project['path']))

    # Test WITH project_path (should work)
    response = client.get('/api/content/status', query_string={
        'path': relative_path,
        'project_path': temp_project['path']
    })

    assert response.status_code == 200, \
        f"With project_path should return 200, got {response.status_code}"

    data = response.get_json()
    assert data['success'] is True
    assert 'path' in data
    assert 'current_stage' in data

    # Test WITHOUT project_path (will fail to find file)
    response = client.get('/api/content/status', query_string={
        'path': relative_path
    })

    # Should return error, but still return JSON
    assert response.status_code in [400, 404]
    data = response.get_json()
    assert data is not None, "Should return JSON even on error"
    assert 'success' in data or 'error' in data


def test_content_all_returns_actual_files(client, temp_project):
    """
    ContentDashboard fetches /api/content/all and expects file list.

    Bug: Endpoint returned empty stages even when files existed.
    This test verifies it actually discovers files.
    """
    # Create some test files in outputs
    outputs_dir = Path(temp_project['outputs'])
    (outputs_dir / 'file1.txt').write_text('content1')
    (outputs_dir / 'file2.md').write_text('# Test')

    response = client.get('/api/content/all', query_string={
        'project_path': temp_project['path']
    })

    assert response.status_code == 200
    data = response.get_json()

    # Verify contract matches ContentDashboard expectations
    assert data['success'] is True, "Frontend checks data.success"
    assert 'stages' in data, "Frontend expects data.stages"
    assert isinstance(data['stages'], dict), "stages should be dict"

    # Verify files were actually discovered
    all_files = []
    for stage_name, files in data['stages'].items():
        all_files.extend(files)

    assert len(all_files) > 0, \
        f"Should discover files in {outputs_dir}. Found: {all_files}"

    # Verify file structure
    if len(all_files) > 0:
        file_obj = all_files[0]
        assert 'path' in file_obj or 'name' in file_obj, \
            f"File objects should have path/name. Got: {file_obj}"


def test_open_folder_endpoint_works_with_real_path(client, temp_project):
    """
    Open Output button calls /api/open-folder.

    Test that it accepts real directory path and doesn't crash.
    """
    response = client.post('/api/open-folder', json={
        'path': temp_project['outputs']
    })

    # On macOS/Linux with 'open'/'xdg-open' available, should succeed
    # May fail in CI without display, but should return JSON
    data = response.get_json()
    assert data is not None, "Should return JSON response"

    if response.status_code == 200:
        assert data.get('success') is True
        assert 'path' in data
    else:
        # If failed (e.g., no display in CI), should return error structure
        assert 'error' in data


def test_api_endpoints_all_return_json_not_html(client, temp_project):
    """
    Critical: All API endpoints must return JSON, never HTML 404 pages.

    Bug: FileStatus tried to JSON.parse HTML 404 page.
    """
    api_calls = [
        ('GET', '/api/health', {}),
        ('GET', '/api/projects', {}),
        ('GET', '/api/content/config', {'project_path': temp_project['path']}),
        ('GET', '/api/content/all', {'project_path': temp_project['path']}),
        ('GET', '/api/content/status', {'path': 'nonexistent.txt', 'project_path': temp_project['path']}),
        ('POST', '/api/open-folder', {'path': '/nonexistent'}),
        ('POST', '/api/pipeline/config', {'pipeline_path': temp_project['pipeline']}),
    ]

    for method, endpoint, params in api_calls:
        if method == 'GET':
            response = client.get(endpoint, query_string=params)
        else:
            response = client.post(endpoint, json=params)

        # Even if endpoint fails, must return JSON
        content_type = response.headers.get('Content-Type', '')
        assert 'json' in content_type.lower(), \
            f"{method} {endpoint} returned {content_type}, not JSON. " \
            f"Status: {response.status_code}. " \
            f"Frontend will fail to parse HTML error pages."

        # Verify it's actually parseable JSON
        try:
            data = response.get_json()
            assert data is not None
        except Exception as e:
            pytest.fail(
                f"{method} {endpoint} returned Content-Type: {content_type} "
                f"but JSON parsing failed: {e}"
            )
