import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../../api/client'

const fmt = (n) => Number(n || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

function Fila({ label, valor, signo, negativo }) {
  return (
    <div className="flex justify-between py-1 text-sm">
      <span className={negativo ? 'text-red-600' : 'text-gray-700'}>{signo ? `(${signo}) ` : ''}{label}</span>
      <span className={negativo ? 'text-red-600' : 'text-gray-700'}>{fmt(valor)}</span>
    </div>
  )
}

function SeccionAjustes({ titulo, saldoLabel, saldo, ajustes, ajustadoLabel, ajustado }) {
  return (
    <div className="card space-y-1">
      <h2 className="font-semibold text-gray-700 mb-2">{titulo}</h2>
      <Fila label={saldoLabel} valor={saldo} />
      {ajustes.map((grupo, i) => (
        grupo.items.map((item, j) => (
          <Fila key={`${i}-${j}`} label={`${grupo.label} — ${item.descripcion} (${item.fecha})`} valor={item.valor} signo={grupo.signo} negativo={grupo.signo === '−'} />
        ))
      ))}
      <div className="flex justify-between pt-2 mt-1 border-t font-bold text-slate-800">
        <span>{ajustadoLabel}</span><span>{fmt(ajustado)}</span>
      </div>
    </div>
  )
}

export default function ConciliacionReporte() {
  const { id } = useParams()
  const [reporte, setReporte] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.get(`/bancos/conciliaciones/${id}/reporte/`).then(({ data }) => setReporte(data)).finally(() => setLoading(false))
  }, [id])

  if (loading || !reporte) return <div className="flex justify-center pt-20"><div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" /></div>

  const ajustesExtracto = [
    { label: 'Depósito en tránsito', signo: '+', items: reporte.ajustes_al_extracto?.depositos_en_transito || [] },
    { label: 'Cheque girado no cobrado', signo: '−', items: reporte.ajustes_al_extracto?.cheques_girados_no_cobrados || [] },
  ]
  const ajustesLibros = [
    { label: 'Nota crédito banco no registrada', signo: '+', items: reporte.ajustes_a_libros?.notas_credito_no_registradas || [] },
    { label: 'Nota débito banco no registrada', signo: '−', items: reporte.ajustes_a_libros?.notas_debito_no_registradas || [] },
    { label: 'Error en libros', signo: '', items: reporte.ajustes_a_libros?.errores_libros || [] },
  ]

  return (
    <div className="max-w-4xl space-y-4">
      <div className="flex justify-between items-start">
        <div>
          <Link to={`/bancos/conciliaciones/${id}`} className="text-xs text-blue-600 hover:underline">← Volver a la conciliación</Link>
          <h1 className="text-2xl font-bold text-slate-800 mt-1">Reporte de Conciliación Bancaria</h1>
          <p className="text-sm text-gray-500">{reporte.cuenta} — Período: {reporte.periodo}</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={() => window.print()}>Imprimir</button>
          <a href={`/api/bancos/conciliaciones/${id}/reporte/?formato=pdf`} target="_blank" rel="noreferrer" className="btn-primary inline-flex items-center">Descargar PDF</a>
        </div>
      </div>

      <SeccionAjustes
        titulo="A. Saldo según extracto bancario"
        saldoLabel="Saldo según extracto bancario"
        saldo={reporte.saldo_extracto_bancario}
        ajustes={ajustesExtracto}
        ajustadoLabel="SALDO EXTRACTO AJUSTADO"
        ajustado={reporte.saldo_extracto_ajustado}
      />

      <SeccionAjustes
        titulo="B. Saldo según libros"
        saldoLabel="Saldo según libros"
        saldo={reporte.saldo_en_libros}
        ajustes={ajustesLibros}
        ajustadoLabel="SALDO LIBROS AJUSTADO"
        ajustado={reporte.saldo_libros_ajustado}
      />

      <div className={`card flex justify-between items-center border-2 ${reporte.conciliado ? 'border-green-600 bg-green-50' : 'border-red-600 bg-red-50'}`}>
        <div className="space-y-1">
          <div className="flex justify-between gap-8 text-sm text-gray-600">
            <span>Saldo extracto ajustado</span><span>{fmt(reporte.saldo_extracto_ajustado)}</span>
          </div>
          <div className="flex justify-between gap-8 text-sm text-gray-600">
            <span>Saldo libros ajustado</span><span>{fmt(reporte.saldo_libros_ajustado)}</span>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs uppercase text-gray-500">Diferencia</p>
          <p className={`text-2xl font-bold ${reporte.conciliado ? 'text-green-700' : 'text-red-600'}`}>{fmt(reporte.diferencia_final)}</p>
          <span className={reporte.conciliado ? 'badge-green' : 'badge-red'}>{reporte.conciliado ? 'CONCILIADO ✓' : 'NO CONCILIADO'}</span>
        </div>
      </div>

      <div className="card">
        <h2 className="font-semibold text-gray-700 mb-2">Resumen de movimientos</h2>
        <div className="grid grid-cols-3 gap-3 text-center text-sm">
          <div><p className="text-2xl font-bold text-slate-800">{reporte.resumen_movimientos?.total_movimientos_extracto}</p><p className="text-xs text-gray-500">Total movimientos</p></div>
          <div><p className="text-2xl font-bold text-green-700">{reporte.resumen_movimientos?.movimientos_conciliados}</p><p className="text-xs text-gray-500">Conciliados</p></div>
          <div><p className="text-2xl font-bold text-yellow-600">{reporte.resumen_movimientos?.movimientos_pendientes}</p><p className="text-xs text-gray-500">Pendientes</p></div>
        </div>
      </div>

      <p className="text-xs text-gray-400 text-right">Fecha de reporte: {reporte.fecha_reporte}</p>
    </div>
  )
}
