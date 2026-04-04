import { useState, useEffect } from 'react'
import ContentApp from './ContentApp'

export default function ProjectView({ project, onSelectPipeline }) {
  const [activeTab, setActiveTab] = useState('pipelines')
  const [pipelines, setPipelines] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (project) {
      setLoading(true)
      fetch(`/api/projects/${project.name}/pipelines`)
        .then(res => res.json())
        .then(data => {
          setPipelines(data.pipelines || [])
          setLoading(false)
        })
        .catch(err => {
          setError(err.message)
          setLoading(false)
        })
    }
  }, [project])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Loading pipelines...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-600">Error: {error}</p>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Project Header */}
      <div className="p-6 border-b border-border bg-background">
        <h2 className="text-2xl font-semibold text-foreground">
          {project.name}
        </h2>
        {project.description && (
          <p className="text-sm text-muted-foreground mt-2">
            {project.description}
          </p>
        )}
        <p className="text-xs text-muted-foreground mt-2 font-mono">
          {project.path}
        </p>

        {/* Tab Navigation */}
        <div className="flex gap-2 mt-4 border-b border-border">
          <button
            onClick={() => setActiveTab('pipelines')}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === 'pipelines'
                ? 'border-accent text-accent-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            📋 Pipelines ({pipelines.length})
          </button>
          <button
            onClick={() => setActiveTab('content')}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === 'content'
                ? 'border-accent text-accent-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            📝 Content Lifecycle
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'pipelines' ? (
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">
              Pipelines ({pipelines.length})
            </h3>

            {pipelines.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <p>No pipelines found in this project.</p>
                <p className="text-sm mt-2">Create a pipeline in the pipelines/ directory.</p>
              </div>
            ) : (
              <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                {pipelines.map((pipeline) => (
                  <button
                    key={pipeline.path}
                    onClick={() => onSelectPipeline(pipeline)}
                    className="text-left p-4 rounded-lg border border-border bg-card hover:bg-accent hover:border-accent-foreground transition-colors"
                  >
                    <div className="font-semibold text-foreground">
                      {pipeline.name}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1 font-mono">
                      {pipeline.path}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <ContentApp project={project} embedded={true} />
        )}
      </div>
    </div>
  )
}
