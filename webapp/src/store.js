import { useState as useStateReact } from 'react'
import { createContainer } from 'react-tracked'

export const initialState = {
  selectedBrand: null,
  selectedFirmware: null,
  selectedRun: null,
  selectedRunData: {},
  selectedRunLogs: [],
  selectedRunGraph: {},
  selectedRunMetadata: {},
  selectedRunView: {
    timeSpan: { min: -1, max: -1 },
    conf: {
      borderThreshold: 0,
      listenThreshold: 0,
      withinThreshold: 0
    },
    binariesById: {},
    metadata: {},
    timeBins: []
  },
  selectedEntries: {},

  emulationStatusByFirmware: {},
  hasFirmwareImage: {},
  runsByFirmware: {},
  selectedBinary: null,
  selectedDataChannel: null,
  selectAnalysesByFirmware: {},
  fuzzExperimentsByFirmware: {}
}

const useValue = () => useStateReact(initialState)

export const {
  Provider: StoreProvider,
  useTrackedState: useState,
  useUpdate: useSetState
} = createContainer(useValue)
