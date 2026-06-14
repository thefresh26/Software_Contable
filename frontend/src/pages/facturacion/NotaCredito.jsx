import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
const EMPTY_LINE = { descripcion: '', cantidad: 1, precio_unitario: 0, descuento_porcentaje: 0, iva_porcentaje: 19 }

export default function NotaCredito() {
  const navigate = useNavigate()
  const [facturas, setFacturas] = useState([])
  const [facturaRef, setFacturaRef] = useState('')
  const [terceroId, setTerceroId] = useState('')
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10))
  const [observaciones, setObservaciones] = useState('')
  const [lines, setLines] = useState([{ ...EMPTY_LINE }])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/facturacion/facturas/?tipo=FV&estado=emitida&page_size=200').then(({ data }) => setFacturas(data.results || []))
  }, [])

  const setLine = (i, k, v) => setLines(prev => { const n = [...prev]; n[i] = { ...n[i], [k]: v }; return n })
  const addLine = () => setLines(p => [...p, { ...EMPTY_LINE }])
  const removeLine = (i) => setLines(p => p.filter((_, idx) => idx !== i))

  const handleFacturaRef = (id) => {
    setFacturaRef(id)
    const f = facturas.find(f => String(f.id) === String(id))
    if (f) setTerceroId(f.tercero)
  }

  const totalLineas = lines.reduce((a, l) => {
    const base = Number(l.precio_unitario) * Number(l.cantidad)
    const desc = base * Number(l.descuento_porcentaje) / 100
    const sub = base - desc
    return a + sub + sub * Number(l.iva_porcentaje) / 100
  }, 0)

  const submit = async (e) => {
    e.preventDefault()
    if (!terceroId) { setError('Seleccione un tercero.'); return }
    setSaving(true); setError('')
    try {
      await api.post('/facturacion/facturas/', {
        tipo: 'NC', tercero: terceroId, fecha, observaciones: `Nota Crédito — Ref: ${facturas.find(f => String(f.id) === String(facturaRef))?.numero || ''}\n${observaciones}`,
        detalles: lines,
      })
      navigate('/facturacion')
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">Nueva Nota Crédito</h1>
      {error && <p className="text-red-600 text-sm bg-red-50 p-2 rounded">{error}</p>}
      <form onSubmit={submit} className="space-y-4">
        <div className="card space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Factura de referencia *</label>
              <select className="input" value={facturaRef} onChange={e => handleFacturaRef(e.target.value)} required>
                <option value="">Seleccionar factura original…</option>
                {facturas.map(f => <option key={f.id} value={f.id}>{f.numero} — {f.tercero_nombre} — {fmt(f.total)}</option>)}
              </select>
            </div>
            <div><label className="label">Fecha *</label><input className="input" type="date" value={fecha} onChange={e => setFecha(e.target.value)} required /></div>
          </div>
          <div>
            <label className="label">Observaciones</label>
            <textarea className="input" rows={2} value={observaciones} onChange={e => setObservaciones(e.target.value)} placeholder="Motivo de la nota crédito…" />
          </div>
        </div>

        <div className="card p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="th">Descripción</th>
                <th className="th w-20">Cant.</th>
                <th className="th w-28">Precio Unit.</th>
                <th className="th w-20">% Desc.</th>
                <th className="th w-20">% IVA</th>
                <th className="th w-8" />
              </tr>
            </thead>
            <tbody className="divide-y">
              {lines.map((l, i) => (
                <tr key={i}>
                  <td className="px-3 py-2"><input className="input text-xs" value={l.descripcion} onChange={e => setLine(i, 'descripcion', e.target.value)} required /></td>
                  <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0.01" step="0.01" value={l.cantidad} onChange={e => setLine(i, 'cantidad', e.target.value)} /></td>
                  <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0" step="0.01" value={l.precio_unitario} onChange={e => setLine(i, 'precio_unitario', e.target.value)} /></td>
                  <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0" max="100" step="0.01" value={l.descuento_porcentaje} onChange={e => setLine(i, 'descuento_porcentaje', e.target.value)} /></td>
                  <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0" max="100" step="0.01" value={l.iva_porcentaje} onChange={e => setLine(i, 'iva_porcentaje', e.target.value)} /></td>
                  <td className="px-3 py-2">{lines.length > 1 && <button type="button" onClick={() => removeLine(i)} className="text-red-400 hover:text-red-600">✕</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex justify-between items-center">
          <button type="button" onClick={addLine} className="text-blue-600 text-sm hover:underline">+ Agregar ítem</button>
          <div className="text-right">
            <p className="text-sm text-gray-500">Total NC: <strong>{fmt(totalLineas)}</strong></p>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <button type="button" onClick={() => navigate('/facturacion')} className="btn-secondary">Cancelar</button>
          <button type="submit" className="btn-primary" disabled={saving || !facturaRef}>{saving ? 'Guardando…' : 'Crear Nota Crédito'}</button>
        </div>
      </form>
    </div>
  )
}
