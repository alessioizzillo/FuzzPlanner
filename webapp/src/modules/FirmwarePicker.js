import { useGetFirmwares } from '@/hooks/queries'
import { useSelectedFirmware, useSetSelectedFirmware, useResetSelectedFirmware } from '@/hooks/store/selectedFirmware'

import Picker from '@/components/Picker'
import Spinner from '@/components/Spinner'
import Error from '@/components/Error'

export default function FirmwarePicker () {
  const selectedFirmware = useSelectedFirmware()
  const setSelectedFirmware = useSetSelectedFirmware()
  const resetSelectedFirmware = useResetSelectedFirmware()
  const { isLoading, isError, error, data } = useGetFirmwares()
  if (isLoading) return <Spinner />
  if (isError) return <Error error={error} />
  return (
    <Picker
      items={data.map(f => ({ id: f, label: f }))}
      selected={selectedFirmware}
      setSelected={id => setSelectedFirmware(id)}
      resetSelected={resetSelectedFirmware}
      placeholder='Select a firmware...'
    />
  )
}
