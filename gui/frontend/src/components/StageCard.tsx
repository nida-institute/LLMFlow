import React, { useState } from 'react';
import { buildFileTree } from '../utils/fileTree';
import FileTreeNode from './FileTreeNode';

function StageCard({ stage, files, nextStage, onFileSelect, onTransition }) {
  const [selectedFiles, setSelectedFiles] = useState(new Set());
  const [viewMode, setViewMode] = useState('tree'); // 'tree' or 'flat'

  // Build tree structure from files
  const fileTree = buildFileTree(files);

  const handleFileToggle = (file) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(file.path)) {
      newSelected.delete(file.path);
    } else {
      newSelected.add(file.path);
    }
    setSelectedFiles(newSelected);
  };

  const handleBulkTransition = () => {
    if (selectedFiles.size === 0 || !nextStage) return;

    const confirmed = confirm(
      `Transition ${selectedFiles.size} file(s) from ${stage.name} to ${nextStage.name}?`
    );

    if (confirmed) {
      selectedFiles.forEach((filePath) => {
        // Remove extension for transition
        const pathWithoutExt = filePath.replace(/\.[^/.]+$/, '');
        onTransition(pathWithoutExt, stage.name, nextStage.name);
      });
      setSelectedFiles(new Set());
    }
  };

  const getStageIcon = () => {
    if (stage.immutable) return '🔒';
    if (stage.protected) return '✏️';
    return '📝';
  };

  const getStageColor = () => {
    if (stage.immutable) return 'bg-secondary border-border';
    if (stage.protected) return 'bg-accent/10 border-accent';
    return 'bg-accent/10 border-accent';
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className={`border rounded-lg overflow-hidden ${getStageColor()}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-border">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-foreground flex items-center gap-2">
            <span>{getStageIcon()}</span>
            <span>{stage.name}</span>
          </h3>
          <span className="text-sm text-muted-foreground">{files.length} files</span>
        </div>
        {stage.protected && (
          <span className="text-xs text-accent-foreground">Protected</span>
        )}
        {stage.immutable && (
          <span className="text-xs text-muted-foreground">Immutable</span>
        )}
      </div>

      {/* File List */}
      <div className="bg-background max-h-96 overflow-y-auto">
        {files.length === 0 ? (
          <div className="px-4 py-8 text-center text-muted-foreground text-sm">
            No files in this stage
          </div>
        ) : (
          <div className="divide-y">
            {files.map((file) => (
              <div
                key={file.path}
                className="px-4 py-3 hover:bg-muted cursor-pointer"
                onClick={() => onFileSelect(file.path)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selectedFiles.has(file.path)}
                        onChange={(e) => {
                          e.stopPropagation();
                          handleFileToggle(file);
                        }}
                        className="h-4 w-4 text-accent"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">
                          {file.path}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatFileSize(file.size)} · Modified{' '}
                          {new Date(file.modified).toLocaleDateString()}
                        </p>
                        {file.metadata && file.metadata.editor && (
                          <p className="text-xs text-muted-foreground">
                            Editor: {file.metadata.editor}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      {nextStage && files.length > 0 && (
        <div className="px-4 py-3 bg-secondary border-t border-border">
          <button
            onClick={handleBulkTransition}
            disabled={selectedFiles.size === 0}
            className={`w-full px-4 py-2 rounded text-sm font-medium ${
              selectedFiles.size > 0
                ? 'bg-accent text-accent-foreground hover:bg-accent/90'
                : 'bg-muted text-muted-foreground cursor-not-allowed'
            }`}
          >
            Send {selectedFiles.size > 0 ? `${selectedFiles.size} file(s)` : ''} to{' '}
            {nextStage.name} →
          </button>
        </div>
      )}
    </div>
  );
}

export default StageCard;
