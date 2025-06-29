import FirmwarePicker from '@/modules/FirmwarePicker'
import RunPicker from '@/modules/RunPicker'
import RunManager from '@/modules/RunManager'
import EmulationControls from '@/modules/EmulationControls'

import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { useSelectedRun } from '@/hooks/store/selectedRun'

export default function Home () {
  const selectedFirmware = useSelectedFirmware()
  const selectedRun = useSelectedRun()

  return (
    <div className='flex flex-col items-stretch max-h-screen min-h-screen p-2'>
      <div className='flex items-center justify-start mb-3 flex-0'>
        <span className='pr-4 text-lg'>FuzzPlanner</span>
        <FirmwarePicker />
        {selectedFirmware && <RunPicker />}
        {selectedFirmware && <EmulationControls />}
      </div>
      {selectedRun && <RunManager className='flex-1' />}
    </div>
  )
}
