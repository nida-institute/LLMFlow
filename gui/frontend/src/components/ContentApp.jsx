import { useState, useEffect } from 'react';
import ContentDashboard from './ContentDashboard';
import FileStatus from './FileStatus';
import DiffViewer from './DiffViewer';
import GitPanel from './GitPanel';

const API_BASE = 'http://localhost:5051/api';

function ContentApp() {
  const [view, setView] = useState('dashboard');
  const [config, setConfig] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await fetch(`${API_BASE}/content/config`);
      const data = await response.json();
      if (data.success) {
        setConfig(data);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError(`Failed to load configuration: ${err.message}`);
    }
  };

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setView('status');
  };

  if (error) {
    return (
      <div className="flex h-screen bg-background items-center justify-center">
        <div className="bg-destructive/10 border border-destructive rounded-lg p-6 max-w-md">
          <h2 className="text-destructive font-semibold text-lg mb-2">Error</h2>
          <p className="text-destructive">{error}</p>
          <button
            onClick={loadConfig}
            className="mt-4 px-4 py-2 bg-destructive text-destructive-foreground rounded hover:bg-destructive/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="flex h-screen bg-background items-center justify-center">
        <div className="text-muted-foreground">Loading configuration...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="w-80 border-r border-border bg-secondary flex flex-col">
        <header className="p-4 border-b border-border">
          <h1 className="text-xl font-semibold text-foreground">Content Lifecycle</h1>
          <p className="text-sm text-muted-foreground mt-1">{config.stages.length} stages configured</p>
        </header>

        <nav className="flex flex-col p-2 border-b border-border">
          <button
            onClick={() => setView('dashboard')}
            className={`px-3 py-2 rounded text-sm text-left ${
              view === 'dashboard'
                ? 'bg-accent text-accent-foreground'
                : 'text-foreground hover:bg-muted'
            }`}
          >
            📊 Dashboard
          </button>
        </nav>

        <div className="p-4 border-b border-border">
          <GitPanel />
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <h3 className="text-sm font-semibold text-foreground mb-2">Stages</h3>
          <div className="space-y-1">
            {config.stages.map((stage) => (
              <div key={stage.name} className="px-3 py-2 rounded bg-muted text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-foreground">{stage.name}</span>
                  <span className="text-xs">{stage.immutable ? '🔒' : stage.protected ? '✏️' : '📝'}</span>
                </div>
                <div className="text-xs text-muted-foreground mt-1">{stage.file_permissions}</div>
              </div>
            ))}
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-hidden bg-background">
        {view === 'dashboard' && <ContentDashboard config={config} onFileSelect={handleFileSelect} />}
        {view === 'status' && selectedFile && <FileStatus file={selectedFile} config={config} onBack={() => setView('dashboard')} />}
        {view === 'diff' && selectedFile && <DiffViewer file={selectedFile} config={config} onBack={() => setView('status')} />}
      </main>
    </div>
  );
}

export default ContentApp;
