import { useQuery, useMutation, useQueries } from '@tanstack/react-query'
import axios from 'axios'

// Configure a default axios instance for the backend
export const api = axios.create({
  baseURL: 'http://localhost:4000',
  headers: { 'Content-Type': 'application/json' }
})

import {
  getFirmwares,
  getRuns,
  getExecutableFiles,
  getProcesses,
  getDataChannels,
  getInteractions
} from '@/requests'

// Helper queries for different run data types
function executableFilesQuery (fwId, runId) {
  return {
    queryKey: ['executableFiles', fwId, runId],
    queryFn: () => getExecutableFiles(fwId, runId),
    enabled: !!fwId && !!runId
  }
}

function processesQuery (fwId, runId) {
  return {
    queryKey: ['processes', fwId, runId],
    queryFn: () => getProcesses(fwId, runId),
    enabled: !!fwId && !!runId
  }
}

function dataChannelsQuery (fwId, runId) {
  return {
    queryKey: ['dataChannels', fwId, runId],
    queryFn: () => getDataChannels(fwId, runId),
    enabled: !!fwId && !!runId
  }
}

function interactionsQuery (fwId, runId) {
  return {
    queryKey: ['interactions', fwId, runId],
    queryFn: () => getInteractions(fwId, runId),
    enabled: !!fwId && !!runId
  }
}

export function useGetExecutableFiles (fwId, runId) {
  return useQuery(executableFilesQuery(fwId, runId))
}

export function useGetProcesses (fwId, runId) {
  return useQuery(processesQuery(fwId, runId))
}

export function useGetDataChannels (fwId, runId) {
  return useQuery(dataChannelsQuery(fwId, runId))
}

export function useGetInteractions (fwId, runId) {
  return useQuery(interactionsQuery(fwId, runId))
}

export function useGetRunData (fwId, runId) {
  return useQueries({
    queries: [
      executableFilesQuery(fwId, runId),
      processesQuery(fwId, runId),
      dataChannelsQuery(fwId, runId),
      interactionsQuery(fwId, runId)
    ]
  })
}

// — Firmware & Runs —
export const useGetFirmwares = () =>
  useQuery(
    ['firmwares'],
    () => api.get('/firmwares').then(res => res.data.firmwares)
  )

export const useGetRuns = (firmwareId) =>
  useQuery(
    ['runs', firmwareId],
    () => api.get('/runs', { params: { firmwareId } }).then(res => res.data.runs),
    { enabled: !!firmwareId }
  )

// — Emulation Controls —
export const useStartEmulation = (firmwareId) =>
  useMutation(() =>
    api.post('/emulate', null, { params: { firmwareId } })
  )

export const usePauseEmulation = (firmwareId) =>
  useMutation(() =>
    api.post('/pause_emulation', null, { params: { firmwareId } })
  )

export const useStopEmulation = (firmwareId) =>
  useMutation(() =>
    api.post('/stop_emulation', null, { params: { firmwareId } })
  )

export const useEmuStatus = (firmwareId) =>
  useQuery(
    ['emu_status', firmwareId],
    () => api.get('/emu_status', { params: { firmwareId } }).then(res => res.data),
    { enabled: !!firmwareId, refetchInterval: 2000 }
  )

// — Data and Experiment Selection / Execution —
export const useGetData = (firmwareId, runId, type) =>
  useQuery(
    ['data', firmwareId, runId, type],
    () => api.get('/data', { params: { firmwareId, runId, type } }).then(res => res.data),
    { enabled: !!firmwareId && !!runId }
  )

export const usePostSelect = (firmwareId, runId) =>
  useMutation((body) =>
    api.post('/select', body, { params: { firmwareId, runId } })
  )

export const usePostExecute = (firmwareId, runId) =>
  useMutation((body) =>
    api.post('/execute', body, { params: { firmwareId, runId } })
  )

// — Frontend-specific endpoints —
export const usePutRun = (firmwareId, runId) =>
  useMutation(() =>
    api.put('/api/run', {}, { params: { firmwareId, runId } })
  )

export const usePutIpFirmware = (firmwareId, IP) =>
  useMutation(() =>
    api.put('/api/ip_firmware', {}, { params: { firmwareId, IP } })
  )

export const usePostSelectRes = (firmwareId, runId) =>
  useMutation((body) =>
    api.post('/api/select_res', body, { params: { firmwareId, runId } })
  )
