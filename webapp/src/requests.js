import { getHttp } from '@/utils'

async function getFile (name, params) {
  try {
    const data = await getHttp(`/api/${name}`, {}, params)
    return data
  } catch (_e) {
    return {}
  }
}

export async function getFirmwares () {
  return await getFile('firmwares', {})
}

export async function getRuns (fwId) {
  return await getFile('runs', { fwId })
}

export async function getExecutableFiles (fwId, runId) {
  return await getFile('file/executable_files', { fwId, runId })
}

export async function getProcesses (fwId, runId) {
  return await getFile('file/processes', { fwId, runId })
}

export async function getDataChannels (fwId, runId) {
  return await getFile('file/data_channels', { fwId, runId })
}

export async function getInteractions (fwId, runId) {
  return await getFile('file/interactions', { fwId, runId })
}
