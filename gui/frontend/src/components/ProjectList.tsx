import { useState, useEffect } from 'react'

export default function ProjectList({ selectedProject, onSelectProject, onSelectPipeline }) {
  const [projects, setProjects] = useState([])
  const [pipelines, setPipelines] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Load projects from registry
    fetch('/api/projects')
      .then(res => res.json())
      .then(data => {
        // API returns {"projects": {"projects": [...]}}
        const projectsList = data.projects?.projects || data.projects || [];
        setProjects(projectsList)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load projects:', err)
        setError(err.message)
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    // Load pipelines when project selected
    if (selectedProject) {
      fetch(`/api/projects/${selectedProject.name}/pipelines`)
        .then(res => res.json())
        .then(data => {
          setPipelines(data.pipelines || [])
        })
        .catch(err => {
          console.error('Failed to load pipelines:', err)
          setPipelines([])
        })
    } else {
      setPipelines([])
    }
  }, [selectedProject])

  if (loading) {
    return (
      <div className="p-4 text-muted-foreground">
        Loading projects...
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 text-red-600">
        Error: {error}
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-auto">
      {/* Projects Section */}
      <div className="p-2">
        <h2 className="px-2 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          Projects ({projects.length})
        </h2>
        {projects.length === 0 ? (
          <p className="px-2 text-sm text-muted-foreground">
            No projects registered. Run `sp init` in a project directory.
          </p>
        ) : (
          <div className="space-y-1">
            {projects.map((project) => (
              <button
                key={project.name}
                onClick={() => onSelectProject(project)}
                className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                  selectedProject?.name === project.name
                    ? 'bg-accent text-accent-foreground font-medium'
                    : 'hover:bg-muted text-foreground'
                }`}
              >
                <div className="font-medium">{project.name}</div>
                {project.description && (
                  <div className="text-xs text-muted-foreground mt-0.5 truncate">
                    {project.description}
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
