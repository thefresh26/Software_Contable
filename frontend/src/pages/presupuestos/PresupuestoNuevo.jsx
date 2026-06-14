import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/client'

export default function PresupuestoNuevo() {
  const navigate = useNavigate()
  const [nombre, setNombre] = useState('')
  const [inicio, setInicio] = useState('')
  const [fin, setFin] = useState('')
  const [items, setItems] = useState([{ cuenta: '', descripcion: '', valor_presupuestado: 0 }])
  const [cuentas, setCuentas] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/contabilidad/cuentas/?page_size=500&permite_movimiento=true').then(({ data }) => setCuentas(data.results || []))
  }, [])

  const setItem = (i, k, v) => setItems(prev => { const n = [...prev]; n[i] = { ...n[i], [k]: v }; return n })
  const addItem = () => setItems(p => [...p, { cuenta: '', descripcion: '', valor_presupuestado: 0 }])
  const removeItem = (i) => setItems(p => p.filter((_, idx) => idx !== i))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      await api.post('/presupuestos/presupuestos/', { nombre, periodo_inicio: inicio, periodo_fin: fin, items })
      navigate('/presupuestos')
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  const totalPresupuestado = items.reduce((a, i) => a + Number(i.valor_presupuestado || 0), 0)

  return (
    <div className="max-w-3xl space-y-5">
      <h1 className="text-2xl font-bold text-slate-800">Nuevo Presupuesto</h1>
      {error && <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">{error}</div>}
      <form onSubmit={submit} className="space-y-5">
        <div className="card grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-3"><label className="label">Nombre *</label><input className="input" value={nombre} onChange={e => setNombre(e.target.value)} required /></div>
          <div><label className="label">Período inicio *</label><input className="input" type="date" value={inicio} onChange={e => setInicio(e.target.value)} required /></div>
          <div><label className="label">Período fin *</label><input className="input" type="date" value={fin} onChange={e => setFin(e.target.value)} required /></div>
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="px-5 py-3 bg-gray-50 border-b flex justify-between items-center">
            <h2 className="font-semibold text-sm text-gray-700">Líneas de Presupuesto</h2>
            <button type="button" onClick={addItem} className="text-blue-600 text-sm hover:underline">+ Agregar línea</button>
          </div>
          <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b"><tr><th className="th">Cuenta</th><th className="th">Descripción</th><th className="th w-40">Valor Presupuestado</th><th className="th w-8" /></tr></thead>
            <tbody className="divide-y">
              {items.map((item, i) => (
                <tr key={i}>
                  <td className="px-3 py-2">
                    <select className="input text-xs" value={item.cuenta} onChange={e => setItem(i, 'cuenta', e.target.value)} required>
                      <option value="">Seleccionar…</option>
                      {cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} — {c.nombre}</option>)}
                    </select>
                  </td>
                  <td className="px-3 py-2"><input className="input text-xs" value={item.descripcion} onChange={e => setItem(i, 'descripcion', e.target.value)} required /></td>
                  <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0" step="1" value={item.valor_presupuestado} onChange={e => setItem(i, 'valor_presupuestado', e.target.value)} /></td>
                  <td className="px-3 py-2">{items.length > 1 && <button type="button" onClick={() => removeItem(i)} className="text-red-400 hover:text-red-600">✕</button>}</td>
                </tr>
              ))}
              <tr className="bg-gray-50 font-semibold">
                <td colSpan={2} className="px-4 py-2 text-right text-xs text-gray-500">TOTAL PRESUPUESTADO</td>
                <td className="px-4 py-2 text-right text-sm">{Number(totalPresupuestado).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })}</td>
                <td />
              </tr>
            </tbody>
          </table>
          </div>
        </div>

        <div className="flex gap-3">
          <button type="button" onClick={() => navigate('/presupuestos')} className="btn-secondary">Cancelar</button>
          <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Crear Presupuesto'}</button>
        </div>
      </form>
    </div>
  )
}
