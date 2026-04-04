import { useState, useEffect } from 'react';
import StageCard from './StageCard';
import { ContentConfig, Project, ContentFile, Stage } from '../types';

interface ContentDashboardProps {
  config: ContentConfig;
  onFileSelect: (filePath: string) => void;
  onViewChange?: (view: string) => void;
  project: Project;
}

function ContentDashboard({ config, onFileSelect, project }: ContentDashboardProps) {
  // Always use relative URLs - frontend is served by Flask backend
  const API_BASE = '/api';

  const [stageData, setStageData] = useState<Record<string, ContentFile[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAllStages();
  }, [config, project]);

  const loadAllStages = async () => {
    try {
      setLoading(true);

      // Include project_path if available
      const url = project?.path
        ? `${API_BASE}/content/all?project_path=${encodeURIComponent(project.path)}`
        : `${API_BASE}/content/all`;

      const response = await fetch(url);
      const data = await response.json();

      if (data.success) {
        setStageData(data.stages);
      } else {
        setError(data.error);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to load stages: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTransition = async (file: string, fromStage: string, toStage: string) => {
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
        // Reload data
        await loadAllStages();
        alert(`Successfully transitioned ${file} from ${fromStage} to ${toStage}`);
      } else {
        alert(`Transition failed: ${result.error}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      alert(`Transition failed: ${errorMessage}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-muted-foreground">Loading stages...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-destructive/10 border border-destructive rounded-lg p-6">
        <h3 className="text-destructive font-semibold mb-2">Error</h3>
        <p className="text-destructive">{error}</p>
        <button
          onClick={loadAllStages}
          className="mt-4 px-4 py-2 bg-destructive text-destructive-foreground rounded hover:bg-destructive/90"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-foreground">Content Stages</h2>
        <button
          onClick={loadAllStages}
          className="px-4 py-2 bg-accent text-accent-foreground rounded hover:bg-accent/90"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {config.stages.map((stage: Stage, index: number) => (
          <StageCard
            key={stage.name}
            stage={stage}
            files={stageData[stage.name] || []}
            nextStage={config.stages[index + 1]}
            onFileSelect={onFileSelect}
            onTransition={handleTransition}
          />
        ))}
      </div>
    </div>
  );
}

export default ContentDashboard;
