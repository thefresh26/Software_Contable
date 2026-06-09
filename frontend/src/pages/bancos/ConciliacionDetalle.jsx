import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
const hoyISO = () => new Date().toISOString().slice(0, 10)

const TIPOS_PARTIDA = [
  { value: 'cheque_girado', label: 'Cheque Girado No Cobrado', afecta: 'extracto', signo: -1 },
  { value: 'deposito_transito', label: 'Depósito en Tránsito', afecta: 'extracto', signo: 1 },
  { value: 'nota_debito', label: 'Nota Débito Banco No Registrada', afecta: 'libros', signo: -1 },
  { value: 'nota_credito', label: 'Nota Crédito Banco No Registrada', afecta: 'libros', signo: 1 },
  { value: 'error_libros', label: 'Error en Libros', afecta: 'libros', signo: 1 },
  { value: 'error_banco', label: 'Error del Banco', afecta: 'extracto', signo: 1 },
  { value: 'otro', label: 'Otro', afecta: 'extracto', signo: 1 },
]

const EMPTY_PARTIDA = { tipo: 'deposito_transito', descripcion: '', fecha: hoyISO(), valor: '', afecta: 'extracto' }

function FormPartida({ conciliacionId, onAdded }) {
  const [form, setForm] = useState(EMPTY_PARTIDA)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const onTipoChange = (tipo) => {
    const meta = TIPOS_PARTIDA.find((t) => t.value === tipo)
    setForm((f) => ({ ...f, tipo, afecta: meta.afecta }))
  }

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    const meta = TIPOS_PARTIDA.find((t) => t.value === form.tipo)
    try {
      await api.post(`/bancos/conciliaciones/${conciliacionId}/partidas/`, {
        ...form,
        valor: Math.abs(Number(form.valor)) * meta.signo,
      })
      setForm(EMPTY_PARTIDA)
      onAdded()
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error al agregar partida')) }
    finally { setSaving(false) }
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label">Tipo</label>
          <select className="input" value={form.tipo} onChange={(e) => onTipoChange(e.target.value)}>
            {TIPOS_PARTIDA.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
        <div><label className="label">Fecha *</label><input className="input" type="date" value={form.fecha} onChange={(e) => set('fecha', e.target.value)} required /></div>
      </div>
      <div><label className="label">Descripción *</label><input className="input" value={form.descripcion} onChange={(e) => set('descripcion', e.target.value)} required /></div>
      <div className="grid grid-cols-2 gap-3 items-end">
        <div><label className="label">Valor (positivo) *</label><input className="input" type="number" min="0" step="1" value={form.valor} onChange={(e) => set('valor', e.target.value)} required /></div>
        <p className="text-xs text-gray-400 pb-2">Afecta: <span className="font-medium capitalize">{form.afecta}</span></p>
      </div>
      <button type="submit" className="btn-primary text-sm" disabled={saving}>{saving ? 'Agregando…' : '+ Agregar partida'}</button>
    </form>
  )
}

export default function ConciliacionDetalle() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [conc, setConc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [autoLoading, setAutoLoading] = useState(false)
  const [finLoading, setFinLoading] = useState(false)
  const [mensaje, setMensaje] = useState('')

  const cargar = () => {
    setLoading(true)
    api.get(`/bancos/conciliaciones/${id}/`).then(({ data }) => setConc(data)).finally(() => setLoading(false))
  }

  useEffect(() => { cargar() }, [id])

  const conciliarAuto = async () => {
    setAutoLoading(true); setMensaje('')
    try {
      const { data } = await api.post(`/bancos/conciliaciones/${id}/conciliar-automatico/`)
      setMensaje(`Se conciliaron automáticamente ${data.conciliados} movimiento(s).`)
      cargar()
    } catch { setMensaje('No se pudo ejecutar la conciliación automática') }
    finally { setAutoLoading(false) }
  }

  const eliminarPartida = async (partidaId) => {
    await api.delete(`/bancos/partidas/${partidaId}/`)
    cargar()
  }

  const finalizar = async () => {
    setFinLoading(true); setMensaje('')
    try {
      const { data } = await api.post(`/bancos/conciliaciones/${id}/finalizar/`)
      setConc(data)
      setMensaje('Conciliación finalizada correctamente.')
    } catch (err) { setMensaje(err.response?.data?.detail || 'No se pudo finalizar la conciliación') }
    finally { setFinLoading(false) }
  }

  if (loading || !conc) return <div className="flex justify-center pt-20"><div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" /></div>

  const partidas = conc.partidas || []
  const sumaExtracto = partidas.filter((p) => p.afecta === 'extracto').reduce((acc, p) => acc + Number(p.valor), 0)
  const sumaLibros = partidas.filter((p) => p.afecta === 'libros').reduce((acc, p) => acc + Number(p.valor), 0)
  const saldoExtractoAjustado = Number(conc.saldo_extracto) + sumaExtracto
  const saldoLibrosAjustado = Number(conc.saldo_libros) + sumaLibros
  const diferenciaAjustada = (saldoExtractoAjustado - saldoLibrosAjustado)
  const cuadra = Math.abs(diferenciaAjustada) < 0.01
  const finalizada = conc.estado === 'finalizada'

  return (
    <div className="space-y-4">
      <div>
        <Link to={`/bancos/extractos/${conc.extracto}`} className="text-xs text-blue-600 hover:underline">← Volver al extracto</Link>
        <div className="flex justify-between items-start mt-1">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Conciliación — {conc.cuenta_nombre}</h1>
            <p className="text-sm text-gray-500">Período: {conc.periodo}</p>
          </div>
          <span className={finalizada ? 'badge-green' : 'badge-yellow'}>{finalizada ? 'Finalizada' : 'Borrador'}</span>
        </div>
      </div>

      {mensaje && <div className="p-3 bg-blue-50 border border-blue-200 text-blue-700 rounded-md text-sm">{mensaje}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card space-y-2">
          <h2 className="font-semibold text-gray-700">Saldo según extracto</h2>
          <div className="flex justify-between text-sm"><span>Saldo extracto</span><span className="font-medium">{fmt(conc.saldo_extracto)}</span></div>
          <div className="flex justify-between text-sm text-gray-500"><span>(+/−) Partidas que afectan extracto</span><span>{fmt(sumaExtracto)}</span></div>
          <div className="flex justify-between text-sm font-bold border-t pt-2"><span>Saldo extracto ajustado</span><span>{fmt(saldoExtractoAjustado)}</span></div>
        </div>
        <div className="card space-y-2">
          <h2 className="font-semibold text-gray-700">Saldo según libros</h2>
          <div className="flex justify-between text-sm"><span>Saldo libros</span><span className="font-medium">{fmt(conc.saldo_libros)}</span></div>
          <div className="flex justify-between text-sm text-gray-500"><span>(+/−) Partidas que afectan libros</span><span>{fmt(sumaLibros)}</span></div>
          <div className="flex justify-between text-sm font-bold border-t pt-2"><span>Saldo libros ajustado</span><span>{fmt(saldoLibrosAjustado)}</span></div>
        </div>
      </div>

      <div className={`card flex justify-between items-center ${cuadra ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
        <div>
          <p className="text-xs uppercase text-gray-500">Diferencia</p>
          <p className={`text-xl font-bold ${cuadra ? 'text-green-700' : 'text-red-600'}`}>{fmt(diferenciaAjustada)}</p>
        </div>
        <span className={cuadra ? 'badge-green' : 'badge-red'}>{cuadra ? 'CONCILIADO ✓' : 'NO CONCILIADO'}</span>
      </div>

      <div className="flex flex-wrap gap-3">
        <button className="btn-secondary" onClick={conciliarAuto} disabled={autoLoading || finalizada}>
          {autoLoading ? 'Procesando…' : 'Conciliación automática'}
        </button>
        <button className="btn-primary" onClick={finalizar} disabled={finLoading || finalizada || !cuadra}>
          {finLoading ? 'Finalizando…' : 'Finalizar conciliación'}
        </button>
        <button className="btn-secondary" onClick={() => navigate(`/bancos/conciliaciones/${id}/reporte`)}>Ver reporte</button>
        <a href={`/api/bancos/conciliaciones/${id}/reporte/?formato=pdf`} target="_blank" rel="noreferrer" className="btn-secondary inline-flex items-center">
          Descargar PDF
        </a>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-3">Agregar partida en tránsito / diferencia</h2>
          {finalizada ? (
            <p className="text-sm text-gray-400">La conciliación está finalizada; no se pueden agregar partidas.</p>
          ) : (
            <FormPartida conciliacionId={id} onAdded={cargar} />
          )}
        </div>
        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 border-b"><h2 className="font-semibold text-gray-700">Partidas registradas ({partidas.length})</h2></div>
          <div className="divide-y divide-gray-100 max-h-[420px] overflow-y-auto">
            {partidas.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-6">Sin partidas registradas</p>
            ) : partidas.map((p) => (
              <div key={p.id} className="px-4 py-3 flex justify-between items-start text-sm">
                <div>
                  <p className="font-medium">{p.descripcion}</p>
                  <p className="text-xs text-gray-400">{p.fecha} — {TIPOS_PARTIDA.find((t) => t.value === p.tipo)?.label || p.tipo} — afecta {p.afecta}</p>
                </div>
                <div className="text-right">
                  <p className={Number(p.valor) < 0 ? 'text-red-600 font-medium' : 'text-green-700 font-medium'}>{fmt(p.valor)}</p>
                  {!finalizada && <button className="text-xs text-red-600 hover:underline" onClick={() => eliminarPartida(p.id)}>Eliminar</button>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
