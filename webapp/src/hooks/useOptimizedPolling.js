import { useEffect, useState, useCallback, useRef } from 'react'
import { pollManager } from '@/utils/PollManager'
import { useState as useGlobalState } from '@/store'

/**
 * Optimized hook for select analyses with centralized polling and ETag support
 */
export function useOptimizedSelectAnalyses(brandId, firmwareId, runId, binaryId, options = {}) {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const unsubscribeRef = useRef(null)

  const globalState = useGlobalState()
  const { includeBinaryFilter = true } = options

  // Use provided params or fall back to global state
  const effectiveBrandId = brandId || globalState.selectedBrand
  const effectiveFirmwareId = firmwareId || globalState.selectedFirmware
  const effectiveRunId = runId || globalState.selectedRun

  useEffect(() => {
    // Clean up previous subscription
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
      unsubscribeRef.current = null
    }

    if (!effectiveBrandId || !effectiveFirmwareId || !effectiveRunId) {
      setData(null)
      setIsLoading(false)
      return
    }

    const params = {
      brandId: effectiveBrandId,
      firmwareId: effectiveFirmwareId,
      runId: effectiveRunId
    }
    if (includeBinaryFilter && binaryId) {
      // Extract basename for API (e.g., '/sbin/atp' -> 'atp')
      params.binaryId = binaryId.split('/').pop()
    }

    setIsLoading(true)
    setError(null)

    unsubscribeRef.current = pollManager.subscribe(
      '/select_analyses',
      params,
      (newData, err) => {
        if (err) {
          setError(err)
          setIsLoading(false)
        } else if (newData) {
          setData(newData)
          setIsLoading(false)
          setError(null)
        }
      },
      {
        initialInterval: 2000,
        minInterval: 1000,
        maxInterval: 30000,
        getInterval: (currentData) => {
          // Smart interval based on whether there are running analyses
          const hasRunning = Object.values(currentData?.running ?? {})
            .flatMap(binary => Object.values(binary))
            .some(a => a.status === 'Running')

          return hasRunning ? 2000 : 10000 // Fast when active, slow when idle
        }
      }
    )

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
        unsubscribeRef.current = null
      }
    }
  }, [effectiveBrandId, effectiveFirmwareId, effectiveRunId, binaryId, includeBinaryFilter])

  const refresh = useCallback(() => {
    // Force immediate refresh by clearing ETag and polling immediately
    if (unsubscribeRef.current) {
      pollManager.forceRefresh()
    }
  }, [])

  return {
    data,
    isLoading,
    error,
    refresh,
    // Legacy compatibility
    running: data?.running ?? {},
    done: data?.done ?? {}
  }
}

/**
 * Optimized hook for fuzz experiments with centralized polling and ETag support
 */
export function useOptimizedFuzzExperiments(brandId, firmwareId, options = {}) {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const unsubscribeRef = useRef(null)

  const globalState = useGlobalState()

  // Use provided params or fall back to global state
  const effectiveBrandId = brandId || globalState.selectedBrand
  const effectiveFirmwareId = firmwareId || globalState.selectedFirmware

  useEffect(() => {
    // Clean up previous subscription
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
      unsubscribeRef.current = null
    }

    if (!effectiveBrandId || !effectiveFirmwareId) {
      setData(null)
      setIsLoading(false)
      return
    }

    const params = {
      brandId: effectiveBrandId,
      firmwareId: effectiveFirmwareId
    }

    setIsLoading(true)
    setError(null)

    unsubscribeRef.current = pollManager.subscribe(
      '/fuzz_experiments',
      params,
      (newData, err) => {
        if (err) {
          setError(err)
          setIsLoading(false)
        } else if (newData) {
          setData(newData)
          setIsLoading(false)
          setError(null)
        }
      },
      {
        initialInterval: 2000,
        minInterval: 2000,
        maxInterval: 30000,
        getInterval: (currentData) => {
          // Fast polling if there are running experiments
          const hasRunning = currentData?.running?.length > 0
          return hasRunning ? 2000 : 10000
        }
      }
    )

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
        unsubscribeRef.current = null
      }
    }
  }, [effectiveBrandId, effectiveFirmwareId])

  const refresh = useCallback(() => {
    if (unsubscribeRef.current) {
      pollManager.forceRefresh()
    }
  }, [])

  return {
    data,
    isLoading,
    error,
    refresh,
    // Legacy compatibility - direct access to arrays
    running: data?.running ?? [],
    done: data?.done ?? []
  }
}

/**
 * Optimized hook for check_run with intelligent polling
 */
export function useOptimizedCheckRun(brandId, firmwareId, options = {}) {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isPolling, setIsPolling] = useState(false)
  const unsubscribeRef = useRef(null)

  const globalState = useGlobalState()

  // Use provided params or fall back to global state
  const effectiveBrandId = brandId || globalState.selectedBrand
  const effectiveFirmwareId = firmwareId || globalState.selectedFirmware

  useEffect(() => {
    // Clean up previous subscription
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
      unsubscribeRef.current = null
    }

    if (!effectiveBrandId || !effectiveFirmwareId) {
      setData(null)
      setIsLoading(false)
      return
    }

    const params = {
      brandId: effectiveBrandId,
      firmwareId: effectiveFirmwareId
    }

    setIsLoading(true)
    setError(null)

    unsubscribeRef.current = pollManager.subscribe(
      '/check_run',
      params,
      (newData, err) => {
        if (err) {
          setError(err)
          setIsLoading(false)
        } else if (newData) {
          setData(newData)
          setIsLoading(false)
          setError(null)
        }
      },
      {
        initialInterval: 1000,
        minInterval: 500,
        maxInterval: 10000,
        getInterval: (currentData) => {
          // Fast polling when booting or transitioning states
          const status = currentData?.status
          if (status === 'booting' || status === 'stopping') {
            return 1000
          }
          // Medium polling when listening (emulation running) or when explicitly polling
          if (status === 'listening' || isPolling) {
            return 2000
          }
          // Slow polling when idle or paused
          return 8000
        }
      }
    )

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
        unsubscribeRef.current = null
      }
    }
  }, [effectiveBrandId, effectiveFirmwareId, isPolling])

  const startPolling = useCallback(() => {
    setIsPolling(true)
    if (unsubscribeRef.current) {
      pollManager.forceRefresh()
    }
  }, [])

  const stopPolling = useCallback(() => {
    setIsPolling(false)
  }, [])

  const refresh = useCallback(() => {
    if (unsubscribeRef.current) {
      pollManager.forceRefresh()
    }
  }, [])

  return {
    data,
    isLoading,
    error,
    refresh,
    startPolling,
    stopPolling,
    isPolling,
    status: data?.status || 'not running'
  }
}

/**
 * Optimized hook for select progress with centralized polling and ETag support
 */
export function useOptimizedSelectProgress(containerName) {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const unsubscribeRef = useRef(null)

  useEffect(() => {
    // Clean up previous subscription
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
      unsubscribeRef.current = null
    }

    if (!containerName) {
      setData(null)
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    unsubscribeRef.current = pollManager.subscribe(
      `/select_progress/${containerName}`,
      {},
      (newData, err) => {
        if (err) {
          setError(err)
          setIsLoading(false)
        } else if (newData) {
          // Handle the case where server returns data but indicates no progress available
          if (newData.phase === 'unknown') {
            setData(null)
          } else {
            setData(newData)
          }
          setIsLoading(false)
          setError(null)
        }
      },
      {
        initialInterval: 2000,
        minInterval: 1000,
        maxInterval: 10000,
        getInterval: (currentData) => {
          // Fast polling when analysis is active, slow when completed
          if (currentData?.phase === 'completed' || currentData?.phase === 'error') {
            return 10000 // Slow polling for completed/error states
          }
          return 2000 // Fast polling for active states
        }
      }
    )

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
        unsubscribeRef.current = null
      }
    }
  }, [containerName])

  const refresh = useCallback(() => {
    if (unsubscribeRef.current) {
      pollManager.forceRefresh()
    }
  }, [])

  return {
    progress: data,
    isLoading,
    error,
    refresh
  }
}

/**
 * Optimized hook for fuzz progress with centralized polling and ETag support
 */
export function useOptimizedFuzzProgress(containerName) {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const unsubscribeRef = useRef(null)

  useEffect(() => {
    // Clean up previous subscription
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
      unsubscribeRef.current = null
    }

    if (!containerName) {
      setData(null)
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    unsubscribeRef.current = pollManager.subscribe(
      `/fuzz_progress/${containerName}`,
      {},
      (newData, err) => {
        if (err) {
          setError(err)
          setIsLoading(false)
        } else if (newData) {
          // Handle the case where server returns data but indicates no progress available
          if (newData.phase === 'unknown') {
            setData(null)
          } else {
            setData(newData)
          }
          setIsLoading(false)
          setError(null)
        }
      },
      {
        initialInterval: 2000,
        minInterval: 1000,
        maxInterval: 10000,
        getInterval: (currentData) => {
          // Fast polling when experiment is active, slow when completed
          if (currentData?.phase === 'completed' || currentData?.phase === 'error') {
            return 10000 // Slow polling for completed/error states
          }
          return 2000 // Fast polling for active states
        }
      }
    )

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
        unsubscribeRef.current = null
      }
    }
  }, [containerName])

  const refresh = useCallback(() => {
    if (unsubscribeRef.current) {
      pollManager.forceRefresh()
    }
  }, [])

  return {
    progress: data,
    isLoading,
    error,
    refresh
  }
}

export function useOptimizedPcapReplayProgress(brandId, firmwareId, pcapName) {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const unsubscribeRef = useRef(null)

  const globalState = useGlobalState()

  const effectiveBrandId = brandId || globalState.selectedBrand
  const effectiveFirmwareId = firmwareId || globalState.selectedFirmware

  useEffect(() => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current()
      unsubscribeRef.current = null
    }

    if (!effectiveBrandId || !effectiveFirmwareId || !pcapName) {
      setData(null)
      setIsLoading(false)
      return
    }

    const params = {
      brandId: effectiveBrandId,
      firmwareId: effectiveFirmwareId,
      pcapName: pcapName
    }

    setIsLoading(true)
    setError(null)

    unsubscribeRef.current = pollManager.subscribe(
      '/pcap_replay_progress',
      params,
      (newData, err) => {
        if (err) {
          setError(err)
          setIsLoading(false)
        } else if (newData) {
          if (newData.status === 'not_running') {
            setData(null)
          } else {
            setData(newData)
          }
          setIsLoading(false)
          setError(null)
        }
      },
      {
        initialInterval: 2000,
        minInterval: 1000,
        maxInterval: 10000,
        getInterval: (currentData) => {
          if (!currentData ||
              currentData.status === 'not_running' ||
              currentData.phase === 'completed' ||
              currentData.phase === 'error') {
            return 10000
          }
          return 2000
        }
      }
    )

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
        unsubscribeRef.current = null
      }
    }
  }, [effectiveBrandId, effectiveFirmwareId, pcapName])

  const refresh = useCallback(() => {
    if (unsubscribeRef.current) {
      pollManager.forceRefresh()
    }
  }, [])

  return {
    data,
    isLoading,
    error,
    refresh,
    progressData: data
  }
}

/**
 * Hook to get polling statistics and control
 */
export function usePollingStats() {
  const [stats, setStats] = useState({
    activePolls: 0,
    totalRequests: 0,
    cachedResponses: 0
  })

  useEffect(() => {
    const updateStats = () => {
      setStats({
        activePolls: pollManager.getActivePolls().length,
        // Note: request counting would need to be implemented in PollManager
        totalRequests: 0,
        cachedResponses: 0
      })
    }

    updateStats()
    const interval = setInterval(updateStats, 5000)

    return () => clearInterval(interval)
  }, [])

  const refreshAll = useCallback(() => {
    pollManager.forceRefresh()
  }, [])

  return {
    stats,
    refreshAll,
    activePolls: pollManager.getActivePolls()
  }
}