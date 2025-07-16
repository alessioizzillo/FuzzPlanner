import { useSelectedBrand } from '@/hooks/store/selectedBrand'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { useSelectedRun } from '@/hooks/store/selectedRun'

import Picker from '@/components/Picker'
import Spinner from '@/components/Spinner'
import Error from '@/components/Error'

export default function FirmwarePicker () {
  const selectedBrand = useSelectedBrand()
  const selectedFirmware = useSelectedFirmware()
  const selectedRun = useSelectedRun()
  const useResetSelectedDataChannel = useResetSelectedDataChannel()


  const { isLoading, isError, error, data } = useGetDataChannels(selectedBrand)

  if (!selectedBrand) return null

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
