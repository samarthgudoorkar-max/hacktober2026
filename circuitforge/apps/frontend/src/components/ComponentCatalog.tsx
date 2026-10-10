import { useState, useEffect, useMemo } from 'react'
import {
  Layers, Search, Plus, Check, Tag, Cpu, Radio,
  Tv, Activity, Sparkles, Filter
} from 'lucide-react'
import { getCatalog } from '../utils/api'
import type { CatalogComponent } from '../types'

interface ComponentCatalogProps {
  onSelectComponent: (componentName: string) => void
}

const CATEGORY_MAP: Record<string, { label: string; icon: React.ElementType; color: string }> = {
  all: { label: 'All Components', icon: Layers, color: 'text-cyan-400' },
  sensor: { label: 'Sensors', icon: Activity, color: 'text-amber-400' },
  display: { label: 'Displays', icon: Tv, color: 'text-purple-400' },
  actuator: { label: 'Actuators', icon: Radio, color: 'text-emerald-400' },
  input: { label: 'Inputs & Controls', icon: Filter, color: 'text-blue-400' },
  passive: { label: 'LEDs & Passives', icon: Sparkles, color: 'text-rose-400' },
  microcontroller: { label: 'Controllers', icon: Cpu, color: 'text-cyan-400' },
}

export function ComponentCatalog({ onSelectComponent }: ComponentCatalogProps) {
  const [components, setComponents] = useState<CatalogComponent[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [addedIds, setAddedIds] = useState<Record<string, boolean>>({})

  useEffect(() => {
    getCatalog()
      .then(setComponents)
      .catch((err) => console.error('Failed to load components', err))
      .finally(() => setLoading(false))
  }, [])

  const handleAdd = (comp: CatalogComponent) => {
    onSelectComponent(comp.name)
    setAddedIds((prev) => ({ ...prev, [comp.id]: true }))
    setTimeout(() => {
      setAddedIds((prev) => ({ ...prev, [comp.id]: false }))
    }, 1500)
  }

  const filtered = useMemo(() => {
    return components.filter((c) => {
      const matchCat =
        selectedCategory === 'all' ||
        (selectedCategory === 'passive'
          ? ['passive', 'output'].includes(c.category)
          : c.category === selectedCategory)
      const q = search.trim().toLowerCase()
      const matchSearch =
        !q ||
        c.name.toLowerCase().includes(q) ||
        c.wokwi_id.toLowerCase().includes(q) ||
        c.description.toLowerCase().includes(q)
      return matchCat && matchSearch
    })
  }, [components, selectedCategory, search])

  const counts = useMemo(() => {
    const res: Record<string, number> = { all: components.length }
    for (const c of components) {
      const cat = ['passive', 'output'].includes(c.category) ? 'passive' : c.category
      res[cat] = (res[cat] || 0) + 1
    }
    return res
  }, [components])

  return (
    <div className="w-full mt-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold text-white tracking-wide">
              Available Wokwi Components
            </h2>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-900/60 border border-cyan-700 text-cyan-300">
              {components.length} Ready
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Browse supported components. Click any card or "+ Add" to include it in your project description.
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            className="forge-input pl-9 py-1.5 text-xs w-full"
            placeholder="Search parts, sensors, displays..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 mb-4 scrollbar-none">
        {Object.entries(CATEGORY_MAP).map(([catKey, meta]) => {
          const count = counts[catKey] ?? 0
          if (catKey !== 'all' && count === 0) return null
          const Icon = meta.icon
          const isActive = selectedCategory === catKey
          return (
            <button
              key={catKey}
              onClick={() => setSelectedCategory(catKey)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-cyan-600/20 text-cyan-300 border border-cyan-600/50 shadow-sm'
                  : 'bg-gray-900/60 text-gray-400 border border-gray-800 hover:text-gray-200 hover:border-gray-700'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${meta.color}`} />
              <span>{meta.label}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${isActive ? 'bg-cyan-900/80 text-cyan-200' : 'bg-gray-800 text-gray-500'}`}>
                {count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Grid of components */}
      {loading ? (
        <div className="text-center py-12 text-sm text-gray-500">
          Loading hardware catalog...
        </div>
      ) : filtered.length === 0 ? (
        <div className="forge-card p-8 text-center text-gray-500 text-xs">
          No components match "{search}". Try searching for sensors, buttons, or displays.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map((comp) => {
            const isAdded = !!addedIds[comp.id]
            return (
              <div
                key={comp.id}
                onClick={() => handleAdd(comp)}
                className="forge-card p-3.5 text-left hover:border-cyan-700/60 transition-all group cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <h3 className="text-sm font-semibold text-gray-200 group-hover:text-cyan-300 transition-colors line-clamp-1">
                      {comp.name}
                    </h3>
                    <span className="text-[11px] font-mono font-medium text-emerald-400 shrink-0 bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-900/40">
                      ₹{comp.unit_price_inr}
                    </span>
                  </div>

                  <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed mb-3">
                    {comp.description}
                  </p>
                </div>

                <div className="flex items-center justify-between gap-2 pt-2 border-t border-gray-800/60 mt-auto">
                  <div className="flex items-center gap-1.5 overflow-hidden">
                    <Tag className="w-3 h-3 text-gray-600 shrink-0" />
                    <span className="text-[10px] font-mono text-gray-400 truncate">
                      {comp.wokwi_id}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleAdd(comp)
                    }}
                    className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-1 rounded transition-colors ${
                      isAdded
                        ? 'bg-emerald-600/20 text-emerald-300 border border-emerald-700/60'
                        : 'bg-gray-800 text-gray-300 hover:bg-cyan-600 hover:text-white'
                    }`}
                  >
                    {isAdded ? (
                      <>
                        <Check className="w-3 h-3" /> Added
                      </>
                    ) : (
                      <>
                        <Plus className="w-3 h-3" /> Add
                      </>
                    )}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
