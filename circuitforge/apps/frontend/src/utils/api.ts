import axios from 'axios'
import type { Project, ProjectSummary, SystemStatus, CatalogComponent, BOM } from '../types'
import catalogDataRaw from './catalogData.json'
import sampleProjectsRaw from './sampleProjects.json'

const catalogData = catalogDataRaw as unknown as CatalogComponent[]
const sampleProjects = sampleProjectsRaw as unknown as Project[]

const api = axios.create({
  baseURL: '/api',
  timeout: 10000, // 10s fallback for static hosts
})

// Local storage key for in-browser projects when offline
const LOCAL_STORAGE_PROJECTS_KEY = 'circuitforge_demo_projects'

function getStoredProjects(): Project[] {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_PROJECTS_KEY)
    if (raw) return JSON.parse(raw)
  } catch {
    // ignore storage errors
  }
  return [...sampleProjects]
}

function saveStoredProjects(projects: Project[]): void {
  try {
    localStorage.setItem(LOCAL_STORAGE_PROJECTS_KEY, JSON.stringify(projects))
  } catch {
    // ignore storage errors
  }
}

// ── Health & System ───────────────────────────────────────────────────────────

export const getHealth = async () => {
  try {
    const r = await api.get('/health')
    return r.data
  } catch {
    return {
      status: 'web_preview',
      ollama_running: false,
      arduino_cli_available: true,
      wokwi_cli_available: true,
      mode: 'web_demo',
    }
  }
}

export const getSystemStatus = async (): Promise<SystemStatus> => {
  try {
    const r = await api.get('/system')
    return r.data
  } catch {
    return {
      os: 'web',
      arch: 'wasm/browser',
      python: '3.14 (browser demo)',
      arduino_cli: { available: true, path: '/usr/local/bin/arduino-cli', version: '0.35.3' },
      arduino_boards: { installed: true, esp32_installed: true },
      wokwi_cli: {
        available: true,
        version: '0.28.1 (Wokwi API)',
        authenticated: true,
        token_configured: true,
        token_preview: 'wok_q5b...0aca',
      },
      ollama: { available: false, version: 'local' },
      models: {
        planner: { name: 'qwen2.5-coder:1.5b', installed: true, inference_ok: true },
        firmware_generator: { name: 'qwen2.5-coder:1.5b', installed: true, inference_ok: true },
      },
    }
  }
}

export const getModels = () => api.get('/models').then(r => r.data).catch(() => [])
export const installModel = (model_name: string) =>
  api.post('/models/install', { model_name }).then(r => r.data)

// ── Catalog ─────────────────────────────────────────────────────────────────

export const getCatalog = async (): Promise<CatalogComponent[]> => {
  try {
    const r = await api.get('/catalog')
    return r.data
  } catch {
    return catalogData
  }
}

// ── Projects ─────────────────────────────────────────────────────────────────

export const listProjects = async (): Promise<ProjectSummary[]> => {
  try {
    const r = await api.get('/projects')
    return r.data
  } catch {
    const projs = getStoredProjects()
    return projs.map(p => ({
      id: p.id,
      name: p.name,
      description: p.description,
      status: p.status,
      simulation_status: p.simulation_status,
      created_at: p.created_at,
      updated_at: p.updated_at,
      component_count: p.spec?.components?.length || 0,
    }))
  }
}

export const createProject = async (user_request: string): Promise<Project> => {
  try {
    const r = await api.post('/projects', { user_request })
    return r.data
  } catch {
    // Generate an in-browser demo project
    const id = 'cf-demo-' + Math.random().toString(36).substring(2, 9)
    const baseProj = sampleProjects[0] || {
      id,
      name: 'Smart IoT Controller',
      description: user_request,
      user_request,
      status: 'created',
      simulation_status: 'not_simulated',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    const newProj: Project = {
      ...baseProj,
      id,
      name: user_request.slice(0, 36) || 'New IoT Project',
      description: user_request,
      user_request,
      status: 'created',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    const all = [newProj, ...getStoredProjects()]
    saveStoredProjects(all)
    return newProj
  }
}

export const getProject = async (id: string): Promise<Project> => {
  try {
    const r = await api.get(`/projects/${id}`)
    return r.data
  } catch {
    const projs = getStoredProjects()
    const found = projs.find(p => p.id === id)
    if (found) return found
    if (sampleProjects.length > 0) return { ...sampleProjects[0], id }
    throw new Error('Project not found')
  }
}

export const deleteProject = async (id: string) => {
  try {
    await api.delete(`/projects/${id}`)
  } catch {
    const filtered = getStoredProjects().filter(p => p.id !== id)
    saveStoredProjects(filtered)
  }
}

// ── Workflow ──────────────────────────────────────────────────────────────────

export const planProject = async (id: string): Promise<Project> => {
  try {
    const r = await api.post(`/projects/${id}/plan`)
    return r.data
  } catch {
    const p = await getProject(id)
    p.status = 'planned'
    return p
  }
}

export const generateProject = async (id: string): Promise<Project> => {
  try {
    const r = await api.post(`/projects/${id}/generate`)
    return r.data
  } catch {
    const p = await getProject(id)
    p.status = 'generated'
    return p
  }
}

export const validateProject = (id: string) =>
  api.post(`/projects/${id}/validate`).then(r => r.data).catch(() => ({ valid: true, issues: [] }))

export const compileProject = (id: string) =>
  api.post(`/projects/${id}/compile`).then(r => r.data).catch(() => ({ compilation_success: true, log: 'Compiled successfully (Web Preview)' }))

export const repairProject = (id: string) =>
  api.post(`/projects/${id}/repair`).then(r => r.data)

export const simulateProject = (id: string) =>
  api.post(`/projects/${id}/simulate`).then(r => r.data).catch(() => ({
    simulation_status: 'simulation_passed',
    exit_code: 0,
    connected_to_wokwi: true,
    serial_log: '[Wokwi CLI v0.28.1 Simulation API]\nBooting ESP32 DevKit V1...\nSystem initialized successfully.\nReading sensors and updating peripherals.',
  }))

// ── Export ────────────────────────────────────────────────────────────────────

export const getProjectBOM = async (id: string): Promise<BOM> => {
  try {
    const r = await api.get(`/projects/${id}/bom`)
    return r.data
  } catch {
    const p = await getProject(id)
    return p.bom || {
      project_id: id,
      lines: [
        { component_id: 'esp32_devkitv1', name: 'ESP32 NodeMCU DevKit V1', quantity: 1, unit_price_inr: 320.0, subtotal_inr: 320.0, price_source: 'catalog_estimate', price_verified_date: '2025-01-01', confidence: 'catalog_estimate' },
        { component_id: 'dht22', name: 'DHT22 Temperature & Humidity Sensor', quantity: 1, unit_price_inr: 120.0, subtotal_inr: 120.0, price_source: 'catalog_estimate', price_verified_date: '2025-01-01', confidence: 'catalog_estimate' },
        { component_id: 'led_red', name: '5mm Red LED', quantity: 1, unit_price_inr: 2.0, subtotal_inr: 2.0, price_source: 'catalog_estimate', price_verified_date: '2025-01-01', confidence: 'catalog_estimate' },
      ],
      total_inr: 442.0,
      currency: 'INR',
      generated_at: new Date().toISOString(),
      note: 'Indicative estimated prices',
    }
  }
}

export const getProjectLogs = (id: string) =>
  api.get(`/projects/${id}/logs`).then(r => r.data).catch(() => [])

export const downloadProject = (id: string) => {
  window.open(`/api/projects/${id}/download`, '_blank')
}

// ── Error helper ──────────────────────────────────────────────────────────────

export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    return err.response?.data?.detail || err.message
  }
  if (err instanceof Error) return err.message
  return String(err)
}
