import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../../api/client'
import { useConfirm } from '../../components/ui/ConfirmDialog'
import { useToast } from '../../context/ToastContext'
import { parseApiError } from '../../utils/errorMessages'
import EmptyState from '../../components/ui/EmptyState'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

const estadoBadge = {
  activo: 'badge-green',
  depreciado: 'badge-gray',
  dado_baja: 'badge-red',
  vendido: 'badge-red',
}

const estadoLabel = {
  activo: 'Activo',
  depreciado: 'Depreciado',
  dado_baja: 'Dado de Baja',
  vendido: 'Vendido',
}

export default function ActivoLista() {
  const navigate = useNavigate()
  const toast = useToast()
  const confirm = useConfirm()
  const [data, setData] = useState([])
  const [categorias, setCategorias] = useState([])
  const [loading, setLoading] = useState(true)
  const [filtroCategoria, setFiltroCategoria] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('')

  useEffect(() => {
    api.get('/activos/categorias/?page_size=100').then(({ data: d }) => setCategorias(d.results || []))
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams({ page_size: '100' })
    if (filtroCategoria) params.set('categoria', filtroCategoria)
    if (filtroEstado) params.set('estado', filtroEstado)
    api.get(`/activos/?${params.toString()}`)
      .then(({ data: d }) => setData(d.results || []))
      .finally(() => setLoading(false))
  }, [filtroCategoria, filtroEstado])

  const darBaja = (activo) => navigate(`/activos/${activo.id}#dar-baja`)

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">Activos Fijos</h1>
        <Link to="/activos/nuevo" className="btn-primary">+ Nuevo Activo</Link>
      </div>

      <div className="card flex flex-wrap gap-3 items-end">
        <div>
          <label className="label">Categoría</label>
          <select className="input" value={filtroCategoria} onChange={e => setFiltroCategoria(e.target.value)}>
            <option value="">Todas</option>
            {categorias.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Estado</label>
          <select className="input" value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)}>
            <option value="">Todos</option>
            <option value="activo">Activo</option>
            <option value="depreciado">Totalmente Depreciado</option>
            <option value="dado_baja">Dado de Baja</option>
            <option value="vendido">Vendido</option>
          </select>
        </div>
      </div>

      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="th">Código</th>
              <th className="th">Nombre</th>
              <th className="th">Categoría</th>
              <th className="th text-right">Valor Compra</th>
              <th className="th text-right">Dep. Acumulada</th>
              <th className="th text-right">Valor en Libros</th>
              <th className="th">% Depreciado</th>
              <th className="th">Estado</th>
              <th className="th" />
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr><td colSpan={9} className="td text-center py-12">
                <div className="flex items-center justify-center gap-2 text-gray-400">
                  <div className="animate-spin h-4 w-4 border-b-2 border-blue-600 rounded-full" />Cargando…
                </div>
              </td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={9}>
                <EmptyState icon="🏢" title="Sin activos fijos registrados" description="Registre los bienes de su empresa: equipos, vehículos, muebles, etc." action={() => navigate('/activos/nuevo')} actionLabel="+ Nuevo Activo" />
              </td></tr>
            ) : data.map(a => (
              <tr key={a.id} className="hover:bg-gray-50">
                <td className="td font-mono text-xs">{a.codigo}</td>
                <td className="td font-medium text-gray-800">{a.nombre}</td>
                <td className="td">{a.categoria_nombre}</td>
                <td className="td text-right">{fmt(a.valor_compra)}</td>
                <td className="td text-right">{fmt(a.valor_depreciado_acumulado)}</td>
                <td className="td text-right font-medium">{fmt(a.valor_en_libros)}</td>
                <td className="td">
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-gray-200 rounded-full h-1.5">
                      <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${Math.min(a.porcentaje_depreciado, 100)}%` }} />
                    </div>
                    <span className="text-xs text-gray-500">{a.porcentaje_depreciado.toFixed(0)}%</span>
                  </div>
                </td>
                <td className="td"><span className={estadoBadge[a.estado] || 'badge-gray'}>{estadoLabel[a.estado] || a.estado}</span></td>
                <td className="td whitespace-nowrap">
                  <div className="flex gap-3 text-xs">
                    <Link to={`/activos/${a.id}`} className="text-blue-600 hover:underline">Ver detalle</Link>
                    <Link to={`/activos/${a.id}/tabla-depreciacion`} className="text-blue-600 hover:underline">Tabla dep.</Link>
                    {a.estado !== 'dado_baja' && a.estado !== 'vendido' && (
                      <button onClick={() => darBaja(a)} className="text-red-600 hover:underline">Dar de baja</button>
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
