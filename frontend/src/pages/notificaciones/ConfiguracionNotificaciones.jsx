import { useEffect, useState } from 'react'
import api from '../../api/client'

function Toggle({ label, checked, onChange }) {
  return (
    <label className="flex items-center justify-between py-2 cursor-pointer">
      <span className="text-sm text-gray-700">{label}</span>
      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${checked ? 'bg-blue-600' : 'bg-gray-300'}`}
      >
        <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${checked ? 'translate-x-4.5' : 'translate-x-1'}`} style={{ transform: checked ? 'translateX(18px)' : 'translateX(2px)' }} />
      </button>
    </label>
  )
}

const EMAIL_TOGGLES = [
  ['email_facturas_vencer', 'Facturas por vencer'],
  ['email_facturas_vencidas', 'Facturas vencidas'],
  ['email_stock_bajo', 'Stock bajo'],
  ['email_pagos', 'Pagos (recibidos y realizados)'],
  ['email_nomina', 'Nómina pendiente'],
  ['email_cotizaciones', 'Cotizaciones por vencer'],
]

const SISTEMA_TOGGLES = [
  ['sistema_stock_bajo', 'Stock bajo'],
  ['sistema_facturas_vencer', 'Facturas por vencer'],
  ['sistema_pagos', 'Pagos'],
]

export default function ConfiguracionNotificaciones() {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [mensaje, setMensaje] = useState('')

  useEffect(() => {
    api.get('/notificaciones/configuracion/').then((res) => setConfig(res.data)).finally(() => setLoading(false))
  }, [])

  const set = (campo, valor) => setConfig((prev) => ({ ...prev, [campo]: valor }))

  const guardar = async () => {
    setGuardando(true)
    setMensaje('')
    try {
      const { data } = await api.put('/notificaciones/configuracion/', config)
      setConfig(data)
      setMensaje('Preferencias guardadas correctamente.')
    } finally {
      setGuardando(false)
    }
  }

  const probarEmail = async () => {
    setMensaje('')
    try {
      const { data } = await api.post('/notificaciones/probar-email/')
      setMensaje(data.mensaje)
    } catch (e) {
      setMensaje(e.response?.data?.error || 'No se pudo enviar el correo de prueba.')
    }
  }

  if (loading || !config) return <div className="flex justify-center pt-20"><div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" /></div>

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-bold text-slate-800">Configuración de Notificaciones</h1>

      {mensaje && (
        <div className="rounded-md bg-blue-50 border border-blue-200 text-blue-800 text-sm px-4 py-2.5">{mensaje}</div>
      )}

      <div className="card">
        <h2 className="font-semibold text-sm text-gray-700 mb-1">Notificaciones por correo electrónico</h2>
        <p className="text-xs text-gray-400 mb-2">Elige qué eventos quieres recibir por email.</p>
        <div className="divide-y">
          {EMAIL_TOGGLES.map(([campo, label]) => (
            <Toggle key={campo} label={label} checked={!!config[campo]} onChange={(v) => set(campo, v)} />
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="font-semibold text-sm text-gray-700 mb-3">Días de anticipación</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Facturas por vencer</label>
            <input type="number" min="1" className="input" value={config.dias_anticipacion_factura}
              onChange={(e) => set('dias_anticipacion_factura', Number(e.target.value))} />
          </div>
          <div>
            <label className="label">Cotizaciones por vencer</label>
            <input type="number" min="1" className="input" value={config.dias_anticipacion_cotizacion}
              onChange={(e) => set('dias_anticipacion_cotizacion', Number(e.target.value))} />
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="font-semibold text-sm text-gray-700 mb-1">Notificaciones del sistema (campana)</h2>
        <p className="text-xs text-gray-400 mb-2">Elige qué eventos generan una notificación dentro del sistema.</p>
        <div className="divide-y">
          {SISTEMA_TOGGLES.map(([campo, label]) => (
            <Toggle key={campo} label={label} checked={!!config[campo]} onChange={(v) => set(campo, v)} />
          ))}
        </div>
      </div>

      <div className="flex gap-3">
        <button onClick={guardar} disabled={guardando} className="btn-primary">
          {guardando ? 'Guardando…' : 'Guardar preferencias'}
        </button>
        <button onClick={probarEmail} className="btn-secondary">Probar email</button>
      </div>
    </div>
  )
}
