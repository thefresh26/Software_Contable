import { useEffect, useState, useCallback } from 'react'
import api from '../api/client'
import { descargarExcel } from '../utils/excel'
import { useToast } from '../context/ToastContext'
import { useConfirm } from '../components/ui/ConfirmDialog'
import { parseApiError, successMessage } from '../utils/errorMessages'
import EmptyState from '../components/ui/EmptyState'
import { HelpIcon } from '../components/ui/Tooltip'

const EMPTY = { tipo: 'cliente', tipo_persona: 'natural', nombre: '', nit: '', email: '', telefono: '', direccion: '', ciudad: '' }

function NitInput({ value, onChange }) {
  const [nitInfo, setNitInfo] = useState(null)

  const checkNit = useCallback(async (nit) => {
    if (nit.length < 3) { setNitInfo(null); return }
    try {
      const { data } = await api.get(`/auth/validar-nit/?nit=${encodeURIComponent(nit)}`)
      setNitInfo(data)
    } catch { setNitInfo(null) }
  }, [])

  const handleChange = (e) => {
    const v = e.target.value
    onChange(v)
    checkNit(v)
  }

  return (
    <div>
      <label className="label flex items-center gap-1">
        NIT / Cédula *
        <HelpIcon text="Para personas jurídicas: número de NIT con dígito verificador (ej: 900123456-7). Para personas naturales: número de cédula de ciudadanía." />
      </label>
      <div className="relative">
        <input
          className="input pr-8"
          value={value}
          onChange={handleChange}
          required
          placeholder="123456789-0"
          title="Formato: número-dígito verificador (ej: 900123456-7)"
        />
        {nitInfo && (
          <span className="absolute right-2 top-1/2 -translate-y-1/2 text-sm">
            {nitInfo.valido ? '✅' : '❌'}
          </span>
        )}
      </div>
      {nitInfo && !nitInfo.valido && nitInfo.digito !== null && (
        <p className="text-xs text-amber-600 mt-0.5">
          Dígito verificador esperado: <strong>{nitInfo.digito}</strong>. Use: {value.replace(/-.*/, '')}-{nitInfo.digito}
        </p>
      )}
    </div>
  )
}

function Modal({ item, onClose, onSaved }) {
  const [form, setForm] = useState(item || EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const toast = useToast()

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      item?.id ? await api.put(`/terceros/${item.id}/`, form) : await api.post('/terceros/', form)
      toast.success(successMessage(item?.id ? 'editar' : 'crear', 'Tercero', form.nombre))
      onSaved()
    } catch (err) {
      setError(parseApiError(err))
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
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-700 text-sm whitespace-pre-line">{error}</p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label flex items-center gap-1">
                Tipo
                <HelpIcon text="Cliente: vende a él. Proveedor: le compra a él. Ambos: es cliente y proveedor al mismo tiempo." />
              </label>
              <select className="input" value={form.tipo} onChange={(e) => set('tipo', e.target.value)}>
                <option value="cliente">Cliente</option>
                <option value="proveedor">Proveedor</option>
                <option value="ambos">Ambos</option>
              </select>
            </div>
            <div>
              <label className="label flex items-center gap-1">
                Persona
                <HelpIcon text="Natural: persona física (cédula). Jurídica: empresa o sociedad (NIT con dígito verificador)." />
              </label>
              <select className="input" value={form.tipo_persona} onChange={(e) => set('tipo_persona', e.target.value)}>
                <option value="natural">Natural</option>
                <option value="juridica">Jurídica</option>
              </select>
            </div>
          </div>
          <div>
            <label className="label">Nombre / Razón social *</label>
            <input className="input" value={form.nombre} onChange={(e) => set('nombre', e.target.value)} required placeholder="Ej: Comerciales López S.A.S." />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <NitInput value={form.nit} onChange={(v) => set('nit', v)} />
            <div>
              <label className="label">Teléfono</label>
              <input className="input" value={form.telefono} onChange={(e) => set('telefono', e.target.value)} placeholder="Ej: 3001234567" />
            </div>
          </div>
          <div>
            <label className="label">Email</label>
            <input className="input" type="email" value={form.email} onChange={(e) => set('email', e.target.value)} placeholder="correo@empresa.com" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Ciudad</label>
              <input className="input" value={form.ciudad} onChange={(e) => set('ciudad', e.target.value)} placeholder="Ej: Bogotá" />
            </div>
            <div>
              <label className="label">Dirección</label>
              <input className="input" value={form.direccion} onChange={(e) => set('direccion', e.target.value)} placeholder="Calle 12 # 34-56" />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? (
                <span className="flex items-center gap-2"><span className="animate-spin h-3 w-3 border-b-2 border-white rounded-full inline-block" />Guardando…</span>
              ) : 'Guardar'}
            </button>
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
  const toast = useToast()
  const confirm = useConfirm()

  const load = () => {
    setLoading(true)
    const params = new URLSearchParams({ page_size: 200 })
    if (search) params.set('search', search)
    if (tipo) params.set('tipo', tipo)
    api.get(`/terceros/?${params}`).then(({ data: d }) => setData(d.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [search, tipo])

  const deactivate = async (tercero) => {
    const ok = await confirm({
      title: 'Desactivar tercero',
      message: `¿Está seguro que desea desactivar a "${tercero.nombre}"? No podrá usarlo en nuevas facturas mientras esté inactivo.`,
      confirmLabel: 'Desactivar',
      danger: true,
    })
    if (!ok) return
    try {
      await api.patch(`/terceros/${tercero.id}/`, { activo: false })
      toast.success(`Tercero "${tercero.nombre}" desactivado correctamente.`)
      load()
    } catch (err) {
      toast.error(parseApiError(err))
    }
  }

  const exportar = async () => {
    try {
      await descargarExcel('/terceros/exportar/', 'terceros.xlsx')
      toast.success(successMessage('exportar', 'Terceros'))
    } catch {
      toast.error('No se pudo exportar. Intente de nuevo.')
    }
  }

  return (
    <div className="space-y-4">
      {modal !== undefined && modal !== false && (
        <Modal item={modal === true ? null : modal} onClose={() => setModal(false)} onSaved={() => { setModal(false); load() }} />
      )}

      <div className="flex flex-wrap justify-between items-center gap-2">
        <h1 className="text-2xl font-bold text-slate-800">Terceros</h1>
        <div className="flex gap-2">
          <button className="btn-excel" onClick={exportar}>⬇ Excel</button>
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
              <tr><td colSpan={7} className="td text-center py-12">
                <div className="flex items-center justify-center gap-2 text-gray-400">
                  <div className="animate-spin h-4 w-4 border-b-2 border-blue-600 rounded-full" />
                  Cargando terceros…
                </div>
              </td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={7}>
                <EmptyState
                  icon="👥"
                  title={search || tipo ? 'Sin resultados para la búsqueda' : 'Aún no tiene terceros registrados'}
                  description={search || tipo ? 'Intente con otros filtros.' : 'Cree clientes y proveedores para poder facturar.'}
                  action={!search && !tipo ? () => setModal(true) : undefined}
                  actionLabel="+ Nuevo Tercero"
                />
              </td></tr>
            ) : data.map((t) => (
              <tr key={t.id} className="hover:bg-gray-50">
                <td className="td font-medium">{t.nombre}</td>
                <td className="td font-mono text-xs">
                  {t.nit}
                  {t.nit_valido === false && <span className="ml-1 text-red-500" title="NIT inválido">❌</span>}
                  {t.nit_valido === true && <span className="ml-1 text-green-500" title="NIT válido">✅</span>}
                </td>
                <td className="td"><span className={tipoBadge[t.tipo]}>{t.tipo}</span></td>
                <td className="td">{t.ciudad}</td>
                <td className="td">{t.telefono}</td>
                <td className="td"><span className={t.activo ? 'badge-green' : 'badge-red'}>{t.activo ? 'Activo' : 'Inactivo'}</span></td>
                <td className="td">
                  <div className="flex gap-2">
                    <button className="text-blue-600 hover:underline text-xs" onClick={() => setModal(t)}>Editar</button>
                    {t.activo && <button className="text-red-500 hover:underline text-xs" onClick={() => deactivate(t)}>Desactivar</button>}
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
