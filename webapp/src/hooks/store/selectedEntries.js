import { useCallback } from 'react'

import { useState, useSetState, initialState } from '@/store'

export function useSelectedEntries () {
  const state = useState()
  return state.selectedEntries
}

export function useSetSelectedEntries () {
  const setState = useSetState()
  return useCallback(
    ({ id, v }) => {
      setState(pr => {
        if (!pr.selectedEntries[id]) {
          return { ...pr, selectedEntries: { ...pr.selectedEntries, [id]: v } }
        } else {
          const { [id]: _, ...e } = pr.selectedEntries
          console.log(e)
          return { ...pr, selectedEntries: e }
        }
      })
    }, []
  )
}

export function useResetSelectedFirmware () {
  const state = useState()
  const setState = useSetState()
  return useCallback(
    () => {
      const { selectedEntries } = initialState
      if (state.runId === null) setState(pr => ({ ...pr, selectedEntries }))
    }, [state.runId, setState]
  )
}
