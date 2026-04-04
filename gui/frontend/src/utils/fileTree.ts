/**
 * File tree utilities for hierarchical file display.
 *
 * Converts flat file lists with paths into tree structures for navigation.
 */

export interface FileInfo {
  path: string;
  size: number;
  modified: string;
  metadata?: Record<string, any>;
}

export interface FileTreeNode {
  name: string;
  type: 'directory' | 'file';
  children?: FileTreeNode[];
  file?: FileInfo;
  path: string;
}

/**
 * Build a tree structure from a flat list of files with paths.
 */
export function buildFileTree(files: FileInfo[]): FileTreeNode {
  const root: FileTreeNode = {
    name: 'root',
    type: 'directory',
    path: '',
    children: []
  };

  files.forEach(file => {
    const parts = file.path.split('/');
    let current = root;

    parts.forEach((part, index) => {
      const isLastPart = index === parts.length - 1;
      const currentPath = parts.slice(0, index + 1).join('/');

      if (isLastPart) {
        // Leaf node (file)
        if (!current.children) {
          current.children = [];
        }
        current.children.push({
          name: part,
          type: 'file',
          path: currentPath,
          file: file
        });
      } else {
        // Directory node
        if (!current.children) {
          current.children = [];
        }

        let childDir = current.children.find(
          child => child.name === part && child.type === 'directory'
        );

        if (!childDir) {
          childDir = {
            name: part,
            type: 'directory',
            path: currentPath,
            children: []
          };
          current.children.push(childDir);
        }

        current = childDir;
      }
    });
  });

  // Sort children: directories first, then files, both alphabetically
  const sortNodes = (node: FileTreeNode) => {
    if (node.children) {
      node.children.sort((a, b) => {
        // Directories before files
        if (a.type !== b.type) {
          return a.type === 'directory' ? -1 : 1;
        }
        // Alphabetical within type
        return a.name.localeCompare(b.name);
      });
      // Recursively sort children
      node.children.forEach(sortNodes);
    }
  };

  sortNodes(root);

  return root;
}

/**
 * Count total files in a tree node (including nested directories).
 */
export function countFiles(node: FileTreeNode): number {
  if (node.type === 'file') {
    return 1;
  }

  if (!node.children || node.children.length === 0) {
    return 0;
  }

  return node.children.reduce((sum, child) => sum + countFiles(child), 0);
}

/**
 * Get all file paths from a tree node (flattened).
 */
export function getFilePaths(node: FileTreeNode): string[] {
  if (node.type === 'file' && node.file) {
    return [node.file.path];
  }

  if (!node.children || node.children.length === 0) {
    return [];
  }

  return node.children.flatMap(child => getFilePaths(child));
}
