import { useCallback } from 'react'
import { useState, useSetState, initialState } from '@/store'

export function useSelectedBrand () {
  const state = useState()
  return state.selectedBrand
}

export function useSetSelectedBrand () {
  const setState = useSetState()
  return useCallback(
    (brandId) => {
      setState(pr => ({
        ...pr,
        selectedBrand: brandId,
        selectedFirmware: null,
        selectedRun: null
      }))
    }, [setState]
  )
}

export function useResetSelectedBrand () {
  const setState = useSetState()
  return useCallback(
    () => setState(pr => ({
      ...pr,
      selectedBrand: null,
      selectedFirmware: null,
      selectedRun: null
    })), [setState]
  )
}
