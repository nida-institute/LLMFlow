import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PipelineView from '../components/PipelineView';

/**
 * Integration tests that verify PipelineView actually loads and displays correctly.
 *
 * These tests check what the user sees, not just that functions work.
 */

describe('PipelineView - What Actually Loads', () => {
  const mockPipeline = {
    name: 'test-pipeline',
    path: 'pipelines/test.yaml',
    full_path: '/path/to/test.yaml'
  };

  const mockProject = {
    name: 'test-project',
    path: '/path/to/project',
    description: 'Test project'
  };

  beforeEach(() => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ vars: {} }),
        ok: true
      }) as any
    );
  });

  it('renders breadcrumb navigation', () => {
    render(<PipelineView pipeline={mockPipeline} project={mockProject} />);

    // Breadcrumb should show project name
    expect(screen.getByText('test-project')).toBeInTheDocument();

    // Breadcrumb should show pipeline name
    expect(screen.getByText('test-pipeline')).toBeInTheDocument();
  });

  it('renders all three action buttons', () => {
    render(<PipelineView pipeline={mockPipeline} project={mockProject} />);

    // Should have Run Pipeline button
    expect(screen.getByText(/Run Pipeline/)).toBeInTheDocument();

    // Should have Open Output button
    expect(screen.getByText(/Open Output/)).toBeInTheDocument();

    // Should have Content Lifecycle button
    expect(screen.getByText(/Content Lifecycle/)).toBeInTheDocument();
  });

  it('Content Lifecycle button is clickable and shows in breadcrumb', async () => {
    render(<PipelineView pipeline={mockPipeline} project={mockProject} />);

    const lifecycleButton = screen.getByText(/Content Lifecycle/);
    expect(lifecycleButton).toBeInTheDocument();

    // Click the button
    fireEvent.click(lifecycleButton);

    // Breadcrumb should now show Content Lifecycle
    await waitFor(() => {
      const breadcrumbItems = screen.getAllByText(/Content Lifecycle/);
      // One in button, one in breadcrumb
      expect(breadcrumbItems.length).toBeGreaterThan(1);
    });
  });

  it('breadcrumb navigation works - clicking pipeline name goes back', async () => {
    render(<PipelineView pipeline={mockPipeline} project={mockProject} />);

    // Click Content Lifecycle
    const lifecycleButton = screen.getByText(/Content Lifecycle/);
    fireEvent.click(lifecycleButton);

    // Verify we're in lifecycle view
    await waitFor(() => {
      expect(screen.getAllByText(/Content Lifecycle/).length).toBeGreaterThan(1);
    });

    // Click pipeline name in breadcrumb to go back
    const breadcrumbButtons = screen.getAllByText('test-pipeline');
    const pipelineBreadcrumb = breadcrumbButtons[0]; // First one is in breadcrumb
    fireEvent.click(pipelineBreadcrumb);

    // Should be back to pipeline view - Configuration section visible
    await waitFor(() => {
      expect(screen.getByText(/Configuration/)).toBeInTheDocument();
    });
  });

  it('displays pipeline header with name and path', () => {
    render(<PipelineView pipeline={mockPipeline} project={mockProject} />);

    // Header should show pipeline name
    const headers = screen.getAllByText('test-pipeline');
    expect(headers.length).toBeGreaterThan(0);

    // Should show the file path
    expect(screen.getByText(/pipelines\/test\.yaml/)).toBeInTheDocument();
  });

  it('Configuration section loads', () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ vars: {} })
    });

    render(<PipelineView pipeline={mockPipeline} project={mockProject} />);

    expect(screen.getByText(/Configuration/)).toBeInTheDocument();
  });

  it('Output section is present', () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ vars: {} })
    });

    render(<PipelineView pipeline={mockPipeline} project={mockProject} />);

    expect(screen.getByText(/Output/)).toBeInTheDocument();
  });

  it('Open Output button is disabled before pipeline runs', () => {
    render(<PipelineView pipeline={mockPipeline} project={mockProject} />);

    const openOutputButton = screen.getByText(/Open Output/);
    expect(openOutputButton).toBeDisabled();
  });

  it('Run Pipeline button is enabled', () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ vars: {} })
    });

    render(<PipelineView pipeline={mockPipeline} project={mockProject} />);

    const runButton = screen.getByText(/Run Pipeline/);
    expect(runButton).not.toBeDisabled();
  });
});

describe('PipelineView - Content Lifecycle Integration', () => {
  const mockPipeline = {
    name: 'test-pipeline',
    path: 'pipelines/test.yaml',
    full_path: '/path/to/test.yaml'
  };

  const mockProject = {
    name: 'test-project',
    path: '/path/to/project'
  };

  it('switches view when Content Lifecycle button clicked', async () => {
    render(<PipelineView pipeline={mockPipeline} project={mockProject} />);

    // Initially in pipeline view - Configuration visible
    expect(screen.queryByText(/Configuration/)).toBeInTheDocument();

    // Click Content Lifecycle button
    const lifecycleButton = screen.getByText(/Content Lifecycle/);
    fireEvent.click(lifecycleButton);

    // Should switch to content lifecycle view
    await waitFor(() => {
      // Configuration section should no longer be visible
      expect(screen.queryByText(/Configuration/)).not.toBeInTheDocument();
    });
  });
});
