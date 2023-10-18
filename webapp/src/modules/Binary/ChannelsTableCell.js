import Bar from '@/components/Bar'
import { useSelectedEntries, useSetSelectedEntries } from '@/hooks/store/selectedEntries'
import useChartDimensions from '@/hooks/useChartDimensions'
import { channelScoreColor } from '@/scales'
import { MinusCircleIcon, PlusCircleIcon } from '@heroicons/react/20/solid'
import { interpolateViridis } from 'd3-scale-chromatic'
import { useCallback, useMemo } from 'react'

function getSettings (colId) {
  if (colId === 'channel') {
    return {
      marginLeft: 10,
      marginTop: 0,
      marginRight: 0,
      marginBottom: 0
    }
  }
  if (['score'].indexOf(colId) >= 0) {
    return {
      marginLeft: 30,
      marginTop: 0,
      marginRight: 0,
      marginBottom: 0
    }
  }
  return {
    marginLeft: 10,
    marginTop: 0,
    marginRight: 0,
    marginBottom: 0
  }
}

function Channel ({ cRef, dms, value }) {
  return (
    <div ref={cRef} className='h-10 overflow-hidden text-sm text-left w-60 text-ellipsis' style={{ direction: 'rtl' }}>
      {value.id}
    </div>
  )
}

function Kind ({ cRef, dms, value }) {
  return (
    <div ref={cRef} className='w-6 h-6'>
      <value.Icon />
    </div>
  )
}

function Select ({ cRef, dms, value }) {
  const { binary, channel, role } = value
  const id = `${binary.id}-${channel.id}`
  const selectedEntries = useSelectedEntries()
  const setSelectedEntries = useSetSelectedEntries()
  const handleClick = useCallback(() => {
    const v = {
      id,
      binary,
      channel
    }
    setSelectedEntries({ id, v })
  }, [binary.id, channel.id])
  return (
    <div ref={cRef} className='w-6 h-6'>
      {['read', 'border', 'rw'].indexOf(role) >= 0 &&
        <>
          {!selectedEntries[id] && <PlusCircleIcon onClick={handleClick} />}
          {selectedEntries[id] && <MinusCircleIcon onClick={handleClick} />}
        </>}
    </div>
  )
}

function mapRole (role) {
  if (role === 'border') return 'B'
  if (role === 'listen') return 'L'
  if (role === 'read') return 'R'
  if (role === 'write') return 'W'
  if (role === 'rw') return 'R/W'
}
function Role ({ cRef, dms, value }) {
  return (
    <div ref={cRef} className='h-6 text-sm'>
      {mapRole(value)}
    </div>
  )
}

export default function ChannelsTableCell ({ colId, value }) {
  const [ref, dms] = useChartDimensions(getSettings(colId))
  if (['score'].indexOf(colId) >= 0) return <Bar cRef={ref} dms={dms} value={value} colorScale={channelScoreColor} />
  if (colId === 'channel') return <Channel cRef={ref} dms={dms} value={value} />
  if (colId === 'kind') return <Kind cRef={ref} dms={dms} value={value} />
  if (colId === 'select') return <Select cRef={ref} dms={dms} value={value} />
  if (colId === 'role') return <Role cRef={ref} dms={dms} value={value} />
  if (colId === 'kind') return <Kind cRef={ref} dms={dms} value={value} />
  return null
}
