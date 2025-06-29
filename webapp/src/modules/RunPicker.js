import { useGetRuns } from '@/hooks/queries'
import {
  useSelectedRun,
  useSetSelectedRun,
  useResetSelectedRun
} from '@/hooks/store/selectedRun'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { useEffect } from 'react'

import Picker from '@/components/Picker'
import Spinner from '@/components/Spinner'
import Error from '@/components/Error'

export default function RunPicker () {
  const firmwareId = useSelectedFirmware()
  const selectedRun = useSelectedRun()
  const setSelectedRun = useSetSelectedRun()
  const resetSelectedRun = useResetSelectedRun()
  const { isLoading, isError, error, data } = useGetRuns(firmwareId)

  useEffect(() => {
    resetSelectedRun()
  }, [firmwareId])

  if (isLoading) return <Spinner />
  if (isError) return <Error error={error} />

  return (
    <Picker
      items={(data || []).map(r => ({ id: r, label: r }))}
      selected={selectedRun}
      setSelected={id => setSelectedRun(id)}
      resetSelected={resetSelectedRun}
      placeholder='Select a run...'
    />
  )
}
