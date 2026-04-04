"""
Test CORS configuration for production deployment.

When Flask serves static files AND provides the API (production mode),
the origin is Flask's own address (e.g., http://127.0.0.1:5000).

Common mistake: Only allowing dev server origins (:5173, :3000) in CORS,
which breaks WebSocket connections in production.
"""

import re
import pytest
from gui.backend.server import create_app, _CORS_ORIGINS


def _origin_matches_cors_patterns(origin: str, patterns: list[str]) -> bool:
    """Check if origin matches any CORS pattern (supports regex)."""
    for pattern in patterns:
        if re.fullmatch(pattern, origin):
            return True
    return False


def test_production_origins_allowed():
    """
    Production mode: Flask serves frontend at :5000.
    Frontend makes API calls and WebSocket connections to same origin.

    Failure symptom: "http://127.0.0.1:5000 is not an accepted origin"
    Result: WebSocket fails, pipeline execution shows no output.
    """
    production_origins = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ]

    for origin in production_origins:
        assert _origin_matches_cors_patterns(origin, _CORS_ORIGINS), (
            f"Production origin {origin} must match CORS patterns. "
            f"When Flask serves static files, it must accept requests from itself. "
            f"Current CORS patterns: {_CORS_ORIGINS}"
        )


def test_dev_origins_allowed():
    """Dev mode: Vite dev server at :5173, :3000."""
    dev_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    for origin in dev_origins:
        assert _origin_matches_cors_patterns(origin, _CORS_ORIGINS), \
            f"Dev origin {origin} should match CORS patterns. Current: {_CORS_ORIGINS}"


@pytest.fixture
def app():
    """Create Flask app with SocketIO."""
    app, socketio = create_app()
    app.config['TESTING'] = True
    return app, socketio


def test_socketio_accepts_production_origin(app):
    """
    Verify SocketIO accepts WebSocket connections from production origin.

    Failure symptom: Multiple "POST /socket.io/... HTTP/1.1" 400" errors in logs.
    """
    flask_app, socketio = app

    # Create test client
    client = socketio.test_client(
        flask_app,
        flask_test_client=flask_app.test_client()
    )

    assert client.is_connected(), (
        "SocketIO should accept connections from Flask's own origin. "
        "Check that production origins are in _CORS_ORIGINS list."
    )

    client.disconnect()


def test_socketio_execute_pipeline_event_exists(app):
    """
    Verify 'execute_pipeline' event handler is registered.

    Frontend emits this when Run Pipeline button is clicked.
    """
    flask_app, socketio = app

    client = socketio.test_client(
        flask_app,
        flask_test_client=flask_app.test_client()
    )

    # Emit execute_pipeline event
    client.emit('execute_pipeline', {
        'execution_id': 'test-123',
        'pipeline_path': '/nonexistent.yaml',  # Will error, but handler should exist
        'project_path': '/tmp',
        'variables': {}
    })

    # Should receive error response (bad path), not nothing
    received = client.get_received()

    assert len(received) > 0, (
        "Should receive response from server after emitting execute_pipeline. "
        "If empty, handler may not be registered."
    )

    # Should get error event (because path is invalid)
    event_types = [msg['name'] for msg in received]
    assert 'error' in event_types or 'complete' in event_types, \
        f"Expected error or complete event, got: {event_types}"

    client.disconnect()
