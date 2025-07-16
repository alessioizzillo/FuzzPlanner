import { useSelectedRunView } from '@/hooks/store/selectedRun'
import { useSelectedRun } from '@/hooks/store/selectedRun'
import { useState } from 'react'
import BinariesTable from '@/modules/BinariesTable/BinariesTable'
import Timeline from './Timeline/Timeline'
import classNames from 'classnames'
import BinaryGraph from './Binary/BinaryGraph'
import RunViewConf from './RunViewConf'
import RunningSelectExperiments from './RunningSelect' // <--- import the new component

export default function RunManager({ className }) {
  const selectedRun = useSelectedRun()
  const runView     = useSelectedRunView()
  const [binariesSorting, setBinariesSorting] = useState([{ id: 'border', desc: true }])
  const [currentBinary, setCurrentBinary] = useState(null)
  const [selectedBinary, setSelectedBinary] = useState(null)

  // If no run has been chosen yet…
  if (!selectedRun) {
    return (
      <div className={classNames('flex items-center justify-center h-full', className)}>
        <p className="text-gray-500">No run selected. Please choose a run to view its analysis.</p>
      </div>
    )
  }

  if (!runView || !runView.binariesById || Object.keys(runView.binariesById).length === 0) {
    return (
      <div className={classNames('flex items-center justify-center h-full', className)}>
        <p className="text-gray-500">Loading run data…</p>
      </div>
    )
  }

  return (
    <div className={classNames('flex flex-col h-full max-h-full overflow-hidden', className)}>
      
      <div className='flex flex-1 overflow-hidden'>

        <div className='flex-initial overflow-auto max-h-full'>
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

        {selectedBinary !== null ? (
          <BinaryGraph
            className='flex-auto pt-2 mx-2 border-l'
            binary={selectedBinary}
            setSelectedBinary={setSelectedBinary}
          />
        ) : (
          <div className='flex-auto' />
        )}

        <div className="flex flex-col flex-none pl-2 border-l w-80 overflow-hidden">
          <RunViewConf className="flex-auto border-b" />
          
          <div className="flex flex-col flex-auto mt-2">
            <RunningSelectExperiments className="flex-auto" />
          </div>
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
