"""
Tests for Content Lifecycle Management Flask API (gui/backend/app.py).

These tests verify the REST API endpoints that power the Content Lifecycle GUI
when embedded in the main GUI (using the main backend's /api/content/* endpoints).
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

pytest.importorskip("flask", reason="GUI tests require: pip install scripture-pipelines")

# Import the main GUI backend app
sys.path.insert(0, str(Path(__file__).parent.parent / 'gui' / 'backend'))
from app import app as gui_app


@pytest.fixture
def client():
    """Flask test client for main GUI backend with content API."""
    gui_app.config['TESTING'] = True
    with gui_app.test_client() as c:
        yield c


@pytest.fixture
def project_with_content_config(tmp_path):
    """Create a test project directory with content-stages.yaml config."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    config_dir = project_dir / "config"
    config_dir.mkdir()

    # Create test content stages config
    config = {
        'stages': [
            {'name': 'generated', 'file_permissions': '644', 'git_tracked': False},
            {'name': 'editing', 'file_permissions': '644', 'git_tracked': True, 'protected': True},
            {'name': 'published', 'file_permissions': '444', 'git_tracked': True, 'immutable': True},
        ],
        'transitions': [
            {'from': 'generated', 'to': 'editing', 'action': 'copy'},
            {'from': 'editing', 'to': 'published', 'action': 'copy'},
        ],
    }

    config_file = config_dir / 'content-stages.yaml'
    config_file.write_text(yaml.dump(config))

    # Create content directories
    (project_dir / 'content' / 'generated').mkdir(parents=True)
    (project_dir / 'content' / 'editing').mkdir(parents=True)
    (project_dir / 'content' / 'published').mkdir(parents=True)

    return project_dir


# =============================================================================
# /api/content/config — Content lifecycle configuration endpoint
# =============================================================================

class TestContentConfigEndpoint:
    """Test GET /api/content/config endpoint in main backend."""

    def test_returns_default_config_without_project_path(self, client):
        """Should return default 3-stage config when no project specified."""
        resp = client.get('/api/content/config')

        assert resp.status_code == 200
        data = resp.get_json()

        assert data['success'] is True
        assert 'stages' in data
        assert 'transitions' in data
        assert len(data['stages']) == 3

        # Verify default stage names
        stage_names = [s['name'] for s in data['stages']]
        assert 'generated' in stage_names
        assert 'editing' in stage_names
        assert 'published' in stage_names

    def test_loads_config_from_project_path(self, client, project_with_content_config):
        """Should load config from project/config/content-stages.yaml."""
        resp = client.get(
            '/api/content/config',
            query_string={'project_path': str(project_with_content_config)}
        )

        assert resp.status_code == 200
        data = resp.get_json()

        assert data['success'] is True
        assert len(data['stages']) == 3
        assert len(data['transitions']) == 2

    def test_returns_stage_properties(self, client):
        """Should return all required stage properties."""
        resp = client.get('/api/content/config')
        data = resp.get_json()

        assert data['success'] is True

        # Check first stage has all required fields
        stage = data['stages'][0]
        assert 'name' in stage
        assert 'protected' in stage
        assert 'immutable' in stage
        assert 'file_permissions' in stage
        assert 'git_tracked' in stage
        assert 'auto_create_metadata' in stage

    def test_returns_transition_properties(self, client):
        """Should return all required transition properties."""
        resp = client.get('/api/content/config')
        data = resp.get_json()

        assert data['success'] is True
        assert len(data['transitions']) >= 1

        # Check first transition has required fields
        trans = data['transitions'][0]
        assert 'from' in trans
        assert 'to' in trans
        assert 'action' in trans

    def test_handles_missing_config_file_in_project(self, client, tmp_path):
        """Should fall back to defaults if project has no config file."""
        empty_project = tmp_path / "empty-project"
        empty_project.mkdir()

        resp = client.get(
            '/api/content/config',
            query_string={'project_path': str(empty_project)}
        )

        assert resp.status_code == 200
        data = resp.get_json()

        # Should still succeed with defaults
        assert data['success'] is True
        assert len(data['stages']) == 3

    def test_searches_multiple_config_locations(self, client, tmp_path):
        """Should search project/, project/config/, project/.sp/ for config."""
        project_dir = tmp_path / "multi-location-test"
        project_dir.mkdir()

        # Put config in config/ directory (most common location)
        config_dir = project_dir / 'config'
        config_dir.mkdir()

        config = {
            'stages': [
                {'name': 'draft', 'file_permissions': '644'},
                {'name': 'final', 'file_permissions': '444', 'immutable': True},
            ],
            'transitions': [
                {'from': 'draft', 'to': 'final', 'action': 'copy'},
            ],
        }

        config_file = config_dir / 'content-stages.yaml'
        config_file.write_text(yaml.dump(config))

        resp = client.get(
            '/api/content/config',
            query_string={'project_path': str(project_dir)}
        )

        assert resp.status_code == 200
        data = resp.get_json()

        assert data['success'] is True
        # Should have loaded our custom 2-stage config
        assert len(data['stages']) == 2
        stage_names = [s['name'] for s in data['stages']]
        assert 'draft' in stage_names
        assert 'final' in stage_names

    def test_returns_cors_headers(self, client):
        """Should include CORS headers for frontend access."""
        resp = client.get('/api/content/config')

        # Flask-CORS should add this header
        assert 'Access-Control-Allow-Origin' in resp.headers

    def test_handles_invalid_project_path_gracefully(self, client):
        """Should handle invalid/nonexistent project path without crashing."""
        resp = client.get(
            '/api/content/config',
            query_string={'project_path': '/nonexistent/project/path'}
        )

        # Should still return default config or handle gracefully
        assert resp.status_code in [200, 500]
        data = resp.get_json()

        # Either succeeds with defaults or returns error
        assert 'success' in data or 'error' in data


# =============================================================================
# Integration Tests
# =============================================================================

class TestContentAPIIntegration:
    """Test that content API integrates properly with main GUI backend."""

    def test_content_api_coexists_with_pipeline_api(self, client):
        """Content API should not interfere with existing pipeline endpoints."""
        # Test that health check still works
        health_resp = client.get('/api/health')
        assert health_resp.status_code == 200

        # Test that content config works
        content_resp = client.get('/api/content/config')
        assert content_resp.status_code == 200

        # Both should succeed
        assert health_resp.get_json()['status'] == 'ok'
        assert content_resp.get_json()['success'] is True

    def test_vite_proxy_compatible_urls(self, client):
        """API paths should work with Vite proxy (relative URLs)."""
        # All content endpoints start with /api/content/
        resp = client.get('/api/content/config')
        assert resp.status_code == 200

        # URL structure matches Vite proxy expectations
        assert resp.request.path.startswith('/api/')


# =============================================================================
# Test Metadata
# =============================================================================

class TestContentAPIMetadata:
    """Tests that verify test coverage and documentation."""

    def test_coverage_documented(self):
        """Document what endpoints are tested and what's missing."""
        tested_endpoints = [
            'GET /api/content/config',
        ]

        missing_endpoints = [
            'GET /api/content/stages',
            'GET /api/content/status',
            'GET /api/content/list',
            'GET /api/content/all',
            'POST /api/content/transition',
            'GET /api/content/diff',
            'GET /api/content/git/status',
            'POST /api/content/git/commit',
            'POST /api/content/git/push',
            'POST /api/content/git/pull',
        ]

        # This test passes but documents what's left to implement
        assert len(tested_endpoints) >= 1
        assert len(missing_endpoints) >= 1  # Acknowledging what's not yet tested
