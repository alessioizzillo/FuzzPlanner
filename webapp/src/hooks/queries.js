import { useQuery, useMutation, useQueries } from '@tanstack/react-query'
import axios from 'axios'

export const api = axios.create({
  baseURL: 'http://localhost:4000',
  headers: { 'Content-Type': 'application/json' }
})

function executableFilesQuery(brandId, fwId, runId) {
  return {
    queryKey: ['executableFiles', brandId, fwId, runId],
    queryFn: () => getExecutableFiles(brandId, fwId, runId),
    enabled: !!brandId && !!fwId && !!runId
  }
}

function processesQuery(brandId, fwId, runId) {
  return {
    queryKey: ['processes', brandId, fwId, runId],
    queryFn: () => getProcesses(brandId, fwId, runId),
    enabled: !!brandId && !!fwId && !!runId
  }
}

function dataChannelsQuery(brandId, fwId, runId) {
  return {
    queryKey: ['dataChannels', brandId, fwId, runId],
    queryFn: () => getDataChannels(brandId, fwId, runId),
    enabled: !!brandId && !!fwId && !!runId
  }
}

function interactionsQuery(brandId, fwId, runId) {
  return {
    queryKey: ['interactions', brandId, fwId, runId],
    queryFn: () => getInteractions(brandId, fwId, runId),
    enabled: !!brandId && !!fwId && !!runId
  }
}

async function getExecutableFiles(brandId, fwId, runId) {
  console.debug('Fetching executable files with params:', { brandId, fwId, runId })
  const res = await api.get('/executable_files', { params: { firmwareId: brandId, fwId, runId } })
  console.debug('Received executable files:', res.data)
  return res.data
}

async function getProcesses(brandId, fwId, runId) {
  const res = await api.get('/processes', { params: { firmwareId: brandId, fwId, runId } })
  return res.data
}

async function getDataChannels(brandId, fwId, runId) {
  const res = await api.get('/data_channels', { params: { firmwareId: brandId, fwId, runId } })
  return res.data
}

async function getInteractions(brandId, fwId, runId) {
  const res = await api.get('/interactions', { params: { firmwareId: brandId, fwId, runId } })
  return res.data
}

async function removeRun(brandId, firmwareId, runId) {
  const res = await api.post('/remove_run', null, { params: { brandId, firmwareId, runId } })
  if (res.status !== 200) {
    throw new Error(`Failed to remove run: ${res.statusText}`)
  }
}

export function useGetExecutableFiles(brandId, fwId, runId) {
  return useQuery(executableFilesQuery(brandId, fwId, runId))
}

export function useGetProcesses(brandId, fwId, runId) {
  return useQuery(processesQuery(brandId, fwId, runId))
}

export function useGetDataChannels(brandId, fwId, runId) {
  return useQuery(dataChannelsQuery(brandId, fwId, runId))
}

export function useGetInteractions(brandId, fwId, runId) {
  return useQuery(interactionsQuery(brandId, fwId, runId))
}

export function useGetRunData(brandId, fwId, runId) {
  return useQueries({
    queries: [
      executableFilesQuery(brandId, fwId, runId),
      processesQuery(brandId, fwId, runId),
      dataChannelsQuery(brandId, fwId, runId),
      interactionsQuery(brandId, fwId, runId)
    ]
  })
}

export const useGetBrands = () =>
  useQuery(['brands'], () => api.get('/brands').then(res => res.data))

export const useGetFirmwares = (brandId) =>
  useQuery(
    ['firmwares', brandId],
    () => api.get('/firmwares', { params: { brandId } }).then(res => res.data.firmwares),
    { enabled: !!brandId }
  )

export const useGetRuns = (brandId, firmwareId, options = {}) =>
  useQuery(
    ['runs', brandId, firmwareId],
    async () => {
      const response = await api.get('/runs', { params: { brandId, firmwareId } });
      return response.data.runs;
    },
    {
      enabled: !!brandId && !!firmwareId,
      ...options
    }
  )
  
export const useStartEmulation = (brandId, firmwareId) =>
  useMutation(() => api.post('/run_capture', null, { params: { brandId, firmwareId } }))

export const usePauseEmulation = (brandId, firmwareId) =>
  useMutation(() => api.post('/pause_run_capture', null, { params: { brandId, firmwareId } }))

export const useStopEmulation = (brandId, firmwareId) =>
  useMutation(() => api.post('/stop_emulation', null, { params: { brandId, firmwareId } }))

export const useResumeEmulation = (brandId, firmwareId) =>
  useMutation(() => api.post('/resume_emulation', null, { params: { brandId, firmwareId } }))

export const useCheckRun = (brandId, firmwareId) =>
  useQuery(
    ['check_run', brandId, firmwareId],
    () => api.get('/check_run', { params: { brandId, firmwareId } }).then(res => res.data),
    { enabled: !!brandId && !!firmwareId }
  )

export const useCheckFirmwareImage = (brandId, firmwareId) =>
  useQuery(
    ['check_firm_img', brandId, firmwareId],
    () => api.get('/check_firm_img', { params: { brandId, firmwareId } }).then(res => res.data),
    { enabled: !!brandId && !!firmwareId }
  )

export const useCreateFirmwareImage = (brandId, firmwareId) =>
  useMutation(() =>
    api.get('/create_firm_img', { params: { brandId, firmwareId } })
      .then(res => {
        if (res.status === 200) return res.data
        throw new Error(`Image creation failed: ${res.statusText}`)
      })
  )

export const usePauseRunCapture = (brandId, firmwareId, factUid = '') =>
  useMutation(() => {
    const params = { brandId, firmwareId }
    if (factUid) params.factUid = factUid
    return api.post('/pause_run_capture', null, { params })
  })

export const useRemoveRun = (brandId, firmwareId, runId) =>
  useMutation(() => removeRun(brandId, firmwareId, runId))

async function fetchEngineFeatures() {
  const res = await api.get('/engine_features')
  return res.data
}

export function useGetEngineFeatures(options = {}) {
  return useQuery(
    ['engine_features'],
    fetchEngineFeatures,
    { enabled: true, ...options }
  )
}

async function fetchDictionaries() {
  const res = await api.get('/dictionaries')
  return res.data
}

export function useGetDictionaries(options = {}) {
  return useQuery(
    ['dictionaries'],
    fetchDictionaries,
    { enabled: true, ...options }
  )
}

async function fetchSelectResult(brandId, firmwareId, runId, binaryId, dataChannelId) {
  const res = await api.post(
    '/select_res',
    null,
    { params: { brandId, firmwareId, runId, binaryId, dataChannelId } }
  )
  return res.data
}

export function useGetSelectResult(
  brandId,
  firmwareId,
  runId,
  binaryId,
  dataChannelId,
  options = {}
) {
  return useQuery(
    ['select_result', brandId, firmwareId, runId, binaryId, dataChannelId],
    () => fetchSelectResult(brandId, firmwareId, runId, binaryId, dataChannelId),
    {
      enabled:
        !!brandId &&
        !!firmwareId &&
        !!runId &&
        !!binaryId &&
        !!dataChannelId,
      ...options
    }
  )
}

export function useExecuteExperiment() {
  return useMutation(async ({ brandId, firmwareId, runId, payload }) => {
    const url = `http://localhost:4000/execute?brandId=${encodeURIComponent(brandId)}&firmwareId=${encodeURIComponent(firmwareId)}`
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || 'Execution failed')
    }
    return res.json()
  })
}

async function postSelect(brandId, firmwareId, runId, binaryId, dataChannelId) {
  const res = await api.post(
    '/select',
    null,
    {
      params: {
        brandId,
        firmwareId,
        runId,
        binaryId,
        dataChannelId
      }
    }
  )
  return res.data
}

export function usePostSelect(brandId, firmwareId, runId, binaryId, dataChannelId, options = {}) {
  return useMutation(
    () => postSelect(brandId, firmwareId, runId, binaryId, dataChannelId),
    { ...options }
  )
}

export function useGetSelectAnalyses(brandId, firmwareId, runId, options = {}) {
  return useQuery({
    queryKey: ['selectAnalyses', brandId, firmwareId, runId],
    queryFn: async () => {
      const res = await api.get('/select_analyses', {
        params: { brandId, firmwareId, runId },
      })
      return res.data
    },
    enabled: !!brandId && !!firmwareId && !!runId,
    ...options,
  })
}

export function useGetFuzzExperiments(brandId, firmwareId) {
  return useQuery({
    queryKey: ['fuzz_experiments', brandId, firmwareId],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (brandId)    params.append('brandId', brandId)
      if (firmwareId) params.append('firmwareId', firmwareId)

      const res = await api.get(`/fuzz_experiments?${params.toString()}`)
      return res.data
    },
    staleTime: 5000,
  })
}

export async function getExperimentInfo({ brandId, firmwareId, expName }) {
  const params = new URLSearchParams({ brandId, firmwareId, expName })
  const res = await api.get(`/exp_info?${params.toString()}`)
  return res.data
}

export async function removeExperiment({ brandId, firmwareId, expName }) {
  const params = new URLSearchParams({ brandId, firmwareId, expName })
  const res = await api.post(`/remove_experiment?${params.toString()}`)
  return res.data
}

export async function removeSelect({ brandId, firmwareId, runId, binaryId, dataChannelId }) {
  const params = new URLSearchParams({ brandId, firmwareId, runId, binaryId, dataChannelId })
  const url = `/remove_select?${params.toString()}`
  try {
    const res = await api.post(url)
    return res.data
  } catch (err) {
    throw err.response?.data || err
  }
}

export async function removeSelectBinary({ brandId, firmwareId, runId, binaryId }) {
  const params = new URLSearchParams({ brandId, firmwareId, runId, binaryId })
  const url = `/remove_select_binary?${params.toString()}`
  try {
    const res = await api.post(url)
    return res.data
  } catch (err) {
    throw err.response?.data || err
  }
}