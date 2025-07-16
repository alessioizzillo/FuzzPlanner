import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useGetSelectAnalyses } from '@/hooks/queries'
import { useState, useSetState } from '@/store'

export function useSelectAnalyses() {
  const state = useState()
  const setState = useSetState()

  const brandId = state.selectedBrand
  const firmwareId = state.selectedFirmware
  const runId = state.selectedRun
  const key = `${brandId}:${firmwareId}:${runId}`

  const queryClient = useQueryClient()

  const query = useGetSelectAnalyses(brandId, firmwareId, runId, {
    refetchInterval: (data) => {
      const runningValues = Object.values(data?.running ?? {})
        .flatMap(binary => Object.values(binary))
      return runningValues.some(a => a.status === 'Running') ? 2000 : false
    },
    enabled: !!brandId && !!firmwareId && !!runId,
  })

  const prevKey = useRef(null)

  useEffect(() => {
    if (query.isSuccess && brandId && firmwareId && runId) {
      setState(prev => ({
        ...prev,
        selectAnalysesByFirmware: {
          ...prev.selectAnalysesByFirmware,
          [key]: {
            running: query.data.running ?? [],
            done: query.data.done ?? [],
          }
        }
      }))
    }
    prevKey.current = key
  }, [query.data, key, brandId, firmwareId, runId, setState])

  const global = state.selectAnalysesByFirmware?.[key] ?? {}

  // Default selected state with binaryId and dataChannelId
  const selected = state.selectedAnalysis ?? {
    type: 'running', // or 'done'
    binaryId: '',
    dataChannelId: '',
  }

  // Setter that merges with previous selected state
  const setSelected = (sel) => {
    setState(prev => ({
      ...prev,
      selectedAnalysis: {
        ...prev.selectedAnalysis,
        ...sel
      }
    }))
  }

  const pollNow = () => {
    if (brandId && firmwareId && runId) {
      console.log('[useSelectAnalyses] Manual poll triggered for', key)
      queryClient.invalidateQueries({
        queryKey: ['selectAnalyses', brandId, firmwareId, runId],
      })
    }
  }

  return {
    running: global.running ?? [],
    done: global.done ?? [],
    selected,
    setSelected,
    pollNow,
  }
}
