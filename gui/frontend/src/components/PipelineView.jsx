import { useState } from 'react'

export default function PipelineView({ pipeline, project }) {
  const [variables, setVariables] = useState({})
  const [output, setOutput] = useState([])
  const [running, setRunning] = useState(false)

  const handleExecute = async () => {
    setRunning(true)
    setOutput([])

    try {
      const response = await fetch('/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pipeline_path: pipeline.path,
          variables
        })
      })

      const result = await response.json()

      if (result.success) {
        setOutput([
          { type: 'success', text: '✅ Pipeline completed successfully' },
          { type: 'stdout', text: result.stdout }
        ])
      } else {
        setOutput([
          { type: 'error', text: '❌ Pipeline failed' },
          { type: 'stderr', text: result.stderr },
          { type: 'stdout', text: result.stdout }
        ])
      }
    } catch (err) {
      setOutput([{ type: 'error', text: `Error: ${err.message}` }])
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="p-6 border-b border-border bg-background">
        <h2 className="text-2xl font-semibold text-foreground">
          {pipeline.name}
        </h2>
        {pipeline.description && (
          <p className="text-sm text-muted-foreground mt-1">
            {pipeline.description}
          </p>
        )}
        <p className="text-xs text-muted-foreground mt-2 font-mono">
          {project.name}/{pipeline.file}
        </p>
      </header>

      {/* Configuration Form */}
      <div className="p-6 border-b border-border bg-secondary">
        <h3 className="font-semibold mb-4">Configuration</h3>

        {Object.keys(pipeline.variables || {}).length === 0 ? (
          <p className="text-sm text-muted-foreground">
            This pipeline has no configurable variables.
          </p>
        ) : (
          <div className="grid gap-4">
            {Object.entries(pipeline.variables).map(([key, defaultValue]) => (
              <div key={key}>
                <label className="block text-sm font-medium mb-1 text-foreground">
                  {key}
                </label>
                <input
                  type="text"
                  value={variables[key] || defaultValue || ''}
                  onChange={(e) => setVariables({ ...variables, [key]: e.target.value })}
                  className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  placeholder={`Enter ${key}`}
                />
              </div>
            ))}
          </div>
        )}

        <button
          onClick={handleExecute}
          disabled={running}
          className={`mt-4 px-6 py-2 rounded-md font-medium transition-colors ${
            running
              ? 'bg-muted text-muted-foreground cursor-not-allowed'
              : 'bg-primary text-primary-foreground hover:bg-primary/90'
          }`}
        >
          {running ? 'Running...' : 'Run Pipeline'}
        </button>
      </div>

      {/* Output */}
      <div className="flex-1 overflow-auto p-6">
        <h3 className="font-semibold mb-4">Output</h3>

        {output.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Output will appear here after execution.
          </p>
        ) : (
          <div className="space-y-2">
            {output.map((item, idx) => (
              <pre
                key={idx}
                className={`p-4 rounded-md text-sm overflow-x-auto ${
                  item.type === 'error' || item.type === 'stderr'
                    ? 'bg-red-50 text-red-900 dark:bg-red-950 dark:text-red-100'
                    : item.type === 'success'
                    ? 'bg-green-50 text-green-900 dark:bg-green-950 dark:text-green-100'
                    : 'bg-muted text-foreground'
                }`}
              >
                {item.text}
              </pre>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
