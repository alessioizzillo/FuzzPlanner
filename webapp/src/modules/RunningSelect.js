import React, { useState, useMemo } from 'react'
import { useOptimizedSelectAnalyses } from '@/hooks/useOptimizedPolling'
import { useRemoveSelect } from '@/hooks/queries'
import SelectProgress from '@/components/SelectProgress'
import Icon from '@/components/Icon'

function flattenAnalyses(nested) {
  const result = []
  for (const brandId in nested) {
    for (const firmwareId in nested[brandId]) {
      for (const runId in nested[brandId][firmwareId]) {
        for (const binaryId in nested[brandId][firmwareId][runId]) {
          const item = nested[brandId][firmwareId][runId][binaryId]
          if (item?.dataChannelIds && Array.isArray(item.dataChannelIds)) {
            for (const channelItem of item.dataChannelIds) {
              if (typeof channelItem === 'object' && channelItem.dataChannelId) {
                result.push({
                  brandId,
                  firmwareId,
                  runId,
                  binaryId: item.binaryId || binaryId,
                  dataChannelId: channelItem.dataChannelId,
                  containerName: channelItem.containerName,
                })
              } else if (typeof channelItem === 'string') {
                result.push({
                  brandId,
                  firmwareId,
                  runId,
                  binaryId: item.binaryId || binaryId,
                  dataChannelId: channelItem,
                })
              }
            }
          } else if (item?.dataChannelId) {
            // Legacy structure support: single dataChannelId
            result.push({
              brandId,
              firmwareId,
              runId,
              binaryId: item.binaryId || binaryId,
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

export default function RunningSelectExperiments({ selectedBinaryFromTable }) {
  const selectedBinaryId = selectedBinaryFromTable?.id

  // Use the optimized polling hook that automatically handles the global state
  const { running: rawRunning, done: rawDone, isLoading, error, refetch } = useOptimizedSelectAnalyses(
    null, // brandId - will be fetched from global state inside the hook
    null, // firmwareId - will be fetched from global state inside the hook
    null, // runId - will be fetched from global state inside the hook
    selectedBinaryId, // binaryId from BinariesTable selection
    { includeBinaryFilter: true }
  )

  const removeSelectMutation = useRemoveSelect()

  const running = useMemo(() => {
    const flattened = flattenAnalyses(rawRunning)
    if (!selectedBinaryId) return []

    // Extract basename for filtering (since API returns basenames)
    const binaryIdForFilter = selectedBinaryId.split('/').pop()
    return flattened.filter(item => item.binaryId === binaryIdForFilter)
  }, [rawRunning, selectedBinaryId])

  const done = useMemo(() => {
    const flattened = flattenAnalyses(rawDone)
    if (!selectedBinaryId) return []

    // Extract basename for filtering (since API returns basenames)
    const binaryIdForFilter = selectedBinaryId.split('/').pop()
    return flattened.filter(item => item.binaryId === binaryIdForFilter)
  }, [rawDone, selectedBinaryId])

  const groupedRunning = useMemo(() => groupByBinaryId(running), [running])
  const groupedDone = useMemo(() => groupByBinaryId(done), [done])

  const [selected, setSelected] = useState({ type: 'running', id: null })
  const [removingId, setRemovingId] = useState(null)

  const handleRemove = async (item, e) => {
    e.stopPropagation() // Prevent selection when clicking remove button

    if (removingId === item.dataChannelId) return // Already removing

    try {
      setRemovingId(item.dataChannelId)
      await removeSelectMutation.mutateAsync({
        brandId: item.brandId,
        firmwareId: item.firmwareId,
        runId: item.runId,
        binaryId: item.binaryId,
        dataChannelId: item.dataChannelId
      })
      // Refetch to update the list
      if (refetch) refetch()
    } catch (error) {
      console.error('Failed to remove select analysis:', error)
    } finally {
      setRemovingId(null)
    }
  }

  const renderGroup = (group, type) => {
    return Object.entries(group).map(([binaryId, items]) => (
      <div key={`${type}-${binaryId}`} className="px-3 py-2 border-b border-gray-200">
        <div className="text-sm font-semibold text-gray-800 mb-1">
          Executable: <span className="font-mono text-gray-700">{binaryId}</span>
        </div>
        <div className="space-y-1">
          {items.map(item => {
            const isSelected = selected.type === type && selected.id === item.dataChannelId
            const isRemoving = removingId === item.dataChannelId
            return (
              <div
                key={`${item.runId}-${item.dataChannelId}`}
                className={`text-xs cursor-pointer transition rounded px-2 py-1 flex items-center justify-between group ${
                  isSelected ? 'bg-blue-100' : 'hover:bg-gray-100'
                }`}
                onClick={() => setSelected({ type, id: item.dataChannelId })}
              >
                <div className="flex-1 min-w-0">
                  <span className="text-gray-600 font-mono break-all">
                    {item.dataChannelId}
                  </span>
                  {type === 'running' && item.containerName && (
                    <SelectProgress containerName={item.containerName} />
                  )}
                </div>
                {type === 'running' && (
                  <button
                    onClick={(e) => handleRemove(item, e)}
                    disabled={isRemoving}
                    className="ml-2 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-red-500 hover:text-red-700 hover:bg-red-50 rounded p-1 disabled:opacity-50 disabled:cursor-not-allowed"
                    title={isRemoving ? "Removing..." : "Remove analysis"}
                  >
                    <Icon
                      name={isRemoving ? "loader" : "trash"}
                      className={`w-3 h-3 ${isRemoving ? 'animate-spin' : ''}`}
                    />
                  </button>
                )}
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
          <div className="p-3 text-sm text-gray-500 text-center">
            {selectedBinaryId ? 'No running analyses' : 'Select a binary from the table above to view analyses'}
          </div>
        )}
      </div>

      <div className="text-base font-semibold text-white-700">
        Completed Data Channel Analyses
      </div>
      <div className="max-h-52 overflow-auto bg-white border border-gray-300 rounded">
        {done.length > 0 ? (
          renderGroup(groupedDone, 'done')
        ) : (
          <div className="p-3 text-sm text-gray-500 text-center">
            {selectedBinaryId ? 'No completed analyses' : 'Select a binary from the table above to view analyses'}
          </div>
        )}
      </div>
    </div>
  )
}
