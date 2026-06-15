import { createContext, useContext, useState, useCallback } from 'react'

const ConfirmContext = createContext(null)

export function ConfirmProvider({ children }) {
  const [state, setState] = useState(null)

  const confirm = useCallback(({ title, message, confirmLabel = 'Confirmar', danger = false }) => {
    return new Promise((resolve) => {
      setState({ title, message, confirmLabel, danger, resolve })
    })
  }, [])

  const handleClose = (result) => {
    state?.resolve(result)
    setState(null)
  }

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {state && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm">
            <div className="px-6 py-5">
              <div className="flex items-start gap-3">
                <span className="text-2xl shrink-0">{state.danger ? '⚠️' : '❓'}</span>
                <div>
                  <h3 className="font-semibold text-gray-800 text-base">{state.title}</h3>
                  {state.message && (
                    <p className="text-sm text-gray-500 mt-1 leading-relaxed">{state.message}</p>
                  )}
                </div>
              </div>
            </div>
            <div className="px-6 pb-5 flex justify-end gap-3">
              <button
                className="btn-secondary text-sm"
                onClick={() => handleClose(false)}
              >
                Cancelar
              </button>
              <button
                className={state.danger ? 'btn-danger text-sm' : 'btn-primary text-sm'}
                onClick={() => handleClose(true)}
              >
                {state.confirmLabel}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  )
}

export const useConfirm = () => {
  const ctx = useContext(ConfirmContext)
  if (!ctx) throw new Error('useConfirm debe usarse dentro de ConfirmProvider')
  return ctx
}
