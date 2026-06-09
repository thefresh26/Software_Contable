import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

const hoy = () => new Date().toISOString().slice(0, 10)
const primerDiaMes = () => {
  const d = new Date(); d.setDate(1); return d.toISOString().slice(0, 10)
}

const EMPTY = {
  empleado: '', periodo_inicio: primerDiaMes(), periodo_fin: hoy(),
  bonificaciones: 0, horas_extra_diurnas: 0, horas_extra_nocturnas: 0,
  retencion_fuente: 0, otras_deducciones: 0,
}

function Fila({ label, valor, tipo = 'normal' }) {
  const cls = {
    normal: 'text-gray-700',
    total: 'font-bold text-gray-900 border-t mt-1 pt-2',
    deduccion: 'text-red-600',
    neto: 'font-bold text-blue-700 text-base border-t mt-2 pt-2',
  }[tipo]
  return (
    <div className={`flex justify-between py-1 ${cls}`}>
      <span className="text-sm">{label}</span>
      <span className="text-sm">{fmt(valor)}</span>
    </div>
  )
}

export default function Liquidar() {
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [empleados, setEmpleados] = useState([])
  const [resultado, setResultado] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/nomina/empleados/?activo=true&page_size=200').then(({ data }) => setEmpleados(data.results || []))
  }, [])

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const calcular = async (e) => {
    e.preventDefault(); setSaving(true); setError(''); setResultado(null)
    try {
      const { data } = await api.post('/nomina/liquidar/', form)
      setResultado(data)
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error al liquidar')) }
    finally { setSaving(false) }
  }

  const empleadoSel = empleados.find((e) => String(e.id) === String(form.empleado))

  return (
    <div className="max-w-4xl space-y-5">
      <h1 className="text-2xl font-bold text-slate-800">Liquidar Nómina</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Formulario */}
        <form onSubmit={calcular} className="card space-y-4">
          <h2 className="font-semibold text-gray-700">Datos del período</h2>
          {error && <p className="text-red-600 text-sm bg-red-50 p-2 rounded">{error}</p>}

          <div>
            <label className="label">Empleado *</label>
            <select className="input" value={form.empleado} onChange={(e) => set('empleado', e.target.value)} required>
              <option value="">Seleccionar…</option>
              {empleados.map((e) => <option key={e.id} value={e.id}>{e.nombre} — {e.cedula}</option>)}
            </select>
            {empleadoSel && <p className="text-xs text-gray-500 mt-1">Salario base: {fmt(empleadoSel.salario_base)}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Período inicio *</label><input className="input" type="date" value={form.periodo_inicio} onChange={(e) => set('periodo_inicio', e.target.value)} required /></div>
            <div><label className="label">Período fin *</label><input className="input" type="date" value={form.periodo_fin} onChange={(e) => set('periodo_fin', e.target.value)} required /></div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Bonificaciones</label><input className="input" type="number" min="0" step="1" value={form.bonificaciones} onChange={(e) => set('bonificaciones', e.target.value)} /></div>
            <div><label className="label">H.E. Diurnas</label><input className="input" type="number" min="0" step="0.5" value={form.horas_extra_diurnas} onChange={(e) => set('horas_extra_diurnas', e.target.value)} /></div>
            <div><label className="label">H.E. Nocturnas</label><input className="input" type="number" min="0" step="0.5" value={form.horas_extra_nocturnas} onChange={(e) => set('horas_extra_nocturnas', e.target.value)} /></div>
            <div><label className="label">Retención en fuente</label><input className="input" type="number" min="0" step="1" value={form.retencion_fuente} onChange={(e) => set('retencion_fuente', e.target.value)} /></div>
            <div><label className="label">Otras deducciones</label><input className="input" type="number" min="0" step="1" value={form.otras_deducciones} onChange={(e) => set('otras_deducciones', e.target.value)} /></div>
          </div>

          <div className="flex gap-3">
            <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Calculando…' : 'Calcular y Guardar'}</button>
            <button type="button" className="btn-secondary" onClick={() => navigate('/nomina/historial')}>Ver historial</button>
          </div>
        </form>

        {/* Resultado */}
        {resultado && (
          <div className="card space-y-3">
            <h2 className="font-semibold text-gray-700">Colilla de Pago</h2>
            <p className="text-xs text-gray-500">{resultado.empleado_nombre} — {resultado.periodo_inicio} a {resultado.periodo_fin}</p>

            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Devengados</p>
              <Fila label="Salario proporcional" valor={resultado.salario_base} />
              {Number(resultado.auxilio_transporte) > 0 && <Fila label="Auxilio de transporte" valor={resultado.auxilio_transporte} />}
              {Number(resultado.valor_horas_extra_diurnas) > 0 && <Fila label="H.E. Diurnas" valor={resultado.valor_horas_extra_diurnas} />}
              {Number(resultado.valor_horas_extra_nocturnas) > 0 && <Fila label="H.E. Nocturnas" valor={resultado.valor_horas_extra_nocturnas} />}
              {Number(resultado.bonificaciones) > 0 && <Fila label="Bonificaciones" valor={resultado.bonificaciones} />}
              <Fila label="Total devengado" valor={resultado.total_devengado} tipo="total" />
            </div>

            <div className="mt-2">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Deducciones</p>
              <Fila label="Salud empleado (4%)" valor={resultado.salud_empleado} tipo="deduccion" />
              <Fila label="Pensión empleado (4%)" valor={resultado.pension_empleado} tipo="deduccion" />
              {Number(resultado.retencion_fuente) > 0 && <Fila label="Retención en fuente" valor={resultado.retencion_fuente} tipo="deduccion" />}
              {Number(resultado.otras_deducciones) > 0 && <Fila label="Otras deducciones" valor={resultado.otras_deducciones} tipo="deduccion" />}
              <Fila label="Total deducido" valor={resultado.total_deducido} tipo="total" />
            </div>

            <Fila label="NETO A PAGAR" valor={resultado.neto_pagar} tipo="neto" />

            <div className="mt-3 pt-3 border-t">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Aportes empresa</p>
              <div className="grid grid-cols-2 gap-1 text-xs text-gray-500">
                <span>Salud (8.5%)</span><span className="text-right">{fmt(resultado.salud_empresa)}</span>
                <span>Pensión (12%)</span><span className="text-right">{fmt(resultado.pension_empresa)}</span>
                <span>ARL (0.52%)</span><span className="text-right">{fmt(resultado.arl)}</span>
                <span>Caja comp. (4%)</span><span className="text-right">{fmt(resultado.caja_compensacion)}</span>
                <span>SENA (2%)</span><span className="text-right">{fmt(resultado.sena)}</span>
                <span>ICBF (3%)</span><span className="text-right">{fmt(resultado.icbf)}</span>
              </div>
            </div>

            <a href={`/api/nomina/liquidaciones/${resultado.id}/colilla/`} target="_blank" rel="noreferrer" className="btn-secondary text-sm inline-block">
              Descargar PDF colilla
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
