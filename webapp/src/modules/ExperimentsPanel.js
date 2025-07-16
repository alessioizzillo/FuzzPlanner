import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useSelectedBrand } from '@/hooks/store/selectedBrand'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { useFuzzExperimentsPolling } from '@/hooks/store/useFuzzExperiments'
import { getExperimentInfo, removeExperiment } from '@/hooks/queries'

export default function ExperimentsPanel() {
  const brandId    = useSelectedBrand()
  const firmwareId = useSelectedFirmware()

  const { data, isFetching, error } = useFuzzExperimentsPolling(brandId, firmwareId)
  const running = data?.running ?? []
  const done    = data?.done    ?? []

  const [selectedExp, setSelectedExp] = useState(null)
  const [expInfo, setExpInfo]         = useState(null)
  const [loadingRemove, setLoadingRemove] = useState(false)

  const [loadingRunningExps, setLoadingRunningExps] = useState(new Set())

  useEffect(() => {
    setLoadingRunningExps(new Set(running))
  }, [running])

  const detailsRef = useRef(null)
  const scrollPos = useRef(0)
  const onScroll = () => {
    if (detailsRef.current) {
      scrollPos.current = detailsRef.current.scrollTop
    }
  }
  useEffect(() => {
    if (detailsRef.current) {
      detailsRef.current.scrollTop = scrollPos.current
    }
  }, [expInfo])

  useEffect(() => {
    if (!selectedExp) {
      setExpInfo(null)
      return
    }

    let isMounted = true

    async function fetchExpInfo() {
      try {
        const info = await getExperimentInfo({ brandId, firmwareId, expName: selectedExp })
        if (!isMounted) return

        setExpInfo(info)

        if (running.includes(selectedExp)) {
          const fuzzerStatsKeys = [
            'fuzz_time',
            'execs_done',
            'execs_per_sec',
            'paths_total',
            'paths_found',
            'paths_favored',
            'bitmap_cvg',
            'stability',
            'unique_crashes',
            'unique_hangs',
          ]

          const hasValidStats = fuzzerStatsKeys.some(key => {
            const val = info[key]
            return val !== undefined && val !== null && val !== 0 && val !== ''
          })

          setLoadingRunningExps(prev => {
            const copy = new Set(prev)
            if (hasValidStats) {
              copy.delete(selectedExp)
            } else {
              copy.add(selectedExp)
            }
            return copy
          })
        } else {
          setLoadingRunningExps(prev => {
            const copy = new Set(prev)
            copy.delete(selectedExp)
            return copy
          })
        }
      } catch (err) {
        console.error('Failed to fetch experiment info:', err)
        if (isMounted) {
          setExpInfo({ error: 'Failed to load experiment info' })

          if (running.includes(selectedExp)) {
            setLoadingRunningExps(prev => new Set(prev).add(selectedExp))
          }
        }
      }
    }

    fetchExpInfo()
    const intervalId = setInterval(fetchExpInfo, 5000)

    return () => {
      isMounted = false
      clearInterval(intervalId)
    }
  }, [brandId, firmwareId, selectedExp, running])

  const handleSelectExperiment = (expName) => {
    setSelectedExp(expName)
  }

  const handleRemoveExperiment = async (expName) => {
    if (!window.confirm(`Are you sure you want to remove experiment "${expName}"?`)) return
    
    setLoadingRemove(true)
    try {
      await removeExperiment({ brandId, firmwareId, expName })

      if (selectedExp === expName) {
        setSelectedExp(null)
        setExpInfo(null)
      }

      setLoadingRunningExps(prev => {
        const copy = new Set(prev)
        copy.delete(expName)
        return copy
      })
    } catch (err) {
      console.error('Failed to remove experiment:', err)
      alert('Failed to remove experiment: ' + err.message)
    } finally {
      setLoadingRemove(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 border border-gray-400 rounded shadow-lg text-black">

      <div className="flex flex-1 overflow-hidden">

        <div className="w-1/2 border-r border-gray-300 flex flex-col">
          <div className="px-4 py-2 font-semibold text-gray-700 border-b">
            Running Experiments
          </div>
          <div className="flex-1 overflow-auto">
            {(isFetching && running.length === 0) && (
              <div className="p-4 text-center text-gray-500">No running</div>
            )}
            {(!isFetching && running.length === 0) && (
              <div className="p-4 text-center text-gray-500">No running</div>
            )}
            {running.map(name => {
              const isSelected = selectedExp === name
              const isLoadingLabel = loadingRunningExps.has(name)

              return (
                <div
                  key={`run_${name}`}
                  className={`px-4 py-2 flex justify-between items-center transition ${
                    isSelected ? 'bg-blue-100 font-semibold' : 'hover:bg-blue-50'
                  }`}
                >
                  <span
                    className="cursor-pointer flex-1"
                    onClick={() => handleSelectExperiment(name)}
                  >
                    {name}
                  </span>

                  {isLoadingLabel ? (
                    <span className="text-xs px-2 py-0.5 rounded bg-yellow-200 text-yellow-800 mr-2">
                      Loading…
                    </span>
                  ) : (
                    <span className="text-xs px-2 py-0.5 rounded bg-green-200 text-green-800 mr-2">
                      Running
                    </span>
                  )}

                  <button
                    className="text-red-500 hover:text-red-700 text-lg font-bold"
                    onClick={() => handleRemoveExperiment(name)}
                    disabled={loadingRemove}
                    title="Stop & Remove Running Experiment"
                  >
                    ❌
                  </button>
                </div>
              )
            })}
          </div>
        </div>

        <div className="w-1/2 flex flex-col">
          <div className="px-4 py-2 font-semibold text-gray-700 border-b">
            Completed Experiments
          </div>
          <div className="flex-1 overflow-auto">
            {(isFetching && done.length === 0) && (
              <div className="p-4 text-center text-gray-500">No completed</div>
            )}
            {(!isFetching && done.length === 0) && (
              <div className="p-4 text-center text-gray-500">No completed</div>
            )}
            {done.map(name => (
              <div
                key={`done_${name}`}
                className={`px-4 py-2 flex justify-between items-center transition ${
                  selectedExp === name ? 'bg-gray-200 font-semibold' : 'hover:bg-gray-100'
                }`}
              >
                <span
                  className="cursor-pointer flex-1"
                  onClick={() => handleSelectExperiment(name)}
                >
                  {name}
                </span>

                <span className="text-xs px-2 py-0.5 rounded bg-gray-200 text-gray-800 mr-2">
                  Done
                </span>

                <button
                  className="text-gray-500 hover:text-red-600 text-lg"
                  onClick={() => handleRemoveExperiment(name)}
                  disabled={loadingRemove}
                  title="Remove Completed Experiment"
                >
                  🗑
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div
        className="h-2/3 border-t border-gray-300 overflow-auto p-4 bg-white"
        ref={detailsRef}
        onScroll={onScroll}
      >
        {selectedExp ? (
          <>
            <div className="font-bold text-blue-700 mb-3 text-lg">
              📄 Details for <span className="underline">{selectedExp}</span>
            </div>

            {!expInfo ? (
              <div className="text-gray-500 italic">Loading experiment info...</div>
            ) : expInfo.error ? (
              <div className="text-red-500">{expInfo.error}</div>
            ) : (
              <div className="space-y-4">

                <div>
                  <h3 className="text-md font-semibold text-gray-700 mb-1">📝 Metadata</h3>
                  <div className="bg-gray-50 border rounded p-3 text-sm space-y-1">
                    {Object.entries(expInfo)
                      .filter(([key]) => typeof expInfo[key] === 'string')
                      .map(([key, value]) => (
                        <div key={key} className="mb-2">
                          <div className="text-gray-600">{key}</div>
                          <div className="font-mono text-sm break-all whitespace-pre-wrap">{value}</div>
                        </div>
                      ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-md font-semibold text-gray-700 mb-1">🎯 Fuzzer Stats</h3>
                  <div className="bg-gray-50 border rounded p-3 text-sm space-y-1">
                    {[
                      'fuzz_time',
                      'execs_done',
                      'execs_per_sec',
                      'paths_total',
                      'paths_found',
                      'paths_favored',
                      'bitmap_cvg',
                      'stability',
                      'unique_crashes',
                      'unique_hangs',
                    ].map(key => (
                      <div key={key} className="flex justify-between border-b border-gray-200 py-0.5">
                        <span className="text-gray-600">{key.replace(/_/g, ' ')}</span>
                        <span>{expInfo[key] !== undefined ? expInfo[key] : '—'}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <details className="mt-4">
                  <summary className="cursor-pointer text-gray-600 font-mono text-sm">Show raw JSON</summary>
                  <pre className="whitespace-pre-wrap text-xs mt-2 bg-gray-100 rounded p-2 max-h-60 overflow-auto">
                    {JSON.stringify(expInfo, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </>
        ) : (
          <div className="text-gray-500 italic">Select an experiment to see details</div>
        )}
      </div>
    </div>
  )
}
