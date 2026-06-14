import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import api from '../../api/client'
import { descargarExcel } from '../../utils/excel'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

function ModalNuevo({ cuentas, onClose, onSaved }) {
  const [form, setForm] = useState({
    fecha: new Date().toISOString().slice(0, 10),
    tipo: 'ingreso', concepto: '', valor: '', cuenta_bancaria: '', es_proyectado: true,
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      await api.post('/contabilidad/flujo-caja/', form)
      onSaved()
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="font-semibold">Nuevo Movimiento Proyectado</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Fecha *</label><input className="input" type="date" value={form.fecha} onChange={e => set('fecha', e.target.value)} required /></div>
            <div><label className="label">Tipo *</label>
              <select className="input" value={form.tipo} onChange={e => set('tipo', e.target.value)}>
                <option value="ingreso">Ingreso</option>
                <option value="egreso">Egreso</option>
              </select>
            </div>
          </div>
          <div><label className="label">Concepto *</label><input className="input" value={form.concepto} onChange={e => set('concepto', e.target.value)} required /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Valor *</label><input className="input" type="number" min="0.01" step="0.01" value={form.valor} onChange={e => set('valor', e.target.value)} required /></div>
            <div><label className="label">Cuenta Bancaria</label>
              <select className="input" value={form.cuenta_bancaria} onChange={e => set('cuenta_bancaria', e.target.value)}>
                <option value="">Sin cuenta</option>
                {cuentas.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function FlujoCaja() {
  const [movimientos, setMovimientos] = useState([])
  const [resumen, setResumen] = useState(null)
  const [proyeccion, setProyeccion] = useState([])
  const [cuentas, setCuentas] = useState([])
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [modal, setModal] = useState(false)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    const p = new URLSearchParams({ page_size: 500 })
    if (desde) p.set('desde', desde)
    if (hasta) p.set('hasta', hasta)
    Promise.all([
      api.get(`/contabilidad/flujo-caja/?${p}`),
      api.get('/contabilidad/flujo-caja/resumen/'),
      api.get('/contabilidad/flujo-caja/proyeccion/?meses=3'),
    ]).then(([m, r, pr]) => {
      setMovimientos(m.data.results || [])
      setResumen(r.data)
      setProyeccion(pr.data)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { api.get('/bancos/cuentas/?page_size=50').then(({ data }) => setCuentas(data.results || [])) }, [])
  useEffect(() => { load() }, [desde, hasta])

  // Calcular saldo acumulado para gráfica
  const chartData = movimientos.reduce((acc, m) => {
    const prev = acc.length ? acc[acc.length - 1].saldo : 0
    const delta = m.tipo === 'ingreso' ? Number(m.valor) : -Number(m.valor)
    return [...acc, { fecha: m.fecha, saldo: prev + delta, concepto: m.concepto }]
  }, [])

  return (
    <div className="space-y-4">
      {modal && <ModalNuevo cuentas={cuentas} onClose={() => setModal(false)} onSaved={() => { setModal(false); load() }} />}

      <div className="flex flex-wrap justify-between items-center gap-2">
        <h1 className="text-2xl font-bold text-slate-800">Flujo de Caja</h1>
        <div className="flex gap-2">
          <button className="btn-excel" onClick={() => descargarExcel('/contabilidad/flujo-caja/exportar/', 'flujo_caja.xlsx').catch(() => alert('Error'))}>⬇ Excel</button>
          <button className="btn-primary" onClick={() => setModal(true)}>+ Movimiento</button>
        </div>
      </div>

      {resumen && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card text-center">
            <p className="text-xs text-gray-500 mb-1">Total Ingresos</p>
            <p className="text-xl font-bold text-green-600">{fmt(resumen.total_ingresos)}</p>
          </div>
          <div className="card text-center">
            <p className="text-xs text-gray-500 mb-1">Total Egresos</p>
            <p className="text-xl font-bold text-red-600">{fmt(resumen.total_egresos)}</p>
          </div>
          <div className="card text-center">
            <p className="text-xs text-gray-500 mb-1">Saldo Actual</p>
            <p className={`text-xl font-bold ${Number(resumen.saldo) >= 0 ? 'text-blue-700' : 'text-red-600'}`}>{fmt(resumen.saldo)}</p>
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <input type="date" className="input w-40" value={desde} onChange={e => setDesde(e.target.value)} placeholder="Desde" />
        <input type="date" className="input w-40" value={hasta} onChange={e => setHasta(e.target.value)} placeholder="Hasta" />
        <button className="btn-secondary" onClick={() => { setDesde(''); setHasta('') }}>Limpiar</button>
      </div>

      {chartData.length > 0 && (
        <div className="card p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Saldo Acumulado</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="fecha" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `$${(v/1000000).toFixed(1)}M`} />
              <Tooltip formatter={(v) => fmt(v)} />
              <Line type="monotone" dataKey="saldo" stroke="#1E3A5F" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {proyeccion.length > 0 && (
        <div className="card p-0">
          <div className="px-5 py-3 border-b bg-gray-50"><h2 className="text-sm font-semibold text-gray-700">Proyección 3 Meses</h2></div>
          <div className="grid grid-cols-3 divide-x">
            {proyeccion.map(p => (
              <div key={p.mes} className="p-4 text-center">
                <p className="text-xs text-gray-500 mb-1">{p.mes}</p>
                <p className="text-sm text-green-600">▲ {fmt(p.ingresos)}</p>
                <p className="text-sm text-red-600">▼ {fmt(p.egresos)}</p>
                <p className={`text-base font-bold mt-1 ${Number(p.saldo) >= 0 ? 'text-blue-700' : 'text-red-600'}`}>{fmt(p.saldo)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="th">Fecha</th>
              <th className="th">Tipo</th>
              <th className="th">Concepto</th>
              <th className="th text-right">Valor</th>
              <th className="th">Cuenta</th>
              <th className="th">Origen</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? <tr><td colSpan={6} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            : movimientos.length === 0 ? <tr><td colSpan={6} className="td text-center py-8 text-gray-400">Sin movimientos</td></tr>
            : movimientos.map(m => (
              <tr key={m.id} className="hover:bg-gray-50">
                <td className="td">{m.fecha}</td>
                <td className="td"><span className={m.tipo === 'ingreso' ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>{m.tipo_display}</span></td>
                <td className="td">{m.concepto}</td>
                <td className="td text-right font-medium">{fmt(m.valor)}</td>
                <td className="td text-xs text-gray-500">{m.cuenta_bancaria_nombre || '—'}</td>
                <td className="td"><span className={m.es_proyectado ? 'badge-yellow' : 'badge-blue'}>{m.es_proyectado ? 'Proyectado' : 'Real'}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
