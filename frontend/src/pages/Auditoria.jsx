import { useEffect, useState } from 'react'
import api from '../api/client'

const ACCIONES = ['', 'crear', 'editar', 'eliminar', 'emitir', 'anular']
const MODELOS = ['', 'Factura', 'Tercero', 'Producto', 'Empleado', 'AsientoContable']
const accionBadge = { crear: 'badge-green', editar: 'badge-blue', eliminar: 'badge-red', emitir: 'badge-yellow', anular: 'badge-gray' }

export default function Auditoria() {
  const [historial, setHistorial] = useState([])
  const [loading, setLoading] = useState(true)
  const [filtro, setFiltro] = useState({ modelo: '', accion: '', desde: '', hasta: '' })
  const [detalle, setDetalle] = useState(null)

  const setF = (k, v) => setFiltro(f => ({ ...f, [k]: v }))

  const load = () => {
    setLoading(true)
    const p = new URLSearchParams({ page_size: 200 })
    if (filtro.modelo) p.set('modelo', filtro.modelo)
    if (filtro.accion) p.set('accion', filtro.accion)
    if (filtro.desde) p.set('desde', filtro.desde)
    if (filtro.hasta) p.set('hasta', filtro.hasta)
    api.get(`/auth/historial/?${p}`).then(({ data }) => setHistorial(data || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filtro])

  return (
    <div className="space-y-4">
      {detalle && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
            <div className="flex justify-between items-center px-6 py-4 border-b">
              <h2 className="font-semibold">Detalle del cambio</h2>
              <button onClick={() => setDetalle(null)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>
            <div className="px-6 py-4 space-y-2 text-sm">
              <p><strong>Modelo:</strong> {detalle.modelo}</p>
              <p><strong>Objeto:</strong> {detalle.objeto_repr}</p>
              <p><strong>Acción:</strong> {detalle.accion_display}</p>
              <p><strong>Usuario:</strong> {detalle.usuario_nombre}</p>
              <p><strong>Fecha:</strong> {detalle.created_at}</p>
              {detalle.ip_address && <p><strong>IP:</strong> {detalle.ip_address}</p>}
              {Object.keys(detalle.cambios || {}).length > 0 && (
                <div>
                  <p className="font-medium mt-2">Cambios:</p>
                  <pre className="bg-gray-50 p-2 rounded text-xs overflow-auto">{JSON.stringify(detalle.cambios, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <h1 className="text-2xl font-bold text-slate-800">Historial de Cambios (Auditoría)</h1>

      <div className="flex flex-wrap gap-3">
        <select className="input w-40" value={filtro.modelo} onChange={e => setF('modelo', e.target.value)}>
          {MODELOS.map(m => <option key={m} value={m}>{m || 'Todos los modelos'}</option>)}
        </select>
        <select className="input w-36" value={filtro.accion} onChange={e => setF('accion', e.target.value)}>
          {ACCIONES.map(a => <option key={a} value={a}>{a || 'Todas las acciones'}</option>)}
        </select>
        <input type="date" className="input w-40" value={filtro.desde} onChange={e => setF('desde', e.target.value)} />
        <input type="date" className="input w-40" value={filtro.hasta} onChange={e => setF('hasta', e.target.value)} />
        <button className="btn-secondary" onClick={() => setFiltro({ modelo: '', accion: '', desde: '', hasta: '' })}>Limpiar</button>
      </div>

      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="th">Fecha</th>
              <th className="th">Acción</th>
              <th className="th">Modelo</th>
              <th className="th">Objeto</th>
              <th className="th">Usuario</th>
              <th className="th" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? <tr><td colSpan={6} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            : historial.length === 0 ? <tr><td colSpan={6} className="td text-center py-8 text-gray-400">Sin registros</td></tr>
            : historial.map(h => (
              <tr key={h.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setDetalle(h)}>
                <td className="td text-xs text-gray-500">{new Date(h.created_at).toLocaleString('es-CO')}</td>
                <td className="td"><span className={accionBadge[h.accion] || 'badge-gray'}>{h.accion_display}</span></td>
                <td className="td font-medium">{h.modelo}</td>
                <td className="td text-xs">{h.objeto_repr}</td>
                <td className="td">{h.usuario_nombre}</td>
                <td className="td text-blue-600 text-xs">Ver →</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
