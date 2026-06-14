import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import api from '../api/client'

const nav = [
  { label: 'Dashboard', to: '/', icon: '📊' },
  { label: 'Terceros', to: '/terceros', icon: '👥' },
  { label: 'Inventario', to: '/inventario', icon: '📦' },
  {
    label: 'Ventas', icon: '🧾',
    children: [
      { label: 'Cotizaciones', to: '/cotizaciones' },
      { label: 'Nueva Cotización', to: '/cotizaciones/nueva' },
      { label: 'Facturas', to: '/facturacion' },
      { label: 'Nueva Factura', to: '/facturacion/nueva' },
      { label: 'Nota Crédito', to: '/facturacion/nota-credito/nueva' },
      { label: 'Nota Débito', to: '/facturacion/nota-debito/nueva' },
      { label: 'Anticipos', to: '/anticipos' },
      { label: 'Resoluciones DIAN', to: '/facturacion/resoluciones' },
    ],
  },
  {
    label: 'Cartera', icon: '💳',
    children: [
      { label: 'Por Cobrar', to: '/cartera/por-cobrar' },
      { label: 'Por Pagar', to: '/cartera/por-pagar' },
      { label: 'Resumen', to: '/cartera/resumen' },
    ],
  },
  {
    label: 'Contabilidad', icon: '📒',
    children: [
      { label: 'Plan de Cuentas', to: '/contabilidad/puc' },
      { label: 'Asientos', to: '/contabilidad/asientos' },
      { label: 'Reportes', to: '/contabilidad/reportes' },
      { label: 'Centros de Costo', to: '/contabilidad/centros-costo' },
      { label: 'Cierre de Período', to: '/contabilidad/cierres' },
      { label: 'Flujo de Caja', to: '/contabilidad/flujo-caja' },
      { label: 'Reporte Personalizado', to: '/reportes/personalizado' },
    ],
  },
  {
    label: 'Presupuesto', icon: '📈',
    children: [
      { label: 'Presupuestos', to: '/presupuestos' },
      { label: 'Nuevo Presupuesto', to: '/presupuestos/nuevo' },
    ],
  },
  {
    label: 'Activos Fijos', icon: '🏢',
    children: [
      { label: 'Activos', to: '/activos' },
      { label: 'Nuevo Activo', to: '/activos/nuevo' },
      { label: 'Reportes Activos', to: '/activos/reportes' },
    ],
  },
  {
    label: 'Nómina', icon: '💰',
    children: [
      { label: 'Empleados', to: '/nomina/empleados' },
      { label: 'Liquidar Nómina', to: '/nomina/liquidar' },
      { label: 'Historial', to: '/nomina/historial' },
    ],
  },
  {
    label: 'Bancos', icon: '🏦',
    children: [
      { label: 'Cuentas Bancarias', to: '/bancos/cuentas' },
    ],
  },
  {
    label: 'Configuración', icon: '⚙️',
    children: [
      { label: 'Empresas', to: '/empresas' },
      { label: 'Notificaciones', to: '/notificaciones' },
      { label: 'Config. Notificaciones', to: '/configuracion/notificaciones' },
      { label: 'Usuarios', to: '/usuarios', roles: ['admin'] },
      { label: 'Importar Datos', to: '/importar' },
      { label: 'Centros de Costo', to: '/contabilidad/centros-costo' },
      { label: 'Auditoría', to: '/auditoria', roles: ['admin'] },
    ],
  },
]

const linkCls = ({ isActive }) =>
  `flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors min-h-[44px] ${
    isActive ? 'bg-blue-700 text-white' : 'text-slate-300 hover:bg-slate-700 hover:text-white'
  }`

function EmpresaSelector({ user, onCambiar }) {
  const [empresas, setEmpresas] = useState([])
  const [cambiando, setCambiando] = useState(false)

  useEffect(() => {
    api.get('/empresas/').then(({ data }) => {
      const lista = Array.isArray(data) ? data : (data.results || [])
      setEmpresas(lista)
    }).catch(() => {})
  }, [user?.empresa_activa])

  async function handleChange(e) {
    const id = e.target.value
    if (!id || cambiando) return
    setCambiando(true)
    try {
      await onCambiar(id)
      window.location.reload()
    } catch {
      setCambiando(false)
    }
  }

  if (empresas.length <= 1) {
    return (
      <p className="text-slate-400 text-xs truncate">
        {user?.empresa_activa?.nombre || user?.empresa || 'Mi Empresa'}
      </p>
    )
  }

  return (
    <select
      className="w-full text-xs bg-slate-700 text-slate-200 border border-slate-600 rounded px-1 py-0.5 mt-0.5"
      value={user?.empresa_activa?.id || ''}
      onChange={handleChange}
      disabled={cambiando}
    >
      {empresas.map(e => (
        <option key={e.id} value={e.id}>{e.nombre}</option>
      ))}
    </select>
  )
}

export default function Sidebar({ isOpen, onClose }) {
  const { user, logout, cambiarEmpresa } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const rol = user?.rol || 'auxiliar'

  const puedeVer = (item) => {
    if (!item.roles) return true
    return item.roles.includes(rol) || user?.is_superuser
  }

  const handleLinkClick = () => {
    if (window.innerWidth < 768) onClose()
  }

  return (
    <aside
      className={`
        fixed inset-y-0 left-0 z-40 w-64 md:w-56 bg-slate-800 flex flex-col shrink-0
        transform transition-transform duration-200 ease-in-out
        md:relative md:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}
    >
      <div className="px-4 py-4 border-b border-slate-700 flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-white font-bold text-lg">ContaApp</p>
          <EmpresaSelector user={user} onCambiar={cambiarEmpresa} />
          <span className="inline-block mt-1 text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded">
            {rol}
          </span>
        </div>
        <button
          onClick={onClose}
          className="md:hidden ml-2 mt-1 text-slate-400 hover:text-white text-lg leading-none"
          aria-label="Cerrar menú"
        >
          ✕
        </button>
      </div>

      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto text-sm">
        {nav.map((item) => {
          if (!puedeVer(item)) return null
          if (item.children) {
            const visibles = item.children.filter(puedeVer)
            if (!visibles.length) return null
            return (
              <div key={item.label}>
                <p className="px-3 pt-3 pb-1 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {item.icon} {item.label}
                </p>
                {visibles.map((child) => (
                  <NavLink
                    key={child.to}
                    to={child.to}
                    className={linkCls}
                    onClick={handleLinkClick}
                  >
                    {child.label}
                  </NavLink>
                ))}
              </div>
            )
          }
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={linkCls}
              end={item.to === '/'}
              onClick={handleLinkClick}
            >
              {item.icon} {item.label}
            </NavLink>
          )
        })}
      </nav>

      <div className="px-4 py-3 border-t border-slate-700">
        <p className="text-slate-400 text-xs mb-1 truncate">{user?.username}</p>
        <div className="flex items-center justify-between">
          <button onClick={logout} className="text-xs text-slate-400 hover:text-white py-1">
            Cerrar sesión →
          </button>
          <button
            onClick={toggleTheme}
            className="text-slate-400 hover:text-white text-lg leading-none p-1 rounded"
            aria-label="Cambiar modo"
            title={theme === 'light' ? 'Activar modo oscuro' : 'Activar modo claro'}
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </div>
    </aside>
  )
}
