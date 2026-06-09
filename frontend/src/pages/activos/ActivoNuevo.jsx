import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

const metodoLabel = {
  linea_recta: 'Línea Recta',
  reduccion_saldos: 'Reducción de Saldos',
  suma_digitos: 'Suma de Dígitos de los Años',
}

export default function ActivoNuevo() {
  const navigate = useNavigate()
  const [categorias, setCategorias] = useState([])
  const [terceros, setTerceros] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    codigo: '', nombre: '', descripcion: '',
    categoria: '', fecha_compra: '', fecha_inicio_depreciacion: '',
    valor_compra: '', valor_residual: '0', vida_util_años: '',
    metodo_depreciacion: 'linea_recta',
    ubicacion: '', numero_serie: '', proveedor: '',
    cuenta_activo: '', cuenta_depreciacion_acumulada: '', cuenta_gasto_depreciacion: '',
  })

  useEffect(() => {
    api.get('/activos/categorias/?page_size=100').then(({ data }) => setCategorias(data.results || []))
    api.get('/terceros/?page_size=200').then(({ data }) => setTerceros(data.results || [])).catch(() => {})
  }, [])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const onCategoria = (id) => {
    set('categoria', id)
    const cat = categorias.find(c => String(c.id) === String(id))
    if (cat) {
      setForm(f => ({
        ...f,
        categoria: id,
        vida_util_años: cat.vida_util_años,
        metodo_depreciacion: cat.metodo_depreciacion,
        cuenta_activo: cat.cuenta_activo || '',
        cuenta_depreciacion_acumulada: cat.cuenta_depreciacion || '',
        cuenta_gasto_depreciacion: cat.cuenta_gasto_depreciacion || '',
      }))
    }
  }

  // Preview de depreciación mensual calculada en tiempo real (línea recta como aproximación general)
  const previewMensual = useMemo(() => {
    const compra = Number(form.valor_compra || 0)
    const residual = Number(form.valor_residual || 0)
    const vida = Number(form.vida_util_años || 0)
    if (!compra || !vida) return null
    const base = compra - residual
    if (base <= 0) return 0
    if (form.metodo_depreciacion === 'reduccion_saldos' && residual > 0) {
      const tasaAnual = 1 - Math.pow(residual / compra, 1 / vida)
      return compra * (tasaAnual / 12)
    }
    if (form.metodo_depreciacion === 'suma_digitos') {
      const sumaDigitos = (vida * (vida + 1)) / 2
      const fraccionAño1 = vida / sumaDigitos
      return (base * fraccionAño1) / 12
    }
    return base / (vida * 12)
  }, [form.valor_compra, form.valor_residual, form.vida_util_años, form.metodo_depreciacion])

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    try {
      const payload = { ...form }
      ;['proveedor', 'cuenta_activo', 'cuenta_depreciacion_acumulada', 'cuenta_gasto_depreciacion'].forEach(k => {
        if (!payload[k]) payload[k] = null
      })
      const { data } = await api.post('/activos/', payload)
      navigate(`/activos/${data.id}`)
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error al guardar')) }
    finally { setSaving(false) }
  }

  return (
    <div className="max-w-3xl space-y-5">
      <h1 className="text-2xl font-bold text-slate-800">Nuevo Activo Fijo</h1>
      {error && <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm break-words">{error}</div>}

      <form onSubmit={submit} className="space-y-5">
        <div className="card grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><label className="label">Código *</label><input className="input" value={form.codigo} onChange={e => set('codigo', e.target.value)} required /></div>
          <div><label className="label">Nombre *</label><input className="input" value={form.nombre} onChange={e => set('nombre', e.target.value)} required /></div>
          <div className="md:col-span-2"><label className="label">Descripción</label><textarea className="input" rows={2} value={form.descripcion} onChange={e => set('descripcion', e.target.value)} /></div>

          <div>
            <label className="label">Categoría *</label>
            <select className="input" value={form.categoria} onChange={e => onCategoria(e.target.value)} required>
              <option value="">Seleccionar…</option>
              {categorias.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Proveedor</label>
            <select className="input" value={form.proveedor} onChange={e => set('proveedor', e.target.value)}>
              <option value="">— Sin proveedor —</option>
              {terceros.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}
            </select>
          </div>

          <div><label className="label">Fecha de compra *</label><input className="input" type="date" value={form.fecha_compra} onChange={e => set('fecha_compra', e.target.value)} required /></div>
          <div><label className="label">Fecha inicio depreciación *</label><input className="input" type="date" value={form.fecha_inicio_depreciacion} onChange={e => set('fecha_inicio_depreciacion', e.target.value)} required /></div>

          <div><label className="label">Valor de compra *</label><input className="input" type="number" min="0" step="1" value={form.valor_compra} onChange={e => set('valor_compra', e.target.value)} required /></div>
          <div><label className="label">Valor residual</label><input className="input" type="number" min="0" step="1" value={form.valor_residual} onChange={e => set('valor_residual', e.target.value)} /></div>

          <div><label className="label">Vida útil (años) *</label><input className="input" type="number" min="1" value={form.vida_util_años} onChange={e => set('vida_util_años', e.target.value)} required /></div>
          <div>
            <label className="label">Método de depreciación *</label>
            <select className="input" value={form.metodo_depreciacion} onChange={e => set('metodo_depreciacion', e.target.value)} required>
              {Object.entries(metodoLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>

          <div><label className="label">Ubicación</label><input className="input" value={form.ubicacion} onChange={e => set('ubicacion', e.target.value)} /></div>
          <div><label className="label">Número de serie</label><input className="input" value={form.numero_serie} onChange={e => set('numero_serie', e.target.value)} /></div>
        </div>

        {previewMensual !== null && (
          <div className="card bg-blue-50 border-blue-200">
            <p className="text-sm text-gray-600">Depreciación mensual estimada (primer mes, método <strong>{metodoLabel[form.metodo_depreciacion]}</strong>)</p>
            <p className="text-2xl font-bold text-blue-700 mt-1">{fmt(previewMensual)}</p>
            <p className="text-xs text-gray-400 mt-1">Cálculo de referencia — el valor real se ajusta mes a mes según el método seleccionado.</p>
          </div>
        )}

        <div className="flex gap-3">
          <button type="button" onClick={() => navigate('/activos')} className="btn-secondary">Cancelar</button>
          <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Crear Activo'}</button>
        </div>
      </form>
    </div>
  )
}
