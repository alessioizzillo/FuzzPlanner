import { useState } from 'react'
import ConfigPanel from '@/modules/ConfigPanel'
import RunManager from '@/modules/RunManager'

export default function TabbedPanel({ config }) {
  const [activeTab, setActiveTab] = useState('config')

  return (
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
          onClick={() => setActiveTab('run')}
        >
          🚀 Run Manager
        </button>
      </div>

      <div className='flex-1 overflow-hidden p-2 bg-gray-900'>
        {activeTab === 'config' && (
          <div className="h-full overflow-auto">
            <ConfigPanel config={config} />
          </div>
        )}
        {activeTab === 'run' && (
          <div className="h-full overflow-hidden">
            <RunManager />
          </div>
        )}
      </div>

    </div>
  )
}
