import { useEffect, useState } from 'react'
import api from '../api/client'
import { descargarExcel } from '../utils/excel'

const EMPTY = { tipo: 'cliente', tipo_persona: 'natural', nombre: '', nit: '', email: '', telefono: '', direccion: '', ciudad: '' }

function Modal({ item, onClose, onSaved }) {
  const [form, setForm] = useState(item || EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      item?.id ? await api.put(`/terceros/${item.id}/`, form) : await api.post('/terceros/', form)
      onSaved()
    } catch (err) {
      setError(JSON.stringify(err.response?.data || 'Error al guardar'))
    } finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="font-semibold text-gray-800">{item?.id ? 'Editar' : 'Nuevo'} Tercero</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Tipo</label>
              <select className="input" value={form.tipo} onChange={(e) => set('tipo', e.target.value)}>
                <option value="cliente">Cliente</option>
                <option value="proveedor">Proveedor</option>
                <option value="ambos">Ambos</option>
              </select>
            </div>
            <div>
              <label className="label">Persona</label>
              <select className="input" value={form.tipo_persona} onChange={(e) => set('tipo_persona', e.target.value)}>
                <option value="natural">Natural</option>
                <option value="juridica">Jurídica</option>
              </select>
            </div>
          </div>
          <div>
            <label className="label">Nombre / Razón social *</label>
            <input className="input" value={form.nombre} onChange={(e) => set('nombre', e.target.value)} required />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">NIT / Cédula *</label>
              <input className="input" value={form.nit} onChange={(e) => set('nit', e.target.value)} required />
            </div>
            <div>
              <label className="label">Teléfono</label>
              <input className="input" value={form.telefono} onChange={(e) => set('telefono', e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label">Email</label>
            <input className="input" type="email" value={form.email} onChange={(e) => set('email', e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Ciudad</label>
              <input className="input" value={form.ciudad} onChange={(e) => set('ciudad', e.target.value)} />
            </div>
            <div>
              <label className="label">Dirección</label>
              <input className="input" value={form.direccion} onChange={(e) => set('direccion', e.target.value)} />
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

const tipoBadge = { cliente: 'badge-green', proveedor: 'badge-yellow', ambos: 'badge-gray' }

export default function Terceros() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [tipo, setTipo] = useState('')
  const [modal, setModal] = useState(null)

  const load = () => {
    setLoading(true)
    const params = new URLSearchParams({ page_size: 200 })
    if (search) params.set('search', search)
    if (tipo) params.set('tipo', tipo)
    api.get(`/terceros/?${params}`).then(({ data: d }) => setData(d.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [search, tipo])

  const deactivate = async (id) => {
    if (!confirm('¿Desactivar este tercero?')) return
    await api.patch(`/terceros/${id}/`, { activo: false })
    load()
  }

  return (
    <div className="space-y-4">
      {modal !== undefined && modal !== false && (
        <Modal item={modal === true ? null : modal} onClose={() => setModal(false)} onSaved={() => { setModal(false); load() }} />
      )}

      <div className="flex flex-wrap justify-between items-center gap-2">
        <h1 className="text-2xl font-bold text-slate-800">Terceros</h1>
        <div className="flex gap-2">
          <button className="btn-excel" onClick={() => descargarExcel('/terceros/exportar/', 'terceros.xlsx').catch(() => alert('Error al exportar'))}>⬇ Excel</button>
          <button className="btn-primary" onClick={() => setModal(true)}>+ Nuevo</button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <input className="input max-w-xs" placeholder="Buscar por nombre o NIT…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <select className="input w-40" value={tipo} onChange={(e) => setTipo(e.target.value)}>
          <option value="">Todos</option>
          <option value="cliente">Clientes</option>
          <option value="proveedor">Proveedores</option>
          <option value="ambos">Ambos</option>
        </select>
      </div>

      <div className="card p-0 overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="th">Nombre</th><th className="th">NIT</th><th className="th">Tipo</th>
              <th className="th">Ciudad</th><th className="th">Teléfono</th><th className="th">Estado</th><th className="th" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={7} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={7} className="td text-center py-8 text-gray-400">Sin resultados</td></tr>
            ) : data.map((t) => (
              <tr key={t.id} className="hover:bg-gray-50">
                <td className="td font-medium">{t.nombre}</td>
                <td className="td">{t.nit}</td>
                <td className="td"><span className={tipoBadge[t.tipo]}>{t.tipo}</span></td>
                <td className="td">{t.ciudad}</td>
                <td className="td">{t.telefono}</td>
                <td className="td"><span className={t.activo ? 'badge-green' : 'badge-red'}>{t.activo ? 'Activo' : 'Inactivo'}</span></td>
                <td className="td">
                  <div className="flex gap-2">
                    <button className="text-blue-600 hover:underline text-xs" onClick={() => setModal(t)}>Editar</button>
                    {t.activo && <button className="text-red-500 hover:underline text-xs" onClick={() => deactivate(t.id)}>Desactivar</button>}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
