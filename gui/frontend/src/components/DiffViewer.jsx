import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:5051/api';

function DiffViewer({ file, config, onBack }) {
  const [fromStage, setFromStage] = useState('');
  const [toStage, setToStage] = useState('');
  const [diff, setDiff] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Set default stages if available
    if (config.stages.length >= 2) {
      setFromStage(config.stages[0].name);
      setToStage(config.stages[1].name);
    }
  }, [config]);

  const loadDiff = async () => {
    if (!fromStage || !toStage) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE}/content/diff?path=${encodeURIComponent(file)}&from_stage=${encodeURIComponent(fromStage)}&to_stage=${encodeURIComponent(toStage)}`
      );
      const data = await response.json();

      if (data.success) {
        setDiff(data);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError(`Failed to load diff: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const renderDiffLine = (line) => {
    if (line.startsWith('+++') || line.startsWith('---')) {
      return <div className="text-gray-600 font-semibold">{line}</div>;
    }
    if (line.startsWith('@@')) {
      return <div className="text-blue-600 bg-blue-50 px-2 py-1 font-mono text-sm">{line}</div>;
    }
    if (line.startsWith('+')) {
      return <div className="text-green-700 bg-green-50 px-2 font-mono text-sm">{line}</div>;
    }
    if (line.startsWith('-')) {
      return <div className="text-red-700 bg-red-50 px-2 font-mono text-sm">{line}</div>;
    }
    return <div className="text-gray-700 px-2 font-mono text-sm">{line}</div>;
  };

  return (
    <div className="bg-background rounded-lg border border-border">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border">
        <button
          onClick={onBack}
          className="text-accent-foreground hover:text-accent text-sm mb-2"
        >
          ← Back
        </button>
        <h2 className="text-xl font-semibold text-foreground">Compare Versions: {file}</h2>
      </div>

      {/* Controls */}
      <div className="px-6 py-4 border-b border-border bg-secondary">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-foreground mb-1">From Stage</label>
            <select
              value={fromStage}
              onChange={(e) => setFromStage(e.target.value)}
              className="w-full px-3 py-2 border border-input rounded bg-background text-foreground focus:ring-accent focus:border-accent"
            >
              <option value="">Select stage...</option>
              {config.stages.map((stage) => (
                <option key={stage.name} value={stage.name}>
                  {stage.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium text-foreground mb-1">To Stage</label>
            <select
              value={toStage}
              onChange={(e) => setToStage(e.target.value)}
              className="w-full px-3 py-2 border border-input rounded bg-background text-foreground focus:ring-accent focus:border-accent"
            >
              <option value="">Select stage...</option>
              {config.stages.map((stage) => (
                <option key={stage.name} value={stage.name}>
                  {stage.name}
                </option>
              ))}
            </select>
          </div>

          <div className="pt-6">
            <button
              onClick={loadDiff}
              disabled={!fromStage || !toStage || loading}
              className="px-6 py-2 bg-accent text-accent-foreground rounded hover:bg-accent/90 disabled:bg-muted disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : 'Compare'}
            </button>
          </div>
        </div>
      </div>

      {/* Diff Output */}
      <div className="px-6 py-4">
        {error && (
          <div className="bg-destructive/10 border border-destructive rounded p-4 mb-4">
            <p className="text-destructive">{error}</p>
          </div>
        )}

        {diff && !diff.has_differences && (
          <div className="bg-accent/10 border border-accent rounded p-4">
            <p className="text-accent-foreground">✓ Files are identical</p>
            <p className="text-sm text-muted-foreground mt-1">
              {fromStage}: {diff.from_file}
            </p>
            <p className="text-sm text-muted-foreground">
              {toStage}: {diff.to_file}
            </p>
          </div>
        )}

        {diff && diff.has_differences && diff.diff_lines && (
          <div className="border border-border rounded overflow-hidden">
            <div className="bg-muted px-4 py-2 border-b border-border">
              <p className="text-sm text-foreground">
                Comparing <span className="font-mono">{diff.from_file}</span> with{' '}
                <span className="font-mono">{diff.to_file}</span>
              </p>
            </div>
            <div className="max-h-[600px] overflow-y-auto">
              {diff.diff_lines.map((line, index) => (
                <div key={index}>{renderDiffLine(line)}</div>
              ))}
            </div>
          </div>
        )}

        {!diff && !loading && !error && (
          <div className="text-center text-muted-foreground py-12">
            Select stages and click Compare to view differences
          </div>
        )}
      </div>
    </div>
  );
}

export default DiffViewer;
