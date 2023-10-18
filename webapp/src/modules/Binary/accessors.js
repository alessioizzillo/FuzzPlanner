import { dataChannelKindsById, getDataChannelKind } from '@/constants'

export function accessorChannel (row) {
  return row.data
}

export function accessorScore (row) {
  return row.data.score
}

export function accessorKind (row) {
  return dataChannelKindsById[getDataChannelKind(row.data.kind)]
}

export function accessorRole (row) {
  console.log(row)
  return row.role
}
