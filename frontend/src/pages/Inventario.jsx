import { useEffect, useState } from 'react'
import api from '../api/client'

const EMPTY_PROD = { codigo: '', nombre: '', descripcion: '', categoria: '', precio_compra: '', precio_venta: '', iva_porcentaje: 19, stock_actual: 0, stock_minimo: 5, unidad_medida: 'UND', activo: true }

function ModalProducto({ item, categorias, onClose, onSaved }) {
  const [form, setForm] = useState(item ? { ...item, categoria: item.categoria || '' } : EMPTY_PROD)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    const body = { ...form, categoria: form.categoria || null }
    try {
      item?.id ? await api.put(`/inventario/productos/${item.id}/`, body) : await api.post('/inventario/productos/', body)
      onSaved()
    } catch (err) { setError(JSON.stringify(err.response?.data || 'Error')) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center px-6 py-4 border-b sticky top-0 bg-white">
          <h2 className="font-semibold text-gray-800">{item?.id ? 'Editar' : 'Nuevo'} Producto</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="px-6 py-4 space-y-3">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Código *</label><input className="input" value={form.codigo} onChange={(e) => set('codigo', e.target.value)} required /></div>
            <div>
              <label className="label">Categoría</label>
              <select className="input" value={form.categoria} onChange={(e) => set('categoria', e.target.value)}>
                <option value="">Sin categoría</option>
                {categorias.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
              </select>
            </div>
          </div>
          <div><label className="label">Nombre *</label><input className="input" value={form.nombre} onChange={(e) => set('nombre', e.target.value)} required /></div>
          <div><label className="label">Descripción</label><textarea className="input" rows={2} value={form.descripcion} onChange={(e) => set('descripcion', e.target.value)} /></div>
          <div className="grid grid-cols-3 gap-3">
            <div><label className="label">Precio compra</label><input className="input" type="number" step="0.01" value={form.precio_compra} onChange={(e) => set('precio_compra', e.target.value)} /></div>
            <div><label className="label">Precio venta</label><input className="input" type="number" step="0.01" value={form.precio_venta} onChange={(e) => set('precio_venta', e.target.value)} /></div>
            <div><label className="label">IVA %</label><input className="input" type="number" step="0.01" value={form.iva_porcentaje} onChange={(e) => set('iva_porcentaje', e.target.value)} /></div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div><label className="label">Stock actual</label><input className="input" type="number" value={form.stock_actual} onChange={(e) => set('stock_actual', e.target.value)} /></div>
            <div><label className="label">Stock mínimo</label><input className="input" type="number" value={form.stock_minimo} onChange={(e) => set('stock_minimo', e.target.value)} /></div>
            <div><label className="label">Unidad</label><input className="input" value={form.unidad_medida} onChange={(e) => set('unidad_medida', e.target.value)} /></div>
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

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

export default function Inventario() {
  const [productos, setProductos] = useState([])
  const [categorias, setCategorias] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [soloBajo, setSoloBajo] = useState(false)
  const [modal, setModal] = useState(false)

  const load = () => {
    setLoading(true)
    const params = new URLSearchParams({ page_size: 200 })
    if (search) params.set('search', search)
    if (soloBajo) params.set('stock_bajo', 'true')
    api.get(`/inventario/productos/?${params}`).then(({ data }) => setProductos(data.results || [])).finally(() => setLoading(false))
  }

  useEffect(() => { api.get('/inventario/categorias/?page_size=100').then(({ data }) => setCategorias(data.results || [])) }, [])
  useEffect(() => { load() }, [search, soloBajo])

  return (
    <div className="space-y-4">
      {modal !== false && (
        <ModalProducto item={modal === true ? null : modal} categorias={categorias} onClose={() => setModal(false)} onSaved={() => { setModal(false); load() }} />
      )}

      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Inventario</h1>
        <button className="btn-primary" onClick={() => setModal(true)}>+ Nuevo Producto</button>
      </div>

      <div className="flex gap-3 items-center">
        <input className="input max-w-xs" placeholder="Buscar producto…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
          <input type="checkbox" checked={soloBajo} onChange={(e) => setSoloBajo(e.target.checked)} className="rounded" />
          Solo bajo mínimo
        </label>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="th">Código</th><th className="th">Nombre</th><th className="th">Categoría</th>
              <th className="th">P. Venta</th><th className="th">IVA</th><th className="th">Stock</th><th className="th" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={7} className="td text-center py-8 text-gray-400">Cargando…</td></tr>
            ) : productos.length === 0 ? (
              <tr><td colSpan={7} className="td text-center py-8 text-gray-400">Sin productos</td></tr>
            ) : productos.map((p) => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="td font-mono text-xs">{p.codigo}</td>
                <td className="td font-medium">{p.nombre}</td>
                <td className="td text-gray-500">{p.categoria_nombre || '—'}</td>
                <td className="td">{fmt(p.precio_venta)}</td>
                <td className="td">{p.iva_porcentaje}%</td>
                <td className="td">
                  <span className={p.bajo_stock ? 'badge-red' : 'badge-green'}>
                    {p.stock_actual} {p.unidad_medida}
                  </span>
                </td>
                <td className="td">
                  <button className="text-blue-600 hover:underline text-xs" onClick={() => setModal(p)}>Editar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
