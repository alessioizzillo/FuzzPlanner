import classNames from 'classnames'
import React from 'react'

export default function Button({ children, onClick, className = '', disabled = false, ...props }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={classNames(
        'px-4 py-2 rounded-lg shadow transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2',
        {
          'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500': !disabled,
          'bg-gray-400 text-gray-700 cursor-not-allowed': disabled
        },
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}
