import { useState, useEffect } from 'react';
import ContentDashboard from './ContentDashboard';
import FileStatus from './FileStatus';
import DiffViewer from './DiffViewer';
import GitPanel from './GitPanel';
import { Project, ContentConfig, ContentFile } from '../types';

interface ContentAppProps {
  project: Project;
  embedded?: boolean;
}

function ContentApp({ project, embedded = false }: ContentAppProps) {
  const [view, setView] = useState<'dashboard' | 'status' | 'diff'>('dashboard');
  const [config, setConfig] = useState<ContentConfig | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Always use relative URLs - frontend is served by Flask backend
  const API_BASE = '/api';

  useEffect(() => {
    loadConfig();
  }, [project]);

  const loadConfig = async () => {
    try {
      // If project is provided, pass project path to API
      const url = project
        ? `${API_BASE}/content/config?project_path=${encodeURIComponent(project.path)}`
        : `${API_BASE}/content/config`;

      const response = await fetch(url);

      // Check if response is ok
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      if (data.success) {
        setConfig(data);
      } else {
        setError(data.error);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to load configuration: ${errorMessage}`);
    }
  };

  const handleFileSelect = (filePath: string) => {
    setSelectedFile(filePath);
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
      <div className={`flex items-center justify-center ${embedded ? 'py-12' : 'h-screen bg-background'}`}>
        <div className="text-muted-foreground">Loading configuration...</div>
      </div>
    );
  }

  // Embedded mode: simpler layout without full-screen sidebar
  if (embedded) {
    return (
      <div className="h-full flex flex-col bg-background">
        {/* Compact header */}
        <div className="px-6 py-4 border-b border-border bg-secondary">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-foreground">Content Lifecycle</h3>
              <p className="text-xs text-muted-foreground mt-1">
                {config.stages.map(s => s.name).join(' → ')}
              </p>
            </div>
            <GitPanel />
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 overflow-auto">
          {view === 'dashboard' && <ContentDashboard config={config} onFileSelect={handleFileSelect} project={project} />}
          {view === 'status' && selectedFile && <FileStatus file={selectedFile} config={config} project={project} onBack={() => setView('dashboard')} />}
          {view === 'diff' && selectedFile && <DiffViewer file={selectedFile} config={config} onBack={() => setView('status')} />}
        </div>
      </div>
    );
  }

  // Standalone mode: full layout with sidebar
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
        {view === 'dashboard' && <ContentDashboard config={config} onFileSelect={handleFileSelect} project={project} />}
        {view === 'status' && selectedFile && <FileStatus file={selectedFile} config={config} project={project} onBack={() => setView('dashboard')} />}
        {view === 'diff' && selectedFile && <DiffViewer file={selectedFile} config={config} onBack={() => setView('status')} />}
      </main>
    </div>
  );
}

export default ContentApp;
