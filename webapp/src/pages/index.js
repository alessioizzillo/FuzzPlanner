import FirmwarePicker from '@/modules/FirmwarePicker'
import RunPicker from '@/modules/RunPicker'

import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { useSelectedRun } from '@/hooks/store/selectedRun'
import RunManager from '@/modules/RunManager'

export default function Home () {
  const selectedFirmware = useSelectedFirmware()
  const selectedRun = useSelectedRun()
  return (
    <div className='flex flex-col items-stretch max-h-screen min-h-screen p-2'>
      <div className='flex items-center justify-start mb-3 flex-0'>
        <span className='pr-4 text-lg'>FuzzPlanner</span>
        <FirmwarePicker />
        {selectedFirmware && <RunPicker />}
      </div>
      {selectedRun && true && <RunManager className='flex-1' />}
    </div>
  )
}
