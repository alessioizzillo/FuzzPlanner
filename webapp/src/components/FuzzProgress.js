import React from 'react'
import { useOptimizedFuzzProgress } from '@/hooks/useOptimizedPolling'

export default function FuzzProgress({ containerName }) {
  const { progress, isLoading: loading, error } = useOptimizedFuzzProgress(containerName)

  if (loading) {
    return <div className="text-xs text-gray-400">Loading...</div>
  }

  if (error) {
    return <div className="text-xs text-red-400">Error: {error}</div>
  }

  if (!progress) {
    return null
  }

  const getPhaseColor = (phase) => {
    switch (phase) {
      case 'booting': return 'text-yellow-500'
      case 'fuzzing': return 'text-blue-500'
      case 'processing': return 'text-purple-500'
      case 'completed': return 'text-green-500'
      case 'error': return 'text-red-500'
      default: return 'text-gray-400'
    }
  }

  const progressPercentage = Math.round(progress.progress * 100)

  return (
    <div className="text-xs mt-1">
      <div className={`font-semibold ${getPhaseColor(progress.phase)}`}>
        {progress.phase.toUpperCase()} {progressPercentage}%
      </div>
      <div className="text-gray-500 mt-0.5">
        {progress.message}
      </div>
      {progress.phase !== 'completed' && (
        <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
          <div
            className={`h-1 rounded-full transition-all duration-300 ${
              progress.phase === 'booting' ? 'bg-yellow-500' :
              progress.phase === 'fuzzing' ? 'bg-blue-500' :
              progress.phase === 'processing' ? 'bg-purple-500' :
              'bg-gray-400'
            }`}
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      )}
    </div>
  )
}