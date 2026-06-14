import { useEffect, useState } from 'react'
import api from '../../api/client'

const MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

function fmtFecha(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function CierresPeriodo() {
  const [cierres, setCierres] = useState([])
  const [loading, setLoading] = useState(true)
  const [accion, setAccion] = useState(null)
  const [modalNuevo, setModalNuevo] = useState(false)
  const [modalCerrar, setModalCerrar] = useState(null)
  const [form, setForm] = useState({ mes: new Date().getMonth() + 1, año: new Date().getFullYear(), notas: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const cargar = () => {
    setLoading(true)
    api.get('/contabilidad/cierres/?page_size=50').then(({ data }) => {
      setCierres(data.results || [])
    }).finally(() => setLoading(false))
  }

  useEffect(() => { cargar() }, [])

  const crearCierre = async (e) => {
    e.preventDefault()
    setSaving(true); setError('')
    const periodo = `${form.año}-${String(form.mes).padStart(2, '0')}-01`
    try {
      await api.post('/contabilidad/cierres/', { periodo, notas: form.notas })
      setModalNuevo(false)
      cargar()
    } catch (err) {
      setError(err.response?.data?.detail || JSON.stringify(err.response?.data || 'Error'))
    } finally { setSaving(false) }
  }

  const cerrarPeriodo = async () => {
    if (!modalCerrar) return
    setAccion(modalCerrar.id)
    try {
      await api.post(`/contabilidad/cierres/${modalCerrar.id}/cerrar/`)
      setModalCerrar(null)
      cargar()
    } catch (err) {
      alert(err.response?.data?.error || 'Error al cerrar período')
    } finally { setAccion(null) }
  }

  const reabrirPeriodo = async (id) => {
    if (!confirm('¿Reabrir este período? Solo administradores pueden hacerlo.')) return
    setAccion(id)
    try {
      await api.post(`/contabilidad/cierres/${id}/reabrir/`)
      cargar()
    } catch (err) {
      alert(err.response?.data?.error || 'No autorizado')
    } finally { setAccion(null) }
  }

  const formatPeriodo = (iso) => {
    const d = new Date(iso + 'T00:00:00')
    return `${MESES[d.getMonth()]} ${d.getFullYear()}`
  }

  const años = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 2 + i)

  return (
    <div className="space-y-4">
      {/* Modal Nuevo Cierre */}
      {modalNuevo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
            <h2 className="text-lg font-semibold mb-4">Crear Cierre de Período</h2>
            {error && <p className="text-sm text-red-600 bg-red-50 p-2 rounded mb-3">{error}</p>}
            <form onSubmit={crearCierre} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Mes</label>
                  <select className="input" value={form.mes} onChange={e => setForm(f => ({ ...f, mes: e.target.value }))}>
                    {MESES.map((m, i) => <option key={i+1} value={i+1}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">Año</label>
                  <select className="input" value={form.año} onChange={e => setForm(f => ({ ...f, año: e.target.value }))}>
                    {años.map(a => <option key={a} value={a}>{a}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="label">Notas (opcional)</label>
                <textarea className="input min-h-[80px]" value={form.notas} onChange={e => setForm(f => ({ ...f, notas: e.target.value }))} />
              </div>
              <div className="flex gap-2 justify-end">
                <button type="button" className="btn-secondary" onClick={() => setModalNuevo(false)}>Cancelar</button>
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Creando…' : 'Crear Período'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Confirmar Cierre */}
      {modalCerrar && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-sm shadow-xl">
            <h2 className="text-lg font-semibold mb-2">Cerrar Período</h2>
            <p className="text-sm text-gray-600 mb-4">
              ¿Estás seguro de cerrar el período <strong>{formatPeriodo(modalCerrar.periodo)}</strong>?
              <br />Una vez cerrado, no se podrán crear ni modificar asientos en este período.
            </p>
            <div className="flex gap-2 justify-end">
              <button className="btn-secondary" onClick={() => setModalCerrar(null)}>Cancelar</button>
              <button className="btn-danger" disabled={accion === modalCerrar.id} onClick={cerrarPeriodo}>
                {accion === modalCerrar.id ? 'Cerrando…' : 'Cerrar Período'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Cierre Contable de Períodos</h1>
        <button className="btn-primary" onClick={() => { setModalNuevo(true); setError('') }}>
          + Nuevo Período
        </button>
      </div>

      <div className="card p-0 overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="th">Período</th>
              <th className="th">Estado</th>
              <th className="th">Cerrado por</th>
              <th className="th">Fecha cierre</th>
              <th className="th">Notas</th>
              <th className="th">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={6} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            ) : cierres.length === 0 ? (
              <tr><td colSpan={6} className="td text-center py-8 text-gray-400">Sin períodos registrados. Crea el primer período.</td></tr>
            ) : cierres.map(c => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="td font-medium">{formatPeriodo(c.periodo)}</td>
                <td className="td">
                  <span className={c.estado === 'cerrado' ? 'badge-red' : 'badge-green'}>
                    {c.estado_display}
                  </span>
                </td>
                <td className="td text-gray-500">{c.cerrado_por_nombre || '—'}</td>
                <td className="td text-gray-500">{fmtFecha(c.cerrado_at)}</td>
                <td className="td text-gray-400 max-w-[200px] truncate">{c.notas || '—'}</td>
                <td className="td">
                  <div className="flex gap-2">
                    {c.estado === 'abierto' && (
                      <button
                        className="btn-danger text-xs px-2 py-1"
                        disabled={accion === c.id}
                        onClick={() => setModalCerrar(c)}
                      >
                        Cerrar
                      </button>
                    )}
                    {c.estado === 'cerrado' && (
                      <button
                        className="btn-secondary text-xs px-2 py-1"
                        disabled={accion === c.id}
                        onClick={() => reabrirPeriodo(c.id)}
                      >
                        Reabrir
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
