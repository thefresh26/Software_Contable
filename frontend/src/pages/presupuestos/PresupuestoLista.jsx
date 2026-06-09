import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

export default function PresupuestoLista() {
  const navigate = useNavigate()
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)
  const [ejecucion, setEjecucion] = useState({})

  useEffect(() => {
    api.get('/presupuestos/presupuestos/?page_size=50').then(({ data: d }) => setData(d.results || [])).finally(() => setLoading(false))
  }, [])

  const cargarEjecucion = async (id) => {
    if (ejecucion[id]) { setExpanded(expanded === id ? null : id); return }
    const { data: d } = await api.get(`/presupuestos/presupuestos/${id}/ejecucion/`)
    setEjecucion(e => ({ ...e, [id]: d }))
    setExpanded(id)
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Presupuestos</h1>
        <Link to="/presupuestos/nuevo" className="btn-primary">+ Nuevo Presupuesto</Link>
      </div>

      <div className="space-y-3">
        {loading ? <div className="card text-center text-gray-400 py-8">Cargando…</div>
        : data.length === 0 ? <div className="card text-center text-gray-400 py-8">Sin presupuestos</div>
        : data.map(p => (
          <div key={p.id} className="card p-0 overflow-hidden">
            <button type="button" className="w-full flex justify-between items-center px-5 py-4 hover:bg-gray-50 text-left" onClick={() => cargarEjecucion(p.id)}>
              <div>
                <p className="font-semibold text-gray-800">{p.nombre}</p>
                <p className="text-xs text-gray-500">{p.periodo_inicio} — {p.periodo_fin}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className={p.estado === 'activo' ? 'badge-green' : 'badge-gray'}>{p.estado}</span>
                <span className="text-xs text-gray-400">{expanded === p.id ? '▲' : '▼'}</span>
              </div>
            </button>

            {expanded === p.id && ejecucion[p.id] && (
              <div className="border-t">
                <div className="px-5 py-3 bg-blue-50 flex justify-between text-sm font-medium">
                  <span>Presupuestado: {fmt(ejecucion[p.id].total_presupuestado)}</span>
                  <span>Ejecutado: {fmt(ejecucion[p.id].total_ejecutado)}</span>
                </div>
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b"><tr><th className="th">Cuenta</th><th className="th">Descripción</th><th className="th text-right">Presupuestado</th><th className="th text-right">Ejecutado</th><th className="th text-right">Diferencia</th><th className="th text-right">% Ejec.</th></tr></thead>
                  <tbody className="divide-y">
                    {ejecucion[p.id].items.map((item, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="td font-mono text-xs">{item.cuenta_codigo}</td>
                        <td className="td">{item.descripcion}</td>
                        <td className="td text-right">{fmt(item.presupuestado)}</td>
                        <td className="td text-right">{fmt(item.ejecutado)}</td>
                        <td className={`td text-right ${Number(item.diferencia) < 0 ? 'text-red-600' : 'text-green-600'}`}>{fmt(item.diferencia)}</td>
                        <td className="td text-right">
                          <div className="flex items-center justify-end gap-2">
                            <div className="w-16 bg-gray-200 rounded-full h-1.5"><div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${Math.min(item.porcentaje_ejecucion, 100)}%` }} /></div>
                            <span>{item.porcentaje_ejecucion}%</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
