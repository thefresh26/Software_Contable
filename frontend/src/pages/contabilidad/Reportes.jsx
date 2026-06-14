import { useState } from 'react'
import api from '../../api/client'
import { descargarExcel } from '../../utils/excel'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

function FilaReporte({ label, valor, nivel = 0, negativo = false }) {
  const indent = nivel * 20
  return (
    <div className={`flex justify-between py-1.5 ${nivel === 0 ? 'font-bold border-t mt-1 pt-3' : ''}`} style={{ paddingLeft: indent }}>
      <span className={`text-sm ${nivel === 0 ? 'text-gray-800' : 'text-gray-600'}`}>{label}</span>
      <span className={`text-sm font-medium ${negativo ? 'text-red-600' : 'text-gray-800'}`}>{fmt(valor)}</span>
    </div>
  )
}

export default function Reportes() {
  const [tab, setTab] = useState('balance')
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10))
  const [desde, setDesde] = useState(new Date(new Date().getFullYear(), 0, 1).toISOString().slice(0, 10))
  const [hasta, setHasta] = useState(new Date().toISOString().slice(0, 10))
  const [balance, setBalance] = useState(null)
  const [resultados, setResultados] = useState(null)
  const [loading, setLoading] = useState(false)
  const [exportando, setExportando] = useState(false)

  const exportar = async (path, filename) => {
    setExportando(true)
    try { await descargarExcel(path, filename) }
    catch { alert('Error al exportar') }
    finally { setExportando(false) }
  }

  const cargarBalance = async () => {
    setLoading(true)
    try {
      const { data } = await api.get(`/contabilidad/asientos/balance-general/?fecha=${fecha}`)
      setBalance(data)
    } finally { setLoading(false) }
  }

  const cargarResultados = async () => {
    setLoading(true)
    try {
      const { data } = await api.get(`/contabilidad/asientos/estado-resultados/?desde=${desde}&hasta=${hasta}`)
      setResultados(data)
    } finally { setLoading(false) }
  }

  return (
    <div className="space-y-5 max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-800">Reportes Contables</h1>

      <div className="flex gap-2">
        <button onClick={() => setTab('balance')} className={tab === 'balance' ? 'btn-primary' : 'btn-secondary'}>Balance General</button>
        <button onClick={() => setTab('resultados')} className={tab === 'resultados' ? 'btn-primary' : 'btn-secondary'}>Estado de Resultados</button>
      </div>

      {tab === 'balance' && (
        <div className="card space-y-4">
          <div className="flex gap-3 items-end flex-wrap">
            <div><label className="label">Al corte de fecha</label><input className="input w-40" type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} /></div>
            <button className="btn-primary" onClick={cargarBalance} disabled={loading}>{loading ? 'Calculando…' : 'Generar'}</button>
            <button className="btn-excel" disabled={exportando} onClick={() => exportar(`/contabilidad/asientos/exportar-balance-general/?fecha=${fecha}`, `balance_general_${fecha}.xlsx`)}>
              {exportando ? '…' : '⬇ Excel'}
            </button>
          </div>

          {balance && (
            <div className="border rounded-lg p-4 space-y-2">
              <h2 className="font-bold text-lg text-center text-gray-800 mb-4">BALANCE GENERAL<br/><span className="text-sm font-normal text-gray-500">Al {fecha}</span></h2>
              <FilaReporte label="ACTIVOS" valor={balance.activos} nivel={0} />
              <FilaReporte label="Total Activos" valor={balance.activos} nivel={1} />
              <FilaReporte label="PASIVOS" valor={balance.pasivos} nivel={0} />
              <FilaReporte label="Total Pasivos" valor={balance.pasivos} nivel={1} />
              <FilaReporte label="PATRIMONIO" valor={balance.patrimonio} nivel={0} />
              {balance.utilidad_ejercicio !== undefined && (
                <FilaReporte label="Utilidad del ejercicio" valor={balance.utilidad_ejercicio} nivel={2} />
              )}
              <FilaReporte label="Total Patrimonio" valor={balance.patrimonio} nivel={1} />
              <div className="border-t mt-3 pt-3">
                <div className="flex justify-between font-bold">
                  <span>Pasivos + Patrimonio</span>
                  <span>{fmt(Number(balance.pasivos) + Number(balance.patrimonio))}</span>
                </div>
                <p className={`text-xs mt-1 ${balance.cuadrado ? 'text-green-600' : 'text-red-600'}`}>
                  {balance.cuadrado ? '✓ Balance cuadrado' : '⚠ Balance descuadrado'}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'resultados' && (
        <div className="card space-y-4">
          <div className="flex gap-3 items-end flex-wrap">
            <div><label className="label">Desde</label><input className="input w-40" type="date" value={desde} onChange={(e) => setDesde(e.target.value)} /></div>
            <div><label className="label">Hasta</label><input className="input w-40" type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} /></div>
            <button className="btn-primary" onClick={cargarResultados} disabled={loading}>{loading ? 'Calculando…' : 'Generar'}</button>
            <button className="btn-excel" disabled={exportando} onClick={() => exportar(`/contabilidad/asientos/exportar-estado-resultados/?desde=${desde}&hasta=${hasta}`, 'estado_resultados.xlsx')}>
              {exportando ? '…' : '⬇ Excel'}
            </button>
          </div>

          {resultados && (
            <div className="border rounded-lg p-4 space-y-2">
              <h2 className="font-bold text-lg text-center text-gray-800 mb-4">ESTADO DE RESULTADOS<br/><span className="text-sm font-normal text-gray-500">{desde} — {hasta}</span></h2>
              <FilaReporte label="INGRESOS OPERACIONALES" valor={resultados.ingresos} nivel={0} />
              <FilaReporte label="Ventas netas" valor={resultados.ingresos} nivel={1} />
              <FilaReporte label="(-) COSTOS DE VENTAS" valor={resultados.costos} nivel={0} negativo />
              <FilaReporte label="Costo mercancía vendida" valor={resultados.costos} nivel={1} />
              <div className="flex justify-between py-2 font-semibold border-t">
                <span className="text-sm">UTILIDAD BRUTA</span>
                <span className={`text-sm ${Number(resultados.utilidad_bruta) >= 0 ? 'text-green-600' : 'text-red-600'}`}>{fmt(resultados.utilidad_bruta)}</span>
              </div>
              <FilaReporte label="(-) GASTOS OPERACIONALES" valor={resultados.gastos} nivel={0} negativo />
              <FilaReporte label="Gastos de administración y ventas" valor={resultados.gastos} nivel={1} />
              <div className="flex justify-between py-3 font-bold border-t text-base">
                <span>UTILIDAD NETA</span>
                <span className={Number(resultados.utilidad_neta) >= 0 ? 'text-green-700' : 'text-red-700'}>{fmt(resultados.utilidad_neta)}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
