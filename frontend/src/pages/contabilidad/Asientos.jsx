import { useEffect, useState } from 'react'
import api from '../../api/client'
import { descargarExcel } from '../../utils/excel'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
const EMPTY_LINE = { cuenta: '', descripcion: '', debito: 0, credito: 0 }

function ModalAsiento({ cuentas, onClose, onSaved }) {
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10))
  const [desc, setDesc] = useState('')
  const [lines, setLines] = useState([{ ...EMPTY_LINE }, { ...EMPTY_LINE }])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const setLine = (i, k, v) => setLines((prev) => { const n = [...prev]; n[i] = { ...n[i], [k]: v }; return n })
  const addLine = () => setLines((p) => [...p, { ...EMPTY_LINE }])
  const removeLine = (i) => setLines((p) => p.filter((_, idx) => idx !== i))

  const totDeb = lines.reduce((a, l) => a + Number(l.debito || 0), 0)
  const totCre = lines.reduce((a, l) => a + Number(l.credito || 0), 0)
  const cuadrado = Math.abs(totDeb - totCre) < 0.01

  const submit = async (e) => {
    e.preventDefault()
    if (!cuadrado) { setError(`El asiento no está cuadrado. Débitos: ${fmt(totDeb)} / Créditos: ${fmt(totCre)}`); return }
    setSaving(true); setError('')
    try {
      await api.post('/contabilidad/asientos/', { fecha, descripcion: desc, es_manual: true, movimientos: lines })
      onSaved()
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center px-6 py-4 border-b sticky top-0 bg-white">
          <h2 className="font-semibold">Nuevo Asiento Manual</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-4">
          {error && <p className="text-red-600 text-sm bg-red-50 p-2 rounded">{error}</p>}
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">Fecha *</label><input className="input" type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} required /></div>
            <div><label className="label">Descripción *</label><input className="input" value={desc} onChange={(e) => setDesc(e.target.value)} required /></div>
          </div>
          <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr><th className="th">Cuenta</th><th className="th">Descripción</th><th className="th w-28">Débito</th><th className="th w-28">Crédito</th><th className="th w-8" /></tr>
            </thead>
            <tbody className="divide-y">
              {lines.map((l, i) => (
                <tr key={i}>
                  <td className="px-3 py-2">
                    <select className="input text-xs" value={l.cuenta} onChange={(e) => setLine(i, 'cuenta', e.target.value)} required>
                      <option value="">Seleccionar…</option>
                      {cuentas.filter((c) => c.permite_movimiento).map((c) => <option key={c.id} value={c.id}>{c.codigo} — {c.nombre}</option>)}
                    </select>
                  </td>
                  <td className="px-3 py-2"><input className="input text-xs" value={l.descripcion} onChange={(e) => setLine(i, 'descripcion', e.target.value)} /></td>
                  <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0" step="0.01" value={l.debito} onChange={(e) => setLine(i, 'debito', e.target.value)} /></td>
                  <td className="px-3 py-2"><input className="input text-xs text-right" type="number" min="0" step="0.01" value={l.credito} onChange={(e) => setLine(i, 'credito', e.target.value)} /></td>
                  <td className="px-3 py-2">{lines.length > 2 && <button type="button" onClick={() => removeLine(i)} className="text-red-400 hover:text-red-600">✕</button>}</td>
                </tr>
              ))}
              <tr className="bg-gray-50 font-medium">
                <td colSpan={2} className="px-3 py-2 text-right text-xs text-gray-500">TOTALES</td>
                <td className="px-3 py-2 text-right text-sm">{fmt(totDeb)}</td>
                <td className="px-3 py-2 text-right text-sm">{fmt(totCre)}</td>
                <td />
              </tr>
            </tbody>
          </table>
          </div>
          {!cuadrado && <p className="text-red-500 text-xs">⚠ Diferencia: {fmt(Math.abs(totDeb - totCre))}</p>}
          <div className="flex justify-between items-center">
            <button type="button" onClick={addLine} className="text-blue-600 text-sm hover:underline">+ Agregar línea</button>
            <div className="flex gap-2">
              <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
              <button type="submit" className="btn-primary" disabled={saving || !cuadrado}>{saving ? 'Guardando…' : 'Guardar Asiento'}</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Asientos() {
  const [asientos, setAsientos] = useState([])
  const [cuentas, setCuentas] = useState([])
  const [loading, setLoading] = useState(true)
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [modal, setModal] = useState(false)
  const [expanded, setExpanded] = useState(null)

  const load = () => {
    setLoading(true)
    const p = new URLSearchParams({ page_size: 200 })
    if (desde) p.set('desde', desde)
    if (hasta) p.set('hasta', hasta)
    api.get(`/contabilidad/asientos/?${p}`).then(({ data }) => setAsientos(data.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { api.get('/contabilidad/cuentas/?page_size=500').then(({ data }) => setCuentas(data.results || [])) }, [])
  useEffect(() => { load() }, [desde, hasta])

  return (
    <div className="space-y-4">
      {modal && <ModalAsiento cuentas={cuentas} onClose={() => setModal(false)} onSaved={() => { setModal(false); load() }} />}

      <div className="flex flex-wrap justify-between items-center gap-2">
        <h1 className="text-2xl font-bold text-slate-800">Libro Diario</h1>
        <div className="flex gap-2">
          <button className="btn-excel" onClick={() => descargarExcel(`/contabilidad/asientos/exportar-libro-diario/?desde=${desde}&hasta=${hasta}`, 'libro_diario.xlsx').catch(() => alert('Error al exportar'))}>⬇ Excel</button>
          <button className="btn-primary" onClick={() => setModal(true)}>+ Asiento Manual</button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <input type="date" className="input w-40" value={desde} onChange={(e) => setDesde(e.target.value)} />
        <span className="self-center text-gray-400">a</span>
        <input type="date" className="input w-40" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        <button className="btn-secondary" onClick={() => { setDesde(''); setHasta('') }}>Limpiar</button>
      </div>

      <div className="space-y-2">
        {loading ? (
          <div className="card text-center text-gray-400 py-8">Cargando…</div>
        ) : asientos.length === 0 ? (
          <div className="card text-center text-gray-400 py-8">Sin asientos</div>
        ) : asientos.map((a) => (
          <div key={a.id} className="card p-0 overflow-hidden">
            <button
              type="button"
              className="w-full flex justify-between items-center px-5 py-3 hover:bg-gray-50 text-left"
              onClick={() => setExpanded(expanded === a.id ? null : a.id)}
            >
              <div className="flex gap-4 items-center">
                <span className="font-mono text-xs text-gray-400">#{String(a.id).padStart(4, '0')}</span>
                <span className="text-sm font-medium text-gray-800">{a.descripcion}</span>
                {!a.es_manual && <span className="badge-blue text-xs px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded">Auto</span>}
              </div>
              <div className="flex gap-4 items-center">
                <span className="text-sm text-gray-500">{a.fecha}</span>
                <span className="text-xs text-gray-400">{expanded === a.id ? '▲' : '▼'}</span>
              </div>
            </button>
            {expanded === a.id && (
              <div className="border-t overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50"><tr><th className="th">Cuenta</th><th className="th">Descripción</th><th className="th text-right">Débito</th><th className="th text-right">Crédito</th></tr></thead>
                  <tbody className="divide-y divide-gray-100">
                    {(a.movimientos || []).map((m) => (
                      <tr key={m.id}>
                        <td className="td font-mono text-xs">{m.cuenta_codigo} — {m.cuenta_nombre}</td>
                        <td className="td text-gray-500">{m.descripcion}</td>
                        <td className="td text-right">{Number(m.debito) > 0 ? fmt(m.debito) : ''}</td>
                        <td className="td text-right">{Number(m.credito) > 0 ? fmt(m.credito) : ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
