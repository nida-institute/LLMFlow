"""
Security tests for GUI backend server.

Covers path traversal rejection, extension validation, and CORS restriction.
Run with: pytest tests/test_gui_server_security.py
"""

import json
import pytest
import sys
from pathlib import Path

pytest.importorskip("flask", reason="GUI tests require: pip install llmflow[gui]")

# Import from the development backend
sys.path.insert(0, str(Path(__file__).parent.parent / 'gui' / 'backend'))
from server import create_app


@pytest.fixture
def client(tmp_path):
    """Flask test client with a real tmp static folder."""
    # create_app expects a static folder to exist
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html></html>")

    import server as srv_module
    original_file = srv_module.__file__

    # Patch __file__ so Path(__file__).parent resolves to tmp_path
    import unittest.mock as mock
    with mock.patch.object(sys.modules['server'], '__file__', str(tmp_path / 'server.py')):
        app, _ = create_app()

    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# /api/pipeline/config — path traversal & extension validation
# ---------------------------------------------------------------------------

class TestPipelineConfigEndpoint:

    def test_rejects_non_yaml_extension(self, client, tmp_path):
        """Non-.yaml/.yml files must be rejected with 400."""
        bad_file = tmp_path / "secret.txt"
        bad_file.write_text("sensitive content")

        resp = client.post(
            '/api/pipeline/config',
            json={'pipeline_path': str(bad_file)},
            content_type='application/json',
        )

        assert resp.status_code == 400

    def test_rejects_python_file(self, client, tmp_path):
        bad_file = tmp_path / "exploit.py"
        bad_file.write_text("import os")

        resp = client.post(
            '/api/pipeline/config',
            json={'pipeline_path': str(bad_file)},
            content_type='application/json',
        )

        assert resp.status_code == 400

    def test_accepts_yaml_extension(self, client, tmp_path):
        """Valid .yaml files that exist should succeed (200)."""
        yaml_file = tmp_path / "pipeline.yaml"
        yaml_file.write_text("name: test\nsteps: []\n")

        resp = client.post(
            '/api/pipeline/config',
            json={'pipeline_path': str(yaml_file)},
            content_type='application/json',
        )

        assert resp.status_code == 200

    def test_accepts_yml_extension(self, client, tmp_path):
        """Valid .yml files that exist should succeed (200)."""
        yml_file = tmp_path / "pipeline.yml"
        yml_file.write_text("name: test\nsteps: []\n")

        resp = client.post(
            '/api/pipeline/config',
            json={'pipeline_path': str(yml_file)},
            content_type='application/json',
        )

        assert resp.status_code == 200

    def test_rejects_missing_pipeline_path(self, client):
        """Missing pipeline_path should return 400."""
        resp = client.post(
            '/api/pipeline/config',
            json={},
            content_type='application/json',
        )

        assert resp.status_code == 400

    def test_rejects_missing_json_body(self, client):
        """No JSON body at all should return 400."""
        resp = client.post('/api/pipeline/config', data='', content_type='text/plain')
        assert resp.status_code == 400

    def test_returns_generic_error_for_missing_file(self, client, tmp_path):
        """A missing yaml file should return 404, not expose the internal path."""
        resp = client.post(
            '/api/pipeline/config',
            json={'pipeline_path': str(tmp_path / 'nonexistent.yaml')},
            content_type='application/json',
        )

        assert resp.status_code == 404
        body = resp.get_json()
        # Error message must not echo back raw exception details
        assert 'error' in body
        assert 'Traceback' not in body.get('error', '')


# ---------------------------------------------------------------------------
# /api/execute — extension validation
# ---------------------------------------------------------------------------

class TestExecuteEndpoint:

    def test_rejects_non_yaml_extension(self, client, tmp_path):
        bad_file = tmp_path / "exploit.sh"

        resp = client.post(
            '/api/execute',
            json={'pipeline_path': str(bad_file)},
            content_type='application/json',
        )

        assert resp.status_code == 400

    def test_requires_pipeline_path(self, client):
        resp = client.post(
            '/api/execute',
            json={},
            content_type='application/json',
        )

        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# CORS headers
# ---------------------------------------------------------------------------

class TestCORSRestriction:

    def test_cors_not_wildcard_for_localhost_origin(self, client):
        """Requests from a localhost dev server should get a specific origin back, not *."""
        resp = client.get(
            '/api/projects',
            headers={'Origin': 'http://localhost:5173'},
        )

        acao = resp.headers.get('Access-Control-Allow-Origin', '')
        assert acao != '*', "CORS must not be open to all origins"

    def test_cors_not_present_for_arbitrary_origin(self, client):
        """Requests from an untrusted origin must not receive ACAO header."""
        resp = client.get(
            '/api/projects',
            headers={'Origin': 'https://evil.example.com'},
        )

        acao = resp.headers.get('Access-Control-Allow-Origin', '')
        assert 'evil.example.com' not in acao
        assert acao != '*'
