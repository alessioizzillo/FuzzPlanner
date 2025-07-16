import { useCallback } from 'react'
import { useSelectAnalyses } from '@/hooks/store/useSelectAnalyses'

export function useSelectedBinary() {
  const { selected } = useSelectAnalyses()
  return selected.type === 'done' ? selected.binaryId : null
}

export function useSetSelectedBinary() {
  const { setSelected } = useSelectAnalyses()
  return useCallback(
    (binaryId) => {
      setSelected({
        type: 'done',
        binaryId,
        dataChannelId: '',
      })
    },
    [setSelected]
  )
}

export function useSelectedDataChannel() {
  const { selected } = useSelectAnalyses()
  return selected.type === 'done' ? selected.dataChannelId : null
}

export function useSetSelectedDataChannel() {
  const { setSelected } = useSelectAnalyses()
  return useCallback(
    (dataChannelId) => {
      setSelected({
        type: 'done',
        dataChannelId,
      })
    },
    [setSelected]
  )
}

export function useResetSelectedBinary() {
  const { setSelected } = useSelectAnalyses()
  return useCallback(() => {
    setSelected({
      type: 'done',
      binaryId: '',
      dataChannelId: '',
    })
  }, [setSelected])
}

export function useResetSelectedDataChannel() {
  const { setSelected } = useSelectAnalyses()
  return useCallback(() => {
    setSelected({
      type: 'done',
      dataChannelId: '',
    })
  }, [setSelected])
}
