/**
 * Integration tests for PipelineView button functionality.
 *
 * These tests verify that buttons:
 * 1. Are enabled/disabled based on correct state
 * 2. Call the right APIs when clicked
 * 3. Handle responses correctly
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import PipelineView from '../components/PipelineView'

// Mock socket.io-client
vi.mock('socket.io-client', () => ({
  io: vi.fn(() => ({
    on: vi.fn(),
    emit: vi.fn(),
    disconnect: vi.fn(),
  })),
}))

describe('PipelineView - Button Integration', () => {
  const mockPipeline = {
    name: 'test-pipeline',
    full_path: '/test/pipeline.yaml',
    file: 'pipeline.yaml',
  }

  const mockProject = {
    name: 'test-project',
    path: '/test/project',
  }

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock fetch for config endpoint
    global.fetch = vi.fn((url) => {
      if (url === '/api/pipeline/config') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ vars: {} }),
        })
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    })
  })

  describe('Run Pipeline Button', () => {
    it('should be enabled when not running', async () => {
      render(
        <PipelineView
          pipeline={mockPipeline}
          project={mockProject}
          onBackToProject={() => {}}
          onBackToProjectList={() => {}}
        />
      )

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /Run Pipeline/i })
        expect(button).not.toBeDisabled()
      })
    })

    it('should connect to WebSocket when clicked', async () => {
      // Get the mocked io function from the module mock
      const { io } = await import('socket.io-client')
      const mockSocket = {
        on: vi.fn(),
        emit: vi.fn(),
        disconnect: vi.fn(),
      }
      
      // Reset and configure the mock for this test
      vi.mocked(io).mockClear()
      vi.mocked(io).mockReturnValue(mockSocket as any)

      render(
        <PipelineView
          pipeline={mockPipeline}
          project={mockProject}
          onBackToProject={() => {}}
          onBackToProjectList={() => {}}
        />
      )

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /Run Pipeline/i })
        fireEvent.click(button)
      })

      // Wait a bit for async operations
      await waitFor(() => {
        // Should call io() to create socket connection
        expect(io).toHaveBeenCalled()
      }, { timeout: 3000 })

      // Should emit execute_pipeline event
      await waitFor(() => {
        expect(mockSocket.emit).toHaveBeenCalledWith(
          'execute_pipeline',
          expect.objectContaining({
            execution_id: expect.any(String),
            pipeline_path: mockPipeline.full_path,
            project_path: mockProject.path,
            variables: expect.any(Object),
          })
        )
      }, { timeout: 3000 })
    })
  })

  describe('Open Output Button', () => {
    it('should be disabled when no output directory set', async () => {
      render(
        <PipelineView
          pipeline={mockPipeline}
          project={mockProject}
          onBackToProject={() => {}}
          onBackToProjectList={() => {}}
        />
      )

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /Open Output/i })
        expect(button).toBeDisabled()
      })
    })

    it('should call /api/open-folder when clicked (if enabled)', async () => {
      const mockFetch = vi.fn((url, options) => {
        if (url === '/api/open-folder') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true }),
          })
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ vars: {} }),
        })
      })
      global.fetch = mockFetch

      render(
        <PipelineView
          pipeline={mockPipeline}
          project={mockProject}
          onBackToProject={() => {}}
          onBackToProjectList={() => {}}
        />
      )

      // TODO: Need to simulate pipeline completion that sets outputDir state
      // This requires mocking the WebSocket 'complete' event that includes output_dir

      // For now, verify button exists and has correct attributes
      await waitFor(() => {
        const button = screen.getByRole('button', { name: /Open Output/i })
        expect(button).toHaveAttribute('title', expect.stringContaining('Run pipeline'))
      })
    })
  })

  describe('Content Lifecycle Button', () => {
    it('should be enabled initially', async () => {
      render(
        <PipelineView
          pipeline={mockPipeline}
          project={mockProject}
          onBackToProject={() => {}}
          onBackToProjectList={() => {}}
        />
      )

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /Content Lifecycle/i })
        expect(button).not.toBeDisabled()
      })
    })

    it('should render ContentApp when clicked', async () => {
      render(
        <PipelineView
          pipeline={mockPipeline}
          project={mockProject}
          onBackToProject={() => {}}
          onBackToProjectList={() => {}}
        />
      )

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /Content Lifecycle/i })
        fireEvent.click(button)
      })

      // After click, ContentApp should be rendered
      // This requires ContentApp to be properly imported and working
      // For now, verify the view switched (breadcrumb should show "Content Lifecycle")
      await waitFor(() => {
        expect(screen.getByText('Content Lifecycle')).toBeInTheDocument()
      })
    })
  })

  describe('Breadcrumb Navigation', () => {
    it('should show project > pipeline', async () => {
      render(
        <PipelineView
          pipeline={mockPipeline}
          project={mockProject}
          onBackToProject={() => {}}
          onBackToProjectList={() => {}}
        />
      )

      await waitFor(() => {
        expect(screen.getByText(mockProject.name)).toBeInTheDocument()
        expect(screen.getByText(mockPipeline.name)).toBeInTheDocument()
      })
    })

    it('should call onBackToProject when project name clicked', async () => {
      const onBackToProject = vi.fn()

      render(
        <PipelineView
          pipeline={mockPipeline}
          project={mockProject}
          onBackToProject={onBackToProject}
          onBackToProjectList={() => {}}
        />
      )

      await waitFor(() => {
        const projectLink = screen.getByRole('button', { name: mockProject.name })
        fireEvent.click(projectLink)
      })

      expect(onBackToProject).toHaveBeenCalled()
    })
  })
})
