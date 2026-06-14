import { useEffect, useState } from 'react'
import api from '../../api/client'
import { descargarExcel } from '../../utils/excel'

function ModalDescuento({ cuenta, onClose, onSaved }) {
  const [form, setForm] = useState({ porcentaje: '', dias_plazo: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      await api.post(`/cartera/por-cobrar/${cuenta.id}/configurar-descuento/`, form)
      onSaved()
    } catch (err) { setError(err.response?.data?.error || 'Error') }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm">
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="font-semibold">Configurar Descuento Pronto Pago</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <p className="text-sm text-gray-500">Pendiente: <strong>{Number(cuenta.valor_pendiente).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })}</strong></p>
          <div>
            <label className="label">% de Descuento *</label>
            <input className="input" type="number" min="0.01" max="100" step="0.01" value={form.porcentaje} onChange={e => setForm(f => ({ ...f, porcentaje: e.target.value }))} required />
          </div>
          <div>
            <label className="label">Días de plazo *</label>
            <input className="input" type="number" min="1" value={form.dias_plazo} onChange={e => setForm(f => ({ ...f, dias_plazo: e.target.value }))} required />
            <p className="text-xs text-gray-400 mt-0.5">Si el cliente paga en este plazo, se aplica el descuento.</p>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Configurar'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
const estadoBadge = { pendiente: 'badge-yellow', parcial: 'badge-gray', pagada: 'badge-green', vencida: 'badge-red' }

function ModalPago({ cuenta, tipo, onClose, onSaved }) {
  const [form, setForm] = useState({ fecha: new Date().toISOString().slice(0, 10), valor: '', medio_pago: 'transferencia', referencia: '', observacion: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      await api.post(`/cartera/${tipo}/${cuenta.id}/registrar-pago/`, form)
      onSaved()
    } catch (err) { setError(err.response?.data?.error || JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="font-semibold">Registrar Pago</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <p className="text-sm text-gray-500">Pendiente: <strong>{fmt(cuenta.valor_pendiente)}</strong></p>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Fecha *</label><input className="input" type="date" value={form.fecha} onChange={e => set('fecha', e.target.value)} required /></div>
            <div><label className="label">Valor *</label><input className="input" type="number" min="0.01" step="0.01" max={cuenta.valor_pendiente} value={form.valor} onChange={e => set('valor', e.target.value)} required /></div>
          </div>
          <div>
            <label className="label">Medio de pago</label>
            <select className="input" value={form.medio_pago} onChange={e => set('medio_pago', e.target.value)}>
              <option value="transferencia">Transferencia</option>
              <option value="efectivo">Efectivo</option>
              <option value="cheque">Cheque</option>
            </select>
          </div>
          <div><label className="label">Referencia</label><input className="input" value={form.referencia} onChange={e => set('referencia', e.target.value)} /></div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Registrar Pago'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function PorCobrar() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [estadoF, setEstadoF] = useState('')
  const [modal, setModal] = useState(null)
  const [modalDescuento, setModalDescuento] = useState(null)

  const load = () => {
    setLoading(true)
    const p = new URLSearchParams({ page_size: 200 })
    if (estadoF) p.set('estado', estadoF)
    api.get(`/cartera/por-cobrar/?${p}`).then(({ data: d }) => setData(d.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [estadoF])

  return (
    <div className="space-y-4">
      {modal && <ModalPago cuenta={modal} tipo="por-cobrar" onClose={() => setModal(null)} onSaved={() => { setModal(null); load() }} />}
      {modalDescuento && <ModalDescuento cuenta={modalDescuento} onClose={() => setModalDescuento(null)} onSaved={() => { setModalDescuento(null); load() }} />}
      <div className="flex flex-wrap justify-between items-center gap-2">
        <h1 className="text-2xl font-bold text-slate-800">Cuentas por Cobrar</h1>
        <button className="btn-excel" onClick={() => descargarExcel('/cartera/exportar/por-cobrar/', 'por_cobrar.xlsx').catch(() => alert('Error al exportar'))}>⬇ Excel</button>
      </div>
      <div className="flex gap-3">
        <select className="input w-40" value={estadoF} onChange={e => setEstadoF(e.target.value)}>
          <option value="">Todos</option>
          {['pendiente', 'parcial', 'pagada', 'vencida'].map(e => <option key={e} value={e}>{e}</option>)}
        </select>
      </div>
      <div className="card p-0 overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b"><tr><th className="th">Factura</th><th className="th">Cliente</th><th className="th">Vencimiento</th><th className="th text-right">Total</th><th className="th text-right">Pagado</th><th className="th text-right">Pendiente</th><th className="th">Estado</th><th className="th" /></tr></thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? <tr><td colSpan={8} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            : data.length === 0 ? <tr><td colSpan={8} className="td text-center py-8 text-gray-400">Sin registros</td></tr>
            : data.map(c => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="td font-mono text-xs">{c.factura_numero}</td>
                <td className="td">{c.tercero_nombre}</td>
                <td className="td">{c.fecha_vencimiento}</td>
                <td className="td text-right">{fmt(c.valor_total)}</td>
                <td className="td text-right text-green-600">{fmt(c.valor_pagado)}</td>
                <td className="td text-right font-semibold">{fmt(c.valor_pendiente)}</td>
                <td className="td">
                  <div className="flex flex-col gap-0.5">
                    <span className={estadoBadge[c.estado]}>{c.estado}</span>
                    {c.descuentos?.some(d => !d.aplicado) && (
                      <span className="text-xs text-green-600 font-medium">💚 Dto. disponible</span>
                    )}
                  </div>
                </td>
                <td className="td">
                  {c.estado !== 'pagada' && (
                    <div className="flex flex-col gap-1">
                      <button className="text-blue-600 hover:underline text-xs" onClick={() => setModal(c)}>Registrar Pago</button>
                      <button className="text-green-600 hover:underline text-xs" onClick={() => setModalDescuento(c)}>+ Descuento</button>
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
