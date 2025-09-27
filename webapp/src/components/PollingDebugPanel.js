import React, { useState, useEffect } from 'react'
import { usePollingStats } from '@/hooks/useOptimizedPolling'
import Icon from '@/components/Icon'

export default function PollingDebugPanel() {
  const { stats, refreshAll, activePolls } = usePollingStats()
  const [isExpanded, setIsExpanded] = useState(false)

  if (process.env.NODE_ENV !== 'development') {
    return null // Only show in development
  }

  return (
    <div className="fixed bottom-4 right-4 bg-gray-800 text-white text-xs rounded-lg shadow-lg z-50">
      <div
        className="px-3 py-2 cursor-pointer flex items-center justify-between min-w-48"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="flex items-center">
          <Icon name="chart" className="w-4 h-4 mr-1" />
          Polling: {stats.activePolls} active
        </span>
        <span className="ml-2">
          {isExpanded ? '▼' : '▲'}
        </span>
      </div>

      {isExpanded && (
        <div className="px-3 py-2 border-t border-gray-700 space-y-2">
          <div className="flex justify-between">
            <span>Active Polls:</span>
            <span>{stats.activePolls}</span>
          </div>

          <div className="space-y-1">
            <div className="font-semibold">Endpoints:</div>
            {activePolls.map((poll, index) => (
              <div key={index} className="text-gray-300 text-xs truncate">
                {poll}
              </div>
            ))}
          </div>

          <button
            onClick={refreshAll}
            className="w-full px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs"
          >
            Force Refresh All
          </button>

          <div className="text-gray-400 text-xs flex flex-col gap-1">
            <div className="flex items-center">
              <Icon name="info" className="w-3 h-3 mr-1" />
              ETag caching active
            </div>
            <div className="flex items-center">
              <Icon name="rocket" className="w-3 h-3 mr-1" />
              Smart backoff enabled
            </div>
          </div>
        </div>
      )}
    </div>
  )
}