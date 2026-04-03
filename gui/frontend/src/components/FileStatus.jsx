import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:5051/api';

function FileStatus({ file, config, onBack, onViewDiff }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStatus();
  }, [file]);

  const loadStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/content/status?path=${encodeURIComponent(file)}`);
      const data = await response.json();

      if (data.success) {
        setStatus(data);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError(`Failed to load status: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTransition = async (fromStage, toStage) => {
    try {
      const response = await fetch(`${API_BASE}/content/transition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_stage: fromStage,
          to_stage: toStage,
          path: file,
        }),
      });

      const result = await response.json();

      if (result.success) {
        await loadStatus();
        alert(`Successfully transitioned from ${fromStage} to ${toStage}`);
      } else {
        alert(`Transition failed: ${result.error}`);
      }
    } catch (err) {
      alert(`Transition failed: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="bg-background rounded-lg border border-border p-6">
        <div className="text-center text-muted-foreground">Loading file status...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-background rounded-lg border border-border p-6">
        <div className="bg-destructive/10 border border-destructive rounded-lg p-4">
          <h3 className="text-destructive font-semibold mb-2">Error</h3>
          <p className="text-destructive">{error}</p>
        </div>
        <button
          onClick={onBack}
          className="mt-4 px-4 py-2 bg-secondary text-foreground rounded hover:bg-muted"
        >
          ← Back
        </button>
      </div>
    );
  }

  return (
    <div className="bg-background rounded-lg border border-border">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div>
            <button
              onClick={onBack}
              className="text-accent-foreground hover:text-accent text-sm mb-2"
            >
              ← Back to Dashboard
            </button>
            <h2 className="text-xl font-semibold text-foreground">{status.path}</h2>
            {status.authoritative_stage && (
              <p className="text-sm text-muted-foreground mt-1">
                Authoritative version: <span className="font-medium">{status.authoritative_stage}</span>
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Stage Status */}
      <div className="px-6 py-4">
        <h3 className="text-lg font-semibold text-foreground mb-4">Stage Status</h3>
        <div className="space-y-4">
          {status.stages.map((stageInfo) => (
            <div
              key={stageInfo.name}
              className={`border rounded-lg p-4 ${
                stageInfo.exists ? 'bg-accent/10 border-accent' : 'bg-secondary border-border'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">
                      {stageInfo.name === status.authoritative_stage
                        ? '★'
                        : stageInfo.exists
                        ? '✓'
                        : '✗'}
                    </span>
                    <h4 className="font-semibold text-foreground">{stageInfo.name}</h4>
                  </div>

                  {stageInfo.exists ? (
                    <div className="text-sm text-muted-foreground space-y-1">
                      <p>Path: {stageInfo.file_path}</p>
                      <p>
                        Size: {stageInfo.file_size} bytes · Modified:{' '}
                        {new Date(stageInfo.modified).toLocaleString()}
                      </p>

                      {stageInfo.metadata && (
                        <div className="mt-2 bg-background rounded p-2 border border-border">
                          <p className="font-medium text-foreground">Metadata:</p>
                          {Object.entries(stageInfo.metadata).map(([key, value]) => (
                            <p key={key} className="text-xs">
                              {key}: {value}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">File not present in this stage</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Next Actions */}
      {status.next_actions && status.next_actions.length > 0 && (
        <div className="px-6 py-4 border-t border-border bg-secondary">
          <h3 className="text-lg font-semibold text-foreground mb-3">Next Actions</h3>
          <div className="space-y-2">
            {status.next_actions.map((action, index) => (
              <div key={index} className="flex items-center justify-between bg-background rounded p-3 border border-border">
                <div>
                  <p className="font-medium text-foreground">
                    {action.from} → {action.to}{' '}
                    <span className="text-sm text-muted-foreground">({action.action})</span>
                  </p>
                  <p className="text-xs text-muted-foreground font-mono mt-1">{action.command}</p>
                </div>
                <button
                  onClick={() => handleTransition(action.from, action.to)}
                  className="px-4 py-2 bg-accent text-accent-foreground rounded hover:bg-accent/90 text-sm"
                >
                  Execute →
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default FileStatus;
