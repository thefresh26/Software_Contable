import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import { ToastProvider } from './context/ToastContext'
import { ConfirmProvider } from './components/ui/ConfirmDialog'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Terceros from './pages/Terceros'
import Inventario from './pages/Inventario'
import FacturaLista from './pages/facturacion/FacturaLista'
import FacturaNueva from './pages/facturacion/FacturaNueva'
import CotizacionLista from './pages/cotizaciones/CotizacionLista'
import CotizacionNueva from './pages/cotizaciones/CotizacionNueva'
import PUC from './pages/contabilidad/PUC'
import Asientos from './pages/contabilidad/Asientos'
import Reportes from './pages/contabilidad/Reportes'
import CentrosCosto from './pages/contabilidad/CentrosCosto'
import PresupuestoLista from './pages/presupuestos/PresupuestoLista'
import PresupuestoNuevo from './pages/presupuestos/PresupuestoNuevo'
import ActivoLista from './pages/activos/ActivoLista'
import ActivoNuevo from './pages/activos/ActivoNuevo'
import ActivoDetalle from './pages/activos/ActivoDetalle'
import TablaDepreciacion from './pages/activos/TablaDepreciacion'
import ActivoReportes from './pages/activos/ActivoReportes'
import NotificacionesLista from './pages/notificaciones/NotificacionesLista'
import ConfiguracionNotificaciones from './pages/notificaciones/ConfiguracionNotificaciones'
import PorCobrar from './pages/cartera/PorCobrar'
import PorPagar from './pages/cartera/PorPagar'
import ResumenCartera from './pages/cartera/ResumenCartera'
import Empleados from './pages/nomina/Empleados'
import Liquidar from './pages/nomina/Liquidar'
import Historial from './pages/nomina/Historial'
import CuentasBancarias from './pages/bancos/CuentasBancarias'
import ExtractoDetalle from './pages/bancos/ExtractoDetalle'
import ConciliacionDetalle from './pages/bancos/ConciliacionDetalle'
import ConciliacionReporte from './pages/bancos/ConciliacionReporte'
import Usuarios from './pages/Usuarios'
import Importar from './pages/Importar'
import EmpresaLista from './pages/empresas/EmpresaLista'
import EmpresaNueva from './pages/empresas/EmpresaNueva'
import CierresPeriodo from './pages/contabilidad/CierresPeriodo'
import FlujoCaja from './pages/contabilidad/FlujoCaja'
import Anticipos from './pages/facturacion/Anticipos'
import NotaCredito from './pages/facturacion/NotaCredito'
import NotaDebito from './pages/facturacion/NotaDebito'
import Auditoria from './pages/Auditoria'
import ResolucionesDIAN from './pages/facturacion/ResolucionesDIAN'
import ReportePersonalizado from './pages/ReportePersonalizado'

export default function App() {
  return (
    <ThemeProvider>
    <AuthProvider>
    <ToastProvider>
    <ConfirmProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="terceros" element={<Terceros />} />
            <Route path="inventario" element={<Inventario />} />
            <Route path="facturacion" element={<FacturaLista />} />
            <Route path="facturacion/nueva" element={<FacturaNueva />} />
            <Route path="cotizaciones" element={<CotizacionLista />} />
            <Route path="cotizaciones/nueva" element={<CotizacionNueva />} />
            <Route path="contabilidad/puc" element={<PUC />} />
            <Route path="contabilidad/asientos" element={<Asientos />} />
            <Route path="contabilidad/reportes" element={<Reportes />} />
            <Route path="contabilidad/centros-costo" element={<CentrosCosto />} />
            <Route path="contabilidad/cierres" element={<CierresPeriodo />} />
            <Route path="contabilidad/flujo-caja" element={<FlujoCaja />} />
            <Route path="anticipos" element={<Anticipos />} />
            <Route path="facturacion/nota-credito/nueva" element={<NotaCredito />} />
            <Route path="facturacion/nota-debito/nueva" element={<NotaDebito />} />
            <Route path="facturacion/resoluciones" element={<ResolucionesDIAN />} />
            <Route path="auditoria" element={<Auditoria />} />
            <Route path="reportes/personalizado" element={<ReportePersonalizado />} />
            <Route path="presupuestos" element={<PresupuestoLista />} />
            <Route path="presupuestos/nuevo" element={<PresupuestoNuevo />} />
            <Route path="activos" element={<ActivoLista />} />
            <Route path="activos/nuevo" element={<ActivoNuevo />} />
            <Route path="activos/reportes" element={<ActivoReportes />} />
            <Route path="activos/:id" element={<ActivoDetalle />} />
            <Route path="activos/:id/tabla-depreciacion" element={<TablaDepreciacion />} />
            <Route path="notificaciones" element={<NotificacionesLista />} />
            <Route path="configuracion/notificaciones" element={<ConfiguracionNotificaciones />} />
            <Route path="cartera/por-cobrar" element={<PorCobrar />} />
            <Route path="cartera/por-pagar" element={<PorPagar />} />
            <Route path="cartera/resumen" element={<ResumenCartera />} />
            <Route path="nomina/empleados" element={<Empleados />} />
            <Route path="nomina/liquidar" element={<Liquidar />} />
            <Route path="nomina/historial" element={<Historial />} />
            <Route path="bancos/cuentas" element={<CuentasBancarias />} />
            <Route path="bancos/extractos/:id" element={<ExtractoDetalle />} />
            <Route path="bancos/conciliaciones/:id" element={<ConciliacionDetalle />} />
            <Route path="bancos/conciliaciones/:id/reporte" element={<ConciliacionReporte />} />
            <Route path="usuarios" element={<Usuarios />} />
            <Route path="importar" element={<Importar />} />
            <Route path="empresas" element={<EmpresaLista />} />
            <Route path="empresas/nueva" element={<EmpresaNueva />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfirmProvider>
    </ToastProvider>
    </AuthProvider>
    </ThemeProvider>
  )
}
