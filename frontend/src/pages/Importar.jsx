import { useState, useRef } from 'react'
import api from '../api/client'

const TABS = [
  { key: 'terceros', label: 'Terceros', columnas: 'tipo | tipo_persona | nombre | nit | email | telefono | direccion | ciudad' },
  { key: 'productos', label: 'Productos', columnas: 'codigo | nombre | categoria | precio_compra | precio_venta | iva_porcentaje | stock_actual | stock_minimo | unidad_medida' },
  { key: 'plan-cuentas', label: 'Plan de Cuentas', columnas: 'codigo | nombre | tipo | nivel' },
]

export default function Importar() {
  const [tab, setTab] = useState('terceros')
  const [archivo, setArchivo] = useState(null)
  const [preview, setPreview] = useState(null)
  const [resultado, setResultado] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef()

  const reset = () => { setArchivo(null); setPreview(null); setResultado(null); setError('') }

  const handleFile = async (e) => {
    const f = e.target.files[0]
    if (!f) return
    setArchivo(f); setPreview(null); setResultado(null); setError(''); setLoading(true)
    try {
      const fd = new FormData(); fd.append('archivo', f)
      const { data } = await api.post(`/importador/${tab}/?preview=true`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setPreview(data.preview || [])
    } catch (err) { setError('Error leyendo archivo: ' + (err.response?.data?.error || err.message)) }
    finally { setLoading(false) }
  }

  const confirmar = async () => {
    if (!archivo) return
    setLoading(true); setError('')
    try {
      const fd = new FormData(); fd.append('archivo', archivo)
      const { data } = await api.post(`/importador/${tab}/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setResultado(data); setPreview(null); setArchivo(null)
      if (fileRef.current) fileRef.current.value = ''
    } catch (err) { setError('Error importando: ' + (err.response?.data?.error || err.message)) }
    finally { setLoading(false) }
  }

  return (
    <div className="max-w-3xl space-y-5">
      <h1 className="text-2xl font-bold text-slate-800">Importar Datos desde Excel</h1>

      {/* Tabs */}
      <div className="flex gap-2">
        {TABS.map(t => (
          <button key={t.key} onClick={() => { setTab(t.key); reset(); if (fileRef.current) fileRef.current.value = '' }}
            className={t.key === tab ? 'btn-primary' : 'btn-secondary'}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Info columnas */}
      <div className="card bg-blue-50 border-blue-200">
        <p className="text-sm font-medium text-blue-700 mb-1">Columnas requeridas:</p>
        <p className="text-xs text-blue-600 font-mono">{TABS.find(t => t.key === tab)?.columnas}</p>
        <div className="mt-3">
          <a href={`/api/importador/plantilla/${tab}/`} className="text-blue-700 text-xs underline hover:no-underline">
            Descargar plantilla Excel vacía →
          </a>
        </div>
      </div>

      {/* Upload */}
      <div className="card">
        <label className="label">Seleccionar archivo Excel (.xlsx)</label>
        <input ref={fileRef} type="file" accept=".xlsx,.xls" onChange={handleFile}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
      </div>

      {error && <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">{error}</div>}
      {loading && <div className="card text-center text-gray-400 py-6">Procesando…</div>}

      {/* Preview */}
      {preview && (
        <div className="card space-y-3">
          <h2 className="font-semibold text-gray-700">Vista previa (primeras {preview.length} filas)</h2>
          <div className="overflow-x-auto">
            <table className="text-xs w-full border-collapse">
              <thead className="bg-gray-50"><tr>{preview[0] && Object.keys(preview[0]).map(k => <th key={k} className="th">{k}</th>)}</tr></thead>
              <tbody>{preview.map((row, i) => <tr key={i} className="border-b">{Object.values(row).map((v, j) => <td key={j} className="td">{String(v)}</td>)}</tr>)}</tbody>
            </table>
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={reset} className="btn-secondary">Cancelar</button>
            <button onClick={confirmar} className="btn-primary" disabled={loading}>
              {loading ? 'Importando…' : `Confirmar importación`}
            </button>
          </div>
        </div>
      )}

      {/* Resultado */}
      {resultado && (
        <div className="card space-y-3">
          <h2 className="font-semibold text-gray-700">Resultado de la importación</h2>
          <div className="flex gap-4">
            <div className="flex-1 p-4 bg-green-50 rounded-lg text-center">
              <p className="text-3xl font-bold text-green-700">{resultado.creados}</p>
              <p className="text-sm text-green-600">registros importados</p>
            </div>
            <div className="flex-1 p-4 bg-red-50 rounded-lg text-center">
              <p className="text-3xl font-bold text-red-700">{resultado.errores?.length || 0}</p>
              <p className="text-sm text-red-600">errores</p>
            </div>
          </div>
          {resultado.errores?.length > 0 && (
            <div className="space-y-1">
              <p className="text-sm font-medium text-red-600">Detalle de errores:</p>
              {resultado.errores.map((e, i) => (
                <div key={i} className="text-xs bg-red-50 px-3 py-1.5 rounded">
                  <strong>Fila {e.fila}:</strong> {e.error}
                </div>
              ))}
            </div>
          )}
          <button onClick={() => setResultado(null)} className="btn-secondary">Nueva importación</button>
        </div>
      )}
    </div>
  )
}
