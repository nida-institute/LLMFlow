import { describe, it, expect } from 'vitest';
import { buildFileTree, countFiles, getFilePaths, FileInfo } from '../utils/fileTree';

describe('buildFileTree', () => {
  it('builds tree from flat file list', () => {
    const files: FileInfo[] = [
      { path: 'ab/abandon.md', size: 1024, modified: '2026-04-04T00:00:00Z' },
      { path: 'ab/abide.md', size: 2048, modified: '2026-04-04T00:00:00Z' },
      { path: 'ch/choose.md', size: 1536, modified: '2026-04-04T00:00:00Z' }
    ];

    const tree = buildFileTree(files);

    expect(tree.name).toBe('root');
    expect(tree.type).toBe('directory');
    expect(tree.children).toHaveLength(2); // 'ab' and 'ch' directories

    const abDir = tree.children?.find(c => c.name === 'ab');
    expect(abDir).toBeDefined();
    expect(abDir?.type).toBe('directory');
    expect(abDir?.children).toHaveLength(2);

    const abandonFile = abDir?.children?.find(c => c.name === 'abandon.md');
    expect(abandonFile).toBeDefined();
    expect(abandonFile?.type).toBe('file');
    expect(abandonFile?.file?.path).toBe('ab/abandon.md');
    expect(abandonFile?.file?.size).toBe(1024);
  });

  it('handles single-level files (no subdirectories)', () => {
    const files: FileInfo[] = [
      { path: 'test.md', size: 1024, modified: '2026-04-04T00:00:00Z' },
      { path: 'another.md', size: 2048, modified: '2026-04-04T00:00:00Z' }
    ];

    const tree = buildFileTree(files);

    expect(tree.children).toHaveLength(2);
    expect(tree.children?.[0].type).toBe('file');
    expect(tree.children?.[1].type).toBe('file');
  });

  it('handles nested directories (3+ levels)', () => {
    const files: FileInfo[] = [
      { path: 'Mark/scenes/Mark_11_12-25.md', size: 1024, modified: '2026-04-04T00:00:00Z' },
      { path: 'Mark/scenes/Mark_11_1-11.md', size: 2048, modified: '2026-04-04T00:00:00Z' },
      { path: 'Mark/Mark_11.md', size: 3072, modified: '2026-04-04T00:00:00Z' }
    ];

    const tree = buildFileTree(files);

    expect(tree.children).toHaveLength(1); // 'Mark' directory

    const markDir = tree.children?.[0];
    expect(markDir?.name).toBe('Mark');
    expect(markDir?.children).toHaveLength(2); // 'scenes' directory and 'Mark_11.md' file

    const scenesDir = markDir?.children?.find(c => c.name === 'scenes');
    expect(scenesDir).toBeDefined();
    expect(scenesDir?.type).toBe('directory');
    expect(scenesDir?.children).toHaveLength(2);
  });

  it('sorts directories before files', () => {
    const files: FileInfo[] = [
      { path: 'zebra.md', size: 1024, modified: '2026-04-04T00:00:00Z' },
      { path: 'ab/test.md', size: 2048, modified: '2026-04-04T00:00:00Z' },
      { path: 'aardvark.md', size: 3072, modified: '2026-04-04T00:00:00Z' }
    ];

    const tree = buildFileTree(files);

    expect(tree.children).toHaveLength(3);
    expect(tree.children?.[0].type).toBe('directory'); // 'ab' directory first
    expect(tree.children?.[0].name).toBe('ab');
    expect(tree.children?.[1].type).toBe('file'); // then files alphabetically
    expect(tree.children?.[1].name).toBe('aardvark.md');
    expect(tree.children?.[2].name).toBe('zebra.md');
  });

  it('sorts alphabetically within same type', () => {
    const files: FileInfo[] = [
      { path: 'zy/test.md', size: 1024, modified: '2026-04-04T00:00:00Z' },
      { path: 'ab/test.md', size: 2048, modified: '2026-04-04T00:00:00Z' },
      { path: 'ch/test.md', size: 3072, modified: '2026-04-04T00:00:00Z' }
    ];

    const tree = buildFileTree(files);

    expect(tree.children?.[0].name).toBe('ab');
    expect(tree.children?.[1].name).toBe('ch');
    expect(tree.children?.[2].name).toBe('zy');
  });

  it('handles empty file list', () => {
    const tree = buildFileTree([]);

    expect(tree.children).toHaveLength(0);
  });

  it('preserves file metadata', () => {
    const files: FileInfo[] = [
      {
        path: 'test.md',
        size: 1024,
        modified: '2026-04-04T00:00:00Z',
        metadata: { editor: 'john', version: 2 }
      }
    ];

    const tree = buildFileTree(files);

    const file = tree.children?.[0];
    expect(file?.file?.metadata).toEqual({ editor: 'john', version: 2 });
  });

  it('sets correct paths for nested nodes', () => {
    const files: FileInfo[] = [
      { path: 'a/b/c.md', size: 1024, modified: '2026-04-04T00:00:00Z' }
    ];

    const tree = buildFileTree(files);

    const aDir = tree.children?.[0];
    expect(aDir?.path).toBe('a');

    const bDir = aDir?.children?.[0];
    expect(bDir?.path).toBe('a/b');

    const cFile = bDir?.children?.[0];
    expect(cFile?.path).toBe('a/b/c.md');
  });
});

describe('countFiles', () => {
  it('counts files in flat structure', () => {
    const files: FileInfo[] = [
      { path: 'a.md', size: 1024, modified: '2026-04-04T00:00:00Z' },
      { path: 'b.md', size: 2048, modified: '2026-04-04T00:00:00Z' }
    ];

    const tree = buildFileTree(files);
    expect(countFiles(tree)).toBe(2);
  });

  it('counts files in nested structure', () => {
    const files: FileInfo[] = [
      { path: 'ab/abandon.md', size: 1024, modified: '2026-04-04T00:00:00Z' },
      { path: 'ab/abide.md', size: 2048, modified: '2026-04-04T00:00:00Z' },
      { path: 'ch/choose.md', size: 1536, modified: '2026-04-04T00:00:00Z' }
    ];

    const tree = buildFileTree(files);
    expect(countFiles(tree)).toBe(3);
  });

  it('counts files in deeply nested structure', () => {
    const files: FileInfo[] = [
      { path: 'a/b/c/d.md', size: 1024, modified: '2026-04-04T00:00:00Z' },
      { path: 'a/b/e.md', size: 2048, modified: '2026-04-04T00:00:00Z' },
      { path: 'a/f.md', size: 3072, modified: '2026-04-04T00:00:00Z' }
    ];

    const tree = buildFileTree(files);
    expect(countFiles(tree)).toBe(3);
  });

  it('returns 0 for empty directory', () => {
    const tree = buildFileTree([]);
    expect(countFiles(tree)).toBe(0);
  });

  it('counts files in subdirectory node', () => {
    const files: FileInfo[] = [
      { path: 'ab/test1.md', size: 1024, modified: '2026-04-04T00:00:00Z' },
      { path: 'ab/test2.md', size: 2048, modified: '2026-04-04T00:00:00Z' },
      { path: 'ch/test3.md', size: 3072, modified: '2026-04-04T00:00:00Z' }
    ];

    const tree = buildFileTree(files);
    const abDir = tree.children?.find(c => c.name === 'ab');
    expect(countFiles(abDir!)).toBe(2);
  });
});

describe('getFilePaths', () => {
  it('gets all file paths from tree', () => {
    const files: FileInfo[] = [
      { path: 'ab/abandon.md', size: 1024, modified: '2026-04-04T00:00:00Z' },
      { path: 'ab/abide.md', size: 2048, modified: '2026-04-04T00:00:00Z' },
      { path: 'ch/choose.md', size: 1536, modified: '2026-04-04T00:00:00Z' }
    ];

    const tree = buildFileTree(files);
    const paths = getFilePaths(tree);

    expect(paths).toHaveLength(3);
    expect(paths).toContain('ab/abandon.md');
    expect(paths).toContain('ab/abide.md');
    expect(paths).toContain('ch/choose.md');
  });

  it('gets file paths from subdirectory node', () => {
    const files: FileInfo[] = [
      { path: 'ab/test1.md', size: 1024, modified: '2026-04-04T00:00:00Z' },
      { path: 'ab/test2.md', size: 2048, modified: '2026-04-04T00:00:00Z' },
      { path: 'ch/test3.md', size: 3072, modified: '2026-04-04T00:00:00Z' }
    ];

    const tree = buildFileTree(files);
    const abDir = tree.children?.find(c => c.name === 'ab');
    const paths = getFilePaths(abDir!);

    expect(paths).toHaveLength(2);
    expect(paths).toContain('ab/test1.md');
    expect(paths).toContain('ab/test2.md');
  });

  it('returns empty array for empty tree', () => {
    const tree = buildFileTree([]);
    const paths = getFilePaths(tree);

    expect(paths).toHaveLength(0);
  });
});
