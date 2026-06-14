import { useEffect, useState } from 'react'
import api from '../../api/client'

const EMPTY = { codigo: '', nombre: '', descripcion: '', activo: true, padre: '' }

function Modal({ item, centros, onClose, onSaved }) {
  const [form, setForm] = useState(item ? { ...item, padre: item.padre || '' } : EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    const body = { ...form, padre: form.padre || null }
    try {
      item?.id ? await api.put(`/contabilidad/centros-costo/${item.id}/`, body) : await api.post('/contabilidad/centros-costo/', body)
      onSaved()
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="font-semibold">{item?.id ? 'Editar' : 'Nuevo'} Centro de Costo</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Código *</label><input className="input font-mono" value={form.codigo} onChange={e => set('codigo', e.target.value)} required /></div>
            <div>
              <label className="label">Centro padre</label>
              <select className="input" value={form.padre} onChange={e => set('padre', e.target.value)}>
                <option value="">Sin padre</option>
                {centros.filter(c => c.id !== item?.id).map(c => <option key={c.id} value={c.id}>{c.codigo} — {c.nombre}</option>)}
              </select>
            </div>
          </div>
          <div><label className="label">Nombre *</label><input className="input" value={form.nombre} onChange={e => set('nombre', e.target.value)} required /></div>
          <div><label className="label">Descripción</label><textarea className="input" rows={2} value={form.descripcion} onChange={e => set('descripcion', e.target.value)} /></div>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={form.activo} onChange={e => set('activo', e.target.checked)} /> Activo
          </label>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function CentrosCosto() {
  const [centros, setCentros] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(false)

  const load = () => {
    setLoading(true)
    api.get('/contabilidad/centros-costo/?page_size=200').then(({ data }) => setCentros(data.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  return (
    <div className="space-y-4">
      {modal !== false && <Modal item={modal === true ? null : modal} centros={centros} onClose={() => setModal(false)} onSaved={() => { setModal(false); load() }} />}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Centros de Costo</h1>
        <button className="btn-primary" onClick={() => setModal(true)}>+ Nuevo</button>
      </div>
      <div className="card p-0 overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b"><tr><th className="th">Código</th><th className="th">Nombre</th><th className="th">Padre</th><th className="th">Estado</th><th className="th" /></tr></thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? <tr><td colSpan={5} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            : centros.length === 0 ? <tr><td colSpan={5} className="td text-center py-8 text-gray-400">Sin centros de costo</td></tr>
            : centros.map(c => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="td font-mono">{c.codigo}</td>
                <td className="td font-medium">{c.nombre}</td>
                <td className="td text-gray-500">{c.padre_nombre || '—'}</td>
                <td className="td"><span className={c.activo ? 'badge-green' : 'badge-red'}>{c.activo ? 'Activo' : 'Inactivo'}</span></td>
                <td className="td"><button className="text-blue-600 hover:underline text-xs" onClick={() => setModal(c)}>Editar</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
