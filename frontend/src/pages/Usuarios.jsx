import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'

const ROLES = ['admin', 'contador', 'auxiliar', 'gerente', 'vendedor']
const EMPTY = { username: '', email: '', first_name: '', last_name: '', empresa: '', nit_empresa: '', rol: 'auxiliar', password: '' }

function Modal({ item, onClose, onSaved }) {
  const [form, setForm] = useState(item ? { ...item, password: '' } : EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      const body = { ...form }
      if (!body.password) delete body.password
      item?.id ? await api.put(`/auth/usuarios/${item.id}/`, body) : await api.post('/auth/registro/', body)
      onSaved()
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center px-6 py-4 border-b sticky top-0 bg-white">
          <h2 className="font-semibold">{item?.id ? 'Editar' : 'Nuevo'} Usuario</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Usuario *</label><input className="input" value={form.username} onChange={e => set('username', e.target.value)} required disabled={!!item?.id} /></div>
            <div><label className="label">Email</label><input className="input" type="email" value={form.email} onChange={e => set('email', e.target.value)} /></div>
            <div><label className="label">Nombre</label><input className="input" value={form.first_name} onChange={e => set('first_name', e.target.value)} /></div>
            <div><label className="label">Apellido</label><input className="input" value={form.last_name} onChange={e => set('last_name', e.target.value)} /></div>
            <div><label className="label">Empresa</label><input className="input" value={form.empresa} onChange={e => set('empresa', e.target.value)} /></div>
            <div><label className="label">NIT Empresa</label><input className="input" value={form.nit_empresa} onChange={e => set('nit_empresa', e.target.value)} /></div>
            <div>
              <label className="label">Rol *</label>
              <select className="input" value={form.rol} onChange={e => set('rol', e.target.value)}>
                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div><label className="label">{item?.id ? 'Nueva contraseña' : 'Contraseña *'}</label><input className="input" type="password" value={form.password} onChange={e => set('password', e.target.value)} required={!item?.id} minLength={8} /></div>
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

export default function Usuarios() {
  const { user } = useAuth()
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(false)

  const load = () => {
    setLoading(true)
    api.get('/auth/usuarios/?page_size=100').then(({ data: d }) => setData(d.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (user?.rol !== 'admin' && !user?.is_superuser) {
    return <div className="card text-center py-20"><p className="text-gray-500 text-lg">Sin permisos para esta sección.</p><p className="text-gray-400 text-sm mt-2">Solo administradores pueden gestionar usuarios.</p></div>
  }

  return (
    <div className="space-y-4">
      {modal !== false && <Modal item={modal === true ? null : modal} onClose={() => setModal(false)} onSaved={() => { setModal(false); load() }} />}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Usuarios</h1>
        <button className="btn-primary" onClick={() => setModal(true)}>+ Nuevo Usuario</button>
      </div>
      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b"><tr><th className="th">Usuario</th><th className="th">Nombre</th><th className="th">Email</th><th className="th">Empresa</th><th className="th">Rol</th><th className="th">Estado</th><th className="th" /></tr></thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? <tr><td colSpan={7} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            : data.map(u => (
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="td font-mono text-sm">{u.username}</td>
                <td className="td">{[u.first_name, u.last_name].filter(Boolean).join(' ') || '—'}</td>
                <td className="td text-gray-500">{u.email || '—'}</td>
                <td className="td">{u.empresa || '—'}</td>
                <td className="td"><span className="badge-gray capitalize">{u.rol}</span></td>
                <td className="td"><span className={u.is_active ? 'badge-green' : 'badge-red'}>{u.is_active ? 'Activo' : 'Inactivo'}</span></td>
                <td className="td"><button className="text-blue-600 hover:underline text-xs" onClick={() => setModal(u)}>Editar</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
