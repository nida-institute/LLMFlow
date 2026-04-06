import { useState, useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'
import ContentApp from './ContentApp'
import { Pipeline, Project, PipelineConfig, OutputLine } from '../types'

interface PipelineViewProps {
  pipeline: Pipeline;
  project: Project;
  onBackToProject: () => void;
  onBackToProjectList: () => void;
}

export default function PipelineView({ pipeline, project, onBackToProject }: PipelineViewProps) {
  const [showContentLifecycle, setShowContentLifecycle] = useState(false)
  const [config, setConfig] = useState<PipelineConfig | null>(null)
  const [variables, setVariables] = useState<Record<string, string>>({})
  const [output, setOutput] = useState<OutputLine[]>([])
  const [running, setRunning] = useState(false)
  const [loadingConfig, setLoadingConfig] = useState(true)
  const [outputDir, setOutputDir] = useState<string | null>(null)
  const socketRef = useRef<Socket | null>(null)
  const outputEndRef = useRef<HTMLDivElement | null>(null)

  // Auto-scroll to bottom when output changes
  useEffect(() => {
    outputEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [output])

  useEffect(() => {
    // Load pipeline config to get variables
    if (pipeline && pipeline.full_path && project) {
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

            // Set output directory from pipeline configuration
            // Always use the displayed output_dir setting, whether it exists or not
            const outputDirFromConfig = varsSection.output_dir || 'output'  // default to 'output' if not specified
            const fullOutputPath = `${project.path}/${outputDirFromConfig}`
            setOutputDir(fullOutputPath)
          }
          setLoadingConfig(false)
        })
        .catch(err => {
          console.error('Failed to load pipeline config:', err)
          setConfig({})
          setLoadingConfig(false)
        })
    }
  }, [pipeline, project])

  // Cleanup socket on unmount
  useEffect(() => {
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect()
      }
    }
  }, [])

  const renderLine = (text: string, idx: number) => {
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
    setOutputDir(null)  // Clear previous output directory

    // Generate unique execution ID
    const executionId = `exec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

    // Connect to WebSocket
    const socket = io()
    socketRef.current = socket

    // Listen for events
    socket.on('status', (data: { message: string }) => {
      setOutput(prev => [...prev, { type: 'status' as const, text: data.message }])
    })

    socket.on('heartbeat', (data: { message: string }) => {
      setOutput(prev => [...prev, { type: 'heartbeat' as const, text: data.message }])
    })

    socket.on('output_batch', (data: { lines: string[] }) => {
      setOutput(prev => [...prev, ...data.lines.map((line: string) => ({ type: 'stdout' as const, text: line }))])
    })

    socket.on('complete', (data: { exit_code: number; output_dir?: string; created_files?: string[]; telemetry?: string }) => {
      const completionItems: OutputLine[] = [{
        type: data.exit_code === 0 ? 'success' as const : 'error' as const,
        text: data.exit_code === 0 ? '✅ Pipeline completed successfully' : '❌ Pipeline failed'
      }]

      // Capture output directory for "Open Folder" button
      if (data.output_dir) {
        setOutputDir(data.output_dir)
      }

      // Add created files section
      if (data.created_files && data.created_files.length > 0) {
        completionItems.push({ type: 'section_header' as const, text: '\n📄 Created Files:' })
        data.created_files.forEach((file: string) => {
          completionItems.push({ type: 'file_link' as const, text: file })
        })
      }

      // Add telemetry report
      if (data.telemetry) {
        completionItems.push({ type: 'telemetry' as const, text: data.telemetry })
      }

      setOutput(prev => [...prev, ...completionItems])
      setRunning(false)
      socket.disconnect()
    })

    socket.on('error', (data: { message: string }) => {
      setOutput(prev => [...prev, { type: 'error' as const, text: `Error: ${data.message}` }])
      setRunning(false)
      socket.disconnect()
    })

    // Emit execution request with unique ID
    socket.emit('execute_pipeline', {
      execution_id: executionId,
      pipeline_path: pipeline.full_path,
      project_path: project.path,
      variables
    })
  }

  const handleOpenOutputFolder = async () => {
    if (!outputDir) return

    try {
      const response = await fetch('/api/open-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: outputDir })
      })

      const data = await response.json()

      if (!response.ok) {
        setOutput(prev => [...prev, {
          type: 'error' as const,
          text: `Failed to open folder: ${data.error}`
        }])
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setOutput(prev => [...prev, {
        type: 'error' as const,
        text: `Failed to open folder: ${errorMessage}`
      }])
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Breadcrumb Navigation */}
      <div className="px-6 py-3 border-b border-border bg-muted/50 flex items-center gap-2 text-sm">
        <button
          onClick={onBackToProject}
          className="text-muted-foreground hover:text-foreground hover:underline"
        >
          {project.name}
        </button>
        <span className="text-muted-foreground">›</span>
        <button
          onClick={() => setShowContentLifecycle(false)}
          className={showContentLifecycle ? 'text-muted-foreground hover:text-foreground hover:underline' : 'text-foreground font-medium'}
        >
          {pipeline.name}
        </button>
        {showContentLifecycle && (
          <>
            <span className="text-muted-foreground">›</span>
            <span className="text-foreground font-medium">Content Lifecycle</span>
          </>
        )}
      </div>

      {showContentLifecycle ? (
        /* Content Lifecycle View */
        <div className="flex-1 overflow-auto">
          <ContentApp project={project} embedded={true} />
        </div>
      ) : (
        /* Pipeline View */
        <>
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
              {Object.entries(varsSection).map(([key, defaultValue]) => {
                const defaultStr = defaultValue !== null && defaultValue !== undefined ? String(defaultValue) : '';
                return (
                <div key={key}>
                  <label className="block text-sm font-medium mb-1 text-foreground">
                    {key}
                  </label>
                  <input
                    type="text"
                    value={variables[key] || ''}
                    onChange={(e) => setVariables({ ...variables, [key]: e.target.value })}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                    placeholder={defaultStr ? `Default: ${defaultStr}` : `Enter ${key}`}
                  />
                  {defaultStr && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Default: {defaultStr}
                    </p>
                  )}
                </div>
              )})}
            </div>
          )
        })()}

        <div className="flex gap-3 mt-4">
          <button
            onClick={handleExecute}
            disabled={running || loadingConfig}
            className={`px-6 py-2 rounded-md font-medium transition-colors ${
              running || loadingConfig
                ? 'bg-muted text-muted-foreground cursor-not-allowed'
                : 'bg-primary text-primary-foreground hover:bg-primary/90'
            }`}
          >
            {running ? 'Running...' : 'Run Pipeline'}
          </button>

          <button
            onClick={handleOpenOutputFolder}
            disabled={!outputDir || running}
            className={`px-6 py-2 rounded-md font-medium transition-colors border ${
              !outputDir || running
                ? 'bg-muted text-muted-foreground border-muted cursor-not-allowed'
                : 'bg-background text-foreground hover:bg-muted border-border'
            }`}
            title={outputDir ? `Open ${outputDir} in file manager` : 'Run pipeline to generate output'}
          >
            📁 Open Output
          </button>

          <button
            onClick={() => setShowContentLifecycle(true)}
            className="px-6 py-2 rounded-md font-medium transition-colors border bg-background text-foreground hover:bg-muted border-border"
            title="Manage content through lifecycle stages"
          >
            📋 Content Lifecycle
          </button>
        </div>
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
              } else if (item.type === 'section_header') {
                return (
                  <div key={idx} className="text-yellow-300 font-semibold text-base mt-4 mb-1">
                    {item.text}
                  </div>
                )
              } else if (item.type === 'file_link') {
                return (
                  <div key={idx} className="ml-4 font-mono text-xs">
                    <a
                      href={`file://${item.text}`}
                      className="text-blue-400 hover:text-blue-300 hover:underline"
                      title={`Click to open: ${item.text}`}
                    >
                      {item.text}
                    </a>
                  </div>
                )
              } else if (item.type === 'telemetry') {
                return (
                  <div key={idx} className="mt-4 pt-4 border-t border-gray-700">
                    <pre className="text-xs font-mono whitespace-pre-wrap text-gray-300">
                      {item.text}
                    </pre>
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
        </>
      )}
    </div>
  )
}
