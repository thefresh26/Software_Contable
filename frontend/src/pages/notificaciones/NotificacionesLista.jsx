import { useEffect, useState } from 'react'
import api from '../../api/client'

const TIPOS = [
  { value: '', label: 'Todos los tipos' },
  { value: 'factura_vencer', label: 'Factura por Vencer' },
  { value: 'factura_vencida', label: 'Factura Vencida' },
  { value: 'stock_bajo', label: 'Stock Bajo' },
  { value: 'pago_recibido', label: 'Pago Recibido' },
  { value: 'pago_realizado', label: 'Pago Realizado' },
  { value: 'nomina_pendiente', label: 'Nómina Pendiente' },
  { value: 'activo_depreciado', label: 'Activo Totalmente Depreciado' },
  { value: 'cotizacion_vencer', label: 'Cotización por Vencer' },
  { value: 'sistema', label: 'Notificación del Sistema' },
]

const PRIORIDAD_BADGE = {
  critica: 'bg-red-100 text-red-800',
  alta: 'bg-yellow-100 text-yellow-800',
  media: 'bg-blue-100 text-blue-800',
  baja: 'bg-gray-100 text-gray-700',
}

const fmtFecha = (iso) => new Date(iso).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })

export default function NotificacionesLista() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [tipo, setTipo] = useState('')
  const [prioridad, setPrioridad] = useState('')
  const [leida, setLeida] = useState('')

  const cargar = () => {
    setLoading(true)
    const params = {}
    if (tipo) params.tipo = tipo
    if (prioridad) params.prioridad = prioridad
    if (leida !== '') params.leida = leida
    api.get('/notificaciones/', { params }).then((res) => {
      setItems(res.data.results || res.data)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { cargar() }, [tipo, prioridad, leida])

  const eliminar = async (id) => {
    if (!confirm('¿Eliminar esta notificación?')) return
    await api.delete(`/notificaciones/${id}/`)
    setItems((prev) => prev.filter((n) => n.id !== id))
  }

  const limpiarLeidas = async () => {
    const leidas = items.filter((n) => n.leida)
    if (leidas.length === 0) return
    if (!confirm(`¿Eliminar ${leidas.length} notificaciones leídas?`)) return
    await Promise.all(leidas.map((n) => api.delete(`/notificaciones/${n.id}/`)))
    setItems((prev) => prev.filter((n) => !n.leida))
  }

  const marcarLeida = async (id) => {
    await api.post(`/notificaciones/${id}/marcar-leida/`)
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, leida: true } : n)))
  }

  const marcarTodas = async () => {
    await api.post('/notificaciones/marcar-todas-leidas/')
    setItems((prev) => prev.map((n) => ({ ...n, leida: true })))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Notificaciones</h1>
        <div className="flex gap-2">
          <button onClick={marcarTodas} className="btn-secondary">Marcar todas como leídas</button>
          <button onClick={limpiarLeidas} className="btn-danger">Limpiar leídas</button>
        </div>
      </div>

      <div className="card flex flex-wrap gap-3 items-end">
        <div>
          <label className="label">Tipo</label>
          <select className="input" value={tipo} onChange={(e) => setTipo(e.target.value)}>
            {TIPOS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Prioridad</label>
          <select className="input" value={prioridad} onChange={(e) => setPrioridad(e.target.value)}>
            <option value="">Todas las prioridades</option>
            <option value="critica">Crítica</option>
            <option value="alta">Alta</option>
            <option value="media">Media</option>
            <option value="baja">Baja</option>
          </select>
        </div>
        <div>
          <label className="label">Estado</label>
          <select className="input" value={leida} onChange={(e) => setLeida(e.target.value)}>
            <option value="">Todas</option>
            <option value="false">No leídas</option>
            <option value="true">Leídas</option>
          </select>
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12"><div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" /></div>
        ) : items.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-12">No hay notificaciones</p>
        ) : (
          <div className="divide-y">
            {items.map((n) => (
              <div key={n.id} className={`px-5 py-4 flex items-start justify-between gap-4 ${n.leida ? '' : 'bg-blue-50/40'}`}>
                <div className="flex gap-3 min-w-0">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium shrink-0 ${PRIORIDAD_BADGE[n.prioridad] || 'bg-gray-100 text-gray-700'}`}>
                    {n.prioridad_display}
                  </span>
                  <div className="min-w-0">
                    <p className={`text-sm ${n.leida ? 'text-gray-600' : 'text-gray-900 font-semibold'}`}>{n.titulo}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{n.mensaje}</p>
                    <p className="text-[11px] text-gray-400 mt-1">{n.tipo_display} · {fmtFecha(n.created_at)}</p>
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  {!n.leida && (
                    <button onClick={() => marcarLeida(n.id)} className="text-xs text-blue-600 hover:underline">Marcar leída</button>
                  )}
                  <button onClick={() => eliminar(n.id)} className="text-xs text-red-600 hover:underline">Eliminar</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
