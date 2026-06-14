import { useState } from 'react'
import api from '../api/client'
import { descargarExcel } from '../utils/excel'

const MODELOS = [
  { key: 'facturas', label: 'Facturas', campos: ['numero', 'tipo', 'fecha', 'total', 'estado'] },
  { key: 'terceros', label: 'Terceros', campos: ['nombre', 'nit', 'tipo', 'email', 'ciudad'] },
  { key: 'movimientos', label: 'Movimientos Contables', campos: ['debito', 'credito', 'descripcion'] },
  { key: 'productos', label: 'Productos', campos: ['codigo', 'nombre', 'stock_actual', 'precio_venta'] },
  { key: 'empleados', label: 'Empleados', campos: ['nombre', 'cedula', 'cargo', 'salario_base'] },
]

export default function ReportePersonalizado() {
  const [modelo, setModelo] = useState('')
  const [camposSeleccionados, setCamposSeleccionados] = useState([])
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const modeloInfo = MODELOS.find(m => m.key === modelo)

  const toggleCampo = (c) => {
    setCamposSeleccionados(prev =>
      prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]
    )
  }

  const handleModelo = (key) => {
    setModelo(key)
    setCamposSeleccionados([])
    setPreview(null)
  }

  const verReporte = async () => {
    if (!modelo) { setError('Seleccione un modelo.'); return }
    setLoading(true); setError('')
    try {
      const { data } = await api.post('/contabilidad/reportes/personalizado/', {
        modelo, campos: camposSeleccionados, filtros: {}, formato: 'json',
      })
      setPreview(data)
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setLoading(false) }
  }

  const exportarExcel = async () => {
    if (!modelo) return
    try {
      const token = localStorage.getItem('access_token')
      const baseURL = import.meta.env.VITE_API_URL || ''
      const resp = await fetch(`${baseURL}/api/contabilidad/reportes/personalizado/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ modelo, campos: camposSeleccionados, filtros: {}, formato: 'excel' }),
      })
      if (!resp.ok) throw new Error('Error al exportar')
      const blob = await resp.blob()
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `reporte_${modelo}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(link.href)
    } catch { alert('Error al exportar') }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">Reporte Personalizado</h1>
      {error && <p className="text-red-600 text-sm bg-red-50 p-2 rounded">{error}</p>}

      <div className="card space-y-4">
        <div>
          <label className="label">Modelo de datos</label>
          <div className="flex flex-wrap gap-2 mt-1">
            {MODELOS.map(m => (
              <button
                key={m.key}
                type="button"
                onClick={() => handleModelo(m.key)}
                className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${modelo === m.key ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 text-gray-600 hover:border-blue-400'}`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        {modeloInfo && (
          <div>
            <label className="label">Columnas a incluir</label>
            <div className="flex flex-wrap gap-2 mt-1">
              {modeloInfo.campos.map(c => (
                <label key={c} className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={camposSeleccionados.includes(c)}
                    onChange={() => toggleCampo(c)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">{c}</span>
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-1">Si no selecciona columnas, se incluyen todas las disponibles.</p>
          </div>
        )}

        <div className="flex gap-2">
          <button className="btn-primary" onClick={verReporte} disabled={!modelo || loading}>
            {loading ? 'Cargando…' : 'Ver primeros 10 registros'}
          </button>
          <button className="btn-excel" onClick={exportarExcel} disabled={!modelo}>
            ⬇ Exportar Excel
          </button>
        </div>
      </div>

      {preview && (
        <div className="card p-0 overflow-x-auto">
          <div className="px-5 py-3 bg-gray-50 border-b flex justify-between items-center">
            <h2 className="text-sm font-semibold text-gray-700">
              Vista previa — {MODELOS.find(m => m.key === preview.modelo)?.label} ({preview.total} registros)
            </h2>
          </div>
          {preview.datos.length === 0 ? (
            <p className="td text-center py-6 text-gray-400">Sin datos para mostrar.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>{Object.keys(preview.datos[0]).map(k => <th key={k} className="th">{k}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {preview.datos.map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    {Object.values(row).map((v, j) => <td key={j} className="td text-xs">{String(v ?? '')}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
