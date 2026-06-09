import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

function ModalConciliar({ movimiento, onClose, onDone }) {
  const [asientoId, setAsientoId] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      await api.post(`/bancos/movimientos/${movimiento.id}/conciliar/`, { asiento_id: Number(asientoId) })
      onDone()
    } catch (err) { setError(err.response?.data?.asiento_id?.[0] || err.response?.data?.detail || 'Error al conciliar') }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="font-semibold">Conciliar movimiento</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="text-sm text-gray-600 bg-gray-50 rounded-md p-3">
            <p className="font-medium">{movimiento.descripcion}</p>
            <p className="text-xs text-gray-400">{movimiento.fecha} — {movimiento.tipo} — {fmt(movimiento.valor)}</p>
          </div>
          <div>
            <label className="label">ID del asiento contable *</label>
            <input className="input" type="number" min="1" value={asientoId} onChange={(e) => setAsientoId(e.target.value)} required />
            <p className="text-xs text-gray-400 mt-1">Ingrese el número del asiento contable que corresponde a este movimiento.</p>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Conciliando…' : 'Conciliar'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function ExtractoDetalle() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [extracto, setExtracto] = useState(null)
  const [movimientos, setMovimientos] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalMov, setModalMov] = useState(null)
  const [iniciando, setIniciando] = useState(false)
  const [mensaje, setMensaje] = useState('')

  const cargar = () => {
    setLoading(true)
    Promise.all([
      api.get(`/bancos/extractos/${id}/`),
      api.get(`/bancos/extractos/${id}/movimientos/`),
    ]).then(([e, m]) => { setExtracto(e.data); setMovimientos(m.data) }).finally(() => setLoading(false))
  }

  useEffect(() => { cargar() }, [id])

  const desconciliar = async (mov) => {
    await api.post(`/bancos/movimientos/${mov.id}/desconciliar/`)
    cargar()
  }

  const irAConciliacion = async () => {
    setIniciando(true); setMensaje('')
    try {
      const { data: existentes } = await api.get(`/bancos/conciliaciones/?extracto=${id}&page_size=1`)
      const existente = (existentes.results || [])[0]
      if (existente) { navigate(`/bancos/conciliaciones/${existente.id}`); return }
      const { data } = await api.post('/bancos/conciliaciones/', { extracto: id })
      navigate(`/bancos/conciliaciones/${data.id}`)
    } catch (err) {
      setMensaje(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'No se pudo iniciar la conciliación')
    } finally { setIniciando(false) }
  }

  if (loading || !extracto) return <div className="flex justify-center pt-20"><div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" /></div>

  const conciliados = movimientos.filter((m) => m.conciliado).length

  return (
    <div className="space-y-4">
      <div>
        <Link to="/bancos/cuentas" className="text-xs text-blue-600 hover:underline">← Volver a cuentas bancarias</Link>
        <div className="flex justify-between items-start mt-1">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Extracto — {extracto.cuenta_nombre}</h1>
            <p className="text-sm text-gray-500">{extracto.periodo_inicio} a {extracto.periodo_fin}</p>
          </div>
          <span className={extracto.estado === 'conciliado' ? 'badge-green' : extracto.estado === 'parcial' ? 'badge-yellow' : 'badge-gray'}>{extracto.estado}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card"><p className="text-xs text-gray-500">Saldo inicial</p><p className="text-lg font-bold text-slate-800">{fmt(extracto.saldo_inicial_extracto)}</p></div>
        <div className="card"><p className="text-xs text-gray-500">Saldo final</p><p className="text-lg font-bold text-slate-800">{fmt(extracto.saldo_final_extracto)}</p></div>
        <div className="card"><p className="text-xs text-gray-500">Total débitos</p><p className="text-lg font-bold text-red-600">{fmt(extracto.total_debitos)}</p></div>
        <div className="card"><p className="text-xs text-gray-500">Total créditos</p><p className="text-lg font-bold text-green-700">{fmt(extracto.total_creditos)}</p></div>
      </div>

      <div className="card flex justify-between items-center">
        <p className="text-sm text-gray-600">
          <span className="font-semibold">{conciliados}</span> de <span className="font-semibold">{movimientos.length}</span> movimientos conciliados
        </p>
        <div className="flex items-center gap-3">
          {mensaje && <p className="text-xs text-red-600">{mensaje}</p>}
          <button className="btn-primary text-sm" onClick={irAConciliacion} disabled={iniciando}>
            {iniciando ? 'Cargando…' : 'Iniciar / ver conciliación'}
          </button>
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="th">Fecha</th><th className="th">Descripción</th><th className="th">Tipo</th>
              <th className="th text-right">Valor</th><th className="th text-right">Saldo</th>
              <th className="th">Asiento</th><th className="th">Estado</th><th className="th" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {movimientos.map((m) => (
              <tr key={m.id} className="hover:bg-gray-50">
                <td className="td whitespace-nowrap">{m.fecha}</td>
                <td className="td">{m.descripcion}</td>
                <td className="td capitalize">{m.tipo}</td>
                <td className={`td text-right ${m.tipo === 'debito' ? 'text-red-600' : 'text-green-700'}`}>{fmt(m.valor)}</td>
                <td className="td text-right text-gray-500">{fmt(m.saldo)}</td>
                <td className="td text-gray-500 text-xs">{m.asiento_contable ? `#${m.asiento_contable} — ${m.asiento_descripcion || ''}` : '—'}</td>
                <td className="td"><span className={m.conciliado ? 'badge-green' : 'badge-gray'}>{m.conciliado ? 'Conciliado' : 'Pendiente'}</span></td>
                <td className="td">
                  {m.conciliado ? (
                    <button className="text-red-600 hover:underline text-xs" onClick={() => desconciliar(m)}>Desconciliar</button>
                  ) : (
                    <button className="text-blue-600 hover:underline text-xs" onClick={() => setModalMov(m)}>Conciliar</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modalMov && (
        <ModalConciliar movimiento={modalMov} onClose={() => setModalMov(null)} onDone={() => { setModalMov(null); cargar() }} />
      )}
    </div>
  )
}
