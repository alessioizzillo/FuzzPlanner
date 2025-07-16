import { useCallback, useEffect } from 'react'
import { useGetRuns } from '@/hooks/queries'
import { useState, useSetState } from '@/store'

export function useSelectedFirmware() {
  const state = useState()
  return state.selectedFirmware
}

export function useSetSelectedFirmware() {
  const setState = useSetState()
  const state = useState()

  const { data: runsData } = useGetRuns(state.selectedBrand, state.selectedFirmware)

  useEffect(() => {
    if (!state.selectedBrand || !state.selectedFirmware) return
    if (runsData) {
      setState(pr => ({
        ...pr,
        selectedRun: null,
        selectedRunData: {},
        selectedRunLogs: [],
        selectedRunGraph: {},
        selectedRunMetadata: {},
        selectedRunView: {
          ...pr.selectedRunView,
          binariesById: {},
          metadata: {},
          timeBins: []
        },
        selectedEntries: {},
        runsByFirmware: {
          ...pr.runsByFirmware,
          [`${state.selectedBrand}:${state.selectedFirmware}`]: runsData
        }
      }))
    }
  }, [state.selectedBrand, state.selectedFirmware, runsData, setState])

  return useCallback((firmwareId) => {
    if (!firmwareId) return

    setState(pr => ({
      ...pr,
      selectedFirmware: firmwareId,
      selectedRun: null,
      selectedRunData: {},
      selectedRunLogs: [],
      selectedRunGraph: {},
      selectedRunMetadata: {},
      selectedRunView: {
        ...pr.selectedRunView,
        binariesById: {},
        metadata: {},
        timeBins: []
      },
      selectedEntries: {}
    }))
  }, [setState])
}

export function useResetSelectedFirmware() {
  const setState = useSetState()
  return useCallback(() => {
    setState(pr => ({
      ...pr,
      selectedFirmware: null,
      selectedRun: null
    }))
  }, [setState])
}
