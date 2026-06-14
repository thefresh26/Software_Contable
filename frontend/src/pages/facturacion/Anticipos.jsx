import { useEffect, useState } from 'react'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
const estadoBadge = { activo: 'badge-green', aplicado: 'badge-blue', devuelto: 'badge-gray' }

function ModalNuevo({ terceros, onClose, onSaved }) {
  const [form, setForm] = useState({ tipo: 'recibido', tercero: '', fecha: new Date().toISOString().slice(0, 10), valor: '', descripcion: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      await api.post('/facturacion/anticipos/', form)
      onSaved()
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="font-semibold">Nuevo Anticipo</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Tipo *</label>
              <select className="input" value={form.tipo} onChange={e => set('tipo', e.target.value)}>
                <option value="recibido">Anticipo Recibido</option>
                <option value="entregado">Anticipo Entregado</option>
              </select>
            </div>
            <div><label className="label">Fecha *</label><input className="input" type="date" value={form.fecha} onChange={e => set('fecha', e.target.value)} required /></div>
          </div>
          <div><label className="label">Tercero *</label>
            <select className="input" value={form.tercero} onChange={e => set('tercero', e.target.value)} required>
              <option value="">Seleccionar…</option>
              {terceros.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}
            </select>
          </div>
          <div><label className="label">Valor *</label><input className="input" type="number" min="0.01" step="0.01" value={form.valor} onChange={e => set('valor', e.target.value)} required /></div>
          <div><label className="label">Descripción</label><textarea className="input" rows={2} value={form.descripcion} onChange={e => set('descripcion', e.target.value)} /></div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ModalAplicar({ anticipo, facturas, onClose, onSaved }) {
  const [facturaId, setFacturaId] = useState('')
  const [valor, setValor] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      await api.post(`/facturacion/anticipos/${anticipo.id}/aplicar/`, { factura_id: facturaId, valor })
      onSaved()
    } catch (err) { setError(err.response?.data?.error || JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm">
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="font-semibold">Aplicar Anticipo</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <p className="text-sm text-gray-500">Disponible: <strong>{fmt(anticipo.valor_disponible)}</strong></p>
          <div><label className="label">Factura *</label>
            <select className="input" value={facturaId} onChange={e => setFacturaId(e.target.value)} required>
              <option value="">Seleccionar…</option>
              {facturas.map(f => <option key={f.id} value={f.id}>{f.numero} — {fmt(f.total)}</option>)}
            </select>
          </div>
          <div><label className="label">Valor a aplicar *</label><input className="input" type="number" min="0.01" step="0.01" max={anticipo.valor_disponible} value={valor} onChange={e => setValor(e.target.value)} required /></div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Aplicando…' : 'Aplicar'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Anticipos() {
  const [anticipos, setAnticipos] = useState([])
  const [terceros, setTerceros] = useState([])
  const [facturas, setFacturas] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalNuevo, setModalNuevo] = useState(false)
  const [modalAplicar, setModalAplicar] = useState(null)
  const [filtroEstado, setFiltroEstado] = useState('')

  const load = () => {
    setLoading(true)
    const p = new URLSearchParams({ page_size: 200 })
    if (filtroEstado) p.set('estado', filtroEstado)
    api.get(`/facturacion/anticipos/?${p}`).then(({ data }) => setAnticipos(data.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => {
    api.get('/terceros/?page_size=500').then(({ data }) => setTerceros(data.results || []))
    api.get('/facturacion/facturas/?tipo=FV&estado=emitida&page_size=200').then(({ data }) => setFacturas(data.results || []))
  }, [])

  useEffect(() => { load() }, [filtroEstado])

  const devolver = async (id) => {
    if (!confirm('¿Devolver este anticipo?')) return
    await api.post(`/facturacion/anticipos/${id}/devolver/`)
    load()
  }

  return (
    <div className="space-y-4">
      {modalNuevo && <ModalNuevo terceros={terceros} onClose={() => setModalNuevo(false)} onSaved={() => { setModalNuevo(false); load() }} />}
      {modalAplicar && <ModalAplicar anticipo={modalAplicar} facturas={facturas} onClose={() => setModalAplicar(null)} onSaved={() => { setModalAplicar(null); load() }} />}

      <div className="flex flex-wrap justify-between items-center gap-2">
        <h1 className="text-2xl font-bold text-slate-800">Anticipos</h1>
        <button className="btn-primary" onClick={() => setModalNuevo(true)}>+ Nuevo Anticipo</button>
      </div>

      <select className="input w-40" value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)}>
        <option value="">Todos</option>
        <option value="activo">Activo</option>
        <option value="aplicado">Aplicado</option>
        <option value="devuelto">Devuelto</option>
      </select>

      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="th">Tipo</th>
              <th className="th">Tercero</th>
              <th className="th">Fecha</th>
              <th className="th text-right">Valor Total</th>
              <th className="th text-right">Disponible</th>
              <th className="th">Estado</th>
              <th className="th">Descripción</th>
              <th className="th" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? <tr><td colSpan={8} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            : anticipos.length === 0 ? <tr><td colSpan={8} className="td text-center py-8 text-gray-400">Sin anticipos</td></tr>
            : anticipos.map(a => (
              <tr key={a.id} className="hover:bg-gray-50">
                <td className="td"><span className="badge-blue">{a.tipo_display}</span></td>
                <td className="td">{a.tercero_nombre}</td>
                <td className="td">{a.fecha}</td>
                <td className="td text-right">{fmt(a.valor)}</td>
                <td className="td text-right font-semibold text-green-700">{fmt(a.valor_disponible)}</td>
                <td className="td"><span className={estadoBadge[a.estado]}>{a.estado_display}</span></td>
                <td className="td text-xs text-gray-500">{a.descripcion || '—'}</td>
                <td className="td">
                  {a.estado === 'activo' && (
                    <div className="flex gap-2">
                      <button className="text-blue-600 hover:underline text-xs" onClick={() => setModalAplicar(a)}>Aplicar</button>
                      <button className="text-red-500 hover:underline text-xs" onClick={() => devolver(a.id)}>Devolver</button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
