import { useCallback } from 'react'

import { useState, useSetState, initialState } from '@/store'
import { getDataChannels, getExecutableFiles, getInteractions, getProcesses } from '@/requests'
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
      Promise.all([
        getExecutableFiles(state.selectedFirmware, runId),
        getProcesses(state.selectedFirmware, runId),
        getDataChannels(state.selectedFirmware, runId),
        getInteractions(state.selectedFirmware, runId)
      ]).then(([executableFiles, processes, dataChannels, interactions]) => {
        const selectedRunData = getRunData({ executableFiles, processes, dataChannels, interactions })
        const selectedRunLogs = getRunLogs({ runData: selectedRunData })
        const selectedRunGraph = getRunGraph({ runData: selectedRunData, runLogs: selectedRunLogs })
        const selectedRunMetadata = getRunMetadata({ runLogs: selectedRunLogs })
        setState(pr => {
          const { metadata, binariesById } = getRunView(
            {
              runGraph: selectedRunGraph,
              timeSpan: initialState.selectedRunView.timeSpan,
              conf: initialState.selectedRunView.conf
            })
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
      })
    }, [setState, state.selectedFirmware]
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
