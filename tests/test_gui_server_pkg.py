"""
Security tests for the installable GUI server (src/llmflow/gui/server.py).

Mirrors test_gui_server_security.py but exercises the package version,
which is what gets installed and bundled — ensuring both copies stay in sync.
"""

import pytest

pytest.importorskip("flask", reason="GUI tests require: pip install scripture-pipelines")

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


# ---------------------------------------------------------------------------
# Content Lifecycle API — ensure src/ version has same endpoints as dev
# ---------------------------------------------------------------------------

class TestPkgContentLifecycleAPI:
    """
    These tests ensure src/llmflow/gui/server.py has the same content endpoints
    as gui/backend/server.py. Missing endpoints cause 404s in production.
    """

    def test_content_config_endpoint_exists(self, client, tmp_path):
        """Frontend ContentApp.tsx calls /api/content/config"""
        resp = client.get('/api/content/config', query_string={
            'project_path': str(tmp_path)
        })
        # Should return 200 with default stages
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'stages' in data
        assert data.get('success') is True

    def test_content_all_endpoint_exists(self, client, tmp_path):
        """Frontend ContentDashboard calls /api/content/all"""
        resp = client.get('/api/content/all', query_string={
            'project_path': str(tmp_path)
        })
        # Should return 200 with empty file list
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'stages' in data or isinstance(data, dict)

    def test_content_status_endpoint_exists(self, client, tmp_path):
        """Frontend FileStatus calls /api/content/status"""
        resp = client.get('/api/content/status', query_string={
            'path': 'test.txt',
            'project_path': str(tmp_path)
        })
        # Should return 404 for nonexistent file (but endpoint should exist)
        assert resp.status_code in [200, 404]
        data = resp.get_json()
        assert isinstance(data, dict)

    def test_open_folder_endpoint_exists(self, client, tmp_path):
        """Frontend PipelineView calls /api/open-folder"""
        resp = client.post('/api/open-folder',
            json={'path': str(tmp_path)},
            content_type='application/json'
        )
        # Should return 200 or error message (but not 404)
        assert resp.status_code != 404
        data = resp.get_json()
        assert isinstance(data, dict)
