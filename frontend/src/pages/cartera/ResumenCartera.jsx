import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

export default function ResumenCartera() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/cartera/resumen/').then(({ data: d }) => setData(d)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center pt-20"><div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" /></div>
  if (!data) return null

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Resumen de Cartera</h1>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card"><p className="text-sm text-gray-500">Por Cobrar</p><p className="text-2xl font-bold text-blue-700">{fmt(data.total_por_cobrar)}</p></div>
        <div className="card"><p className="text-sm text-gray-500">Por Pagar</p><p className="text-2xl font-bold text-red-600">{fmt(data.total_por_pagar)}</p></div>
        <div className="card"><p className="text-sm text-gray-500">Vencido por Cobrar</p><p className="text-2xl font-bold text-red-600">{fmt(data.vencido_por_cobrar)}</p></div>
        <div className="card"><p className="text-sm text-gray-500">Vencido por Pagar</p><p className="text-2xl font-bold text-red-600">{fmt(data.vencido_por_pagar)}</p></div>
      </div>

      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="font-semibold text-gray-700">Próximos vencimientos por cobrar (30 días)</h2>
          <Link to="/cartera/por-cobrar" className="text-blue-600 text-sm hover:underline">Ver todos →</Link>
        </div>
        {data.proximos_vencimientos_cobrar?.length === 0 ? (
          <p className="text-sm text-gray-400">Sin vencimientos próximos</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b"><tr><th className="th">Factura</th><th className="th">Cliente</th><th className="th">Vencimiento</th><th className="th text-right">Pendiente</th><th className="th">Estado</th></tr></thead>
            <tbody className="divide-y">
              {(data.proximos_vencimientos_cobrar || []).map((r, i) => (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="td font-mono text-xs">{r.factura__numero}</td>
                  <td className="td">{r.tercero__nombre}</td>
                  <td className="td">{r.fecha_vencimiento}</td>
                  <td className="td text-right font-medium">{fmt(r.valor_pendiente)}</td>
                  <td className="td"><span className={r.estado === 'vencida' ? 'badge-red' : 'badge-yellow'}>{r.estado}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
