import { useSelectedRunView } from '@/hooks/store/selectedRun'
import { useState } from 'react'
import BinariesTable from '@/modules/BinariesTable/BinariesTable'
import Timeline from './Timeline/Timeline'
import classNames from 'classnames'
import SelectedEntries from './SelectedEntries'
import BinaryGraph from './Binary/BinaryGraph'
import RunViewConf from './RunViewConf'

export default function RunManager ({ className }) {
  const runView = useSelectedRunView()
  const [binariesSorting, setBinariesSorting] = useState([{ id: 'border', desc: true }])
  const [currentBinary, setCurrentBinary] = useState(null)
  const [selectedBinary, setSelectedBinary] = useState(null)
  return (
    <div className={classNames('flex flex-col overflow-y-hidden', className)}>
      <div className='flex flex-1 pb-2 overflow-y-hidden'>
        <div className='flex-initial mb-1 overflow-y-auto'>
          <BinariesTable
            binaries={Object.values(runView.binariesById)}
            sorting={binariesSorting}
            setSorting={setBinariesSorting}
            currentBinary={currentBinary}
            setCurrentBinary={setCurrentBinary}
            selectedBinary={selectedBinary}
            setSelectedBinary={setSelectedBinary}
          />
        </div>
        {selectedBinary !== null &&
          <BinaryGraph
            className='flex-auto pt-2 mx-2 border-l'
            binary={selectedBinary}
            setSelectedBinary={setSelectedBinary}
          />}
        {selectedBinary === null && <div className='flex-auto' />}
        <div className='flex flex-col flex-none pl-2 border-l w-80'>
          <RunViewConf className='flex-auto border-b' />
          <SelectedEntries className='flex-auto' />
        </div>
      </div>
      <Timeline
        className='flex-none pt-2 mt-2 border-t border-gray-300 h-36'
        currentBinary={currentBinary}
        selectedBinary={selectedBinary}
      />
    </div>
  )
}
