import { useState, useEffect } from 'react'
import ProjectList from './components/ProjectList'
import PipelineView from './components/PipelineView'
import ProjectView from './components/ProjectView'
import type { Project, Pipeline, HealthStatus } from './types'

function App() {
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null)
  const [health, setHealth] = useState<HealthStatus | null>(null)

  useEffect(() => {
    // Check backend health
    fetch('/api/health')
      .then(res => res.json())
      .then((data: HealthStatus) => setHealth(data))
      .catch((err: unknown) => console.error('Health check failed:', err))
  }, [])

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="w-80 border-r border-border bg-secondary flex flex-col">
        <header className="p-4 border-b border-border">
          <h1 className="text-xl font-semibold text-foreground">
            Scripture Pipelines
          </h1>
          {health && !health.sp_cli_available && (
            <p className="text-xs text-red-600 mt-1">
              ⚠️ sp CLI not available
            </p>
          )}
        </header>

        <ProjectList
          selectedProject={selectedProject}
          onSelectProject={(project: Project) => {
            setSelectedProject(project)
            setSelectedPipeline(null)
          }}
          onSelectPipeline={(pipeline: Pipeline) => {
            setSelectedPipeline(pipeline)
          }}
        />
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {selectedPipeline && selectedProject ? (
          <PipelineView
            pipeline={selectedPipeline}
            project={selectedProject}
            onBackToProject={() => setSelectedPipeline(null)}
            onBackToProjectList={() => {
              setSelectedPipeline(null)
              setSelectedProject(null)
            }}
          />
        ) : selectedProject ? (
          <ProjectView
            project={selectedProject}
            onSelectPipeline={(pipeline: Pipeline) => setSelectedPipeline(pipeline)}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <div className="text-center">
              <p className="text-lg">Select a project to get started</p>
              <p className="text-sm mt-2">Choose a project from the sidebar</p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
