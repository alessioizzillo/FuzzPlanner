import ExperimentsPanel from './ExperimentsPanel'
import ExperimentLauncher from './ExperimentLauncher'
import TargetPicker from './TargetPicker'
import { useSelectedRun } from '@/hooks/store/selectedRun'
import { 
  useSelectedBinary, 
  useSelectedDataChannel,
} from '@/hooks/store/selectedBinaryDataChannel'

export default function ConfigPanel() {
  const selectedBinary = useSelectedBinary()
  const selectedDataChannel = useSelectedDataChannel()
  const selectedRun = useSelectedRun()

  return (
    <div className="flex h-full bg-gray-900 text-gray-200 overflow-hidden">

      <div className="w-3/4 h-full flex flex-col overflow-hidden">
        {selectedRun && <TargetPicker />}

        {selectedBinary && selectedDataChannel && (
          <div className="flex-1 overflow-auto mt-6">
            <ExperimentLauncher />
          </div>
        )}
      </div>

      <div className="w-1/4 h-full border-l border-gray-700 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-auto p-4">
          <ExperimentsPanel />
        </div>
      </div>

    </div>
  )
}
