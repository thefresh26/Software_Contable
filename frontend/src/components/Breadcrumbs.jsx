import { Link, useLocation } from 'react-router-dom'

const LABELS = {
  '': 'Dashboard',
  'terceros': 'Terceros',
  'inventario': 'Inventario',
  'facturacion': 'Facturas',
  'nueva': 'Nueva',
  'nota-credito': 'Nota Crédito',
  'nota-debito': 'Nota Débito',
  'anticipos': 'Anticipos',
  'resoluciones': 'Resoluciones DIAN',
  'cotizaciones': 'Cotizaciones',
  'contabilidad': 'Contabilidad',
  'puc': 'Plan de Cuentas',
  'asientos': 'Libro Diario',
  'reportes': 'Reportes',
  'centros-costo': 'Centros de Costo',
  'cierres': 'Cierres de Período',
  'flujo-caja': 'Flujo de Caja',
  'presupuestos': 'Presupuestos',
  'nuevo': 'Nuevo',
  'activos': 'Activos Fijos',
  'nomina': 'Nómina',
  'empleados': 'Empleados',
  'liquidar': 'Liquidar',
  'historial': 'Historial',
  'cartera': 'Cartera',
  'por-cobrar': 'Por Cobrar',
  'por-pagar': 'Por Pagar',
  'resumen': 'Resumen',
  'bancos': 'Bancos',
  'cuentas': 'Cuentas',
  'extractos': 'Extracto',
  'conciliaciones': 'Conciliación',
  'reporte': 'Reporte',
  'empresas': 'Empresas',
  'notificaciones': 'Notificaciones',
  'configuracion': 'Configuración',
  'usuarios': 'Usuarios',
  'importar': 'Importar',
  'auditoria': 'Auditoría',
  'personalizado': 'Personalizado',
}

export default function Breadcrumbs() {
  const { pathname } = useLocation()
  if (pathname === '/') return null

  const parts = pathname.split('/').filter(Boolean)
  const crumbs = [{ label: 'Dashboard', to: '/' }]

  let path = ''
  parts.forEach((part) => {
    path += `/${part}`
    const label = LABELS[part] || (isNaN(Number(part)) ? part : `#${part}`)
    crumbs.push({ label, to: path })
  })

  if (crumbs.length <= 1) return null

  return (
    <nav className="flex items-center gap-1 text-xs text-gray-400 mb-4 flex-wrap" aria-label="Ruta de navegación">
      {crumbs.map((crumb, i) => (
        <span key={crumb.to} className="flex items-center gap-1">
          {i > 0 && <span className="text-gray-300">/</span>}
          {i === crumbs.length - 1 ? (
            <span className="text-gray-600 font-medium">{crumb.label}</span>
          ) : (
            <Link to={crumb.to} className="hover:text-blue-600 hover:underline transition-colors">
              {crumb.label}
            </Link>
          )}
        </span>
      ))}
    </nav>
  )
}
