import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

const estadoBadge = { borrador: 'badge-gray', emitida: 'badge-green', anulada: 'badge-red' }
const tipoLabel = { FV: 'Fact. Venta', FC: 'Fact. Compra', NC: 'Nota Crédito', ND: 'Nota Débito' }

export default function FacturaLista() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ tipo: '', estado: '', fecha_desde: '', fecha_hasta: '' })
  const [accion, setAccion] = useState(null)

  const load = () => {
    setLoading(true)
    const p = new URLSearchParams({ page_size: 200 })
    Object.entries(filters).forEach(([k, v]) => { if (v) p.set(k, v) })
    api.get(`/facturacion/facturas/?${p}`).then(({ data: d }) => setData(d.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filters])

  const emitir = async (id) => {
    if (!confirm('¿Emitir esta factura?')) return
    setAccion(id)
    try { await api.post(`/facturacion/facturas/${id}/emitir/`); load() }
    catch (e) { alert(e.response?.data?.error || 'Error al emitir') }
    finally { setAccion(null) }
  }

  const anular = async (id) => {
    if (!confirm('¿Anular esta factura? Esta acción revertirá el stock.')) return
    setAccion(id)
    try { await api.post(`/facturacion/facturas/${id}/anular/`); load() }
    catch (e) { alert(e.response?.data?.error || 'Error al anular') }
    finally { setAccion(null) }
  }

  const setF = (k, v) => setFilters((f) => ({ ...f, [k]: v }))

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Facturas</h1>
        <Link to="/facturacion/nueva" className="btn-primary">+ Nueva Factura</Link>
      </div>

      <div className="flex flex-wrap gap-3">
        <select className="input w-40" value={filters.tipo} onChange={(e) => setF('tipo', e.target.value)}>
          <option value="">Todos los tipos</option>
          <option value="FV">Fact. Venta</option>
          <option value="FC">Fact. Compra</option>
          <option value="NC">Nota Crédito</option>
          <option value="ND">Nota Débito</option>
        </select>
        <select className="input w-36" value={filters.estado} onChange={(e) => setF('estado', e.target.value)}>
          <option value="">Todos los estados</option>
          <option value="borrador">Borrador</option>
          <option value="emitida">Emitida</option>
          <option value="anulada">Anulada</option>
        </select>
        <input type="date" className="input w-40" value={filters.fecha_desde} onChange={(e) => setF('fecha_desde', e.target.value)} />
        <input type="date" className="input w-40" value={filters.fecha_hasta} onChange={(e) => setF('fecha_hasta', e.target.value)} />
        <button className="btn-secondary" onClick={() => setFilters({ tipo: '', estado: '', fecha_desde: '', fecha_hasta: '' })}>Limpiar</button>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="th">Número</th><th className="th">Tipo</th><th className="th">Tercero</th>
              <th className="th">Fecha</th><th className="th">Total</th><th className="th">Estado</th><th className="th" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={7} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={7} className="td text-center py-8 text-gray-400">Sin facturas</td></tr>
            ) : data.map((f) => (
              <tr key={f.id} className="hover:bg-gray-50">
                <td className="td font-mono text-xs font-semibold">{f.numero}</td>
                <td className="td"><span className="badge-gray">{tipoLabel[f.tipo]}</span></td>
                <td className="td">{f.tercero_nombre}</td>
                <td className="td">{f.fecha}</td>
                <td className="td font-medium">{fmt(f.total)}</td>
                <td className="td"><span className={estadoBadge[f.estado]}>{f.estado}</span></td>
                <td className="td">
                  <div className="flex gap-2 items-center">
                    {f.estado === 'borrador' && (
                      <button className="btn-success text-xs px-2 py-1" disabled={accion === f.id} onClick={() => emitir(f.id)}>
                        Emitir
                      </button>
                    )}
                    {f.estado === 'emitida' && (
                      <>
                        <a href={`/api/facturacion/facturas/${f.id}/pdf/`} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline text-xs">PDF</a>
                        <button className="text-red-500 hover:underline text-xs" disabled={accion === f.id} onClick={() => anular(f.id)}>Anular</button>
                      </>
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
