import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import {
  useStartEmulation,
  usePauseEmulation,
  useStopEmulation,
  useEmuStatus
} from '@/hooks/queries'
import Button from '@/components/Button'

export default function EmulationControls () {
  const firmwareId = useSelectedFirmware()
  const { data } = useEmuStatus(firmwareId)
  const { mutate: start } = useStartEmulation(firmwareId)
  const { mutate: pause } = usePauseEmulation(firmwareId)
  const { mutate: stop } = useStopEmulation(firmwareId)

  return (
    <div className='flex gap-2 ml-4'>
      <Button onClick={() => start()}>Start</Button>
      <Button onClick={() => pause()}>Pause</Button>
      <Button onClick={() => stop()}>Stop</Button>
      <span>Status: {data?.status || 'UNKNOWN'}</span>
    </div>
  )
}
