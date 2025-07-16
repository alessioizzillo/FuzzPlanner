import { useGetRuns } from '@/hooks/queries'
import {
  useSelectedRun,
  useSetSelectedRun,
  useResetSelectedRun,
  useRemoveSelectedRun
} from '@/hooks/store/selectedRun'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { useSelectedBrand } from '@/hooks/store/selectedBrand'

import { useResetSelectedBinary, useResetSelectedDataChannel } from '@/hooks/store/selectedBinaryDataChannel'

import { FaTrashAlt } from 'react-icons/fa'

import Picker from '@/components/Picker'
import Spinner from '@/components/Spinner'
import Error from '@/components/Error'

export default function RunPicker () {
  const firmwareId = useSelectedFirmware()
  const brandId = useSelectedBrand()
  const selectedRun = useSelectedRun()
  const setSelectedRun = useSetSelectedRun()
  const resetSelectedRun = useResetSelectedRun()
  const removeSelectedRun = useRemoveSelectedRun(brandId, firmwareId, selectedRun)
  const resetSelectedBinary = useResetSelectedBinary()
  const resetSelectedDataChannel = useResetSelectedDataChannel()

  const { isLoading, isError, error, data: runs, refetch } = useGetRuns(brandId, firmwareId)

  if (isLoading) return <Spinner />
  if (isError) return <Error error={error} />

  const handleSelect = id => {
    setSelectedRun(id)
  }

  const handleRemoveSelectedRun = async () => {
    await removeSelectedRun()
    resetSelectedBinary()
    resetSelectedDataChannel()
    resetSelectedRun()
  }

  return (
    <div className="flex items-center">
      <div className="relative flex items-center">
        <Picker
          items={runs.map(r => ({ id: r, label: r }))}
          selected={selectedRun}
          setSelected={handleSelect}
          resetSelected={resetSelectedRun}
          placeholder="Select a run..."
          onOpen={() => {
            refetch()
          }}
        />
        {selectedRun && (
          <button
            onClick={handleRemoveSelectedRun}
            className="absolute right-0 mr-1 text-red-500 hover:text-red-700 p-0"
            title="Remove selected run"
          >
            <FaTrashAlt size={14} />
          </button>
        )}
      </div>
    </div>
  )
}
