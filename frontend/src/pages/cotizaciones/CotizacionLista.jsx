import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../api/client'
import { useToast } from '../../context/ToastContext'
import { useConfirm } from '../../components/ui/ConfirmDialog'
import { parseApiError } from '../../utils/errorMessages'
import EmptyState from '../../components/ui/EmptyState'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
const estadoBadge = { borrador: 'badge-gray', enviada: 'badge-yellow', aprobada: 'badge-green', rechazada: 'badge-red', vencida: 'badge-red' }

export default function CotizacionLista() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ estado: '', fecha_desde: '', fecha_hasta: '' })
  const [accion, setAccion] = useState(null)
  const toast = useToast()
  const confirm = useConfirm()

  const load = () => {
    setLoading(true)
    const p = new URLSearchParams({ page_size: 200 })
    Object.entries(filters).forEach(([k, v]) => { if (v) p.set(k, v) })
    api.get(`/presupuestos/cotizaciones/?${p}`).then(({ data: d }) => setData(d.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filters])

  const setF = (k, v) => setFilters(f => ({ ...f, [k]: v }))

  const aprobar = async (c) => {
    const ok = await confirm({
      title: 'Aprobar cotización',
      message: `¿Aprobar la cotización ${c.numero}? Quedará lista para convertir en factura.`,
      confirmLabel: 'Aprobar',
    })
    if (!ok) return
    setAccion(c.id)
    try {
      await api.post(`/presupuestos/cotizaciones/${c.id}/aprobar/`)
      toast.success(`Cotización ${c.numero} aprobada correctamente.`)
      load()
    } catch (e) {
      toast.error(parseApiError(e) || 'Error al aprobar la cotización.')
    } finally { setAccion(null) }
  }

  const convertir = async (c) => {
    const ok = await confirm({
      title: 'Convertir a Factura',
      message: `¿Convertir la cotización ${c.numero} en una Factura de Venta? La cotización quedará cerrada.`,
      confirmLabel: 'Convertir en Factura',
    })
    if (!ok) return
    setAccion(c.id)
    try {
      await api.post(`/presupuestos/cotizaciones/${c.id}/convertir-factura/`)
      toast.success(`Cotización ${c.numero} convertida a factura. Revise en el módulo de Facturación.`)
      load()
    } catch (e) {
      toast.error(parseApiError(e) || 'Error al convertir la cotización.')
    } finally { setAccion(null) }
  }

  const hayFiltros = Object.values(filters).some(Boolean)

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Cotizaciones</h1>
        <Link to="/cotizaciones/nueva" className="btn-primary">+ Nueva Cotización</Link>
      </div>
      <div className="flex flex-wrap gap-3">
        <select className="input w-40" value={filters.estado} onChange={e => setF('estado', e.target.value)}>
          <option value="">Todos los estados</option>
          {['borrador','enviada','aprobada','rechazada','vencida'].map(e => <option key={e} value={e}>{e.charAt(0).toUpperCase() + e.slice(1)}</option>)}
        </select>
        <input type="date" className="input w-40" value={filters.fecha_desde} onChange={e => setF('fecha_desde', e.target.value)} />
        <input type="date" className="input w-40" value={filters.fecha_hasta} onChange={e => setF('fecha_hasta', e.target.value)} />
        {hayFiltros && <button className="btn-secondary" onClick={() => setFilters({ estado: '', fecha_desde: '', fecha_hasta: '' })}>Limpiar</button>}
      </div>
      <div className="card p-0 overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr><th className="th">Número</th><th className="th">Cliente</th><th className="th">Fecha</th><th className="th">Vence</th><th className="th">Total</th><th className="th">Estado</th><th className="th" /></tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={7} className="td text-center py-12">
                <div className="flex items-center justify-center gap-2 text-gray-400">
                  <div className="animate-spin h-4 w-4 border-b-2 border-blue-600 rounded-full" />Cargando…
                </div>
              </td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={7}>
                <EmptyState
                  icon="📋"
                  title={hayFiltros ? 'Sin cotizaciones para los filtros aplicados' : 'Aún no tiene cotizaciones'}
                  description="Las cotizaciones le permiten proponerle precios a sus clientes antes de emitir la factura."
                  action={!hayFiltros ? undefined : undefined}
                />
              </td></tr>
            ) : data.map(c => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="td font-mono text-xs font-semibold">{c.numero}</td>
                <td className="td">{c.tercero_nombre}</td>
                <td className="td">{c.fecha}</td>
                <td className="td">{c.fecha_vencimiento}</td>
                <td className="td font-medium">{fmt(c.total)}</td>
                <td className="td"><span className={estadoBadge[c.estado]}>{c.estado}</span></td>
                <td className="td">
                  <div className="flex gap-2">
                    <a href={`/api/presupuestos/cotizaciones/${c.id}/pdf/`} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline text-xs">PDF</a>
                    {(c.estado === 'borrador' || c.estado === 'enviada') && (
                      <button className="text-green-600 hover:underline text-xs" disabled={accion === c.id} onClick={() => aprobar(c)}>Aprobar</button>
                    )}
                    {c.estado === 'aprobada' && (
                      <button className="text-blue-700 hover:underline text-xs" disabled={accion === c.id} onClick={() => convertir(c)}>→ Factura</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
