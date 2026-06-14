import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

const BADGE_COLORS = {
  Tercero: 'badge-blue',
  Factura: 'badge-green',
  Producto: 'badge-yellow',
  Empleado: 'badge-purple',
}

export default function BusquedaGlobal() {
  const [query, setQuery] = useState('')
  const [resultados, setResultados] = useState([])
  const [abierto, setAbierto] = useState(false)
  const [loading, setLoading] = useState(false)
  const [indice, setIndice] = useState(0)
  const inputRef = useRef(null)
  const navigate = useNavigate()

  // Ctrl+K shortcut
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
        setAbierto(true)
      }
      if (e.key === 'Escape') {
        setAbierto(false)
        setQuery('')
        inputRef.current?.blur()
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])

  // Debounce search 300ms
  useEffect(() => {
    if (query.length < 2) { setResultados([]); return }
    setLoading(true)
    const timer = setTimeout(async () => {
      try {
        const { data } = await api.get(`/buscar/?q=${encodeURIComponent(query)}`)
        setResultados(data.resultados || [])
        setIndice(0)
      } catch { setResultados([]) }
      finally { setLoading(false) }
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  const irA = useCallback((url) => {
    navigate(url)
    setAbierto(false)
    setQuery('')
    inputRef.current?.blur()
  }, [navigate])

  const handleKeyDown = (e) => {
    if (!abierto || !resultados.length) return
    if (e.key === 'ArrowDown') { e.preventDefault(); setIndice(i => Math.min(i + 1, resultados.length - 1)) }
    if (e.key === 'ArrowUp') { e.preventDefault(); setIndice(i => Math.max(i - 1, 0)) }
    if (e.key === 'Enter') { e.preventDefault(); irA(resultados[indice].url) }
  }

  return (
    <div className="relative flex-1 max-w-xs mx-4 hidden sm:block">
      <div className="relative">
        <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-sm pointer-events-none">🔍</span>
        <input
          ref={inputRef}
          type="text"
          placeholder="Buscar... (Ctrl+K)"
          value={query}
          onChange={e => { setQuery(e.target.value); setAbierto(true) }}
          onFocus={() => setAbierto(true)}
          onBlur={() => setTimeout(() => setAbierto(false), 150)}
          onKeyDown={handleKeyDown}
          className="w-full pl-8 pr-3 py-1.5 text-sm rounded-md border border-gray-300 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          style={{ minHeight: 'unset' }}
        />
        {loading && <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-400">...</span>}
      </div>

      {abierto && resultados.length > 0 && (
        <div className="absolute top-full mt-1 left-0 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 overflow-hidden">
          {resultados.map((r, i) => (
            <button
              key={`${r.tipo}-${r.id}`}
              className={`w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-gray-50 ${i === indice ? 'bg-blue-50' : ''}`}
              onMouseDown={() => irA(r.url)}
              onMouseEnter={() => setIndice(i)}
            >
              <span className={`${BADGE_COLORS[r.tipo] || 'badge-gray'} shrink-0`}>{r.tipo}</span>
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{r.titulo}</p>
                <p className="text-xs text-gray-500 truncate">{r.subtitulo}</p>
              </div>
            </button>
          ))}
        </div>
      )}

      {abierto && query.length >= 2 && !loading && resultados.length === 0 && (
        <div className="absolute top-full mt-1 left-0 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 px-4 py-3">
          <p className="text-sm text-gray-500">Sin resultados para "{query}"</p>
        </div>
      )}
    </div>
  )
}
