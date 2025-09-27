import { useCallback, useEffect, useState } from 'react'
import { useSelectedBrand } from '@/hooks/store/selectedBrand'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'

import {
  useCheckFirmwareImage,
  useCreateFirmwareImage,
  useStartEmulation,
  usePauseEmulation,
  useStopEmulation
} from '@/hooks/queries'

import { useOptimizedCheckRun } from '@/hooks/useOptimizedPolling'

export default function EmulationPanel() {
  const brandId = useSelectedBrand()
  const firmwareId = useSelectedFirmware()

  const {
    data: imgData,
    isLoading: imgLoading,
    refetch: refetchImage
  } = useCheckFirmwareImage(brandId, firmwareId)

  const {
    data: statusData,
    status,
    startPolling,
    stopPolling,
    refresh: refreshStatus
  } = useOptimizedCheckRun(brandId, firmwareId)

  const hasImage = imgData?.status === 'succeeded'

  const createImageMutation = useCreateFirmwareImage(brandId, firmwareId)
  const onCreateImage = useCallback(async () => {
    await createImageMutation.mutateAsync({ params: { brandId, firmwareId } })
    refetchImage()
  }, [brandId, firmwareId, createImageMutation, refetchImage])

  const startMutation = useStartEmulation(brandId, firmwareId)
  const pauseMutation = usePauseEmulation(brandId, firmwareId)
  const stopMutation = useStopEmulation(brandId, firmwareId)

  const [isOperationPending, setIsOperationPending] = useState(false)
  const [pendingOperation, setPendingOperation] = useState(null) // 'start', 'pause', 'stop'

  const getButtonConfig = (currentStatus) => {
    switch (currentStatus) {
      case 'not running':
      case 'idle':
        return {
          start: { enabled: true, label: 'Start Emulation' },
          pause: { enabled: false, label: 'Pause Emulation' },
          stop: { enabled: false, label: 'Stop Emulation' }
        }

      case 'booting':
      case 'listening':
        return {
          start: { enabled: false, label: 'Start Emulation' },
          pause: { enabled: true, label: 'Pause Emulation' },
          stop: { enabled: true, label: 'Stop Emulation' }
        }

      case 'paused':
        return {
          start: { enabled: true, label: 'Resume Emulation' },
          pause: { enabled: false, label: 'Pause Emulation' },
          stop: { enabled: true, label: 'Stop Emulation' }
        }

      case 'stopping':
        return {
          start: { enabled: false, label: 'Start Emulation' },
          pause: { enabled: false, label: 'Pause Emulation' },
          stop: { enabled: false, label: 'Stop Emulation' }
        }

      default:
        return {
          start: { enabled: false, label: 'Start Emulation' },
          pause: { enabled: false, label: 'Pause Emulation' },
          stop: { enabled: false, label: 'Stop Emulation' }
        }
    }
  }

  const buttonConfig = status ? getButtonConfig(status) : {
    start: { enabled: false, label: 'Loading...' },
    pause: { enabled: false, label: 'Loading...' },
    stop: { enabled: false, label: 'Loading...' }
  }

  const getDisplayLabel = (key) => {
    const base = buttonConfig[key].label || ''
    const isPendingForKey = pendingOperation === key

    if (isPendingForKey) {
      if (base.toLowerCase().startsWith('resume')) return 'Resuming...'
      if (base.toLowerCase().startsWith('start')) return 'Starting...'
      if (base.toLowerCase().startsWith('pause')) return 'Pausing...'
      if (base.toLowerCase().startsWith('stop')) return 'Stopping...'
      return base + '...'
    }

    return base
  }

  useEffect(() => {
    if (!pendingOperation) return
    if (!status) return

    const cfg = getButtonConfig(status)
    if (cfg && cfg[pendingOperation] && !cfg[pendingOperation].enabled) {
      setIsOperationPending(false)
      setPendingOperation(null)
    }
  }, [status, pendingOperation])

  const onStart = useCallback(async () => {
    if (isOperationPending) return

    setIsOperationPending(true)
    setPendingOperation('start')
    startPolling()

    try {
      await startMutation.mutateAsync({ params: { brandId, firmwareId } })
      refreshStatus()
    } catch (error) {
      setIsOperationPending(false)
      setPendingOperation(null)
      console.error('Start emulation failed:', error)
    }
  }, [brandId, firmwareId, startMutation, refreshStatus, startPolling, isOperationPending])

  const onPause = useCallback(async () => {
    if (isOperationPending) return

    setIsOperationPending(true)
    setPendingOperation('pause')

    try {
      await pauseMutation.mutateAsync({ params: { brandId, firmwareId } })
      refreshStatus()
    } catch (error) {
      setIsOperationPending(false)
      setPendingOperation(null)
      console.error('Pause emulation failed:', error)
    }
  }, [brandId, firmwareId, pauseMutation, refreshStatus, isOperationPending])

  const onStop = useCallback(async () => {
    if (isOperationPending) return

    setIsOperationPending(true)
    setPendingOperation('stop')

    setPendingOperation('stop-pause')

    stopPolling()

    try {
      await stopMutation.mutateAsync({ params: { brandId, firmwareId } })
      refreshStatus()
    } catch (error) {
      setIsOperationPending(false)
      setPendingOperation(null)
      console.error('Stop emulation failed:', error)
    }
  }, [brandId, firmwareId, stopMutation, refreshStatus, stopPolling, isOperationPending])

  if (!brandId || !firmwareId) return null

  return (
    <div className="flex flex-col border p-4 my-2 space-y-4">
      <div className="flex items-center space-x-4">
        <button
          className="px-3 py-1 bg-blue-600 text-white rounded disabled:opacity-50"
          onClick={onCreateImage}
          disabled={!brandId || !firmwareId || imgLoading || hasImage || createImageMutation.isLoading || imgData?.status === 'running'}
        >
          {createImageMutation.isLoading
            ? 'Creating...'
            : 'Create Image'}
        </button>
        <span>
          Image status:&nbsp;
          <strong>
            {imgLoading
              ? 'Checking...'
              : hasImage
                ? imgData?.status === 'running'
                  ? 'Running'
                  : 'Present'
                : imgData?.status === 'running'
                  ? 'Running'
                  : 'Not present'}
          </strong>
        </span>

        <button
          className="px-3 py-1 bg-green-600 text-white rounded disabled:opacity-50"
          onClick={onStart}
          disabled={!hasImage || !buttonConfig.start.enabled || (isOperationPending && pendingOperation === 'start')}
        >
          {getDisplayLabel('start')}
        </button>
        <button
          className="px-3 py-1 bg-yellow-600 text-white rounded disabled:opacity-50"
          onClick={onPause}
          disabled={!hasImage || !buttonConfig.pause.enabled || (isOperationPending && (pendingOperation === 'pause' || pendingOperation === 'stop'))}
        >
          {getDisplayLabel('pause')}
        </button>
        <button
          className="px-3 py-1 bg-red-600 text-white rounded disabled:opacity-50"
          onClick={onStop}
          disabled={!hasImage || !buttonConfig.stop.enabled || (isOperationPending && pendingOperation === 'stop')}
        >
          {getDisplayLabel('stop')}
        </button>
        <span>
          Status:&nbsp;
          <strong>
            {status}
            {status === 'listening' && statusData?.ip ? (
              <> — Connect to IP: <strong>{statusData.ip}</strong></>
            ) : null}
          </strong>
        </span>
      </div>
    </div>
  )
}
