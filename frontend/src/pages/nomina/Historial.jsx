import { useEffect, useState } from 'react'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

export default function Historial() {
  const [data, setData] = useState([])
  const [empleados, setEmpleados] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ empleado: '', mes: '', año: '' })
  const [resumen, setResumen] = useState(null)

  const load = () => {
    setLoading(true)
    const p = new URLSearchParams({ page_size: 200 })
    if (filters.empleado) p.set('empleado', filters.empleado)
    if (filters.mes) p.set('mes', filters.mes)
    if (filters.año) p.set('año', filters.año)
    api.get(`/nomina/liquidaciones/?${p}`).then(({ data: d }) => setData(d.results || [])).finally(() => setLoading(false))
  }

  const cargarResumen = () => {
    if (!filters.mes || !filters.año) return
    api.get(`/nomina/liquidaciones/resumen-mes/?mes=${filters.mes}&año=${filters.año}`).then(({ data }) => setResumen(data))
  }

  useEffect(() => { api.get('/nomina/empleados/?page_size=200').then(({ data }) => setEmpleados(data.results || [])) }, [])
  useEffect(() => { load() }, [filters])
  useEffect(() => { cargarResumen() }, [filters.mes, filters.año])

  const setF = (k, v) => setFilters((f) => ({ ...f, [k]: v }))
  const meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
  const años = [2024, 2025, 2026]

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-slate-800">Historial de Nómina</h1>

      <div className="flex flex-wrap gap-3">
        <select className="input w-52" value={filters.empleado} onChange={(e) => setF('empleado', e.target.value)}>
          <option value="">Todos los empleados</option>
          {empleados.map((e) => <option key={e.id} value={e.id}>{e.nombre}</option>)}
        </select>
        <select className="input w-36" value={filters.mes} onChange={(e) => setF('mes', e.target.value)}>
          <option value="">Mes</option>
          {meses.map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
        </select>
        <select className="input w-28" value={filters.año} onChange={(e) => setF('año', e.target.value)}>
          <option value="">Año</option>
          {años.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
        <button className="btn-secondary" onClick={() => setFilters({ empleado: '', mes: '', año: '' })}>Limpiar</button>
      </div>

      {resumen && (
        <div className="card grid grid-cols-2 md:grid-cols-4 gap-4">
          <div><p className="text-xs text-gray-500">Liquidaciones</p><p className="text-2xl font-bold text-gray-800">{resumen.cantidad_liquidaciones}</p></div>
          <div><p className="text-xs text-gray-500">Total devengado</p><p className="text-lg font-bold text-gray-800">{fmt(resumen.total_devengado)}</p></div>
          <div><p className="text-xs text-gray-500">Total deducido</p><p className="text-lg font-bold text-red-600">{fmt(resumen.total_deducido)}</p></div>
          <div><p className="text-xs text-gray-500">Neto a pagar</p><p className="text-lg font-bold text-blue-700">{fmt(resumen.neto_pagar)}</p></div>
        </div>
      )}

      <div className="card p-0 overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="th">Empleado</th><th className="th">Período</th>
              <th className="th text-right">Devengado</th><th className="th text-right">Deducido</th>
              <th className="th text-right">Neto</th><th className="th">Estado</th><th className="th" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={7} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={7} className="td text-center py-8 text-gray-400">Sin liquidaciones</td></tr>
            ) : data.map((l) => (
              <tr key={l.id} className="hover:bg-gray-50">
                <td className="td font-medium">{l.empleado_nombre}</td>
                <td className="td text-xs text-gray-500">{l.periodo_inicio} — {l.periodo_fin}</td>
                <td className="td text-right">{fmt(l.total_devengado)}</td>
                <td className="td text-right text-red-600">{fmt(l.total_deducido)}</td>
                <td className="td text-right font-semibold text-blue-700">{fmt(l.neto_pagar)}</td>
                <td className="td"><span className={l.estado === 'pagada' ? 'badge-green' : 'badge-yellow'}>{l.estado}</span></td>
                <td className="td">
                  <a href={`/api/nomina/liquidaciones/${l.id}/colilla/`} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline text-xs">PDF</a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
