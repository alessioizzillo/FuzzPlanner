import { useGetFirmwares } from '@/hooks/queries'
import {
  useSelectedFirmware,
  useSetSelectedFirmware,
  useResetSelectedFirmware
} from '@/hooks/store/selectedFirmware'
import { useResetSelectedRun } from '@/hooks/store/selectedRun'

import Picker from '@/components/Picker'
import Spinner from '@/components/Spinner'
import Error from '@/components/Error'

export default function FirmwarePicker () {
  const selectedFirmware = useSelectedFirmware()
  const setSelectedFirmware = useSetSelectedFirmware()
  const resetSelectedFirmware = useResetSelectedFirmware()
  const resetSelectedRun = useResetSelectedRun()
  const { isLoading, isError, error, data } = useGetFirmwares()

  const handleSelect = id => {
    setSelectedFirmware(id)
    resetSelectedRun()
  }

  if (isLoading) return <Spinner />
  if (isError) return <Error error={error} />

  return (
    <Picker
      items={data.map(f => ({ id: f, label: f }))}
      selected={selectedFirmware}
      setSelected={handleSelect}
      resetSelected={resetSelectedFirmware}
      placeholder='Select a firmware...'
    />
  )
}
