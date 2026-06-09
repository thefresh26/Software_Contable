import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

export default function TablaDepreciacion() {
  const { id } = useParams()
  const [tabla, setTabla] = useState(null)
  const [aplicadas, setAplicadas] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.get(`/activos/${id}/tabla-depreciacion/`),
      api.get(`/activos/${id}/depreciaciones/`),
    ]).then(([t, d]) => { setTabla(t.data); setAplicadas(d.data) })
      .finally(() => setLoading(false))
  }, [id])

  const exportarPDF = () => window.print()

  if (loading || !tabla) return <div className="flex justify-center pt-20"><div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" /></div>

  const periodosAplicados = new Set(aplicadas.map(d => d.periodo.slice(0, 7)))

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-start print:hidden">
        <div>
          <Link to={`/activos/${id}`} className="text-xs text-blue-600 hover:underline">← Volver al activo</Link>
          <h1 className="text-2xl font-bold text-slate-800 mt-1">Tabla de Depreciación</h1>
          <p className="text-sm text-gray-500">{tabla.activo}</p>
        </div>
        <button onClick={exportarPDF} className="btn-secondary">Exportar a PDF</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card"><p className="text-xs text-gray-500">Valor de compra</p><p className="text-lg font-bold text-slate-800">{fmt(tabla.valor_compra)}</p></div>
        <div className="card"><p className="text-xs text-gray-500">Valor residual</p><p className="text-lg font-bold text-slate-800">{fmt(tabla.valor_residual)}</p></div>
        <div className="card"><p className="text-xs text-gray-500">Vida útil</p><p className="text-lg font-bold text-slate-800">{tabla.vida_util_meses} meses</p></div>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="th">Mes</th>
              <th className="th">Período</th>
              <th className="th text-right">Dep. del mes</th>
              <th className="th text-right">Dep. acumulada</th>
              <th className="th text-right">Valor en libros</th>
              <th className="th">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {tabla.tabla.map(fila => {
              const aplicada = periodosAplicados.has(fila.periodo)
              return (
                <tr key={fila.mes} className={aplicada ? 'bg-green-50/40' : ''}>
                  <td className="td">{fila.mes}</td>
                  <td className="td">{fila.periodo}</td>
                  <td className="td text-right">{fmt(fila.valor_depreciacion)}</td>
                  <td className="td text-right">{fmt(fila.depreciacion_acumulada)}</td>
                  <td className="td text-right font-medium">{fmt(fila.valor_en_libros)}</td>
                  <td className="td">
                    {aplicada ? <span className="badge-green">Aplicada</span> : <span className="badge-gray">Proyectada</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
