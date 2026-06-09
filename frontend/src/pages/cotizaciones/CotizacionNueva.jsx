import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/client'

const hoy = () => new Date().toISOString().slice(0, 10)
const en30 = () => { const d = new Date(); d.setDate(d.getDate() + 30); return d.toISOString().slice(0, 10) }
const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
const EMPTY = { producto: '', descripcion: '', cantidad: 1, precio_unitario: 0, iva_porcentaje: 19 }

function calcLine(l) {
  const sub = Number(l.precio_unitario) * Number(l.cantidad)
  const iva = sub * Number(l.iva_porcentaje) / 100
  return { ...l, subtotal: sub, iva_valor: iva, total: sub + iva }
}

export default function CotizacionNueva() {
  const navigate = useNavigate()
  const [tercero, setTercero] = useState('')
  const [fecha, setFecha] = useState(hoy())
  const [fechaVenc, setFechaVenc] = useState(en30())
  const [obs, setObs] = useState('')
  const [terminos, setTerminos] = useState('')
  const [lines, setLines] = useState([{ ...EMPTY }])
  const [terceros, setTerceros] = useState([])
  const [productos, setProductos] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/terceros/?page_size=500&activo=true').then(({ data }) => setTerceros(data.results || []))
    api.get('/inventario/productos/?page_size=500&activo=true').then(({ data }) => setProductos(data.results || []))
  }, [])

  const setLine = (i, k, v) => {
    setLines(prev => {
      const next = [...prev]
      next[i] = calcLine({ ...next[i], [k]: v })
      if (k === 'producto') {
        const prod = productos.find(p => String(p.id) === String(v))
        if (prod) next[i] = calcLine({ ...next[i], producto: prod.id, descripcion: prod.nombre, precio_unitario: prod.precio_venta, iva_porcentaje: prod.iva_porcentaje })
      }
      return next
    })
  }

  const totales = lines.reduce((a, l) => { const c = calcLine(l); return { sub: a.sub + c.subtotal, iva: a.iva + c.iva_valor, total: a.total + c.total } }, { sub: 0, iva: 0, total: 0 })

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      const detalles = lines.map(l => ({ producto: l.producto || null, descripcion: l.descripcion, cantidad: l.cantidad, precio_unitario: l.precio_unitario, iva_porcentaje: l.iva_porcentaje }))
      await api.post('/presupuestos/cotizaciones/', { tercero, fecha, fecha_vencimiento: fechaVenc, observaciones: obs, terminos, detalles })
      navigate('/cotizaciones')
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="max-w-5xl space-y-5">
      <h1 className="text-2xl font-bold text-slate-800">Nueva Cotización</h1>
      {error && <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">{error}</div>}
      <form onSubmit={submit} className="space-y-5">
        <div className="card grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <label className="label">Cliente *</label>
            <select className="input" value={tercero} onChange={e => setTercero(e.target.value)} required>
              <option value="">Seleccionar…</option>
              {terceros.map(t => <option key={t.id} value={t.id}>{t.nombre} — {t.nit}</option>)}
            </select>
          </div>
          <div><label className="label">Fecha *</label><input className="input" type="date" value={fecha} onChange={e => setFecha(e.target.value)} required /></div>
          <div><label className="label">Vencimiento *</label><input className="input" type="date" value={fechaVenc} onChange={e => setFechaVenc(e.target.value)} required /></div>
          <div className="md:col-span-2"><label className="label">Observaciones</label><input className="input" value={obs} onChange={e => setObs(e.target.value)} /></div>
          <div className="md:col-span-2"><label className="label">Términos y condiciones</label><input className="input" value={terminos} onChange={e => setTerminos(e.target.value)} /></div>
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="px-5 py-3 bg-gray-50 border-b flex justify-between items-center">
            <h2 className="font-semibold text-gray-700 text-sm">Ítems</h2>
            <button type="button" onClick={() => setLines(p => [...p, { ...EMPTY }])} className="text-blue-600 text-sm hover:underline">+ Agregar ítem</button>
          </div>
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50"><tr><th className="th w-48">Producto</th><th className="th">Descripción</th><th className="th w-20">Cant.</th><th className="th w-28">P. Unitario</th><th className="th w-20">IVA %</th><th className="th w-28 text-right">Total</th><th className="th w-8" /></tr></thead>
            <tbody className="divide-y">
              {lines.map((l, i) => {
                const c = calcLine(l)
                return (
                  <tr key={i}>
                    <td className="px-3 py-2"><select className="input text-xs" value={l.producto} onChange={e => setLine(i, 'producto', e.target.value)}><option value="">Libre…</option>{productos.map(p => <option key={p.id} value={p.id}>{p.codigo} — {p.nombre}</option>)}</select></td>
                    <td className="px-3 py-2"><input className="input text-xs" value={l.descripcion} onChange={e => setLine(i, 'descripcion', e.target.value)} required /></td>
                    <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0.01" step="0.01" value={l.cantidad} onChange={e => setLine(i, 'cantidad', e.target.value)} /></td>
                    <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0" step="0.01" value={l.precio_unitario} onChange={e => setLine(i, 'precio_unitario', e.target.value)} /></td>
                    <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0" step="0.01" value={l.iva_porcentaje} onChange={e => setLine(i, 'iva_porcentaje', e.target.value)} /></td>
                    <td className="px-3 py-2 text-right font-medium">{fmt(c.total)}</td>
                    <td className="px-3 py-2">{lines.length > 1 && <button type="button" onClick={() => setLines(p => p.filter((_, idx) => idx !== i))} className="text-red-400 hover:text-red-600">✕</button>}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        <div className="flex justify-end">
          <div className="card w-56 space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-gray-500">Subtotal</span><span>{fmt(totales.sub)}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">IVA</span><span>{fmt(totales.iva)}</span></div>
            <div className="flex justify-between font-bold border-t pt-2"><span>TOTAL</span><span className="text-blue-700 text-base">{fmt(totales.total)}</span></div>
          </div>
        </div>

        <div className="flex gap-3">
          <button type="button" onClick={() => navigate('/cotizaciones')} className="btn-secondary">Cancelar</button>
          <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar Cotización'}</button>
        </div>
      </form>
    </div>
  )
}
