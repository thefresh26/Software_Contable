import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import api from '../api/client'

function KpiCard({ label, value, sub, color = 'blue' }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    red: 'bg-red-50 text-red-700',
    yellow: 'bg-yellow-50 text-yellow-700',
  }
  return (
    <div className="card flex flex-col gap-1">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold ${colors[color].split(' ')[1]}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400">{sub}</p>}
    </div>
  )
}

const fmt = (n) =>
  Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

export default function Dashboard() {
  const [kpis, setKpis] = useState({ ventas: 0, compras: 0, utilidad: 0, stockBajo: 0 })
  const [grafica, setGrafica] = useState([])
  const [alertas, setAlertas] = useState([])
  const [periodosAbiertos, setPeriodosAbiertos] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const hoy = new Date()
    const año = hoy.getFullYear()
    const mes = String(hoy.getMonth() + 1).padStart(2, '0')
    const inicio = `${año}-${mes}-01`
    const fin = `${año}-${mes}-${new Date(año, hoy.getMonth() + 1, 0).getDate()}`

    Promise.all([
      api.get(`/facturacion/facturas/?tipo=FV&estado=emitida&fecha_desde=${inicio}&fecha_hasta=${fin}&page_size=1000`),
      api.get(`/facturacion/facturas/?tipo=FC&estado=emitida&fecha_desde=${inicio}&fecha_hasta=${fin}&page_size=1000`),
      api.get('/inventario/productos/?stock_bajo=true&page_size=100'),
      api.get('/contabilidad/cierres/?estado=abierto&page_size=50'),
    ]).then(([fv, fc, stock, cierres]) => {
      const ventas = (fv.data.results || []).reduce((a, f) => a + Number(f.total), 0)
      const compras = (fc.data.results || []).reduce((a, f) => a + Number(f.total), 0)
      setKpis({ ventas, compras, utilidad: ventas - compras, stockBajo: stock.data.count || 0 })
      setAlertas((stock.data.results || []).slice(0, 5))
      const hace60 = new Date(); hace60.setDate(hace60.getDate() - 60)
      const viejos = (cierres.data.results || []).filter(c => new Date(c.periodo) < hace60)
      setPeriodosAbiertos(viejos)
    }).catch(() => {}).finally(() => setLoading(false))

    // Gráfica últimos 6 meses
    const meses = []
    for (let i = 5; i >= 0; i--) {
      const d = new Date(hoy.getFullYear(), hoy.getMonth() - i, 1)
      meses.push({
        label: d.toLocaleString('es-CO', { month: 'short' }),
        año: d.getFullYear(),
        mes: d.getMonth() + 1,
      })
    }

    Promise.all(
      meses.map(({ año: a, mes: m }) => {
        const ini = `${a}-${String(m).padStart(2, '0')}-01`
        const fin2 = `${a}-${String(m).padStart(2, '0')}-${new Date(a, m, 0).getDate()}`
        return api.get(`/facturacion/facturas/?tipo=FV&estado=emitida&fecha_desde=${ini}&fecha_hasta=${fin2}&page_size=1000`)
      })
    ).then((results) => {
      setGrafica(
        meses.map(({ label }, i) => ({
          mes: label,
          ventas: (results[i].data.results || []).reduce((a, f) => a + Number(f.total), 0),
        }))
      )
    }).catch(() => {})
  }, [])

  if (loading) return <div className="flex justify-center pt-20"><div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" /></div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>

      {periodosAbiertos.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-yellow-600 text-lg">⚠️</span>
            <p className="text-sm text-yellow-800 font-medium">
              {periodosAbiertos.length} período{periodosAbiertos.length > 1 ? 's' : ''} contable{periodosAbiertos.length > 1 ? 's' : ''} sin cerrar con más de 60 días de antigüedad.
            </p>
          </div>
          <Link to="/contabilidad/cierres" className="text-xs text-yellow-700 hover:underline font-medium shrink-0">
            Ver cierres →
          </Link>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Ventas del mes" value={fmt(kpis.ventas)} color="blue" />
        <KpiCard label="Compras del mes" value={fmt(kpis.compras)} color="yellow" />
        <KpiCard label="Utilidad bruta" value={fmt(kpis.utilidad)} color={kpis.utilidad >= 0 ? 'green' : 'red'} />
        <KpiCard label="Productos bajo stock" value={kpis.stockBajo} sub="productos bajo mínimo" color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2">
          <h2 className="text-base font-semibold text-gray-700 mb-4">Ventas últimos 6 meses</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={grafica} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v / 1e6).toFixed(1)}M`} />
              <Tooltip formatter={(v) => fmt(v)} />
              <Bar dataKey="ventas" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="text-base font-semibold text-gray-700 mb-3">Alertas de Stock</h2>
          {alertas.length === 0 ? (
            <p className="text-sm text-gray-400">Sin alertas pendientes</p>
          ) : (
            <ul className="space-y-2">
              {alertas.map((p) => (
                <li key={p.id} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 truncate">{p.nombre}</span>
                  <span className="badge-red ml-2">{p.stock_actual} {p.unidad_medida}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
