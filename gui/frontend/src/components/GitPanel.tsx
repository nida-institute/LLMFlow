import React, { useState, useEffect } from 'react';

const API_BASE = '/api';

function GitPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [gitStatus, setGitStatus] = useState(null);
  const [commitMessage, setCommitMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadGitStatus();
    }
  }, [isOpen]);

  const loadGitStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/content/git/status`);
      const data = await response.json();

      if (data.success) {
        setGitStatus(data);
      }
    } catch (err) {
      console.error('Failed to load git status:', err);
    }
  };

  const handleCommit = async () => {
    if (!commitMessage.trim()) {
      setMessage({ type: 'error', text: 'Please enter a commit message' });
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/content/git/commit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: commitMessage }),
      });

      const result = await response.json();

      if (result.success) {
        setMessage({ type: 'success', text: 'Changes committed successfully' });
        setCommitMessage('');
        await loadGitStatus();
      } else {
        setMessage({ type: 'error', text: result.error });
      }
    } catch (err) {
      setMessage({ type: 'error', text: `Commit failed: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handlePush = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/content/git/push`, {
        method: 'POST',
      });

      const result = await response.json();

      if (result.success) {
        setMessage({ type: 'success', text: 'Changes pushed successfully' });
      } else {
        setMessage({ type: 'error', text: result.error });
      }
    } catch (err) {
      setMessage({ type: 'error', text: `Push failed: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handlePull = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/content/git/pull`, {
        method: 'POST',
      });

      const result = await response.json();

      if (result.success) {
        setMessage({ type: 'success', text: 'Changes pulled successfully' });
        await loadGitStatus();
      } else {
        setMessage({ type: 'error', text: result.error });
      }
    } catch (err) {
      setMessage({ type: 'error', text: `Pull failed: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    if (status === 'M') return '📝';
    if (status === 'A') return '➕';
    if (status === 'D') return '🗑️';
    if (status === '??') return '❓';
    return '📄';
  };

  return (
    <div className="relative">
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-4 py-2 bg-secondary text-foreground rounded hover:bg-muted flex items-center gap-2"
      >
        <span>🔧</span>
        <span>Git</span>
        {gitStatus && gitStatus.files && gitStatus.files.length > 0 && (
          <span className="bg-destructive text-destructive-foreground text-xs rounded-full px-2 py-0.5">
            {gitStatus.files.length}
          </span>
        )}
      </button>

      {/* Panel */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black bg-opacity-25 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Panel Content */}
          <div className="absolute right-0 top-full mt-2 w-96 bg-background rounded-lg shadow-xl border border-border z-50">
            <div className="px-4 py-3 border-b border-border">
              <h3 className="font-semibold text-foreground">Git Operations</h3>
            </div>

            <div className="px-4 py-4 max-h-96 overflow-y-auto">
              {message && (
                <div
                  className={`mb-4 p-3 rounded ${
                    message.type === 'success'
                      ? 'bg-accent/10 text-accent-foreground'
                      : 'bg-destructive/10 text-destructive'
                  }`}
                >
                  {message.text}
                </div>
              )}

              {/* Status */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-foreground mb-2">Uncommitted Changes</h4>
                {gitStatus && gitStatus.files && gitStatus.files.length > 0 ? (
                  <div className="space-y-1">
                    {gitStatus.files.map((file, index) => (
                      <div
                        key={index}
                        className="text-sm bg-secondary px-3 py-2 rounded flex items-center gap-2"
                      >
                        <span>{getStatusIcon(file.status)}</span>
                        <span className="text-muted-foreground font-mono text-xs">{file.status}</span>
                        <span className="text-foreground flex-1 truncate">{file.path}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No uncommitted changes</p>
                )}
              </div>

              {/* Commit */}
              {gitStatus && gitStatus.files && gitStatus.files.length > 0 && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Commit Message
                  </label>
                  <textarea
                    value={commitMessage}
                    onChange={(e) => setCommitMessage(e.target.value)}
                    className="w-full px-3 py-2 border border-input rounded bg-background text-foreground focus:ring-accent focus:border-accent"
                    rows="3"
                    placeholder="Enter commit message..."
                  />
                  <button
                    onClick={handleCommit}
                    disabled={loading || !commitMessage.trim()}
                    className="mt-2 w-full px-4 py-2 bg-accent text-accent-foreground rounded hover:bg-accent/90 disabled:bg-muted disabled:cursor-not-allowed"
                  >
                    {loading ? 'Committing...' : 'Commit Changes'}
                  </button>
                </div>
              )}

              {/* Push/Pull */}
              <div className="space-y-2">
                <button
                  onClick={handlePull}
                  disabled={loading}
                  className="w-full px-4 py-2 bg-accent text-accent-foreground rounded hover:bg-accent/90 disabled:bg-muted disabled:cursor-not-allowed"
                >
                  {loading ? 'Pulling...' : '↓ Pull from Remote'}
                </button>
                <button
                  onClick={handlePush}
                  disabled={loading}
                  className="w-full px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:bg-muted disabled:cursor-not-allowed"
                >
                  {loading ? 'Pushing...' : '↑ Push to Remote'}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default GitPanel;
