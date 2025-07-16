import BrandPicker from '@/modules/BrandPicker'
import FirmwarePicker from '@/modules/FirmwarePicker'
import RunPicker from '@/modules/RunPicker'
import EmulationPanel from '@/modules/EmulationPanel'
import ConfigPanel from '@/modules/ConfigPanel'
import RunManager from '@/modules/RunManager'

import { useSelectedBrand } from '@/hooks/store/selectedBrand'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'

import { useState } from 'react'

export default function Home () {
  const selectedBrand = useSelectedBrand()
  const selectedFirmware = useSelectedFirmware()
  const [selectedRun, setSelectedRun] = useState(null)
  const [activeTab, setActiveTab] = useState('config')

  return (
    <div className='flex flex-col h-screen max-h-screen'>

      <div className='flex items-center justify-between p-2 space-x-2 border-b border-gray-700 bg-gray-900 text-gray-200'>
        <span className='text-lg'>FuzzPlanner</span>
      </div>

      <div className='flex flex-col flex-1 overflow-hidden p-2'>

        <div className='flex space-x-2 mb-2'>
          <BrandPicker />
          {selectedBrand && <FirmwarePicker />}
          {selectedBrand && selectedFirmware && (
            <RunPicker
              selectedRun={selectedRun}
              onRunSelect={setSelectedRun}
            />
          )}
        </div>

        {selectedBrand && selectedFirmware && (
          <div className="flex flex-col flex-1 overflow-hidden space-y-2">
            <EmulationPanel className='flex-none' />

            <div className='flex flex-col h-full max-h-full overflow-hidden border rounded bg-gray-900 text-gray-200'>

              <div className='flex border-b border-gray-700 bg-gray-800 flex-none'>
                <button
                  className={`px-4 py-2 flex-1 text-center transition-colors ${
                    activeTab === 'config'
                      ? 'bg-gray-900 font-bold border-b-2 border-blue-500 text-white'
                      : 'hover:bg-gray-700 text-gray-400'
                  }`}
                  onClick={() => setActiveTab('config')}
                >
                  ⚙️ Config Panel
                </button>
                <button
                  className={`px-4 py-2 flex-1 text-center transition-colors ${
                    activeTab === 'run'
                      ? 'bg-gray-900 font-bold border-b-2 border-blue-500 text-white'
                      : 'hover:bg-gray-700 text-gray-400'
                  }`}
                  onClick={() => {
                    console.log('Run Manager button clicked, selectedRun:', selectedRun)
                    setActiveTab('run')
                  }}
                  title={!selectedRun ? 'Select a run first to access Run Manager' : undefined}
                >
                  🚀 Run Manager
                </button>
              </div>

              <div className='flex-1 overflow-hidden p-2 bg-gray-900'>
                {activeTab === 'config' && (
                  <div className="h-full overflow-auto">
                    <ConfigPanel />
                  </div>
                )}
                {activeTab === 'run' && (
                  <div className="h-full overflow-hidden">
                    <RunManager />
                  </div>
                )}
              </div>

            </div>

          </div>
        )}
      </div>
    </div>
  )
}
