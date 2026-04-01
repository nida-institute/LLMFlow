"""
Security tests for the installable GUI server (src/llmflow/gui/server.py).

Mirrors test_gui_server_security.py but exercises the package version,
which is what gets installed and bundled — ensuring both copies stay in sync.
"""

import pytest

pytest.importorskip("flask", reason="GUI tests require: pip install llmflow[gui]")

from llmflow.gui.server import create_app


@pytest.fixture
def client():
    """Flask test client backed by the real bundled static folder."""
    app, _ = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# /api/pipeline/config — extension validation & path traversal
# ---------------------------------------------------------------------------

class TestPkgPipelineConfigEndpoint:

    def test_rejects_non_yaml_extension(self, client, tmp_path):
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
        yaml_file = tmp_path / "pipeline.yaml"
        yaml_file.write_text("name: test\nsteps: []\n")

        resp = client.post(
            '/api/pipeline/config',
            json={'pipeline_path': str(yaml_file)},
            content_type='application/json',
        )

        assert resp.status_code == 200

    def test_rejects_missing_pipeline_path(self, client):
        resp = client.post(
            '/api/pipeline/config',
            json={},
            content_type='application/json',
        )
        assert resp.status_code == 400

    def test_rejects_missing_json_body(self, client):
        resp = client.post('/api/pipeline/config', data='', content_type='text/plain')
        assert resp.status_code == 400

    def test_returns_404_for_missing_file(self, client, tmp_path):
        resp = client.post(
            '/api/pipeline/config',
            json={'pipeline_path': str(tmp_path / 'nonexistent.yaml')},
            content_type='application/json',
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /api/execute — extension validation
# ---------------------------------------------------------------------------

class TestPkgExecuteEndpoint:

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

class TestPkgCORSRestriction:

    def test_cors_not_wildcard_for_localhost_origin(self, client):
        resp = client.get(
            '/api/projects',
            headers={'Origin': 'http://localhost:5173'},
        )
        acao = resp.headers.get('Access-Control-Allow-Origin', '')
        assert acao != '*'

    def test_cors_not_present_for_arbitrary_origin(self, client):
        resp = client.get(
            '/api/projects',
            headers={'Origin': 'https://evil.example.com'},
        )
        acao = resp.headers.get('Access-Control-Allow-Origin', '')
        assert 'evil.example.com' not in acao
        assert acao != '*'
