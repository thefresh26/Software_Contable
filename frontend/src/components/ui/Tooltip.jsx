import { useState } from 'react'

export default function Tooltip({ text, children, position = 'top' }) {
  const [visible, setVisible] = useState(false)

  const posClass = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  }[position]

  return (
    <span
      className="relative inline-flex items-center"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && (
        <span
          className={`absolute z-50 ${posClass} w-56 rounded-md bg-slate-800 text-white text-xs px-3 py-2 shadow-lg leading-snug pointer-events-none`}
          role="tooltip"
        >
          {text}
        </span>
      )}
    </span>
  )
}

export function HelpIcon({ text, position }) {
  return (
    <Tooltip text={text} position={position}>
      <span
        className="ml-1 inline-flex items-center justify-center w-4 h-4 rounded-full bg-gray-200 text-gray-500 text-xs font-bold cursor-help hover:bg-blue-100 hover:text-blue-600 transition-colors"
        tabIndex={0}
        aria-label="Ayuda"
      >
        ?
      </span>
    </Tooltip>
  )
}
