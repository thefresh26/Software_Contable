import { useEffect, useState } from 'react'
import api from '../../api/client'

function ModalNueva({ onClose, onSaved }) {
  const [form, setForm] = useState({
    numero_resolucion: '', fecha_resolucion: '', fecha_inicio_vigencia: '',
    fecha_fin_vigencia: '', prefijo: '', consecutivo_desde: '', consecutivo_hasta: '',
    consecutivo_actual: '', tipo: 'venta',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      await api.post('/facturacion/resoluciones/', { ...form, consecutivo_actual: form.consecutivo_desde })
      onSaved()
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="font-semibold">Nueva Resolución DIAN</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Número de Resolución *</label><input className="input" value={form.numero_resolucion} onChange={e => set('numero_resolucion', e.target.value)} required /></div>
            <div><label className="label">Tipo *</label>
              <select className="input" value={form.tipo} onChange={e => set('tipo', e.target.value)}>
                <option value="venta">Venta</option>
                <option value="compra">Compra</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div><label className="label">Fecha Resolución *</label><input className="input" type="date" value={form.fecha_resolucion} onChange={e => set('fecha_resolucion', e.target.value)} required /></div>
            <div><label className="label">Inicio Vigencia *</label><input className="input" type="date" value={form.fecha_inicio_vigencia} onChange={e => set('fecha_inicio_vigencia', e.target.value)} required /></div>
            <div><label className="label">Fin Vigencia *</label><input className="input" type="date" value={form.fecha_fin_vigencia} onChange={e => set('fecha_fin_vigencia', e.target.value)} required /></div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div><label className="label">Prefijo</label><input className="input" value={form.prefijo} onChange={e => set('prefijo', e.target.value)} placeholder="ej: FV" /></div>
            <div><label className="label">Consec. Desde *</label><input className="input" type="number" min="1" value={form.consecutivo_desde} onChange={e => set('consecutivo_desde', e.target.value)} required /></div>
            <div><label className="label">Consec. Hasta *</label><input className="input" type="number" min="1" value={form.consecutivo_hasta} onChange={e => set('consecutivo_hasta', e.target.value)} required /></div>
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

export default function ResolucionesDIAN() {
  const [resoluciones, setResoluciones] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(false)

  const load = () => {
    setLoading(true)
    api.get('/facturacion/resoluciones/?page_size=50').then(({ data }) => setResoluciones(data.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const activar = async (id) => {
    await api.post(`/facturacion/resoluciones/${id}/activar/`)
    load()
  }

  return (
    <div className="space-y-4">
      {modal && <ModalNueva onClose={() => setModal(false)} onSaved={() => { setModal(false); load() }} />}

      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Resoluciones DIAN</h1>
        <button className="btn-primary" onClick={() => setModal(true)}>+ Nueva Resolución</button>
      </div>

      <div className="space-y-4">
        {loading ? <div className="card text-center py-8 text-gray-400">Cargando…</div>
        : resoluciones.length === 0 ? <div className="card text-center py-8 text-gray-400">Sin resoluciones. Cree una para habilitar los consecutivos DIAN.</div>
        : resoluciones.map(r => {
          const pct = r.porcentaje_uso || 0
          const diasVence = r.dias_para_vencer || 0
          const alertaConsec = pct >= 90
          const alertaVigencia = diasVence < 30
          return (
            <div key={r.id} className={`card border-l-4 ${r.activa ? 'border-green-500' : 'border-gray-300'}`}>
              <div className="flex flex-wrap justify-between items-start gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="font-semibold text-gray-800">Resolución {r.numero_resolucion}</h2>
                    {r.activa && <span className="badge-green">Activa</span>}
                    <span className="badge-blue">{r.tipo_display}</span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Prefijo: <strong>{r.prefijo || '(sin prefijo)'}</strong> —
                    Vigencia: {r.fecha_inicio_vigencia} a {r.fecha_fin_vigencia}
                  </p>
                  <p className="text-sm text-gray-500">
                    Consecutivos: {r.consecutivo_desde} — {r.consecutivo_hasta} |
                    Actual: <strong>{r.consecutivo_actual}</strong>
                  </p>
                </div>
                {!r.activa && (
                  <button className="btn-primary text-sm" onClick={() => activar(r.id)}>Activar</button>
                )}
              </div>

              <div className="mt-3">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Uso de consecutivos</span>
                  <span>{pct}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-yellow-400' : 'bg-green-500'}`}
                    style={{ width: `${Math.min(pct, 100)}%` }}
                  />
                </div>
              </div>

              {alertaConsec && (
                <p className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                  Alerta: Quedan menos del 10% de consecutivos disponibles.
                </p>
              )}
              {alertaVigencia && (
                <p className="mt-2 text-xs text-yellow-700 bg-yellow-50 p-2 rounded">
                  Alerta: La resolución vence en {diasVence} días.
                </p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
