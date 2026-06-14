import { useEffect, useState } from 'react'
import api from '../../api/client'

const TIPOS = ['activo', 'pasivo', 'patrimonio', 'ingreso', 'gasto', 'costo']
const EMPTY = { codigo: '', nombre: '', tipo: 'activo', padre: '', nivel: 4, activa: true, permite_movimiento: true }

function Modal({ item, cuentas, onClose, onSaved }) {
  const [form, setForm] = useState(item ? { ...item, padre: item.padre || '' } : EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    const body = { ...form, padre: form.padre || null }
    try {
      item?.id ? await api.put(`/contabilidad/cuentas/${item.id}/`, body) : await api.post('/contabilidad/cuentas/', body)
      onSaved()
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="font-semibold">{item?.id ? 'Editar' : 'Nueva'} Cuenta PUC</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Código *</label><input className="input font-mono" value={form.codigo} onChange={(e) => set('codigo', e.target.value)} required /></div>
            <div>
              <label className="label">Nivel *</label>
              <select className="input" value={form.nivel} onChange={(e) => set('nivel', Number(e.target.value))}>
                {[1, 2, 3, 4].map((n) => <option key={n} value={n}>Nivel {n}</option>)}
              </select>
            </div>
          </div>
          <div><label className="label">Nombre *</label><input className="input" value={form.nombre} onChange={(e) => set('nombre', e.target.value)} required /></div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Tipo *</label>
              <select className="input" value={form.tipo} onChange={(e) => set('tipo', e.target.value)}>
                {TIPOS.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Cuenta padre</label>
              <select className="input" value={form.padre} onChange={(e) => set('padre', e.target.value)}>
                <option value="">Sin padre</option>
                {cuentas.filter((c) => c.id !== item?.id).map((c) => <option key={c.id} value={c.id}>{c.codigo} — {c.nombre}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-6">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={form.activa} onChange={(e) => set('activa', e.target.checked)} /> Activa
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={form.permite_movimiento} onChange={(e) => set('permite_movimiento', e.target.checked)} /> Permite movimiento
            </label>
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

export default function PUC() {
  const [cuentas, setCuentas] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [tipoF, setTipoF] = useState('')
  const [modal, setModal] = useState(false)

  const load = () => {
    setLoading(true)
    const p = new URLSearchParams({ page_size: 500 })
    if (search) p.set('search', search)
    if (tipoF) p.set('tipo', tipoF)
    api.get(`/contabilidad/cuentas/?${p}`).then(({ data }) => setCuentas(data.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [search, tipoF])

  return (
    <div className="space-y-4">
      {modal !== false && (
        <Modal item={modal === true ? null : modal} cuentas={cuentas} onClose={() => setModal(false)} onSaved={() => { setModal(false); load() }} />
      )}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Plan de Cuentas PUC</h1>
        <button className="btn-primary" onClick={() => setModal(true)}>+ Nueva Cuenta</button>
      </div>
      <div className="flex flex-wrap gap-3">
        <input className="input max-w-xs" placeholder="Buscar código o nombre…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <select className="input w-36" value={tipoF} onChange={(e) => setTipoF(e.target.value)}>
          <option value="">Todos</option>
          {TIPOS.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
        </select>
      </div>
      <div className="card p-0 overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr><th className="th">Código</th><th className="th">Nombre</th><th className="th">Tipo</th><th className="th">Nivel</th><th className="th">Mov.</th><th className="th" /></tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={6} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            ) : cuentas.length === 0 ? (
              <tr><td colSpan={6} className="td text-center py-8 text-gray-400">Sin cuentas</td></tr>
            ) : cuentas.map((c) => (
              <tr key={c.id} className={`hover:bg-gray-50 ${c.nivel <= 2 ? 'font-semibold' : ''}`}>
                <td className="td font-mono" style={{ paddingLeft: `${(c.nivel - 1) * 20 + 16}px` }}>{c.codigo}</td>
                <td className="td">{c.nombre}</td>
                <td className="td"><span className="badge-gray capitalize">{c.tipo}</span></td>
                <td className="td text-center">{c.nivel}</td>
                <td className="td text-center">{c.permite_movimiento ? '✓' : '—'}</td>
                <td className="td"><button className="text-blue-600 hover:underline text-xs" onClick={() => setModal(c)}>Editar</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
