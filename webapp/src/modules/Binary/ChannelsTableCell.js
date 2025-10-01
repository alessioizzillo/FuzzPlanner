import Bar from '@/components/Bar'
import { PaperAirplaneIcon, CheckCircleIcon } from '@heroicons/react/20/solid'
import { useSelectedEntries, useSetSelectedEntries } from '@/hooks/store/selectedEntries'
import useChartDimensions from '@/hooks/useChartDimensions'
import { channelScoreColor } from '@/scales'
import { MinusCircleIcon, PlusCircleIcon } from '@heroicons/react/20/solid'
import { interpolateViridis } from 'd3-scale-chromatic'
import { useSelectedBrand } from '@/hooks/store/selectedBrand'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { useSelectedRun } from '@/hooks/store/selectedRun'
import { useSelectAnalyses } from '@/hooks/store/useSelectAnalyses'
import { useOptimizedSelectAnalyses } from '@/hooks/useOptimizedPolling'
import { usePostSelect } from '@/hooks/queries'
import { useCallback, useState } from 'react'

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

const checkboxStates = new Map()

function Select({ cRef, dms, value }) {
  const { binary, channel, role } = value
  const checkboxKey = `${binary.id}:::${channel.id}`

  const brandId = useSelectedBrand()
  const firmwareId = useSelectedFirmware()
  const runId = useSelectedRun()

  const postSelectMutation = usePostSelect(brandId, firmwareId, runId, binary.id, channel.id)
  const [sent, setSent] = useState(false)

  const { pollNow } = useSelectAnalyses()
  const { refresh: forceRefresh } = useOptimizedSelectAnalyses(brandId, firmwareId, runId, null, { includeBinaryFilter: false })

  const handleClick = useCallback(() => {
    const ignoreAddr = checkboxStates.get(checkboxKey) || false

    console.log(
      '%c[Selection] Sending to analysis:',
      'color: green; font-weight: bold;',
      { brandId, firmwareId, runId, binaryId: binary.id, channelId: channel.id, ignoreAddr }
    )

    postSelectMutation.mutate(ignoreAddr, {
      onSuccess: () => {
        setSent(true)
        forceRefresh() // Use optimized polling force refresh
        setTimeout(() => setSent(false), 3000)
      },
    })
  }, [brandId, firmwareId, runId, binary.id, channel.id, checkboxKey, postSelectMutation, forceRefresh])

  return (
    <div ref={cRef} className="flex items-center justify-center">
      <div className="w-6 h-6 flex items-center justify-center">
        {['read', 'border', 'rw'].includes(role) && (
          <>
            {!sent ? (
              <PaperAirplaneIcon
                onClick={handleClick}
                className="cursor-pointer text-blue-600 hover:text-blue-800 transition-all duration-200 hover:scale-110 active:scale-95 transform hover:rotate-12"
              />
            ) : (
              <CheckCircleIcon className="text-green-600 animate-bounce" />
            )}
          </>
        )}
      </div>
    </div>
  )
}

function NoAddr({ cRef, value }) {
  const checkboxKey = `${value.binary?.id}:::${value.channel?.id}`
  const [ignoreAddr, setIgnoreAddr] = useState(checkboxStates.get(checkboxKey) || false)

  const handleChange = (e) => {
    const checked = e.target.checked
    setIgnoreAddr(checked)
    checkboxStates.set(checkboxKey, checked)
  }

  return (
    <div ref={cRef} className='h-6 flex items-center justify-center'>
      <input
        type="checkbox"
        checked={ignoreAddr}
        onChange={handleChange}
        className="w-4 h-4 accent-blue-500 cursor-pointer"
        title="Ignore address in socket matching (match port only)"
      />
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
  if (colId === 'no_addr') return <NoAddr cRef={ref} value={value} />
  return null
}
