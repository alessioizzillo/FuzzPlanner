import { useGetAnalysisProgress } from '@/hooks/queries'

export default function AnalysisProgress({ containerName }) {
  const { data: progress, isLoading, isError } = useGetAnalysisProgress(containerName)

  if (!containerName) return null
  if (isLoading) return <div className="text-sm text-gray-500">Loading progress...</div>
  if (isError || !progress) return null

  const getPhaseColor = (phase) => {
    switch (phase) {
      case 'booting': return 'bg-blue-500'
      case 'analyzing': return 'bg-yellow-500'
      case 'replaying': return 'bg-purple-500'
      case 'processing': return 'bg-orange-500'
      case 'fuzzing': return 'bg-green-500'
      case 'completed': return 'bg-green-600'
      case 'error': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getPhaseIcon = (phase) => {
    switch (phase) {
      case 'booting': return '🚀'
      case 'analyzing': return '🔍'
      case 'replaying': return '🔁'
      case 'processing': return '⚙️'
      case 'fuzzing': return '🎯'
      case 'completed': return '✅'
      case 'error': return '❌'
      default: return '⏳'
    }
  }

  const progressPercent = Math.round(progress.progress * 100)

  return (
    <div className="bg-gray-800 border border-gray-600 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getPhaseIcon(progress.phase)}</span>
          <span className="font-semibold text-white capitalize">{progress.phase}</span>
          <span className="text-sm text-gray-400">({containerName})</span>
        </div>
        <span className="text-sm font-medium text-white">{progressPercent}%</span>
      </div>

      <div className="mb-3">
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${getPhaseColor(progress.phase)}`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      <div className="text-sm text-gray-300 mb-2">
        {progress.message}
      </div>

      {progress.details && Object.keys(progress.details).length > 0 && (
        <div className="text-xs text-gray-400 mt-2">
          <details>
            <summary className="cursor-pointer hover:text-white">Details</summary>
            <pre className="mt-1 bg-gray-900 p-2 rounded text-xs overflow-auto">
              {JSON.stringify(progress.details, null, 2)}
            </pre>
          </details>
        </div>
      )}

      <div className="text-xs text-gray-500 mt-2">
        Last updated: {new Date(progress.timestamp).toLocaleTimeString()}
      </div>
    </div>
  )
}