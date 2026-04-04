import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import FileTreeNode from '../components/FileTreeNode';
import { FileTreeNode as TreeNodeType } from '../utils/fileTree';

describe('FileTreeNode Component', () => {
  const mockOnFileSelect = vi.fn();

  beforeEach(() => {
    mockOnFileSelect.mockClear();
  });

  it('renders a file node', () => {
    const fileNode: TreeNodeType = {
      name: 'test.md',
      type: 'file',
      path: 'test.md',
      file: {
        path: 'test.md',
        size: 1024,
        modified: '2026-04-04T00:00:00Z'
      }
    };

    render(<FileTreeNode node={fileNode} depth={0} onFileSelect={mockOnFileSelect} />);

    expect(screen.getByText('test.md')).toBeInTheDocument();
    expect(screen.getByText(/1\.0 KB/)).toBeInTheDocument();
  });

  it('renders a directory node', () => {
    const dirNode: TreeNodeType = {
      name: 'ab',
      type: 'directory',
      path: 'ab',
      children: [
        {
          name: 'test.md',
          type: 'file',
          path: 'ab/test.md',
          file: { path: 'ab/test.md', size: 1024, modified: '2026-04-04T00:00:00Z' }
        }
      ]
    };

    render(<FileTreeNode node={dirNode} depth={0} onFileSelect={mockOnFileSelect} />);

    expect(screen.getByText('ab')).toBeInTheDocument();
    expect(screen.getByText(/1 file/)).toBeInTheDocument();
  });

  it('expands directory when clicked', () => {
    const dirNode: TreeNodeType = {
      name: 'ab',
      type: 'directory',
      path: 'ab',
      children: [
        {
          name: 'test.md',
          type: 'file',
          path: 'ab/test.md',
          file: { path: 'ab/test.md', size: 1024, modified: '2026-04-04T00:00:00Z' }
        }
      ]
    };

    render(<FileTreeNode node={dirNode} depth={0} onFileSelect={mockOnFileSelect} />);

    // Initially collapsed - file not visible
    expect(screen.queryByText('test.md')).not.toBeInTheDocument();

    // Click to expand
    const folderButton = screen.getByText('ab').closest('button');
    fireEvent.click(folderButton!);

    // File should now be visible
    expect(screen.getByText('test.md')).toBeInTheDocument();
  });

  it('collapses directory when clicked twice', () => {
    const dirNode: TreeNodeType = {
      name: 'ab',
      type: 'directory',
      path: 'ab',
      children: [
        {
          name: 'test.md',
          type: 'file',
          path: 'ab/test.md',
          file: { path: 'ab/test.md', size: 1024, modified: '2026-04-04T00:00:00Z' }
        }
      ]
    };

    render(<FileTreeNode node={dirNode} depth={0} onFileSelect={mockOnFileSelect} />);

    const folderButton = screen.getByText('ab').closest('button');

    // Expand
    fireEvent.click(folderButton!);
    expect(screen.getByText('test.md')).toBeInTheDocument();

    // Collapse
    fireEvent.click(folderButton!);
    expect(screen.queryByText('test.md')).not.toBeInTheDocument();
  });

  it('calls onFileSelect when file is clicked', () => {
    const fileNode: TreeNodeType = {
      name: 'test.md',
      type: 'file',
      path: 'test.md',
      file: {
        path: 'test.md',
        size: 1024,
        modified: '2026-04-04T00:00:00Z'
      }
    };

    render(<FileTreeNode node={fileNode} depth={0} onFileSelect={mockOnFileSelect} />);

    const fileElement = screen.getByText('test.md').closest('div');
    fireEvent.click(fileElement!);

    // Expects path without extension (matches StageCard behavior)
    expect(mockOnFileSelect).toHaveBeenCalledWith('test');
  });

  it('renders nested directories', () => {
    const dirNode: TreeNodeType = {
      name: 'Mark',
      type: 'directory',
      path: 'Mark',
      children: [
        {
          name: 'scenes',
          type: 'directory',
          path: 'Mark/scenes',
          children: [
            {
              name: 'Mark_11_12-25.md',
              type: 'file',
              path: 'Mark/scenes/Mark_11_12-25.md',
              file: { path: 'Mark/scenes/Mark_11_12-25.md', size: 1024, modified: '2026-04-04T00:00:00Z' }
            }
          ]
        }
      ]
    };

    render(<FileTreeNode node={dirNode} depth={0} onFileSelect={mockOnFileSelect} />);

    // Expand Mark directory
    const markButton = screen.getByText('Mark').closest('button');
    fireEvent.click(markButton!);

    // Scenes subdirectory should be visible
    expect(screen.getByText('scenes')).toBeInTheDocument();

    // Expand scenes directory
    const scenesButton = screen.getByText('scenes').closest('button');
    fireEvent.click(scenesButton!);

    // File should be visible
    expect(screen.getByText('Mark_11_12-25.md')).toBeInTheDocument();
  });

  it('applies indentation based on depth', () => {
    const fileNode: TreeNodeType = {
      name: 'test.md',
      type: 'file',
      path: 'test.md',
      file: { path: 'test.md', size: 1024, modified: '2026-04-04T00:00:00Z' }
    };

    const { container } = render(
      <FileTreeNode node={fileNode} depth={2} onFileSelect={mockOnFileSelect} />
    );

    const element = container.firstChild as HTMLElement;
    expect(element.style.paddingLeft).toBe('32px'); // 2 * 16px
  });

  it('displays folder icon for directories', () => {
    const dirNode: TreeNodeType = {
      name: 'ab',
      type: 'directory',
      path: 'ab',
      children: []
    };

    render(<FileTreeNode node={dirNode} depth={0} onFileSelect={mockOnFileSelect} />);

    // Should show folder icon (📁 when collapsed)
    expect(screen.getByText(/📁/)).toBeInTheDocument();
  });

  it('changes folder icon when expanded', () => {
    const dirNode: TreeNodeType = {
      name: 'ab',
      type: 'directory',
      path: 'ab',
      children: [
        {
          name: 'test.md',
          type: 'file',
          path: 'ab/test.md',
          file: { path: 'ab/test.md', size: 1024, modified: '2026-04-04T00:00:00Z' }
        }
      ]
    };

    render(<FileTreeNode node={dirNode} depth={0} onFileSelect={mockOnFileSelect} />);

    // Collapsed - closed folder
    expect(screen.getByText(/📁/)).toBeInTheDocument();

    // Expand
    const folderButton = screen.getByText('ab').closest('button');
    fireEvent.click(folderButton!);

    // Expanded - open folder
    expect(screen.getByText(/📂/)).toBeInTheDocument();
  });

  it('displays file icon for files', () => {
    const fileNode: TreeNodeType = {
      name: 'test.md',
      type: 'file',
      path: 'test.md',
      file: { path: 'test.md', size: 1024, modified: '2026-04-04T00:00:00Z' }
    };

    render(<FileTreeNode node={fileNode} depth={0} onFileSelect={mockOnFileSelect} />);

    expect(screen.getByText(/📄/)).toBeInTheDocument();
  });

  it('displays file count for directories', () => {
    const dirNode: TreeNodeType = {
      name: 'ab',
      type: 'directory',
      path: 'ab',
      children: [
        {
          name: 'test1.md',
          type: 'file',
          path: 'ab/test1.md',
          file: { path: 'ab/test1.md', size: 1024, modified: '2026-04-04T00:00:00Z' }
        },
        {
          name: 'test2.md',
          type: 'file',
          path: 'ab/test2.md',
          file: { path: 'ab/test2.md', size: 2048, modified: '2026-04-04T00:00:00Z' }
        }
      ]
    };

    render(<FileTreeNode node={dirNode} depth={0} onFileSelect={mockOnFileSelect} />);

    expect(screen.getByText(/2 files/)).toBeInTheDocument();
  });

  it('handles empty directory', () => {
    const dirNode: TreeNodeType = {
      name: 'empty',
      type: 'directory',
      path: 'empty',
      children: []
    };

    render(<FileTreeNode node={dirNode} depth={0} onFileSelect={mockOnFileSelect} />);

    expect(screen.getByText('empty')).toBeInTheDocument();
    expect(screen.getByText(/0 files/)).toBeInTheDocument();
  });
});
