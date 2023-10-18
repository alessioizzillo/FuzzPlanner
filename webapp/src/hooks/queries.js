import { useQueries, useQuery } from '@tanstack/react-query'

import { getFirmwares, getRuns, getExecutableFiles, getProcesses, getDataChannels, getInteractions } from '@/requests'

export function useGetFirmwares () {
  return useQuery({
    queryKey: ['firmwares'],
    queryFn: getFirmwares
  })
}

export function useGetRuns (fwId) {
  return useQuery({
    queryKey: ['runs', fwId],
    queryFn: () => getRuns(fwId)
  })
}

function executableFilesQuery (fwId, runId) {
  return {
    queryKey: ['executableFiles', fwId, runId],
    queryFn: () => getExecutableFiles(fwId, runId)
  }
}

function processesQuery (fwId, runId) {
  return {
    queryKey: ['processes', fwId, runId],
    queryFn: () => getProcesses(fwId, runId)
  }
}

function dataChannelsQuery (fwId, runId) {
  return {
    queryKey: ['dataChannels', fwId, runId],
    queryFn: () => getDataChannels(fwId, runId)
  }
}

function interactionsQuery (fwId, runId) {
  return {
    queryKey: ['interactions', fwId, runId],
    queryFn: () => getInteractions(fwId, runId)
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
