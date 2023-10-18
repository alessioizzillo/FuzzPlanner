import { useCallback } from 'react'

import { useState, useSetState, initialState } from '@/store'

export function useLogsGraph () {
  const state = useState()
  return state.logsGraph
}

export function useSetLogsGraph () {
  const setState = useSetState()
  return useCallback(
    () => {
      setState(pr => ({ ...pr, graphSpan: { start, end } }))
    }, [setState]
  )
}

export function useResetLogsGraph () {
  const setState = useSetState()
  return useCallback(
    () => {
      setState(pr => ({ ...pr, logsGraph: initialState.logsGraph }))
    }, [setState]
  )
}
