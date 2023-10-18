import classNames from 'classnames'
import { useMemo } from 'react'
import { interpolateViridis } from 'd3-scale-chromatic'
import { Tooltip } from 'react-tooltip'

import { inputPathsLength, getDataChannelKind, dataChannelKindsById } from '@/constants'

import useChartDimensions from '@/hooks/useChartDimensions'
import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { useSelectedRun } from '@/hooks/store/selectedRun'
import { useBinariesView } from '@/hooks/graphs'
import { useRunLogs } from '@/hooks/data'

const chartSettings = {
  marginLeft: 0,
  marginTop: 0,
  marginRight: 0,
  marginBottom: 0
}

function sanitizeId (str) {
  // Remove any leading or trailing whitespace
  str = str.trim()
  // Replace any characters that are not alphanumeric, underscore, or hyphen with an underscore
  str = str.replace(/[^a-zA-Z0-9_-]/g, '_')
  // Ensure the first character is a letter (IDs cannot start with a number)
  if (/^[^a-zA-Z]/.test(str)) {
    str = 'id_' + str // Prepend 'id_' if the first character is not a letter
  }
  return str
}

function Binary ({ bin }) {
  return (
    <div className='flex items-center py-1 pl-4 mr-2 text-sm'>
      <div className='flex py-1'>
        <div className={classNames('w-4 h-4 border', bin.data.is_proprietary ? 'bg-slate-300' : '')} />
        <div className={classNames('w-4 h-4 border', !bin.data.is_proprietary ? 'bg-slate-300' : '')} />
      </div>
      <div className='w-48 px-2 overflow-hidden text-ellipsis whitespace-nowrap'>{bin.id}</div>
    </div>

  )
}
function InputStep ({ step }) {
  const { color, Icon } = useMemo(() => (dataChannelKindsById[getDataChannelKind(step.top_channel.kind)]), [step])
  return (
    <>
      <div id={sanitizeId(`input-step_${step.id}`)} className='flex items-center text-xs text-center w-14'>
        <div className='flex flex-col items-center'>
          <svg width={16} height={16}>
            <rect stroke='gray' fillOpacity={0} x={0} y={0} height={16} width={16} />
            <rect fill={interpolateViridis(step.top_channel.score)} x={0} y={0} height={16} width={16 * step.top_channel.score} />
          </svg>
          <div className='w-6 h-4 mt-1'>{step.top_channel.counts}</div>

        </div>
        <div className='flex flex-col items-center'>
          <Icon className='w-4 h-4' fill={color} />
          <div className='w-6 h-4 mt-1'>{Object.keys(step.channels).length}</div>
        </div>
      </div>
      <Tooltip anchorSelect={`#${sanitizeId(`input-step_${step.id}`)}`} place='top' clickable>
        <div className='text-sm'>
          <div>
            <span>{step.binarySource.type === 'binary' ? step.binarySource.id : 'Border'}</span>
            <span>{' -> '}</span>
            <span>{step.top_channel.id}</span>
          </div>
          <div />
        </div>
      </Tooltip>
    </>
  )
}
function InputPath ({ path, className }) {
  return (
    <div className={classNames('flex items-start pt-2 pb-1', className)}>
      <div className='flex'>
        {Array.from(Array(inputPathsLength - path.steps.length)).map((_, ix) => (<div key={ix} className='w-14' />))}
        {path.steps.map((s, ix) => (
          <InputStep key={s.binarySource.id} step={s} />
        ))}
      </div>
      <div className='flex items-center'>
        <div className='pr-2 text-xs'>{path.score.toFixed(2)}</div>
        <svg width={60} height={16}>
          <rect fill={interpolateViridis(path.score)} x={0} y={0} height={16} width={path.score * 60} />
        </svg>
      </div>
    </div>
  )
}
function Input ({ bin, className }) {
  return (
    <div className={className}>
      <div className='flex flex-col'>
        {bin.in_paths.slice(0, 2).map((p, ix) => (
          <InputPath key={p.id} path={p} className={classNames(ix > 0 ? 'border-t border-slate-500' : '')} />
        ))}
      </div>
    </div>
  )
}
function Output ({ bin }) {
  return (<div className='text-sm'>{bin.out_score.toFixed(2)}</div>)
}
export default function BinariesView ({ className }) {
  const [ref, dms] = useChartDimensions(chartSettings)
  const selectedFirmware = useSelectedFirmware()
  const selectedRun = useSelectedRun()
  const binData = useBinariesView(selectedFirmware, selectedRun, -1)
  const runLogs = useRunLogs(selectedFirmware, selectedRun)
  return (
    <div ref={ref} className={classNames('overflow-y-auto', className)}>
      <div className='flex'>
        <div className='w-80'>Input</div>
        <div className='pl-4 mr-2 w-60'>Binary</div>
        <div>Output</div>
      </div>
      <div className='flex flex-col'>
        {Object.values(binData.binaries).sort((a, b) => b.in_score - a.in_score).map((bin, bix) => (
          <div key={bin.id} className='flex items-start mr-2 border-b'>
            <Input className='w-80' bin={bin} />
            <Binary bin={bin} />
            <Output bin={bin} />
          </div>
        ))}
      </div>
    </div>
  )
}
