import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'

const PRIORIDAD_DOT = {
  critica: 'bg-red-500',
  alta: 'bg-yellow-500',
  media: 'bg-blue-500',
  baja: 'bg-gray-400',
}

const fmtFecha = (iso) => {
  const d = new Date(iso)
  return d.toLocaleString('es-CO', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export default function NotificationBell() {
  const [count, setCount] = useState(0)
  const [items, setItems] = useState([])
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  const cargarCount = () => {
    api.get('/notificaciones/no-leidas-count/').then((res) => setCount(res.data.count)).catch(() => {})
  }

  const cargarUltimas = () => {
    api.get('/notificaciones/?ordering=-created_at').then((res) => {
      const data = res.data.results || res.data
      setItems(data.slice(0, 10))
    }).catch(() => {})
  }

  useEffect(() => {
    cargarCount()
    const interval = setInterval(cargarCount, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const onClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const toggle = () => {
    const next = !open
    setOpen(next)
    if (next) cargarUltimas()
  }

  const marcarLeida = async (id) => {
    await api.post(`/notificaciones/${id}/marcar-leida/`)
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, leida: true } : n)))
    cargarCount()
  }

  const marcarTodas = async () => {
    await api.post('/notificaciones/marcar-todas-leidas/')
    setItems((prev) => prev.map((n) => ({ ...n, leida: true })))
    setCount(0)
  }

  return (
    <div className="relative" ref={ref}>
      <button onClick={toggle} className="relative p-2 rounded-full hover:bg-slate-100 text-xl leading-none" aria-label="Notificaciones">
        🔔
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-red-600 text-white text-[10px] font-bold">
            {count > 99 ? '99+' : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b bg-gray-50">
            <p className="font-semibold text-sm text-gray-700">Notificaciones</p>
            <button onClick={marcarTodas} className="text-xs text-blue-600 hover:underline">Marcar todas como leídas</button>
          </div>
          <div className="max-h-96 overflow-y-auto divide-y">
            {items.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">No tienes notificaciones</p>
            ) : (
              items.map((n) => (
                <div
                  key={n.id}
                  className={`px-4 py-3 flex gap-2 cursor-pointer hover:bg-gray-50 ${n.leida ? '' : 'bg-blue-50/40'}`}
                  onClick={() => !n.leida && marcarLeida(n.id)}
                >
                  <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${PRIORIDAD_DOT[n.prioridad] || 'bg-gray-400'}`} />
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm ${n.leida ? 'text-gray-600' : 'text-gray-900 font-medium'}`}>{n.titulo}</p>
                    <p className="text-xs text-gray-500 truncate">{n.mensaje}</p>
                    <p className="text-[11px] text-gray-400 mt-0.5">{fmtFecha(n.created_at)}</p>
                  </div>
                </div>
              ))
            )}
          </div>
          <Link to="/notificaciones" onClick={() => setOpen(false)} className="block text-center text-sm text-blue-600 hover:underline py-2.5 border-t bg-gray-50">
            Ver todas
          </Link>
        </div>
      )}
    </div>
  )
}
