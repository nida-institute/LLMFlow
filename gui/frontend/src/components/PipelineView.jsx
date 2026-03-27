import { useState, useEffect, useRef } from 'react'
import { io } from 'socket.io-client'

export default function PipelineView({ pipeline, project }) {
  const [config, setConfig] = useState(null)
  const [variables, setVariables] = useState({})
  const [output, setOutput] = useState([])
  const [running, setRunning] = useState(false)
  const [loadingConfig, setLoadingConfig] = useState(true)
  const socketRef = useRef(null)
  const outputEndRef = useRef(null)

  // Auto-scroll to bottom when output changes
  useEffect(() => {
    outputEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [output])

  useEffect(() => {
    // Load pipeline config to get variables
    if (pipeline && pipeline.full_path) {
      setLoadingConfig(true)
      fetch('/api/pipeline/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pipeline_path: pipeline.full_path })
      })
        .then(res => res.json())
        .then(data => {
          if (data.error) {
            console.error('Config error:', data.error)
            setConfig({})
          } else {
            setConfig(data)
            // Initialize variables with defaults from vars or variables section
            const varsSection = data.vars || data.variables || {}
            if (varsSection && Object.keys(varsSection).length > 0) {
              setVariables(varsSection)
            }
          }
          setLoadingConfig(false)
        })
        .catch(err => {
          console.error('Failed to load pipeline config:', err)
          setConfig({})
          setLoadingConfig(false)
        })
    }
  }, [pipeline])

  // Cleanup socket on unmount
  useEffect(() => {
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect()
      }
    }
  }, [])

  const renderLine = (text, idx) => {
    // Detect file paths and make them clickable
    const filePathRegex = /([\w\-./]+\.(yaml|yml|txt|md|json|xml|csv|tsv|gpt))/g
    const parts = text.split(filePathRegex)

    return (
      <div key={idx} className="font-mono text-xs leading-relaxed">
        {parts.map((part, i) => {
          if (part.match(filePathRegex)) {
            const fullPath = project?.path ? `${project.path}/${part}` : part
            return (
              <a
                key={i}
                href={`file://${fullPath}`}
                className="text-blue-600 dark:text-blue-400 hover:underline"
                title={`Click to open: ${fullPath}`}
              >
                {part}
              </a>
            )
          }
          return <span key={i}>{part}</span>
        })}
      </div>
    )
  }

  const handleExecute = () => {
    setRunning(true)
    setOutput([])

    // Connect to WebSocket
    const socket = io()
    socketRef.current = socket

    // Listen for events
    socket.on('status', (data) => {
      setOutput(prev => [...prev, { type: 'status', text: data.message }])
    })

    socket.on('heartbeat', (data) => {
      setOutput(prev => [...prev, { type: 'heartbeat', text: data.message }])
    })

    socket.on('output_batch', (data) => {
      setOutput(prev => [...prev, ...data.lines.map(line => ({ type: 'stdout', text: line }))])
    })

    socket.on('complete', (data) => {
      setOutput(prev => [...prev, {
        type: data.exit_code === 0 ? 'success' : 'error',
        text: data.exit_code === 0 ? '✅ Pipeline completed successfully' : '❌ Pipeline failed'
      }])
      setRunning(false)
      socket.disconnect()
    })

    socket.on('error', (data) => {
      setOutput(prev => [...prev, { type: 'error', text: `Error: ${data.message}` }])
      setRunning(false)
      socket.disconnect()
    })

    // Emit execution request
    socket.emit('execute_pipeline', {
      pipeline_path: pipeline.full_path,
      project_path: project.path,
      variables
    })
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

        {loadingConfig ? (
          <p className="text-sm text-muted-foreground">Loading configuration...</p>
        ) : (() => {
          const varsSection = config?.vars || config?.variables || {}
          return Object.keys(varsSection).length === 0 ? (
            <p className="text-sm text-muted-foreground">
              This pipeline has no configurable variables.
            </p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {Object.entries(varsSection).map(([key, defaultValue]) => (
                <div key={key}>
                  <label className="block text-sm font-medium mb-1 text-foreground">
                    {key}
                  </label>
                  <input
                    type="text"
                    value={variables[key] || ''}
                    onChange={(e) => setVariables({ ...variables, [key]: e.target.value })}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                    placeholder={defaultValue ? `Default: ${defaultValue}` : `Enter ${key}`}
                  />
                  {defaultValue && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Default: {defaultValue}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )
        })()}

        <button
          onClick={handleExecute}
          disabled={running || loadingConfig}
          className={`mt-4 px-6 py-2 rounded-md font-medium transition-colors ${
            running || loadingConfig
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
            Click "Run Pipeline" to execute. Output will stream in real-time.
          </p>
        ) : (
          <div className="space-y-0.5 bg-gray-900 text-gray-100 p-4 rounded-lg">
            {output.map((item, idx) => {
              if (item.type === 'status' || item.type === 'heartbeat') {
                return (
                  <div key={idx} className="text-blue-400 italic text-sm mb-2">
                    {item.text}
                  </div>
                )
              } else if (item.type === 'success') {
                return (
                  <div key={idx} className="text-green-400 font-semibold text-lg mt-4 mb-2">
                    {item.text}
                  </div>
                )
              } else if (item.type === 'error') {
                return (
                  <div key={idx} className="text-red-400 font-semibold text-lg mt-4 mb-2">
                    {item.text}
                  </div>
                )
              } else {
                return renderLine(item.text, idx)
              }
            })}
            <div ref={outputEndRef} />
          </div>
        )}
      </div>
    </div>
  )
}
