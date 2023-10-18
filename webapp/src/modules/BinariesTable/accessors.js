import { getCVSS, getHighestBaseScore } from '@/cveUtils'

export function accessorBinary (row) {
  return row.data
}

export function accessorProprietary (row) {
  return row.data.exec.is_proprietary ? 1 : 0
}

export function accessorCve (row) {
  return getHighestBaseScore(row.data.exec.cves)
}

export function accessorCwe (row) {
  return row.data.exec.cwes.length > 5 ? 1 : row.data.exec.cwes.length / 5
}

export function accessorListen (row) {
  let maxListen = 0
  Object.values(row.listenChannelsById).forEach(ch => {
    if (!row.borderChannelsById[ch.id]) maxListen = Math.max(maxListen, ch.data.score)
  })
  return maxListen
}
export function accessorBorder (row) {
  let maxBorder = 0
  Object.values(row.borderChannelsById).forEach(ch => { maxBorder = Math.max(maxBorder, ch.data.score) })
  return maxBorder
}
export function accessorWithinRead (row) {
  let maxWithinRead = 0
  Object.values(row.withinReadChannelsById).forEach(ch => { maxWithinRead = Math.max(maxWithinRead, ch.data.score) })
  return maxWithinRead
}
export function accessorSpawnParent (row) {
  let numSpawnParents = 0
  numSpawnParents += Object.values(row.spawnParentExecsById).length
  return numSpawnParents
}
export function accessorWithinWrite (row) {
  let maxWithinWrite = 0
  Object.values(row.withinWriteChannelsById).forEach(ch => { maxWithinWrite = Math.max(maxWithinWrite, ch.data.score) })
  return maxWithinWrite
}
export function accessorSpawnChild (row) {
  let numSpawnChildren = 0
  numSpawnChildren += Object.values(row.spawnChildExecsById).length
  return numSpawnChildren
}
