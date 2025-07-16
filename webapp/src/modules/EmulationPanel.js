import { useCallback, useEffect, useState } from 'react'
import { useSelectedBrand } from '@/hooks/store/selectedBrand'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'

import {
  useCheckFirmwareImage,
  useCreateFirmwareImage,
  useStartEmulation,
  usePauseEmulation,
  useStopEmulation,
  useCheckRun
} from '@/hooks/queries'

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
    refetch: refetchStatus, 
    isFetching: statusLoading
  } = useCheckRun(brandId, firmwareId)

  const hasImage = imgData?.status === 'succeeded'

  const createImageMutation = useCreateFirmwareImage(brandId, firmwareId)
  const onCreateImage = useCallback(async () => {
    await createImageMutation.mutateAsync({ params: { brandId, firmwareId } })
    refetchImage()
  }, [brandId, firmwareId, createImageMutation, refetchImage])

  const startMutation = useStartEmulation(brandId, firmwareId)
  const pauseMutation = usePauseEmulation(brandId, firmwareId)
  const stopMutation  = useStopEmulation(brandId, firmwareId)

  const onStart = useCallback(async () => {
    await startMutation.mutateAsync({ params: { brandId, firmwareId } })
    refetchStatus()
  }, [brandId, firmwareId, startMutation, refetchStatus])

  const onPause = useCallback(async () => {
    await pauseMutation.mutateAsync({ params: { brandId, firmwareId } })
    refetchStatus()
  }, [brandId, firmwareId, pauseMutation, refetchStatus])

  const onStop = useCallback(async () => {
    await stopMutation.mutateAsync({ params: { brandId, firmwareId } })
    refetchStatus()
  }, [brandId, firmwareId, stopMutation, refetchStatus])

  const [polling, setPolling] = useState(false)

  useEffect(() => {
    if (statusData?.status === 'booting') {
      setPolling(true)
      const intervalId = setInterval(async () => {
        if (polling) refetchStatus()
      }, 2000)
      return () => clearInterval(intervalId)
    } else {
      setPolling(false)
    }
  }, [statusData, refetchStatus, polling])

  const status = statusData?.status || 'idle'

  useEffect(() => {
    refetchStatus()
  }, [refetchStatus])

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
            ? 'Creating…'
            : 'Create Image'}
        </button>
        <span>
          Image status:&nbsp;
          <strong>
            {imgLoading
              ? 'Checking…'
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
          disabled={
            !hasImage || 
            startMutation.isLoading || 
            ['booting','listening'].includes(status)
          }
        >
          {startMutation.isLoading 
            ? (status === 'paused' ? 'Resuming…' : 'Starting…')
            : (status === 'paused' ? 'Resume Emulation' : 'Start Emulation')}
        </button>
        <button
          className="px-3 py-1 bg-yellow-600 text-white rounded disabled:opacity-50"
          onClick={onPause}
          disabled={!hasImage || !['booting','listening'].includes(status) || pauseMutation.isLoading}
        >
          {pauseMutation.isLoading ? 'Pausing…' : 'Pause Emulation'}
        </button>
        <button
          className="px-3 py-1 bg-red-600 text-white rounded disabled:opacity-50"
          onClick={onStop}
          disabled={!hasImage || !['booting', 'listening', 'paused'].includes(status) || stopMutation.isLoading}
        >
          {stopMutation.isLoading ? 'Stopping…' : 'Stop Emulation'}
        </button>
        <span>
          Status:&nbsp;
          <strong>
            {statusLoading ? status : statusData?.previousStatus || status}
            {status === 'listening' && statusData?.ip ? (
              <> — Connect to IP: <strong>{statusData.ip}</strong></>
            ) : null}
          </strong>
        </span>
      </div>
    </div>
  )
}
