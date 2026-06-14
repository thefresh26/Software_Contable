import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

const estadoBadge = { activo: 'badge-green', depreciado: 'badge-gray', dado_baja: 'badge-red', vendido: 'badge-red' }
const estadoLabel = { activo: 'Activo', depreciado: 'Totalmente Depreciado', dado_baja: 'Dado de Baja', vendido: 'Vendido' }

const hoyISO = () => new Date().toISOString().slice(0, 10)
const periodoActual = () => new Date().toISOString().slice(0, 7)

export default function ActivoDetalle() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [activo, setActivo] = useState(null)
  const [tabla, setTabla] = useState(null)
  const [aplicadas, setAplicadas] = useState([])
  const [loading, setLoading] = useState(true)
  const [aplicando, setAplicando] = useState(false)
  const [mensaje, setMensaje] = useState('')

  const [showBaja, setShowBaja] = useState(false)
  const [bajaForm, setBajaForm] = useState({ fecha: hoyISO(), motivo: '', valor_venta: 0, observaciones: '' })
  const [bajaError, setBajaError] = useState('')
  const [bajaSaving, setBajaSaving] = useState(false)

  const cargar = () => {
    setLoading(true)
    Promise.all([
      api.get(`/activos/${id}/`),
      api.get(`/activos/${id}/tabla-depreciacion/`),
      api.get(`/activos/${id}/depreciaciones/`),
    ]).then(([a, t, d]) => {
      setActivo(a.data)
      setTabla(t.data)
      setAplicadas(d.data)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { cargar() }, [id])

  useEffect(() => {
    if (window.location.hash === '#dar-baja') setShowBaja(true)
  }, [])

  const aplicarMes = async () => {
    setAplicando(true); setMensaje('')
    try {
      const { data } = await api.post(`/activos/${id}/aplicar-depreciacion/`, { periodo: periodoActual() })
      setMensaje(`Depreciación aplicada: ${fmt(data.depreciacion.valor_depreciacion)} — Asiento #${data.depreciacion.asiento}`)
      cargar()
    } catch (err) {
      setMensaje(err.response?.data?.error || 'No se pudo aplicar la depreciación')
    } finally { setAplicando(false) }
  }

  const submitBaja = async (e) => {
    e.preventDefault(); setBajaSaving(true); setBajaError('')
    try {
      await api.post(`/activos/${id}/dar-baja/`, bajaForm)
      navigate('/activos')
    } catch (err) { setBajaError(err.response?.data?.error || 'Error al dar de baja') }
    finally { setBajaSaving(false) }
  }

  if (loading || !activo) return <div className="flex justify-center pt-20"><div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" /></div>

  // Construir serie del valor en libros: aplicadas (reales) + proyección restante
  const grafica = []
  const periodosAplicados = new Set(aplicadas.map(d => d.periodo.slice(0, 7)))
  aplicadas.slice().reverse().forEach(d => grafica.push({ periodo: d.periodo.slice(0, 7), valor: Number(d.valor_en_libros) }))
  if (tabla) {
    tabla.tabla.forEach(fila => {
      if (!periodosAplicados.has(fila.periodo)) grafica.push({ periodo: fila.periodo, valor: fila.valor_en_libros })
    })
  }

  const puedeAplicar = activo.estado === 'activo'
  const puedeDarBaja = activo.estado !== 'dado_baja' && activo.estado !== 'vendido'

  return (
    <div className="space-y-5">
      <div className="flex justify-between items-start">
        <div>
          <Link to="/activos" className="text-xs text-blue-600 hover:underline">← Volver a activos</Link>
          <h1 className="text-2xl font-bold text-slate-800 mt-1">{activo.nombre}</h1>
          <p className="text-sm text-gray-500">{activo.codigo} — {activo.categoria_nombre}</p>
        </div>
        <span className={estadoBadge[activo.estado] || 'badge-gray'}>{estadoLabel[activo.estado] || activo.estado}</span>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card"><p className="text-xs text-gray-500">Valor de compra</p><p className="text-xl font-bold text-slate-800">{fmt(activo.valor_compra)}</p></div>
        <div className="card"><p className="text-xs text-gray-500">Depreciación acumulada</p><p className="text-xl font-bold text-yellow-700">{fmt(activo.valor_depreciado_acumulado)}</p></div>
        <div className="card"><p className="text-xs text-gray-500">Valor en libros</p><p className="text-xl font-bold text-green-700">{fmt(activo.valor_en_libros)}</p></div>
        <div className="card"><p className="text-xs text-gray-500">% Depreciado</p><p className="text-xl font-bold text-blue-700">{activo.porcentaje_depreciado.toFixed(1)}%</p></div>
      </div>

      <div className="card grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <div><p className="text-xs text-gray-400">Fecha compra</p><p>{activo.fecha_compra}</p></div>
        <div><p className="text-xs text-gray-400">Inicio depreciación</p><p>{activo.fecha_inicio_depreciacion}</p></div>
        <div><p className="text-xs text-gray-400">Vida útil</p><p>{activo.vida_util_años} años</p></div>
        <div><p className="text-xs text-gray-400">Método</p><p>{activo.metodo_depreciacion}</p></div>
        <div><p className="text-xs text-gray-400">Valor residual</p><p>{fmt(activo.valor_residual)}</p></div>
        <div><p className="text-xs text-gray-400">Ubicación</p><p>{activo.ubicacion || '—'}</p></div>
        <div><p className="text-xs text-gray-400">Número de serie</p><p>{activo.numero_serie || '—'}</p></div>
        <div><p className="text-xs text-gray-400">Proveedor</p><p>{activo.proveedor_nombre || '—'}</p></div>
      </div>

      <div className="card">
        <h2 className="text-base font-semibold text-gray-700 mb-4">Valor en libros a lo largo del tiempo</h2>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={grafica} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="periodo" tick={{ fontSize: 10 }} interval={Math.ceil(grafica.length / 12)} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v / 1e6).toFixed(1)}M`} />
            <Tooltip formatter={(v) => fmt(v)} />
            <Line type="monotone" dataKey="valor" stroke="#2563eb" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex flex-wrap gap-3 items-center">
        {puedeAplicar && (
          <button onClick={aplicarMes} className="btn-primary" disabled={aplicando}>
            {aplicando ? 'Aplicando…' : `Aplicar depreciación de ${periodoActual()}`}
          </button>
        )}
        <Link to={`/activos/${id}/tabla-depreciacion`} className="btn-secondary">Ver tabla de depreciación completa</Link>
        {puedeDarBaja && (
          <button onClick={() => setShowBaja(s => !s)} className="btn-danger">Dar de baja</button>
        )}
        {mensaje && <span className="text-sm text-gray-600">{mensaje}</span>}
      </div>

      {showBaja && (
        <form onSubmit={submitBaja} className="card space-y-4 max-w-xl" id="dar-baja">
          <h2 className="text-base font-semibold text-gray-700">Dar de baja este activo</h2>
          {bajaError && <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">{bajaError}</div>}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div><label className="label">Fecha *</label><input className="input" type="date" value={bajaForm.fecha} onChange={e => setBajaForm(f => ({ ...f, fecha: e.target.value }))} required /></div>
            <div><label className="label">Valor de venta</label><input className="input" type="number" min="0" step="1" value={bajaForm.valor_venta} onChange={e => setBajaForm(f => ({ ...f, valor_venta: e.target.value }))} /></div>
            <div className="md:col-span-2"><label className="label">Motivo *</label><input className="input" value={bajaForm.motivo} onChange={e => setBajaForm(f => ({ ...f, motivo: e.target.value }))} required /></div>
            <div className="md:col-span-2"><label className="label">Observaciones</label><textarea className="input" rows={2} value={bajaForm.observaciones} onChange={e => setBajaForm(f => ({ ...f, observaciones: e.target.value }))} /></div>
          </div>
          <div className="flex gap-3">
            <button type="button" className="btn-secondary" onClick={() => setShowBaja(false)}>Cancelar</button>
            <button type="submit" className="btn-danger" disabled={bajaSaving}>{bajaSaving ? 'Procesando…' : 'Confirmar baja'}</button>
          </div>
        </form>
      )}

      <div className="card p-0 overflow-x-auto">
        <div className="px-5 py-3 bg-gray-50 border-b">
          <h2 className="font-semibold text-sm text-gray-700">Depreciaciones aplicadas vs proyectadas</h2>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr><th className="th">Período</th><th className="th text-right">Dep. del mes</th><th className="th text-right">Dep. acumulada</th><th className="th text-right">Valor en libros</th><th className="th">Estado</th></tr>
          </thead>
          <tbody className="divide-y">
            {aplicadas.slice().reverse().map(d => (
              <tr key={d.id} className="bg-green-50/40">
                <td className="td">{d.periodo.slice(0, 7)}</td>
                <td className="td text-right">{fmt(d.valor_depreciacion)}</td>
                <td className="td text-right">{fmt(d.valor_acumulado)}</td>
                <td className="td text-right">{fmt(d.valor_en_libros)}</td>
                <td className="td"><span className="badge-green">Aplicada</span></td>
              </tr>
            ))}
            {tabla && tabla.tabla.filter(f => !periodosAplicados.has(f.periodo)).slice(0, 12).map(f => (
              <tr key={f.periodo} className="text-gray-400">
                <td className="td">{f.periodo}</td>
                <td className="td text-right">{fmt(f.valor_depreciacion)}</td>
                <td className="td text-right">{fmt(f.depreciacion_acumulada)}</td>
                <td className="td text-right">{fmt(f.valor_en_libros)}</td>
                <td className="td"><span className="badge-gray">Proyectada</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
