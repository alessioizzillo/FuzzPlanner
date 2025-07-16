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

export async function getRuns (brandId, fwId) {
  return await getFile('runs', { fwId })
}

export async function getExecutableFiles (brandId, fwId, runId) {
  return await getFile('file/executable_files', { brandId, fwId, runId })
}

export async function getProcesses (brandId, fwId, runId) {
  return await getFile('file/processes', { brandId, fwId, runId })
}

export async function getDataChannels (brandId, fwId, runId) {
  return await getFile('file/data_channels', { brandId, fwId, runId })
}

export async function getInteractions (brandId, fwId, runId) {
  return await getFile('file/interactions', { brandId, fwId, runId })
}
