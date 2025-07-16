import { useCallback } from 'react'

import { useState, useSetState, initialState } from '@/store'
import { getDataChannels, getExecutableFiles, getInteractions, getProcesses } from '@/requests'
import { useRemoveRun } from '../queries'
import { getRunData, getRunGraph, getRunLogs, getRunMetadata, getRunView } from '@/data'

// GET
export function useSelectedRun () {
  const state = useState()
  return state.selectedRun
}

export function useSelectedRunData () {
  const state = useState()
  return state.selectedRunData
}

export function useSelectedRunLogs () {
  const state = useState()
  return state.selectedRunLogs
}

export function useSelectedRunGraph () {
  const state = useState()
  return state.selectedRunGraph
}

export function useSelectedRunView () {
  const state = useState()
  return state.selectedRunView
}

export function useSelectedRunMetadata () {
  const state = useState()
  return state.selectedRunMetadata
}

// SET
export function useSetSelectedRun () {
  const state = useState()
  const setState = useSetState()

  return useCallback(
    (runId) => {
      console.log('[DEBUG] Setting selected run:', runId)
      console.log('[DEBUG] Current state:', {
        brand: state.selectedBrand,
        firmware: state.selectedFirmware
      })

      Promise.all([
        getExecutableFiles(state.selectedBrand, state.selectedFirmware, runId),
        getProcesses(state.selectedBrand, state.selectedFirmware, runId),
        getDataChannels(state.selectedBrand, state.selectedFirmware, runId),
        getInteractions(state.selectedBrand, state.selectedFirmware, runId)
      ]).then(([executableFiles, processes, dataChannels, interactions]) => {
        
        console.log('[DEBUG] Fetched data:', { executableFiles, processes, dataChannels, interactions })

        const selectedRunData = getRunData({ executableFiles, processes, dataChannels, interactions })
        console.log('[DEBUG] selectedRunData:', selectedRunData)

        const selectedRunLogs = getRunLogs({ runData: selectedRunData })
        console.log('[DEBUG] selectedRunLogs:', selectedRunLogs)

        const selectedRunGraph = getRunGraph({ runData: selectedRunData, runLogs: selectedRunLogs })
        console.log('[DEBUG] selectedRunGraph:', selectedRunGraph)

        const selectedRunMetadata = getRunMetadata({ runLogs: selectedRunLogs })
        console.log('[DEBUG] selectedRunMetadata:', selectedRunMetadata)

        setState(pr => {
          const { metadata, binariesById } = getRunView({
            runGraph: selectedRunGraph,
            timeSpan: initialState.selectedRunView.timeSpan,
            conf: initialState.selectedRunView.conf
          })

          console.log('[DEBUG] Run View:', { metadata, binariesById })

          return {
            ...pr,
            selectedRun: runId,
            selectedRunData,
            selectedRunLogs,
            selectedRunGraph,
            selectedRunMetadata,
            selectedRunView: {
              ...pr.selectedRunView,
              binariesById,
              metadata
            }
          }
        })
      }).catch(err => {
        console.error('[ERROR] Failed to set selected run:', err)
      })
    },
    [setState, state.selectedBrand, state.selectedFirmware] // 🔧 included selectedBrand for completeness
  )
}

export function useSetSelectedRunView () {
  const state = useState()
  const setState = useSetState()
  return useCallback(
    ({ timeSpan, conf }) => {
      const t = timeSpan || state.selectedRunView.timeSpan
      const c = conf || state.selectedRunView.conf
      const { metadata, binariesById } = getRunView({ runLogs: state.selectedRunLogs, runGraph: state.selectedRunGraph, timeSpan: t, conf: c })
      setState(pr => ({
        ...pr,
        selectedRunView: {
          timeSpan: t,
          conf: c,
          binariesById,
          metadata
        }
      }))
    }, [setState, state.selectedRun, state.selectedRunGraph]
  )
}
export function useSetSelectedRunViewConfEntry () {
  const setState = useSetState()
  return useCallback(
    ({ id, v }) => {
      setState(pr => {
        const conf = { ...pr.selectedRunView.conf, [id]: v }
        const timeSpan = pr.selectedRunView.timeSpan
        const { metadata, binariesById } = getRunView({ runLogs: pr.selectedRunLogs, runGraph: pr.selectedRunGraph, timeSpan, conf })
        return {
          ...pr,
          selectedRunView: {
            timeSpan,
            conf,
            binariesById,
            metadata
          }
        }
      })
    }, [setState]
  )
}

// RESET
export function useResetSelectedRun () {
  const setState = useSetState()
  return useCallback(
    () => {
      setState(pr => ({
        ...pr,
        selectedRun: initialState.selectedRun,
        selectedRunData: initialState.selectedRunData,
        selectedRunLogs: initialState.selectedRunLogs,
        selectedRunGraph: initialState.selectedRunGraph,
        selectedRunView: initialState.selectedRunView,
        selectedRunMetadata: initialState.selectedRunMetadata,
        selectedEntries: initialState.selectedEntries
      }))
    }, [setState]
  )
}

export const useRemoveSelectedRun = (brandId, firmwareId, runId) => {
  const setState = useSetState()
  const mutation = useRemoveRun(brandId, firmwareId, runId)

  return useCallback(() => {
    mutation.mutate(null, {
      onSuccess: () => {
        setState(pr => ({
          ...pr,
          selectedRun: null,
          selectedRunData: {},
          selectedRunLogs: [],
          selectedRunGraph: {},
          selectedRunView: {
            timeSpan: { min: -1, max: -1 },
            conf: {
              borderThreshold: 0,
              listenThreshold: 0,
              withinThreshold: 0
            },
            binariesById: {},
            metadata: {},
            timeBins: []
          },
          selectedRunMetadata: {}
        }))
      }
    })
  }, [mutation, setState])
}

