import React, { useState } from 'react';
import { FileTreeNode as TreeNodeType, countFiles } from '../utils/fileTree';

interface FileTreeNodeProps {
  node: TreeNodeType;
  depth: number;
  onFileSelect: (path: string) => void;
  selectedFiles?: Set<string>;
}

function FileTreeNode({ node, depth, onFileSelect, selectedFiles }: FileTreeNodeProps) {
  const [expanded, setExpanded] = useState(false);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleClick = () => {
    if (node.type === 'directory') {
      setExpanded(!expanded);
    } else if (node.file) {
      // Remove extension for file selection (matches original StageCard behavior)
      const pathWithoutExt = node.file.path.replace(/\.[^/.]+$/, '');
      onFileSelect(pathWithoutExt);
    }
  };

  const paddingLeft = depth * 16;

  if (node.type === 'file' && node.file) {
    const isSelected = selectedFiles?.has(node.file.path);

    return (
      <div
        style={{ paddingLeft: `${paddingLeft}px` }}
        className={`px-4 py-2 hover:bg-muted cursor-pointer flex items-center gap-2 ${
          isSelected ? 'bg-accent/20' : ''
        }`}
        onClick={handleClick}
      >
        <span>📄</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-foreground truncate">
            {node.name}
          </p>
          <p className="text-xs text-muted-foreground">
            {formatFileSize(node.file.size)}
          </p>
        </div>
      </div>
    );
  }

  // Directory node
  const fileCount = countFiles(node);
  const fileText = fileCount === 1 ? '1 file' : `${fileCount} files`;

  return (
    <div style={{ paddingLeft: `${paddingLeft}px` }}>
      <button
        onClick={handleClick}
        className="w-full px-4 py-2 hover:bg-muted cursor-pointer flex items-center gap-2 text-left"
      >
        <span>{expanded ? '📂' : '📁'}</span>
        <div className="flex-1">
          <span className="text-sm font-medium text-foreground">{node.name}</span>
          <span className="text-xs text-muted-foreground ml-2">({fileText})</span>
        </div>
      </button>

      {expanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeNode
              key={child.path}
              node={child}
              depth={depth + 1}
              onFileSelect={onFileSelect}
              selectedFiles={selectedFiles}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default FileTreeNode;
