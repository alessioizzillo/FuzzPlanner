import React, { useCallback, useEffect, useState } from 'react'
import create from 'zustand'
import {
  useGetEngineFeatures,
  useGetDictionaries,
  useGetSelectResult,
  useExecuteExperiment
} from '@/hooks/queries'

import { useSelectedRun } from '@/hooks/store/selectedRun'
import { useSelectAnalyses } from '@/hooks/store/useSelectAnalyses'
import {
  useSelectedBinary,
  useSetSelectedBinary,
  useSelectedDataChannel,
  useSetSelectedDataChannel
} from '@/hooks/store/selectedBinaryDataChannel'
import { useSelectedBrand } from '@/hooks/store/selectedBrand'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'

const useLocalStore = create(set => ({
  engineFeatures: [],
  selected_dict_type: '',
  analysisParams: [],

  setEngineFeatures: features => set(() => ({ engineFeatures: features })),
  setEngineFeature: (idx, value) =>
    set(state => {
      const ef = [...state.engineFeatures]
      if (ef[idx]) ef[idx] = { ...ef[idx], value }
      return { engineFeatures: ef }
    }),

  setDictType: val => set(() => ({ selected_dict_type: val })),
  setAnalysisParams: params => set(() => ({ analysisParams: params })),
}))

export default function ExperimentLauncher() {
  const brandId    = useSelectedBrand()
  const firmwareId = useSelectedFirmware()
  const runId      = useSelectedRun()

  const { running, done, selected, setSelected } = useSelectAnalyses()

  const flatten = nested =>
    Object.values(nested).flatMap(binMap => Object.values(binMap))
  const runningList = flatten(running)
  const doneList    = flatten(done)
  const allAnalyses = [...runningList, ...doneList]

  const binaries = Array.from(new Set(allAnalyses.map(a => a.binaryId))).filter(Boolean)

  const selectedBinary      = useSelectedBinary()
  const setSelectedBinary   = useSetSelectedBinary()
  const selectedDataChannel = useSelectedDataChannel()
  const setSelectedDataChannel = useSetSelectedDataChannel()

  const channelOptions = selectedBinary
    ? Array.from(
        new Set(
          allAnalyses
            .filter(a => a.binaryId === selectedBinary)
            .map(a => a.dataChannelId)
        )
      ).filter(Boolean)
    : []

  const { data: engine_features_data = [], isLoading: efLoading } = useGetEngineFeatures()
  const { data: dict_types          = [], isLoading: dtLoading } = useGetDictionaries()
  const { data: selectResult         = [], isLoading: paramLoading } =
    useGetSelectResult(brandId, firmwareId, runId, selectedBinary, selectedDataChannel)
  const executeMutation = useExecuteExperiment()

  const engineFeatures    = useLocalStore(s => s.engineFeatures)
  const setEngineFeatures = useLocalStore(s => s.setEngineFeatures)
  const setEngineFeature  = useLocalStore(s => s.setEngineFeature)
  const selected_dict_type = useLocalStore(s => s.selected_dict_type)
  const setDictType        = useLocalStore(s => s.setDictType)
  const analysisParams     = useLocalStore(s => s.analysisParams)
  const setAnalysisParams  = useLocalStore(s => s.setAnalysisParams)

  useEffect(() => {
    if (!efLoading) {
      setEngineFeatures(engine_features_data.map(f => ({ ...f, value: f.default })))
    }
  }, [efLoading, engine_features_data, setEngineFeatures])

  useEffect(() => {
    if (!paramLoading) {
      setAnalysisParams(selectResult)
    }
  }, [paramLoading, selectResult, setAnalysisParams])

  const handleBinaryChange = useCallback(binId => {
    setSelectedBinary(binId)
    setSelectedDataChannel('')
    setSelected({ type: 'done', binaryId: binId, dataChannelId: '' })
  }, [setSelected, setSelectedBinary, setSelectedDataChannel])

  const handleChannelChange = useCallback(dcId => {
    setSelectedDataChannel(dcId)
    setSelected({ type: 'done', dataChannelId: dcId })
  }, [setSelected, setSelectedDataChannel])

  const [paramIdx, setParamIdx] = useState(null)
  const onParamSelect = idx => setParamIdx(idx === '' ? null : Number(idx))

  const onExecute = () => {
    if (!selectedBinary)      { alert('Select a binary first'); return }
    if (!selectedDataChannel) { alert('Select a data channel first'); return }
    if (!selected_dict_type)  { alert('Select a dictionary type first'); return }
    if (paramIdx === null)     { alert('Select an analysis parameter first'); return }

    const p = analysisParams[paramIdx]
    const payload = {
      runId,
      executableId: selectedBinary,
      data_channel_id: selectedDataChannel,
      chosen_dictionary_type: selected_dict_type,
      chosen_parameters: {
        syscall: p.syscall,
        pc: p.pc || '0x0',
        pattern: p.pattern
      },
      set_engine_features: engineFeatures.map(f => ({ name: f.name, type: f.type, value: f.value }))
    }

    executeMutation.mutate(
      { brandId, firmwareId, payload },
      {
        onSuccess: () => alert('Execution request sent successfully'),
        onError: err => alert(`Execution failed: ${err.message}`)
      }
    )
  }

  const canExecute = Boolean(
    selectedBinary &&
    selectedDataChannel &&
    selected_dict_type &&
    paramIdx !== null
  )

  return (
    <div className="w-full h-full overflow-auto p-4 space-y-6">
      <div>
        <h2 className="text-lg font-bold mb-4 text-blue-400">⚙️ Engine Features</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-8 gap-3">
          {efLoading
            ? <p>Loading features…</p>
            : engineFeatures.map((f, i) => (
                <div key={f.name} className="flex flex-col justify-between items-center p-2 bg-gray-800 rounded hover:shadow w-full" style={{ minHeight: '3rem' }}>
                  <span className="text-xs text-gray-100 text-center whitespace-normal break-words w-full">{f.name}</span>
                  {f.type === 'boolean'
                    ? <input type="checkbox" className="mt-2 accent-blue-500" checked={f.value === 'true' || f.value === true} onChange={e => setEngineFeature(i, e.target.checked.toString())} style={{ alignSelf: 'center' }}/>
                    : <input type={f.type === 'integer' ? 'number' : 'text'} className="mt-2 border rounded px-1 py-0.5 w-full text-xs text-black" value={f.value} onChange={e => setEngineFeature(i, e.target.value)} style={{ alignSelf: 'center', maxWidth: '100%' }}/>
                  }
                </div>
              ))
          }
        </div>
      </div>

      <div>
        <h2 className="text-lg font-bold mb-4 text-green-400">📦 Dictionary Type</h2>
        {dtLoading
          ? <p>Loading dictionaries…</p>
          : <select className="border px-2 py-1 bg-gray-800 text-gray-100 rounded" value={selected_dict_type} onChange={e => setDictType(e.target.value)}>
              <option value="" disabled>Select a dictionary…</option>
              {dict_types.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
        }
      </div>

      <div>
        <h2 className="text-lg font-bold mb-4 text-red-400">🔍 Analysis Parameters</h2>
        {paramLoading
          ? <p>Loading parameters…</p>
          : <select className="border px-2 py-1 bg-gray-800 text-gray-100 rounded w-full" value={paramIdx !== null ? paramIdx : ''} onChange={e => onParamSelect(e.target.value)}>
              <option value="">Select a parameter…</option>
              {analysisParams.map((p, i) => <option key={i} value={i}>{p.syscall} | {p.pattern || 'no pattern'}</option>)}
            </select>
        }
      </div> 

      <div className="mt-6">
        <button onClick={onExecute} disabled={!canExecute || executeMutation.isLoading} className={`bg-blue-600 text-white font-bold px-6 py-3 rounded hover:bg-blue-700 ${(!canExecute || executeMutation.isLoading) ? 'opacity-50 cursor-not-allowed' : ''}`}>{executeMutation.isLoading ? 'Executing...' : 'Execute Experiment'}</button>
      </div>

    </div>
  )
}