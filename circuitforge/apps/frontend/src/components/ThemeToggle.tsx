import { useState, useEffect } from 'react'
import { Sun, Moon } from 'lucide-react'

export function ThemeToggle() {
  const [isLight, setIsLight] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('circuitforge_theme')
      if (saved) return saved === 'light'
      return window.matchMedia('(prefers-color-scheme: light)').matches
    }
    return false
  })

  useEffect(() => {
    if (isLight) {
      document.documentElement.classList.add('light')
      document.documentElement.classList.remove('dark')
      localStorage.setItem('circuitforge_theme', 'light')
    } else {
      document.documentElement.classList.remove('light')
      document.documentElement.classList.add('dark')
      localStorage.setItem('circuitforge_theme', 'dark')
    }
  }, [isLight])

  const toggleTheme = () => setIsLight((prev) => !prev)

  return (
    <button
      onClick={toggleTheme}
      type="button"
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-700 bg-gray-800/80 hover:bg-gray-700 text-gray-200 hover:text-cyan-400 transition-all text-xs font-medium shadow-sm hover:border-cyan-500/50"
      title={isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode (Light Button)'}
      aria-label="Toggle Light and Dark Theme"
    >
      {isLight ? (
        <>
          <Moon className="w-3.5 h-3.5 text-blue-500" />
          <span>Dark Mode</span>
        </>
      ) : (
        <>
          <Sun className="w-3.5 h-3.5 text-amber-400 animate-spin-slow" />
          <span>Light Mode</span>
        </>
      )}
    </button>
  )
}
