import { useCallback } from 'react'

import { useState, useSetState, initialState } from '@/store'

// GET
export function useSelectedPcap () {
  const state = useState()
  return state.selectedPcap
}

export function useSelectedPcapAnalysis () {
  const state = useState()
  return state.selectedPcapAnalysis
}

// SET
export function useSetSelectedPcap () {
  const state = useState()
  const setState = useSetState()

  return useCallback(
    (pcapName) => {
      console.log('[DEBUG] Setting selected PCAP:', pcapName)
      console.log('[DEBUG] Current state:', {
        brand: state.selectedBrand,
        firmware: state.selectedFirmware
      })

      setState(pr => ({
        ...pr,
        selectedPcap: pcapName,
        selectedPcapAnalysis: initialState.selectedPcapAnalysis
      }))
    },
    [setState, state.selectedBrand, state.selectedFirmware]
  )
}


// RESET
export function useResetSelectedPcap () {
  const setState = useSetState()
  return useCallback(
    () => {
      setState(pr => ({
        ...pr,
        selectedPcap: initialState.selectedPcap,
        selectedPcapAnalysis: initialState.selectedPcapAnalysis
      }))
    }, [setState]
  )
}

