import { useState, useCallback, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Cpu, Zap, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import { createProject, planProject, getErrorMessage, getSystemStatus } from '../utils/api'
import { ThemeToggle } from '../components/ThemeToggle'
import { ComponentCatalog } from '../components/ComponentCatalog'
import type { SystemStatus } from '../types'

export default function HomePage() {
  const navigate = useNavigate()
  const [request, setRequest] = useState('')
  const [loading, setLoading] = useState(false)
  const [sysStatus, setSysStatus] = useState<SystemStatus | null>(null)

  useEffect(() => {
    getSystemStatus().then(setSysStatus).catch(() => {})
  }, [])

  const handleCreate = useCallback(async (text?: string) => {
    const req = (text ?? request).trim()
    if (!req || req.length < 10) {
      toast.error('Please describe your IoT project (at least 10 characters)')
      return
    }
    setLoading(true)
    try {
      const project = await createProject(req)
      toast.success('Project created! Starting AI planning...')
      // Immediately trigger planning
      await planProject(project.id)
      navigate(`/project/${project.id}`)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [request, navigate])

  const handleSelectComponent = useCallback((compName: string) => {
    setRequest((prev) => {
      const trimmed = prev.trim()
      if (!trimmed) {
        return `ESP32 project with ${compName}`
      }
      if (trimmed.toLowerCase().includes(compName.toLowerCase())) {
        toast('Component already in description', { icon: 'ℹ️' })
        return prev
      }
      return `${trimmed}, including a ${compName}`
    })
    toast.success(`Added ${compName} to project description`)
  }, [])

  return (
    <div className="min-h-screen circuit-bg flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-600 flex items-center justify-center">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-white">CircuitForge <span className="text-cyan-400">AI</span></span>
          <div className="flex-1" />
          <Link to="/setup" className="text-sm text-gray-400 hover:text-cyan-400 transition-colors">
            System Setup
          </Link>
          <Link to="/projects" className="text-sm text-gray-400 hover:text-cyan-400 transition-colors ml-4 mr-4">
            Projects
          </Link>
          <ThemeToggle />
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <div className="text-center mb-8 max-w-2xl">
          <div className="inline-flex items-center gap-2 bg-cyan-900/30 border border-cyan-800 rounded-full px-4 py-1.5 mb-5 text-sm text-cyan-400">
            <span className="w-2 h-2 rounded-full bg-cyan-400 pulse-dot inline-block" />
            Local-First · AI-Powered · Privacy Preserving
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4 leading-tight">
            Describe your IoT idea.<br />
            <span className="text-cyan-400">We build the circuit.</span>
          </h1>
          <p className="text-gray-400 text-base sm:text-lg leading-relaxed">
            From natural language to validated circuits, Arduino firmware, and Wokwi simulations —
            all locally on your machine.
          </p>

          {sysStatus && (
            <div className="flex flex-wrap items-center justify-center gap-2 mt-5 text-xs">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border ${sysStatus.ollama.available ? 'bg-cyan-950/60 border-cyan-800 text-cyan-300' : 'bg-amber-950/60 border-amber-800 text-amber-300'}`}>
                {sysStatus.ollama.available ? <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> : <AlertCircle className="w-3.5 h-3.5 text-amber-400" />}
                Ollama: {sysStatus.ollama.available ? `${[sysStatus.models.planner?.installed, sysStatus.models.firmware_generator?.installed].filter(Boolean).length}/2 models ready` : 'Catalog Fallback'}
              </span>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border ${sysStatus.arduino_cli.available ? 'bg-indigo-950/60 border-indigo-800 text-indigo-300' : 'bg-gray-800 border-gray-700 text-gray-400'}`}>
                {sysStatus.arduino_cli.available ? <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" /> : <AlertCircle className="w-3.5 h-3.5 text-gray-500" />}
                Arduino CLI: {sysStatus.arduino_cli.available ? 'v1.5.1' : 'Not installed'}
              </span>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border ${sysStatus.wokwi_cli?.available ? 'bg-teal-950/60 border-teal-800 text-teal-300' : 'bg-gray-800 border-gray-700 text-gray-400'}`}>
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
                Wokwi CLI: {sysStatus.wokwi_cli?.available ? 'Ready (Licensed)' : 'Manual Mode'}
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border bg-emerald-950/60 border-emerald-800 text-emerald-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Backend: 127.0.0.1:8000
              </span>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="w-full max-w-4xl">
          <div className="forge-card p-6 glow-cyan">
            <label className="block text-sm font-medium text-gray-400 mb-3">
              Describe your IoT project
            </label>
            <textarea
              className="forge-input resize-none text-base leading-relaxed mb-4"
              rows={3}
              value={request}
              onChange={e => setRequest(e.target.value)}
              placeholder="e.g. Build an ESP32 weather station with DHT22, SSD1306 OLED display, and buzzer alert..."
              disabled={loading}
              onKeyDown={e => {
                if (e.key === 'Enter' && e.metaKey) handleCreate()
              }}
            />
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-600">
                {request.length} chars · ⌘+Enter to submit
              </span>
              <button
                className="btn-primary text-base px-6 py-2.5"
                onClick={() => handleCreate()}
                disabled={loading || request.trim().length < 10}
              >
                {loading ? (
                  <><Loader2 className="w-5 h-5 spinner" /> Planning with AI...</>
                ) : (
                  <><Zap className="w-5 h-5" /> Build Circuit</>
                )}
              </button>
            </div>
          </div>

          {/* Available Components Catalog */}
          <ComponentCatalog onSelectComponent={handleSelectComponent} />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-4 text-center text-xs text-gray-700">
        CircuitForge AI · Local-first · Wokwi CLI Connected · No cloud AI required
      </footer>
    </div>
  )
}
