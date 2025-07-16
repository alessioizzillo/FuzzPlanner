import React, { useState, useMemo } from 'react'
import { useSelectAnalyses } from '@/hooks/store/useSelectAnalyses'

function flattenAnalyses(nested) {
  const result = []
  for (const brandId in nested) {
    for (const firmwareId in nested[brandId]) {
      for (const runId in nested[brandId][firmwareId]) {
        for (const binaryId in nested[brandId][firmwareId][runId]) {
          const item = nested[brandId][firmwareId][runId][binaryId]
          if (item?.dataChannelId) {
            result.push({
              brandId,
              firmwareId,
              runId,
              binaryId,
              dataChannelId: item.dataChannelId,
            })
          }
        }
      }
    }
  }
  return result
}

function groupByBinaryId(items) {
  const grouped = {}
  for (const item of items) {
    if (!grouped[item.binaryId]) {
      grouped[item.binaryId] = []
    }
    grouped[item.binaryId].push(item)
  }
  return grouped
}

export default function RunningSelectExperiments() {
  const { running: rawRunning, done: rawDone } = useSelectAnalyses()

  const running = useMemo(() => flattenAnalyses(rawRunning), [rawRunning])
  const done = useMemo(() => flattenAnalyses(rawDone), [rawDone])

  const groupedRunning = useMemo(() => groupByBinaryId(running), [running])
  const groupedDone = useMemo(() => groupByBinaryId(done), [done])

  const [selected, setSelected] = useState({ type: 'running', id: null })

  const renderGroup = (group, type) => {
    return Object.entries(group).map(([binaryId, items]) => (
      <div key={`${type}-${binaryId}`} className="px-3 py-2 border-b border-gray-200">
        <div className="text-sm font-semibold text-gray-800 mb-1">
          Executable: <span className="font-mono text-gray-700">{binaryId}</span>
        </div>
        <div className="space-y-1">
          {items.map(item => {
            const isSelected = selected.type === type && selected.id === item.dataChannelId
            return (
              <div
                key={`${item.runId}-${item.dataChannelId}`}
                className={`text-xs cursor-pointer transition rounded px-2 py-1 ${
                  isSelected ? 'bg-blue-100' : 'hover:bg-gray-100'
                }`}
                onClick={() => setSelected({ type, id: item.dataChannelId })}
              >
                <span className="text-gray-600 font-mono break-all">
                  {item.dataChannelId}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    ))
  }

  return (
    <div className="w-full space-y-6">
      <div className="text-base font-semibold text-white-700">
        Running Data Channel Analyses
      </div>
      <div className="max-h-52 overflow-auto bg-white border border-gray-300 rounded">
        {running.length > 0 ? (
          renderGroup(groupedRunning, 'running')
        ) : (
          <div className="p-2 text-sm text-gray-500">No running analyses</div>
        )}
      </div>

      <div className="text-base font-semibold text-white-700">
        Completed Data Channel Analyses
      </div>
      <div className="max-h-52 overflow-auto bg-white border border-gray-300 rounded">
        {done.length > 0 ? (
          renderGroup(groupedDone, 'done')
        ) : (
          <div className="p-2 text-sm text-gray-500">No completed analyses</div>
        )}
      </div>
    </div>
  )
}
