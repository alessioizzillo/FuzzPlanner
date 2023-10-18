import { useCallback } from 'react'

import { useState, useSetState, initialState } from '@/store'

export function useSelectedFirmware () {
  const state = useState()
  return state.selectedFirmware
}

export function useSetSelectedFirmware () {
  const state = useState()
  const setState = useSetState()
  return useCallback(
    (firmwareId) => {
      if (state.runId === null) setState(pr => ({ ...pr, selectedFirmware: firmwareId }))
      else setState(pr => ({ ...pr, selectedFirmware: firmwareId, selectedRun: null }))
    }, [state.runId, setState]
  )
}

export function useResetSelectedFirmware () {
  const state = useState()
  const setState = useSetState()
  return useCallback(
    () => {
      const { selectedFirmware, selectedRun } = initialState
      if (state.runId === null) setState(pr => ({ ...pr, selectedFirmware }))
      else setState(pr => ({ ...pr, selectedFirmware, selectedRun }))
    }, [state.runId, setState]
  )
}
