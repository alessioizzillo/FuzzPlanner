import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useOptimizedFuzzExperiments } from '@/hooks/useOptimizedPolling'
import { useSelectedBrand } from '@/hooks/store/selectedBrand'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { getExperimentInfo, removeExperiment } from '@/hooks/queries'
import FuzzProgress from '@/components/FuzzProgress'
import Icon from '@/components/Icon'

export default function ExperimentsPanel() {
  const brandId = useSelectedBrand()
  const firmwareId = useSelectedFirmware()
  const { data, isLoading: isFetching, error, running, done } = useOptimizedFuzzExperiments()

  const [selectedExp, setSelectedExp] = useState(null)
  const [expInfo, setExpInfo]         = useState(null)
  const [removingExps, setRemovingExps] = useState(new Set())

  const [loadingRunningExps, setLoadingRunningExps] = useState(new Set())

  const visibleRunning = useMemo(() => {
    const filtered = running.filter(exp => {
      const name = typeof exp === 'string' ? exp : exp.name
      const isRemoving = removingExps.has(name)
      return !isRemoving
    })
    return filtered
  }, [running, removingExps])

  const visibleDone = useMemo(() => {
    const filtered = done.filter(name => {
      const isRemoving = removingExps.has(name)
      return !isRemoving
    })
    return filtered
  }, [done, removingExps])

  useEffect(() => {
    const runningNames = running.map(exp =>
      typeof exp === 'string' ? exp : exp.name
    )
    setLoadingRunningExps(new Set(runningNames))
  }, [running])

  useEffect(() => {
    const allExperimentNames = new Set([
      ...running.map(exp => typeof exp === 'string' ? exp : exp.name),
      ...done
    ])

    setRemovingExps(prev => {
      const cleaned = new Set()
      for (const expName of prev) {
        if (allExperimentNames.has(expName)) {
          cleaned.add(expName)
        }
      }
      return cleaned
    })
  }, [running, done])

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

        if (running.some(exp => (typeof exp === 'string' ? exp : exp.name) === selectedExp)) {
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

          if (running.some(exp => (typeof exp === 'string' ? exp : exp.name) === selectedExp)) {
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
    if (removingExps.has(expName)) return

    if (selectedExp === expName) {
      setSelectedExp(null)
      setExpInfo(null)
    }

    setRemovingExps(prev => {
      const newSet = new Set(prev).add(expName)
      return newSet
    })

    try {
      await removeExperiment({ brandId, firmwareId, expName })

      setLoadingRunningExps(prev => {
        const copy = new Set(prev)
        copy.delete(expName)
        return copy
      })
    } catch (err) {
      console.error('Failed to remove experiment:', err)
      alert('Failed to remove experiment: ' + err.message)

      setRemovingExps(prev => {
        const copy = new Set(prev)
        copy.delete(expName)
        return copy
      })
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
            {(isFetching && visibleRunning.length === 0) && (
              <div className="p-4 text-center text-gray-500">No running</div>
            )}
            {(!isFetching && visibleRunning.length === 0) && (
              <div className="p-4 text-center text-gray-500">No running</div>
            )}
            {visibleRunning.map(exp => {
              const name = typeof exp === 'string' ? exp : exp.name
              const status = typeof exp === 'object' ? exp.status : 'unknown'

              const isSelected = selectedExp === name
              const isLoadingLabel = loadingRunningExps.has(name)

              const getStatusDisplay = () => {
                switch (status) {
                  case 'booting':
                    return {
                      text: 'Booting',
                      className: 'bg-orange-200 text-orange-800'
                    }
                  case 'fuzzing':
                    return {
                      text: 'Fuzzing',
                      className: 'bg-green-200 text-green-800'
                    }
                  default:
                    return {
                      text: 'Running',
                      className: 'bg-blue-200 text-blue-800'
                    }
                }
              }

              const statusDisplay = getStatusDisplay()

              return (
                <div
                  key={`run_${name}`}
                  className={`px-4 py-2 transition ${
                    isSelected ? 'bg-blue-100 font-semibold' : 'hover:bg-blue-50'
                  }`}
                >
                  {/* Top row: Name and Remove button */}
                  <div className="flex justify-between items-center mb-1">
                    <span
                      className="cursor-pointer flex-1 truncate pr-2"
                      onClick={() => handleSelectExperiment(name)}
                      title={name}
                    >
                      {name}
                    </span>

                    <button
                      className={`-ml-5 rounded transition-colors ${
                        removingExps.has(name)
                          ? 'text-gray-400 cursor-not-allowed'
                          : 'text-red-500 hover:text-red-700 hover:bg-red-50'
                      }`}
                      onClick={() => handleRemoveExperiment(name)}
                      disabled={removingExps.has(name)}
                      title={removingExps.has(name) ? "Removing..." : "Stop & Remove Running Experiment"}
                    >
                      <Icon
                        name={removingExps.has(name) ? "loading" : "trash"}
                        className={`w-4 h-4 ${removingExps.has(name) ? 'animate-spin' : ''}`}
                      />
                    </button>
                  </div>

                  {/* Bottom row: Progress info */}
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      {typeof exp === 'object' && exp.container_name && (
                        <FuzzProgress containerName={exp.container_name} />
                      )}
                    </div>
                  </div>
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
            {(isFetching && visibleDone.length === 0) && (
              <div className="p-4 text-center text-gray-500">No completed</div>
            )}
            {(!isFetching && visibleDone.length === 0) && (
              <div className="p-4 text-center text-gray-500">No completed</div>
            )}
            {visibleDone.map(name => (
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

                <button
                  className={`-ml-5 rounded transition-colors ${
                    removingExps.has(name)
                      ? 'text-gray-400 cursor-not-allowed'
                      : 'text-red-500 hover:text-red-700 hover:bg-red-50'
                  }`}
                  onClick={() => handleRemoveExperiment(name)}
                  disabled={removingExps.has(name)}
                  title={removingExps.has(name) ? "Removing..." : "Remove Completed Experiment"}
                >
                  <Icon
                    name={removingExps.has(name) ? "loading" : "trash"}
                    className={`w-4 h-4 ${removingExps.has(name) ? 'animate-spin' : ''}`}
                  />
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
            <div className="font-bold text-blue-700 mb-3 text-lg flex items-center gap-2">
              <Icon name="document" className="w-5 h-5" />
              Details for <span className="underline">{selectedExp}</span>
            </div>

            {!expInfo ? (
              <div className="text-gray-500 italic">Loading experiment info...</div>
            ) : expInfo.error ? (
              <div className="text-red-500">{expInfo.error}</div>
            ) : (
              <div className="space-y-4">

                <div>
                  <h3 className="text-md font-semibold text-gray-700 mb-1 flex items-center gap-2">
                    <Icon name="metadata" className="w-4 h-4" />
                    Metadata
                  </h3>
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
                  <h3 className="text-md font-semibold text-gray-700 mb-1 flex items-center gap-2">
                    <Icon name="stats" className="w-4 h-4" />
                    Fuzzer Stats
                  </h3>
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
