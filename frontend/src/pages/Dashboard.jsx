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

function PasoOnboarding({ numero, titulo, descripcion, to, accion, hecho }) {
  return (
    <div className={`flex items-start gap-4 p-4 rounded-lg border ${hecho ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${hecho ? 'bg-green-500 text-white' : 'bg-blue-100 text-blue-700'}`}>
        {hecho ? '✓' : numero}
      </div>
      <div className="flex-1 min-w-0">
        <p className={`font-medium text-sm ${hecho ? 'text-green-700 line-through' : 'text-gray-800'}`}>{titulo}</p>
        <p className="text-xs text-gray-500 mt-0.5">{descripcion}</p>
      </div>
      {!hecho && to && (
        <Link to={to} className="btn-primary text-xs px-3 py-1 shrink-0">{accion || 'Ir →'}</Link>
      )}
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
  const [onboarding, setOnboarding] = useState({
    empresa: false, tercero: false, producto: false, factura: false,
  })
  const [esNuevo, setEsNuevo] = useState(false)

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
      api.get('/empresas/?page_size=1'),
      api.get('/terceros/?page_size=1'),
      api.get('/inventario/productos/?page_size=1'),
      api.get('/facturacion/facturas/?page_size=1'),
    ]).then(([fv, fc, stock, cierres, emp, terc, prod, fact]) => {
      const ventas = (fv.data.results || []).reduce((a, f) => a + Number(f.total), 0)
      const compras = (fc.data.results || []).reduce((a, f) => a + Number(f.total), 0)
      setKpis({ ventas, compras, utilidad: ventas - compras, stockBajo: stock.data.count || 0 })
      setAlertas((stock.data.results || []).slice(0, 5))
      const hace60 = new Date(); hace60.setDate(hace60.getDate() - 60)
      const viejos = (cierres.data.results || []).filter(c => new Date(c.periodo) < hace60)
      setPeriodosAbiertos(viejos)

      const tieneEmpresa = (emp.data.count || emp.data.results?.length || 0) > 0
      const tieneTercero = (terc.data.count || terc.data.results?.length || 0) > 0
      const tieneProducto = (prod.data.count || prod.data.results?.length || 0) > 0
      const tieneFactura = (fact.data.count || fact.data.results?.length || 0) > 0
      setOnboarding({ empresa: tieneEmpresa, tercero: tieneTercero, producto: tieneProducto, factura: tieneFactura })
      setEsNuevo(!tieneFactura && !tieneProducto)
    }).catch(() => {}).finally(() => setLoading(false))

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

  if (loading) return (
    <div className="flex flex-col items-center justify-center pt-20 gap-3">
      <div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" />
      <p className="text-sm text-gray-400">Cargando dashboard…</p>
    </div>
  )

  const todosLosPasos = onboarding.empresa && onboarding.tercero && onboarding.producto && onboarding.factura

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
        <p className="text-xs text-gray-400">
          {new Date().toLocaleDateString('es-CO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>

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

      {esNuevo && !todosLosPasos && (
        <div className="card bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200">
          <div className="flex items-start gap-3 mb-4">
            <span className="text-2xl">👋</span>
            <div>
              <h2 className="font-bold text-gray-800">¡Bienvenido a ContaApp!</h2>
              <p className="text-sm text-gray-500">Complete estos pasos para empezar a usar el sistema.</p>
            </div>
          </div>
          <div className="space-y-2">
            <PasoOnboarding numero={1} titulo="Configure su empresa" descripcion="Ingrese el nombre, NIT y datos de su empresa." to="/empresas/nueva" accion="Configurar" hecho={onboarding.empresa} />
            <PasoOnboarding numero={2} titulo="Cree su primer tercero" descripcion="Registre clientes y proveedores con su NIT." to="/terceros" accion="Ir a Terceros" hecho={onboarding.tercero} />
            <PasoOnboarding numero={3} titulo="Agregue productos o servicios" descripcion="Defina los productos que vende o compra." to="/inventario" accion="Ir a Inventario" hecho={onboarding.producto} />
            <PasoOnboarding numero={4} titulo="Emita su primera factura" descripcion="Cree y emita una factura de venta." to="/facturacion/nueva" accion="Nueva Factura" hecho={onboarding.factura} />
          </div>
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
          {grafica.every(g => g.ventas === 0) ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <span className="text-4xl mb-3">📉</span>
              <p className="text-sm text-gray-400">Sin ventas registradas aún.</p>
              <Link to="/facturacion/nueva" className="btn-primary text-sm mt-3">Crear primera factura</Link>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={grafica} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v / 1e6).toFixed(1)}M`} />
                <Tooltip formatter={(v) => fmt(v)} />
                <Bar dataKey="ventas" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card">
          <h2 className="text-base font-semibold text-gray-700 mb-3">Alertas de Stock</h2>
          {alertas.length === 0 ? (
            <div className="flex flex-col items-center py-6 text-center gap-2">
              <span className="text-3xl">✅</span>
              <p className="text-sm text-gray-400">Todo el inventario está sobre el mínimo.</p>
            </div>
          ) : (
            <ul className="space-y-2">
              {alertas.map((p) => (
                <li key={p.id} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 truncate">{p.nombre}</span>
                  <span className="badge-red ml-2 shrink-0">{p.stock_actual} {p.unidad_medida}</span>
                </li>
              ))}
              <li className="pt-2 border-t">
                <Link to="/inventario" className="text-xs text-blue-600 hover:underline">Ver inventario completo →</Link>
              </li>
            </ul>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Nueva Factura', to: '/facturacion/nueva', icon: '🧾' },
          { label: 'Nuevo Tercero', to: '/terceros', icon: '👤' },
          { label: 'Registrar Pago', to: '/cartera/por-cobrar', icon: '💳' },
          { label: 'Ver Reportes', to: '/contabilidad/reportes', icon: '📊' },
        ].map(acc => (
          <Link key={acc.to} to={acc.to} className="card flex flex-col items-center gap-2 py-4 hover:bg-blue-50 hover:border-blue-200 border border-transparent transition-colors text-center cursor-pointer">
            <span className="text-2xl">{acc.icon}</span>
            <span className="text-xs font-medium text-gray-700">{acc.label}</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
