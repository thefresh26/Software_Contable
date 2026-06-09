import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

const EMPTY = { nombre: '', banco: '', numero_cuenta: '', tipo: 'corriente', cuenta_contable: '', saldo_inicial: 0 }

function ModalCuenta({ onClose, onSaved }) {
  const [form, setForm] = useState(EMPTY)
  const [cuentasPUC, setCuentasPUC] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  useEffect(() => {
    api.get('/contabilidad/puc/?page_size=500&permite_movimiento=true').then(({ data }) => setCuentasPUC(data.results || []))
  }, [])

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      await api.post('/bancos/cuentas/', form)
      onSaved()
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center px-6 py-4 border-b sticky top-0 bg-white">
          <h2 className="font-semibold">Nueva Cuenta Bancaria</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div><label className="label">Nombre *</label><input className="input" value={form.nombre} onChange={(e) => set('nombre', e.target.value)} required /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Banco *</label><input className="input" value={form.banco} onChange={(e) => set('banco', e.target.value)} required /></div>
            <div><label className="label">Número de cuenta *</label><input className="input" value={form.numero_cuenta} onChange={(e) => set('numero_cuenta', e.target.value)} required /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Tipo</label>
              <select className="input" value={form.tipo} onChange={(e) => set('tipo', e.target.value)}>
                <option value="corriente">Cuenta Corriente</option>
                <option value="ahorros">Cuenta de Ahorros</option>
                <option value="fiduciaria">Cuenta Fiduciaria</option>
              </select>
            </div>
            <div><label className="label">Saldo inicial</label><input className="input" type="number" min="0" step="1" value={form.saldo_inicial} onChange={(e) => set('saldo_inicial', e.target.value)} /></div>
          </div>
          <div>
            <label className="label">Cuenta contable (PUC) *</label>
            <select className="input" value={form.cuenta_contable} onChange={(e) => set('cuenta_contable', e.target.value)} required>
              <option value="">Seleccionar…</option>
              {cuentasPUC.map((c) => <option key={c.id} value={c.id}>{c.codigo} — {c.nombre}</option>)}
            </select>
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

function ModalImportar({ cuenta, onClose, onImported }) {
  const [archivo, setArchivo] = useState(null)
  const [saldoInicial, setSaldoInicial] = useState(cuenta.saldo_actual || 0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef()

  const submit = async (e) => {
    e.preventDefault()
    if (!archivo) return
    setLoading(true); setError('')
    try {
      const fd = new FormData()
      fd.append('archivo', archivo)
      fd.append('cuenta_id', cuenta.id)
      fd.append('saldo_inicial', saldoInicial)
      const { data } = await api.post('/bancos/extractos/importar/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      onImported(data)
    } catch (err) { setError(err.response?.data?.error || JSON.stringify(err.response?.data) || 'Error al importar') }
    finally { setLoading(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="font-semibold">Importar extracto — {cuenta.nombre}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div>
            <label className="label">Archivo (.xlsx, .xls o .csv)</label>
            <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" onChange={(e) => setArchivo(e.target.files[0])}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
          </div>
          <div><label className="label">Saldo inicial del período</label><input className="input" type="number" step="1" value={saldoInicial} onChange={(e) => setSaldoInicial(e.target.value)} /></div>
          <p className="text-xs text-gray-500">Columnas esperadas: fecha | descripcion | referencia | debitos | creditos | saldo</p>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" className="btn-primary" disabled={loading || !archivo}>{loading ? 'Importando…' : 'Importar'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

function CuentaCard({ cuenta, onChanged }) {
  const navigate = useNavigate()
  const [saldo, setSaldo] = useState(null)
  const [extractos, setExtractos] = useState(null)
  const [showExtractos, setShowExtractos] = useState(false)
  const [showImportar, setShowImportar] = useState(false)

  useEffect(() => {
    api.get(`/bancos/cuentas/${cuenta.id}/saldo/`).then(({ data }) => setSaldo(data)).catch(() => {})
  }, [cuenta.id])

  const cargarExtractos = () => {
    setShowExtractos((v) => !v)
    if (!extractos) {
      api.get(`/bancos/extractos/?cuenta=${cuenta.id}&page_size=100`).then(({ data }) => setExtractos(data.results || []))
    }
  }

  const recargarExtractos = () => {
    api.get(`/bancos/extractos/?cuenta=${cuenta.id}&page_size=100`).then(({ data }) => setExtractos(data.results || []))
  }

  return (
    <div className="card space-y-3">
      {showImportar && (
        <ModalImportar cuenta={cuenta} onClose={() => setShowImportar(false)} onImported={(data) => {
          setShowImportar(false); recargarExtractos(); setShowExtractos(true)
          navigate(`/bancos/extractos/${data.extracto_id}`)
        }} />
      )}
      <div className="flex justify-between items-start">
        <div>
          <p className="font-semibold text-slate-800">{cuenta.nombre}</p>
          <p className="text-xs text-gray-500">{cuenta.banco} — {cuenta.numero_cuenta}</p>
          <p className="text-xs text-gray-400 capitalize">{cuenta.tipo} · {cuenta.cuenta_contable_codigo} {cuenta.cuenta_contable_nombre}</p>
        </div>
        <span className={cuenta.activa ? 'badge-green' : 'badge-red'}>{cuenta.activa ? 'Activa' : 'Inactiva'}</span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-sm border-t pt-3">
        <div><p className="text-xs text-gray-400">Saldo libros</p><p className="font-semibold">{saldo ? fmt(saldo.saldo_libros) : '—'}</p></div>
        <div><p className="text-xs text-gray-400">Saldo extracto</p><p className="font-semibold">{saldo && saldo.saldo_extracto != null ? fmt(saldo.saldo_extracto) : '—'}</p></div>
        <div><p className="text-xs text-gray-400">Diferencia</p><p className={`font-semibold ${saldo && Number(saldo.diferencia) !== 0 ? 'text-red-600' : 'text-green-700'}`}>{saldo && saldo.diferencia != null ? fmt(saldo.diferencia) : '—'}</p></div>
      </div>

      <div className="flex gap-2 pt-1">
        <button className="btn-secondary text-xs" onClick={cargarExtractos}>{showExtractos ? 'Ocultar extractos' : 'Ver extractos'}</button>
        <button className="btn-secondary text-xs" onClick={() => setShowImportar(true)}>Importar extracto</button>
      </div>

      {showExtractos && (
        <div className="border-t pt-3 space-y-1">
          {!extractos ? (
            <p className="text-xs text-gray-400">Cargando…</p>
          ) : extractos.length === 0 ? (
            <p className="text-xs text-gray-400">Sin extractos importados</p>
          ) : extractos.map((ex) => (
            <button key={ex.id} onClick={() => navigate(`/bancos/extractos/${ex.id}`)}
              className="w-full text-left text-xs px-3 py-2 rounded-md hover:bg-gray-50 flex justify-between items-center border border-gray-100">
              <span>{ex.periodo_inicio} a {ex.periodo_fin} — {ex.movimientos_count} movimientos</span>
              <span className="flex items-center gap-2">
                <span className="text-gray-500">{fmt(ex.saldo_final_extracto)}</span>
                <span className={ex.estado === 'conciliado' ? 'badge-green' : ex.estado === 'parcial' ? 'badge-yellow' : 'badge-gray'}>{ex.estado}</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function CuentasBancarias() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(false)

  const load = () => {
    setLoading(true)
    api.get('/bancos/cuentas/?page_size=200').then(({ data: d }) => setData(d.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  return (
    <div className="space-y-4">
      {modal && <ModalCuenta onClose={() => setModal(false)} onSaved={() => { setModal(false); load() }} />}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Cuentas Bancarias</h1>
        <button className="btn-primary" onClick={() => setModal(true)}>+ Nueva Cuenta</button>
      </div>

      {loading ? (
        <p className="text-center text-gray-400 py-8">Cargando…</p>
      ) : data.length === 0 ? (
        <p className="text-center text-gray-400 py-8">Sin cuentas bancarias registradas</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {data.map((c) => <CuentaCard key={c.id} cuenta={c} onChanged={load} />)}
        </div>
      )}
    </div>
  )
}
