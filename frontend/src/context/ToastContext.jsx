import { createContext, useContext, useState, useCallback } from 'react'

const ToastContext = createContext(null)

let nextId = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const add = useCallback((message, type = 'info', duration = 4000) => {
    const id = ++nextId
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => remove(id), duration)
    return id
  }, [])

  const remove = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const toast = {
    success: (msg, dur) => add(msg, 'success', dur),
    error: (msg, dur) => add(msg, 'error', dur || 6000),
    info: (msg, dur) => add(msg, 'info', dur),
    warning: (msg, dur) => add(msg, 'warning', dur),
  }

  return (
    <ToastContext.Provider value={{ toast, toasts, remove }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={remove} />
    </ToastContext.Provider>
  )
}

const ICONS = {
  success: '✅',
  error: '❌',
  info: 'ℹ️',
  warning: '⚠️',
}

const BG = {
  success: 'bg-green-50 border-green-200 text-green-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
}

function ToastContainer({ toasts, onRemove }) {
  if (toasts.length === 0) return null
  return (
    <div className="fixed bottom-4 right-4 z-[200] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-start gap-3 p-3 pr-4 rounded-lg border shadow-lg pointer-events-auto animate-fade-in ${BG[t.type]}`}
        >
          <span className="text-base shrink-0 mt-0.5">{ICONS[t.type]}</span>
          <p className="text-sm flex-1 leading-snug">{t.message}</p>
          <button
            onClick={() => onRemove(t.id)}
            className="shrink-0 opacity-50 hover:opacity-100 text-lg leading-none ml-1"
            aria-label="Cerrar"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}

export const useToast = () => {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast debe usarse dentro de ToastProvider')
  return ctx.toast
}
