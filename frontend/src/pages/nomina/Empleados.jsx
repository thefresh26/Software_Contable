import { useEffect, useState } from 'react'
import api from '../../api/client'

const EMPTY = { nombre: '', cedula: '', cargo: '', departamento: '', salario_base: '', fecha_ingreso: '', tipo_contrato: 'indefinido', activo: true, cuenta_bancaria: '', banco: '' }

function Modal({ item, onClose, onSaved }) {
  const [form, setForm] = useState(item || EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      item?.id ? await api.put(`/nomina/empleados/${item.id}/`, form) : await api.post('/nomina/empleados/', form)
      onSaved()
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  const fmt = (n) => Number(n || 0).toLocaleString('es-CO')

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center px-6 py-4 border-b sticky top-0 bg-white">
          <h2 className="font-semibold">{item?.id ? 'Editar' : 'Nuevo'} Empleado</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div><label className="label">Nombre completo *</label><input className="input" value={form.nombre} onChange={(e) => set('nombre', e.target.value)} required /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Cédula *</label><input className="input" value={form.cedula} onChange={(e) => set('cedula', e.target.value)} required /></div>
            <div><label className="label">Fecha de ingreso *</label><input className="input" type="date" value={form.fecha_ingreso} onChange={(e) => set('fecha_ingreso', e.target.value)} required /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Cargo *</label><input className="input" value={form.cargo} onChange={(e) => set('cargo', e.target.value)} required /></div>
            <div><label className="label">Departamento</label><input className="input" value={form.departamento} onChange={(e) => set('departamento', e.target.value)} /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Salario base *</label><input className="input" type="number" min="0" step="1" value={form.salario_base} onChange={(e) => set('salario_base', e.target.value)} required /></div>
            <div>
              <label className="label">Tipo de contrato</label>
              <select className="input" value={form.tipo_contrato} onChange={(e) => set('tipo_contrato', e.target.value)}>
                <option value="indefinido">Indefinido</option>
                <option value="fijo">Término fijo</option>
                <option value="obra_labor">Obra o labor</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Banco</label><input className="input" value={form.banco} onChange={(e) => set('banco', e.target.value)} /></div>
            <div><label className="label">Cuenta bancaria</label><input className="input" value={form.cuenta_bancaria} onChange={(e) => set('cuenta_bancaria', e.target.value)} /></div>
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

const fmtCOP = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

export default function Empleados() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [modal, setModal] = useState(false)

  const load = () => {
    setLoading(true)
    const p = new URLSearchParams({ page_size: 200 })
    if (search) p.set('search', search)
    api.get(`/nomina/empleados/?${p}`).then(({ data: d }) => setData(d.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [search])

  return (
    <div className="space-y-4">
      {modal !== false && (
        <Modal item={modal === true ? null : modal} onClose={() => setModal(false)} onSaved={() => { setModal(false); load() }} />
      )}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Empleados</h1>
        <button className="btn-primary" onClick={() => setModal(true)}>+ Nuevo Empleado</button>
      </div>
      <input className="input max-w-xs" placeholder="Buscar por nombre o cédula…" value={search} onChange={(e) => setSearch(e.target.value)} />
      <div className="card p-0 overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr><th className="th">Nombre</th><th className="th">Cédula</th><th className="th">Cargo</th><th className="th">Dept.</th><th className="th">Salario</th><th className="th">Contrato</th><th className="th">Estado</th><th className="th" /></tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={8} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={8} className="td text-center py-8 text-gray-400">Sin empleados</td></tr>
            ) : data.map((e) => (
              <tr key={e.id} className="hover:bg-gray-50">
                <td className="td font-medium">{e.nombre}</td>
                <td className="td font-mono text-xs">{e.cedula}</td>
                <td className="td">{e.cargo}</td>
                <td className="td text-gray-500">{e.departamento || '—'}</td>
                <td className="td">{fmtCOP(e.salario_base)}</td>
                <td className="td capitalize">{e.tipo_contrato.replace('_', ' ')}</td>
                <td className="td"><span className={e.activo ? 'badge-green' : 'badge-red'}>{e.activo ? 'Activo' : 'Inactivo'}</span></td>
                <td className="td"><button className="text-blue-600 hover:underline text-xs" onClick={() => setModal(e)}>Editar</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
