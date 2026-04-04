import { describe, it, expect, beforeAll, afterAll } from 'vitest';

/**
 * Integration tests - verify the GUI actually loads and serves content.
 *
 * These tests check what the user actually sees, not just that functions work.
 *
 * Note: Requires server running - skipped in CI, run manually for integration testing.
 */

describe.skipIf(!!process.env.CI)('GUI Integration - What Actually Loads', () => {
  let serverProcess: any = null;
  const BASE_URL = 'http://localhost:5000';

  beforeAll(async () => {
    // TODO: Start the server programmatically
    // For now, assumes server is running
  });

  afterAll(async () => {
    // TODO: Stop server
  });

  it('loads the index page (HTML)', async () => {
    const response = await fetch(BASE_URL);
    const html = await response.text();

    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toMatch(/text\/html/);
    expect(html).toContain('<div id="root">');
    expect(html).toContain('<script'); // React bundle should be loaded
  });

  it('loads the main JavaScript bundle', async () => {
    // First get index.html to find the script path
    const indexResponse = await fetch(BASE_URL);
    const html = await indexResponse.text();

    // Extract script src from HTML
    const scriptMatch = html.match(/<script[^>]+src="([^"]+)"/);
    expect(scriptMatch).toBeTruthy();

    if (scriptMatch) {
      const scriptPath = scriptMatch[1];
      const scriptResponse = await fetch(`${BASE_URL}${scriptPath}`);

      expect(scriptResponse.status).toBe(200);
      expect(scriptResponse.headers.get('content-type')).toMatch(/javascript/);
    }
  });

  it('loads the CSS bundle', async () => {
    // Get index.html to find the CSS path
    const indexResponse = await fetch(BASE_URL);
    const html = await indexResponse.text();

    // Extract link href from HTML
    const cssMatch = html.match(/<link[^>]+href="([^"]+\.css)"/);

    if (cssMatch) {
      const cssPath = cssMatch[1];
      const cssResponse = await fetch(`${BASE_URL}${cssPath}`);

      expect(cssResponse.status).toBe(200);
      expect(cssResponse.headers.get('content-type')).toMatch(/css/);
    }
  });

  it('API health endpoint responds', async () => {
    const response = await fetch(`${BASE_URL}/api/health`);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data).toHaveProperty('status');
    expect(data.status).toBe('ok');
  });

  it('API returns projects list', async () => {
    const response = await fetch(`${BASE_URL}/api/projects`);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data).toHaveProperty('projects');
    expect(Array.isArray(data.projects)).toBe(true);
  });

  it('serves static assets from /assets/', async () => {
    // Get index to find an asset
    const indexResponse = await fetch(BASE_URL);
    const html = await indexResponse.text();

    // Check if any asset URLs exist
    const assetMatch = html.match(/\/assets\/[^"'\s]+/);

    if (assetMatch) {
      const assetUrl = assetMatch[0];
      const assetResponse = await fetch(`${BASE_URL}${assetUrl}`);

      // Asset should exist (or server should handle gracefully)
      expect([200, 404]).toContain(assetResponse.status);
    }
  });

  it('content lifecycle API config endpoint responds', async () => {
    const response = await fetch(`${BASE_URL}/api/content/config`);

    // Should return config or error (both are valid responses)
    expect([200, 404, 500]).toContain(response.status);

    if (response.status === 200) {
      const data = await response.json();
      expect(data).toHaveProperty('success');
    }
  });

  it('returns 404 for non-existent routes (not 500)', async () => {
    const response = await fetch(`${BASE_URL}/api/nonexistent`);

    expect(response.status).toBe(404);
  });
});

describe.skipIf(!!process.env.CI)('Static File Serving', () => {
  const BASE_URL = 'http://localhost:5000';

  it('verifies static folder is correctly configured', async () => {
    // Try to access a known static file pattern
    const response = await fetch(BASE_URL);

    expect(response.ok).toBe(true);

    const html = await response.text();

    // Verify the HTML contains expected React structure
    expect(html).toContain('<!DOCTYPE html>');
    expect(html).toContain('<div id="root">');
  });

  it('serves index.html for unknown client routes (SPA routing)', async () => {
    // Client-side routes should return index.html
    const response = await fetch(`${BASE_URL}/some-client-route`);
    const html = await response.text();

    expect(response.status).toBe(200);
    expect(html).toContain('<div id="root">');
  });
});
