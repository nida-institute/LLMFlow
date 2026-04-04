# Test Improvements to Catch GUI Regressions

## Root Causes Identified

### Issue 1: Run Pipeline - WebSocket CORS Failure
**Error:** `http://127.0.0.1:5000 is not an accepted origin`

**Root cause:** CORS config in `server.py` only allows dev server origins:
```python
_CORS_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
```

But production Flask serves from `:5000`, which is NOT in the list!

**Test that would catch this:**
```python
# tests/test_gui_server.py

def test_socketio_accepts_production_origin(app, socketio):
    """Verify WebSocket accepts connections from Flask's own origin."""
    client = socketio.test_client(app, flask_test_client=app.test_client())

    # This should connect successfully, not get CORS rejection
    assert client.is_connected()

    # Verify we can emit events
    client.emit('execute_pipeline', {
        'execution_id': 'test-123',
        'pipeline_path': '/path/to/test.yaml',
        'project_path': '/path/to/project',
        'variables': {}
    })

    received = client.get_received()
    # Should get response, not CORS error
    assert len(received) > 0

def test_cors_includes_self_origin():
    """When serving static files, server must accept requests from its own origin."""
    # If Flask runs on :5000, that origin must be in CORS list
    # This is a configuration test, not runtime
    from gui.backend.server import _CORS_ORIGINS

    # In production, we serve static files from Flask itself
    # So Flask's origin must be allowed
    production_origins = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ]

    for origin in production_origins:
        assert origin in _CORS_ORIGINS, \
            f"Production origin {origin} must be in CORS allow list"
```

---

### Issue 2: Content Lifecycle - Missing API Endpoint
**Error:** `GET /api/content/config?project_path=... HTTP/1.1" 404`

**Root cause:** ContentApp expects `/api/content/config` but server doesn't implement it.

**Test that would catch this:**
```python
# tests/test_gui_api_completeness.py

def test_all_frontend_endpoints_exist(app):
    """Verify every API endpoint called by frontend is implemented."""
    client = app.test_client()

    # List of endpoints the frontend actually calls
    required_endpoints = [
        ('/api/health', 'GET'),
        ('/api/projects', 'GET'),
        ('/api/projects/demo/pipelines', 'GET'),
        ('/api/pipeline/config', 'POST'),
        ('/api/content/config', 'GET'),  # ContentApp needs this!
        ('/api/open-folder', 'POST'),
        ('/socket.io/', 'GET'),  # WebSocket handshake
    ]

    for endpoint, method in required_endpoints:
        if method == 'GET':
            response = client.get(endpoint)
        elif method == 'POST':
            response = client.post(endpoint, json={})

        assert response.status_code != 404, \
            f"Frontend calls {method} {endpoint} but server returns 404"

def test_content_lifecycle_api_contract():
    """Content Lifecycle button requires /api/content/config endpoint."""
    client = app.test_client()

    response = client.get('/api/content/config?project_path=/test')

    # Should return JSON with content lifecycle config
    assert response.status_code == 200
    data = response.get_json()
    assert 'stages' in data or 'config' in data
```

---

### Issue 3: Open Output - Handler Not Wired
**Status:** Endpoint `/api/open-folder` EXISTS in server.py (line 257)

**Potential issue:** Frontend might not be calling it correctly.

**Test that would catch this:**
```typescript
// gui/frontend/src/test/PipelineView.integration.test.tsx

describe('PipelineView - Open Output Button', () => {
  it('should call /api/open-folder when button is clicked', async () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true })
      })
    )
    global.fetch = mockFetch

    const mockPipeline = { name: 'test', full_path: '/test.yaml' }
    const mockProject = { name: 'demo', path: '/demo' }

    render(
      <PipelineView
        pipeline={mockPipeline}
        project={mockProject}
        onBackToProject={() => {}}
        onBackToProjectList={() => {}}
      />
    )

    // Simulate pipeline completion that sets outputDir
    // (This is the key: button is disabled until outputDir is set)

    const button = screen.getByRole('button', { name: /Open Output/i })

    // Should be disabled initially
    expect(button).toBeDisabled()

    // After pipeline runs and sets outputDir state...
    // TODO: Need to trigger completion event that sets outputDir

    // Button should enable
    // Click should call API
    fireEvent.click(button)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/open-folder',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('path')
        })
      )
    })
  })
})
```

---

## Issue 4: /api/health Missing
**Error:** `GET /api/health HTTP/1.1" 404`

**Root cause:** `App.tsx` checks health on mount, but server has no `/api/health` endpoint.

**Test:**
```python
def test_health_endpoint_exists(app):
    """Frontend checks /api/health on mount."""
    client = app.test_client()
    response = client.get('/api/health')

    assert response.status_code == 200
    data = response.get_json()
    assert 'sp_cli_available' in data
```

---

## Summary: Test Categories We Need

### 1. **Backend API Contract Tests** (Python)
- Verify all endpoints frontend calls are implemented
- Verify endpoints return correct status codes (200, not 404)
- Verify response schemas match what frontend expects

### 2. **CORS Configuration Tests** (Python)
- Verify production origin (Flask's own :5000) is in CORS list
- Verify WebSocket accepts connections from production origin

### 3. **Frontend Integration Tests** (TypeScript)
- Verify button clicks call correct API endpoints
- Verify WebSocket connection is attempted with correct config
- Verify state changes (like `outputDir` being set) enable/disable buttons correctly

### 4. **E2E Smoke Tests** (Optional - Playwright/Cypress)
- Start production server
- Click "Run Pipeline" → verify WebSocket connects
- Click "Open Output" → verify API call made
- Click "Content Lifecycle" → verify component renders

---

## Immediate Fix Needed

**server.py line ~26:**
```python
_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    # ADD THESE for production (Flask serving static files):
    "http://localhost:5000",
    "http://127.0.0.1:5000",
]
```

This single change would fix the WebSocket issue immediately.
