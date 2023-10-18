import { FaGlobe, FaFloppyDisk, FaCodeCompare, FaGear } from 'react-icons/fa6'
import { PiFile, PiFileDashed } from 'react-icons/pi'

export const dataChannelKinds = ['network_socket', 'file', 'virtual_file', 'device', 'internal_channel', 'other']

export const eventTypes = ['init', 'fork', 'spawn', 'border', 'listen', 'within']

export const groupedEventTypes = [
  {
    id: 'border',
    label: 'Border',
    types: ['border']
  },
  {
    id: 'listen',
    label: 'Listen',
    types: ['listen']
  },
  {
    id: 'within',
    label: 'R W',
    types: ['within']
  },
  {
    id: 'spawn',
    label: 'Spawn',
    types: ['spawn']
  },
  {
    id: 'init-fork',
    label: 'Fork',
    types: ['init', 'fork']
  }
]

export const groupedEventTypesMapping = {
  border: 'border',
  within: 'within',
  listen: 'listen',
  spawn: 'spawn',
  init: 'init-fork',
  fork: 'init-fork'
}

export const dataChannelsMapping = {
  file: 'file',
  virtual_file: 'virtual_file',
  device: 'device',
  pipe: 'internal_channel',
  unix_socket: 'internal_channel',
  inet_socket: 'network_socket',
  inet6_socket: 'network_socket',
  netlink_socket: 'internal_channel',
  packet_socket: 'internal_channel'
}

export function getDataChannelKind (id) {
  return dataChannelsMapping[id] || 'other'
}

export const dataChannelKindsById = {
  network_socket: {
    id: 'network_socket',
    label: 'Network Socket',
    color: '#fdb462',
    Icon: FaGlobe
  },
  file: {
    id: 'file',
    label: 'File',
    color: '#8dd3c7',
    Icon: PiFile
  },
  virtual_file: {
    id: 'virtual_file',
    label: 'Virtual File',
    color: '#ffffb3',
    Icon: PiFileDashed
  },
  device: {
    id: 'device',
    label: 'Device',
    color: '#fb8072',
    Icon: FaFloppyDisk
  },
  internal_channel: {
    id: 'internal_channel',
    label: 'Internal Channel',
    color: '#bebada',
    Icon: FaCodeCompare
  },
  other: {
    id: 'other',
    label: 'Other',
    color: '#80b1d3',
    Icon: FaGear
  }
}

export const inputPathsLength = 1

export const timeBins = 100
