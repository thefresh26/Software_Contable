import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../api/client'
import { descargarExcel } from '../../utils/excel'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

function Card({ label, value, color = 'blue' }) {
  const colors = { blue: 'text-blue-700', green: 'text-green-700', yellow: 'text-yellow-700', slate: 'text-slate-700' }
  return (
    <div className="card">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold ${colors[color]}`}>{value}</p>
    </div>
  )
}

export default function ActivoReportes() {
  const [resumen, setResumen] = useState(null)
  const [porCategoria, setPorCategoria] = useState([])
  const [proximos, setProximos] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/activos/reportes/resumen/'),
      api.get('/activos/reportes/por-categoria/'),
      api.get('/activos/reportes/proximos-depreciar/'),
    ]).then(([r, c, p]) => {
      setResumen(r.data)
      setPorCategoria(c.data)
      setProximos(p.data)
    }).finally(() => setLoading(false))
  }, [])

  if (loading || !resumen) return <div className="flex justify-center pt-20"><div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" /></div>

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-2">
        <h1 className="text-2xl font-bold text-slate-800">Reportes de Activos Fijos</h1>
        <button className="btn-excel" onClick={() => descargarExcel('/activos/exportar/', 'activos_fijos.xlsx').catch(() => alert('Error al exportar'))}>⬇ Excel</button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card label="Total activos activos" value={resumen.activos_activos} color="blue" />
        <Card label="Valor bruto total" value={fmt(resumen.valor_bruto)} color="slate" />
        <Card label="Depreciación acumulada total" value={fmt(resumen.depreciacion_acumulada)} color="yellow" />
        <Card label="Valor en libros total" value={fmt(resumen.valor_en_libros)} color="green" />
      </div>

      <div className="card p-0 overflow-x-auto">
        <div className="px-5 py-3 bg-gray-50 border-b">
          <h2 className="font-semibold text-sm text-gray-700">Activos por categoría</h2>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="th">Categoría</th>
              <th className="th text-right">Total Activos</th>
              <th className="th text-right">Valor Bruto</th>
              <th className="th text-right">Dep. Acumulada</th>
              <th className="th text-right">Valor en Libros</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {porCategoria.map(c => (
              <tr key={c.categoria} className="hover:bg-gray-50">
                <td className="td font-medium text-gray-800">{c.categoria}</td>
                <td className="td text-right">{c.total_activos}</td>
                <td className="td text-right">{fmt(c.valor_bruto)}</td>
                <td className="td text-right">{fmt(c.depreciacion_acumulada)}</td>
                <td className="td text-right font-medium">{fmt(c.valor_en_libros)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card p-0 overflow-x-auto">
        <div className="px-5 py-3 bg-gray-50 border-b">
          <h2 className="font-semibold text-sm text-gray-700">Próximos a depreciarse completamente (12 meses)</h2>
        </div>
        {proximos.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">No hay activos próximos a depreciarse completamente</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="th">Código</th>
                <th className="th">Nombre</th>
                <th className="th">Categoría</th>
                <th className="th text-right">Valor en Libros Actual</th>
                <th className="th">Fin Depreciación</th>
                <th className="th" />
              </tr>
            </thead>
            <tbody className="divide-y">
              {proximos.map(a => (
                <tr key={a.codigo} className="hover:bg-gray-50">
                  <td className="td font-mono text-xs">{a.codigo}</td>
                  <td className="td font-medium text-gray-800">{a.nombre}</td>
                  <td className="td">{a.categoria}</td>
                  <td className="td text-right">{fmt(a.valor_en_libros_actual)}</td>
                  <td className="td"><span className="badge-yellow">{a.periodo_fin_depreciacion}</span></td>
                  <td className="td"><Link to={`/activos`} className="text-blue-600 hover:underline text-xs">Ver activo</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
