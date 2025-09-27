import classNames from 'classnames'
import React from 'react'

export default function Button({ children, onClick, className = '', disabled = false, ...props }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={classNames(
        'px-4 py-2 rounded-lg shadow transition-all duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 transform active:scale-95',
        {
          'bg-blue-600 hover:bg-blue-700 hover:shadow-lg text-white focus:ring-blue-500 hover:-translate-y-0.5': !disabled,
          'bg-gray-400 text-gray-700 cursor-not-allowed opacity-60': disabled
        },
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}
