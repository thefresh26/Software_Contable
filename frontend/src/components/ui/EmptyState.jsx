export default function EmptyState({ icon = '📭', title, description, action, actionLabel }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <span className="text-5xl mb-4">{icon}</span>
      <h3 className="text-base font-semibold text-gray-700 mb-1">{title}</h3>
      {description && <p className="text-sm text-gray-400 max-w-xs mb-5">{description}</p>}
      {action && (
        <button onClick={action} className="btn-primary text-sm">
          {actionLabel || 'Crear primero'}
        </button>
      )}
    </div>
  )
}
