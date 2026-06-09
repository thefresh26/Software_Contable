import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/client'

const hoy = () => new Date().toISOString().slice(0, 10)
const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

const EMPTY_LINE = { producto: '', producto_nombre: '', descripcion: '', cantidad: 1, precio_unitario: 0, descuento_porcentaje: 0, iva_porcentaje: 19 }

function calcLine(l) {
  const base = Number(l.precio_unitario) * Number(l.cantidad)
  const desc = base * Number(l.descuento_porcentaje) / 100
  const sub = base - desc
  const iva = sub * Number(l.iva_porcentaje) / 100
  return { ...l, subtotal: sub, iva_valor: iva, total: sub + iva }
}

export default function FacturaNueva() {
  const navigate = useNavigate()
  const [tipo, setTipo] = useState('FV')
  const [tercero, setTercero] = useState('')
  const [fecha, setFecha] = useState(hoy())
  const [fechaVenc, setFechaVenc] = useState('')
  const [obs, setObs] = useState('')
  const [lines, setLines] = useState([{ ...EMPTY_LINE }])
  const [terceros, setTerceros] = useState([])
  const [productos, setProductos] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/terceros/?page_size=500&activo=true').then(({ data }) => setTerceros(data.results || []))
    api.get('/inventario/productos/?page_size=500&activo=true').then(({ data }) => setProductos(data.results || []))
  }, [])

  const setLine = (i, k, v) => {
    setLines((prev) => {
      const next = [...prev]
      next[i] = calcLine({ ...next[i], [k]: v })
      if (k === 'producto') {
        const prod = productos.find((p) => String(p.id) === String(v))
        if (prod) {
          next[i] = calcLine({
            ...next[i],
            producto: prod.id,
            producto_nombre: prod.nombre,
            descripcion: prod.nombre,
            precio_unitario: prod.precio_venta,
            iva_porcentaje: prod.iva_porcentaje,
          })
        }
      }
      return next
    })
  }

  const addLine = () => setLines((prev) => [...prev, { ...EMPTY_LINE }])
  const removeLine = (i) => setLines((prev) => prev.filter((_, idx) => idx !== i))

  const totales = lines.reduce(
    (acc, l) => {
      const c = calcLine(l)
      return { subtotal: acc.subtotal + c.subtotal, iva: acc.iva + c.iva_valor, total: acc.total + c.total }
    },
    { subtotal: 0, iva: 0, total: 0 }
  )

  const submit = async (e) => {
    e.preventDefault()
    if (!tercero) { setError('Seleccione un tercero'); return }
    if (lines.some((l) => !l.producto)) { setError('Todos los ítems deben tener un producto'); return }
    setSaving(true); setError('')
    try {
      const detalles = lines.map((l) => ({
        producto: l.producto,
        descripcion: l.descripcion || l.producto_nombre,
        cantidad: l.cantidad,
        precio_unitario: l.precio_unitario,
        descuento_porcentaje: l.descuento_porcentaje,
        iva_porcentaje: l.iva_porcentaje,
      }))
      const { data } = await api.post('/facturacion/facturas/', {
        tipo, tercero, fecha, fecha_vencimiento: fechaVenc || null, observaciones: obs, detalles,
      })
      navigate('/facturacion')
    } catch (err) {
      setError(JSON.stringify(err.response?.data || 'Error al guardar'))
    } finally { setSaving(false) }
  }

  return (
    <div className="max-w-5xl space-y-5">
      <h1 className="text-2xl font-bold text-slate-800">Nueva Factura</h1>

      {error && <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">{error}</div>}

      <form onSubmit={submit} className="space-y-5">
        {/* Cabecera */}
        <div className="card grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="label">Tipo *</label>
            <select className="input" value={tipo} onChange={(e) => setTipo(e.target.value)}>
              <option value="FV">Factura de Venta</option>
              <option value="FC">Factura de Compra</option>
              <option value="NC">Nota Crédito</option>
              <option value="ND">Nota Débito</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="label">Tercero *</label>
            <select className="input" value={tercero} onChange={(e) => setTercero(e.target.value)} required>
              <option value="">Seleccionar…</option>
              {terceros.map((t) => <option key={t.id} value={t.id}>{t.nombre} — {t.nit}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Fecha *</label>
            <input className="input" type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} required />
          </div>
          <div>
            <label className="label">Vencimiento</label>
            <input className="input" type="date" value={fechaVenc} onChange={(e) => setFechaVenc(e.target.value)} />
          </div>
          <div className="md:col-span-3">
            <label className="label">Observaciones</label>
            <input className="input" value={obs} onChange={(e) => setObs(e.target.value)} />
          </div>
        </div>

        {/* Líneas */}
        <div className="card p-0 overflow-hidden">
          <div className="px-5 py-3 bg-gray-50 border-b flex justify-between items-center">
            <h2 className="font-semibold text-gray-700 text-sm">Ítems</h2>
            <button type="button" onClick={addLine} className="text-blue-600 text-sm hover:underline">+ Agregar ítem</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="th w-48">Producto</th><th className="th">Descripción</th>
                  <th className="th w-20">Cant.</th><th className="th w-28">P. Unitario</th>
                  <th className="th w-20">Desc %</th><th className="th w-20">IVA %</th>
                  <th className="th w-28 text-right">Total</th><th className="th w-8" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {lines.map((l, i) => {
                  const c = calcLine(l)
                  return (
                    <tr key={i}>
                      <td className="px-3 py-2">
                        <select className="input text-xs" value={l.producto} onChange={(e) => setLine(i, 'producto', e.target.value)}>
                          <option value="">Seleccionar…</option>
                          {productos.map((p) => <option key={p.id} value={p.id}>{p.codigo} — {p.nombre}</option>)}
                        </select>
                      </td>
                      <td className="px-3 py-2"><input className="input text-xs" value={l.descripcion} onChange={(e) => setLine(i, 'descripcion', e.target.value)} /></td>
                      <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0.01" step="0.01" value={l.cantidad} onChange={(e) => setLine(i, 'cantidad', e.target.value)} /></td>
                      <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0" step="0.01" value={l.precio_unitario} onChange={(e) => setLine(i, 'precio_unitario', e.target.value)} /></td>
                      <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0" max="100" step="0.01" value={l.descuento_porcentaje} onChange={(e) => setLine(i, 'descuento_porcentaje', e.target.value)} /></td>
                      <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0" step="0.01" value={l.iva_porcentaje} onChange={(e) => setLine(i, 'iva_porcentaje', e.target.value)} /></td>
                      <td className="px-3 py-2 text-right font-medium">{fmt(c.total)}</td>
                      <td className="px-3 py-2">
                        {lines.length > 1 && <button type="button" onClick={() => removeLine(i)} className="text-red-400 hover:text-red-600">✕</button>}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Totales */}
        <div className="flex justify-end">
          <div className="card w-64 space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-gray-500">Subtotal</span><span>{fmt(totales.subtotal)}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">IVA</span><span>{fmt(totales.iva)}</span></div>
            <div className="flex justify-between font-bold border-t pt-2"><span>TOTAL</span><span className="text-blue-700 text-base">{fmt(totales.total)}</span></div>
          </div>
        </div>

        <div className="flex gap-3">
          <button type="button" onClick={() => navigate('/facturacion')} className="btn-secondary">Cancelar</button>
          <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar como borrador'}</button>
        </div>
      </form>
    </div>
  )
}
