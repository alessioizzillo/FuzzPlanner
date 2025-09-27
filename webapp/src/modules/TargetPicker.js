import React, { useCallback, useState } from 'react'
import Picker from '@/components/Picker'
import Icon from '@/components/Icon'
import { useSelectedBrand } from '@/hooks/store/selectedBrand'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { useSelectedRun } from '@/hooks/store/selectedRun'
import { useOptimizedSelectAnalyses } from '@/hooks/useOptimizedPolling'
import {
  useSelectedBinary,
  useSetSelectedBinary,
  useSelectedDataChannel,
  useSetSelectedDataChannel
} from '@/hooks/store/selectedBinaryDataChannel'

import { removeSelect, removeSelectBinary } from '@/hooks/queries'

function flattenAnalyses(nested) {
  const result = []
  for (const brandId in nested) {
    const fwMap = nested[brandId]
    for (const firmwareId in fwMap) {
      const runMap = fwMap[firmwareId]
      for (const runId in runMap) {
        const binaryMap = runMap[runId]
        for (const binaryId in binaryMap) {
          const item = binaryMap[binaryId]
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

export default function TargetPicker() {
  const brandId = useSelectedBrand()
  const firmwareId = useSelectedFirmware()
  const runId = useSelectedRun()

  // For Target Binary picker, we want to see ALL binaries, not filtered by currently selected binary
  const { running, done, refresh } = useOptimizedSelectAnalyses(null, null, null, null, { includeBinaryFilter: false })

  const selectedBinary = useSelectedBinary()
  const setSelectedBinary = useSetSelectedBinary()
  const selectedDataChannel = useSelectedDataChannel()
  const setSelectedDataChannel = useSetSelectedDataChannel()

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const runningList = flattenAnalyses(running)
  const doneList = flattenAnalyses(done)

  const binaries = Array.from(new Set([
    ...runningList.map(a => a.binaryId),
    ...doneList.map(a => a.binaryId),
  ])).filter(Boolean)

  const channels = Array.from(new Set([
    ...runningList.filter(a => a.binaryId === selectedBinary).map(a => a.dataChannelId),
    ...doneList.filter(a => a.binaryId === selectedBinary).map(a => a.dataChannelId),
  ])).filter(Boolean)

  const handleBinaryChange = useCallback(id => {
    setSelectedBinary(id)
    setSelectedDataChannel('')
  }, [setSelectedBinary, setSelectedDataChannel])

  const handleChannelChange = useCallback(id => {
    setSelectedDataChannel(id)
  }, [setSelectedDataChannel])

  const handleRemoveChannel = useCallback(async () => {
    if (!selectedBinary || !selectedDataChannel) return
    setLoading(true)
    setError(null)
    try {
      await removeSelect({
        brandId,
        firmwareId,
        runId,
        binaryId: selectedBinary,
        dataChannelId: selectedDataChannel
      })

      setSelectedDataChannel('')

      await refresh()
    } catch (e) {
      setError(e.message || 'Failed to remove data channel select analysis')
    } finally {
      setLoading(false)
    }
  }, [
    brandId, firmwareId, runId,
    selectedBinary, selectedDataChannel,
    setSelectedDataChannel, refresh
  ])

  const handleRemoveBinary = useCallback(async () => {
    if (!selectedBinary) return
    setLoading(true)
    setError(null)
    try {
      await removeSelectBinary({
        brandId,
        firmwareId,
        runId,
        binaryId: selectedBinary
      })

      setSelectedBinary('')
      setSelectedDataChannel('')

      await refresh()
    } catch (e) {
      setError(e.message || 'Failed to remove binary select analyses')
    } finally {
      setLoading(false)
    }
  }, [
    brandId, firmwareId, runId,
    selectedBinary, setSelectedBinary,
    setSelectedDataChannel, refresh
  ])

  return (
    <div className="flex space-x-4">
      <div className="flex-1 min-w-0">
        <h2 className="text-lg font-bold mb-2 text-yellow-400 flex items-center gap-2">
          <Icon name="target" className="w-5 h-5" />
          Target Binary
        </h2>
        <div className="flex items-center">
          <Picker
            items={binaries.map(b => ({ id: b, label: b }))}
            selected={selectedBinary || ''}
            setSelected={handleBinaryChange}
            resetSelected={() => handleBinaryChange('')}
            placeholder={binaries.length === 0 ? 'No binaries available' : 'Select a binary...'}
            disabled={loading}
          />
          {selectedBinary && (
            <button
              title="Remove all select analyses for this binary"
              onClick={handleRemoveBinary}
              disabled={loading}
              className="-ml-5 rounded transition-colors text-red-500 hover:text-red-700 hover:bg-red-50 disabled:text-gray-400 disabled:cursor-not-allowed"
              type="button"
            >
              <Icon name="trash" className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <h2 className="text-lg font-bold mb-2 text-yellow-400 flex items-center gap-2">
          <Icon name="analyze" className="w-5 h-5" />
          Data Channel
        </h2>
        <div className="flex items-center">
          <Picker
            items={channels.map(c => ({ id: c, label: c }))}
            selected={selectedDataChannel || ''}
            setSelected={handleChannelChange}
            resetSelected={() => handleChannelChange('')}
            placeholder={channels.length === 0 ? 'No channels available' : 'Select a data channel...'}
            disabled={!selectedBinary || loading}
          />
          {selectedBinary && selectedDataChannel && (
            <button
              title="Remove select analysis for this data channel"
              onClick={handleRemoveChannel}
              disabled={loading}
              className="-ml-5 rounded transition-colors text-red-500 hover:text-red-700 hover:bg-red-50 disabled:text-gray-400 disabled:cursor-not-allowed"
              type="button"
            >
              <Icon name="trash" className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="text-red-600 mt-2 col-span-full">
          Error: {error}
        </div>
      )}
    </div>
  )
}
