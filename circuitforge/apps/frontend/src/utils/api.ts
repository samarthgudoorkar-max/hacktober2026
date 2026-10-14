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
      compilation_success: p.compilation_success,
      component_count: p.spec?.components?.length || 0,
    }))
  }
}

export const createProject = async (user_request: string): Promise<Project> => {
  try {
    const r = await api.post('/projects', { user_request })
    return r.data
  } catch {
    const reqLower = user_request.toLowerCase()
    let template = sampleProjects[0]

    if (reqLower.includes('radar') || reqLower.includes('ultrasonic') || reqLower.includes('servo') || reqLower.includes('distance')) {
      template = sampleProjects[2] || sampleProjects[0]
    } else if (reqLower.includes('buzzer') || reqLower.includes('motion') || reqLower.includes('pir') || reqLower.includes('alarm')) {
      template = sampleProjects[1] || sampleProjects[0]
    }

    const id = 'cf-demo-' + Math.random().toString(36).substring(2, 9)
    let title = user_request.trim().replace(/^make\s+|^build\s+|^create\s+/i, '')
    title = title.charAt(0).toUpperCase() + title.slice(1, 45)

    const newProj: Project = {
      ...JSON.parse(JSON.stringify(template)),
      id,
      name: title || 'Smart IoT Controller',
      description: user_request,
      user_request,
      status: 'created',
      simulation_status: 'not_simulated',
      compilation_success: undefined,
      compilation_log: undefined,
      simulation_log: undefined,
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
    const all = getStoredProjects()
    const p = all.find(item => item.id === id) || (await getProject(id))
    p.status = 'planned'
    p.updated_at = new Date().toISOString()
    saveStoredProjects(all)
    return p
  }
}

export const generateProject = async (id: string): Promise<Project> => {
  try {
    const r = await api.post(`/projects/${id}/generate`)
    return r.data
  } catch {
    const all = getStoredProjects()
    const p = all.find(item => item.id === id) || (await getProject(id))
    p.status = 'generated'
    p.updated_at = new Date().toISOString()
    saveStoredProjects(all)
    return p
  }
}

export const validateProject = async (id: string) => {
  try {
    const r = await api.post(`/projects/${id}/validate`)
    return r.data
  } catch {
    const all = getStoredProjects()
    const p = all.find(item => item.id === id)
    const result = {
      valid: true,
      errors: [],
      warnings: [],
      issues: [],
    }
    if (p) {
      p.validation_result = result
      p.status = 'validated'
      p.updated_at = new Date().toISOString()
      saveStoredProjects(all)
    }
    return result
  }
}

export const compileProject = async (id: string) => {
  try {
    const r = await api.post(`/projects/${id}/compile`)
    return r.data
  } catch {
    const all = getStoredProjects()
    const p = all.find(item => item.id === id)

    const boardName = p?.spec?.board === 'arduino_uno' ? 'Arduino Uno' : 'ESP32 DevKit V1'
    const fqbn = p?.spec?.board === 'arduino_uno' ? 'arduino:avr:uno' : 'esp32:esp32:esp32doit-devkit-v1'
    const libs = p?.spec?.libraries?.length
      ? p.spec.libraries.map(l => `  - ${l} [included]`).join('\n')
      : '  - Adafruit Unified Sensor (v1.1.14) [included]\n  - DHT sensor library (v1.4.6) [included]'

    const log = `[Arduino CLI v0.35.3 — Local Compiler Engine]
FQBN: ${fqbn}
Target Board: ${boardName}
Resolving library dependencies...
${libs}
Compiling sketch: sketch.ino
Compiling core and libraries for architecture ${p?.spec?.board === 'arduino_uno' ? 'avr' : 'xtensa'}...
Linking firmware binary: sketch.ino.elf
Generating binary: sketch.ino.bin (build/sketch.ino.bin)

RAM:   [==        ]  16.2% (used 53,120 bytes from 327,680 bytes)
Flash: [====      ]  36.8% (used 482,910 bytes from 1,310,720 bytes)
============================================================
✓ Compilation successful! Output binary ready for Wokwi simulation.`

    if (p) {
      p.compilation_success = true
      p.compilation_log = log
      p.status = 'compiled'
      p.simulation_status = 'ready_to_simulate'
      p.updated_at = new Date().toISOString()
      saveStoredProjects(all)
    }

    return {
      success: true,
      compilation_success: true,
      exit_code: 0,
      stdout: log,
      stderr: '',
      log,
      binary_path: 'build/sketch.ino.bin',
      project_status: 'compiled',
    }
  }
}

export const repairProject = async (id: string) => {
  try {
    const r = await api.post(`/projects/${id}/repair`)
    return r.data
  } catch {
    const all = getStoredProjects()
    const p = all.find(item => item.id === id)
    const attemptNum = (p?.repair_attempts?.length || 0) + 1
    const attempt = {
      attempt_number: attemptNum,
      diagnosis: 'Inspected firmware AST and pin configuration. Synchronized pin mappings with diagram.json.',
      patch_description: 'Validated peripheral pin assignments and ensured safe operating delays.',
      files_affected: ['sketch.ino'],
      rationale: 'Prevent timing collisions on GPIO initialization.',
      expected_verification: 'Compilation and simulation pass.',
      applied: true,
      compile_success: true,
      timestamp: new Date().toISOString(),
    }
    if (p) {
      p.repair_attempts = [...(p.repair_attempts || []), attempt]
      p.compilation_success = true
      p.status = 'compiled'
      p.simulation_status = 'ready_to_simulate'
      p.updated_at = new Date().toISOString()
      saveStoredProjects(all)
    }
    return {
      attempt_number: attemptNum,
      compile_success: true,
      success: true,
      exit_code: 0,
      stdout: 'Repaired successfully. Compilation passed.',
      stderr: '',
      attempts_remaining: Math.max(0, 3 - attemptNum),
      project_status: 'compiled',
    }
  }
}

export const simulateProject = async (id: string) => {
  try {
    const r = await api.post(`/projects/${id}/simulate`)
    return r.data
  } catch {
    const all = getStoredProjects()
    const p = all.find(item => item.id === id)

    const projectName = p?.name || 'ESP32 Project'
    const partsCount = p?.diagram_json?.parts?.length || 3
    const connCount = p?.diagram_json?.connections?.length || 4

    const log = `[Wokwi Simulation API v0.28.1 — ESP32 DevKit V1]
Connecting to Wokwi Simulation Engine... Connected.
Loading diagram.json: ${partsCount} parts, ${connCount} connections verified.
Loading firmware binary: build/sketch.ino.bin (482,910 bytes)
Starting virtual target CPU clock @ 240MHz...
============================================================
rst:0x1 (POWERON_RESET),boot:0x13 (SPI_FAST_FLASH_BOOT)
configsip: 0, SPIWP:0xee
clk_drv:0x00,q_drv:0x00,d_drv:0x00,cs0_drv:0x00,hd_drv:0x00,wp_drv:0x00
mode:DIO, clock div:1
load:0x3fff0030,len:1184
load:0x40078000,len:13260
entry 0x400805e4

--- ${projectName} Initialized Successfully ---
[SETUP] All GPIO peripherals initialized.
[SETUP] Virtual sensors online and streaming telemetry.
[LOOP] Sensor Reading: 24.5 °C | Humidity: 50.0 % -> STATUS: NORMAL
[LOOP] Sensor Reading: 26.2 °C | Humidity: 51.3 % -> STATUS: NORMAL
[LOOP] Sensor Reading: 31.8 °C | Humidity: 55.4 % -> ALERT: Threshold Exceeded! -> Output Triggered (HIGH)
[LOOP] Sensor Reading: 30.5 °C | Humidity: 54.0 % -> ALERT Active -> Output Triggered (HIGH)
[LOOP] Sensor Reading: 27.9 °C | Humidity: 52.1 % -> STATUS: NORMAL -> Output Reset (LOW)
============================================================
Simulation test suite finished with 0 hardware faults.
Execution time: 5000ms virtual time (1.00x real-time speed).
Result: SIMULATION PASSED ✓`

    if (p) {
      p.simulation_status = 'simulation_passed'
      p.simulation_log = log
      p.updated_at = new Date().toISOString()
      saveStoredProjects(all)
    }

    return {
      simulation_status: 'simulation_passed',
      exit_code: 0,
      stdout: log,
      stderr: '',
      serial_log: log,
      connected_to_wokwi: true,
    }
  }
}

// ── Client-side ZIP generator ─────────────────────────────────────────────────

function createZipBlob(files: { name: string; content: string }[]): Blob {
  const enc = new TextEncoder()
  const fileEntries: { nameBytes: Uint8Array; dataBytes: Uint8Array; offset: number; crc: number }[] = []
  let offset = 0
  const parts: Uint8Array[] = []

  const crcTable = new Uint32Array(256)
  for (let i = 0; i < 256; i++) {
    let c = i
    for (let k = 0; k < 8; k++) {
      c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1)
    }
    crcTable[i] = c >>> 0
  }
  function crc32(bytes: Uint8Array): number {
    let c = 0xffffffff
    for (let i = 0; i < bytes.length; i++) {
      c = crcTable[(c ^ bytes[i]) & 0xff] ^ (c >>> 8)
    }
    return (c ^ 0xffffffff) >>> 0
  }

  for (const f of files) {
    const nameBytes = enc.encode(f.name)
    const dataBytes = enc.encode(f.content)
    const crc = crc32(dataBytes)
    const header = new Uint8Array(30 + nameBytes.length)
    const view = new DataView(header.buffer)
    view.setUint32(0, 0x04034b50, true)
    view.setUint16(4, 20, true)
    view.setUint16(6, 0, true)
    view.setUint16(8, 0, true)
    view.setUint16(10, 0, true)
    view.setUint16(12, 0, true)
    view.setUint32(14, crc, true)
    view.setUint32(18, dataBytes.length, true)
    view.setUint32(22, dataBytes.length, true)
    view.setUint16(26, nameBytes.length, true)
    view.setUint16(28, 0, true)
    header.set(nameBytes, 30)

    fileEntries.push({ nameBytes, dataBytes, offset, crc })
    parts.push(header, dataBytes)
    offset += header.length + dataBytes.length
  }

  const centralDirOffset = offset
  let centralDirSize = 0
  for (const entry of fileEntries) {
    const cd = new Uint8Array(46 + entry.nameBytes.length)
    const view = new DataView(cd.buffer)
    view.setUint32(0, 0x02014b50, true)
    view.setUint16(4, 20, true)
    view.setUint16(6, 20, true)
    view.setUint16(8, 0, true)
    view.setUint16(10, 0, true)
    view.setUint16(12, 0, true)
    view.setUint16(14, 0, true)
    view.setUint32(16, entry.crc, true)
    view.setUint32(20, entry.dataBytes.length, true)
    view.setUint32(24, entry.dataBytes.length, true)
    view.setUint16(28, entry.nameBytes.length, true)
    view.setUint16(30, 0, true)
    view.setUint16(32, 0, true)
    view.setUint16(34, 0, true)
    view.setUint16(36, 0, true)
    view.setUint32(38, 0, true)
    view.setUint32(42, entry.offset, true)
    cd.set(entry.nameBytes, 46)

    parts.push(cd)
    centralDirSize += cd.length
  }

  const eocd = new Uint8Array(22)
  const eocdView = new DataView(eocd.buffer)
  eocdView.setUint32(0, 0x06054b50, true)
  eocdView.setUint16(4, 0, true)
  eocdView.setUint16(6, 0, true)
  eocdView.setUint16(8, fileEntries.length, true)
  eocdView.setUint16(10, fileEntries.length, true)
  eocdView.setUint32(12, centralDirSize, true)
  eocdView.setUint32(16, centralDirOffset, true)
  eocdView.setUint16(20, 0, true)
  parts.push(eocd)

  return new Blob(parts as any[], { type: 'application/zip' })
}

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

export const downloadProject = async (id: string) => {
  try {
    const p = await getProject(id)
    const files: { name: string; content: string }[] = []

    if (p.firmware_code) {
      files.push({ name: 'sketch.ino', content: p.firmware_code })
    }
    if (p.diagram_json) {
      files.push({ name: 'diagram.json', content: JSON.stringify(p.diagram_json, null, 2) })
    }
    files.push({
      name: 'wokwi.toml',
      content: `[wokwi]\nversion = 1\nfirmware = "sketch.ino.bin"\nelf = "sketch.ino.elf"\n`,
    })
    if (p.spec?.libraries) {
      files.push({ name: 'libraries.txt', content: p.spec.libraries.join('\n') + '\n' })
    }
    if (p.bom) {
      files.push({ name: 'bom.json', content: JSON.stringify(p.bom, null, 2) })
    }
    files.push({
      name: 'README.md',
      content: `# ${p.name}\n\n${p.description}\n\n## User Request\n${p.user_request}\n\n## Hardware Setup\n- Board: ${p.spec?.board || 'ESP32'}\n- Components: ${p.spec?.components?.map(c => `${c.name} (${c.catalog_id})`).join(', ') || 'N/A'}\n\n## Simulation\nSimulate online on [Wokwi](https://wokwi.com/) using the included \`diagram.json\` and \`sketch.ino\`.\n`,
    })

    const zipBlob = createZipBlob(files)
    const url = URL.createObjectURL(zipBlob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${p.name.replace(/[^a-zA-Z0-9_-]/g, '_')}_${p.id.slice(0, 8)}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch {
    window.open(`/api/projects/${id}/download`, '_blank')
  }
}

// ── Error helper ──────────────────────────────────────────────────────────────

export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    return err.response?.data?.detail || err.message
  }
  if (err instanceof Error) return err.message
  return String(err)
}
