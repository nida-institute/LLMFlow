import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import App from '../App';

// Mock fetch globally
global.fetch = vi.fn();

describe('App Component - Actual Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock health check
    global.fetch.mockImplementation((url) => {
      if (url.includes('/api/health')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'ok', sp_cli_available: true }),
        });
      }
      if (url.includes('/api/projects')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ projects: [] }),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });
  });

  it('renders the app title', async () => {
    render(<App />);

    // Should show the Scripture Pipelines title
    expect(screen.getByText('Scripture Pipelines')).toBeInTheDocument();
  });

  it('shows initial empty state message', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Select a project to get started/i)).toBeInTheDocument();
    });
  });

  it('calls health check API on mount', async () => {
    render(<App />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/health');
    });
  });

  it('does not show blank screen', async () => {
    const { container } = render(<App />);

    // Should have actual content, not just empty divs
    expect(container.textContent).not.toBe('');
    expect(container.querySelector('#root')).toBeTruthy();
  });

  it('renders sidebar', async () => {
    render(<App />);

    // Sidebar should be present
    const sidebar = screen.getByRole('complementary', { hidden: true }) ||
                    screen.getByText('Scripture Pipelines').closest('aside');
    expect(sidebar).toBeInTheDocument();
  });

  it('renders main content area', async () => {
    const { container } = render(<App />);

    // Should have a main element
    const main = container.querySelector('main');
    expect(main).toBeInTheDocument();
  });
});
