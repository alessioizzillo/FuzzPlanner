import Bar from '@/components/Bar'
import { Square } from '@/components/Square'
import useChartDimensions from '@/hooks/useChartDimensions'
import { channelScoreColor, cveScoreColor } from '@/scales'
import classNames from 'classnames'
import { interpolateViridis } from 'd3-scale-chromatic'

function getSettings (colId) {
  if (colId === 'binary') {
    return {
      marginLeft: 10,
      marginTop: 0,
      marginRight: 0,
      marginBottom: 0
    }
  }
  if (['listen', 'border', 'withinRead', 'withinWrite'].indexOf(colId) >= 0) {
    return {
      marginLeft: 30,
      marginTop: 0,
      marginRight: 0,
      marginBottom: 0
    }
  }
  return {
    marginLeft: 0,
    marginTop: 0,
    marginRight: 0,
    marginBottom: 0
  }
}

function Binary ({ cRef, dms, value }) {
  return (
    <div ref={cRef} className='w-40 h-10 overflow-hidden text-sm text-left text-ellipsis whitespace-nowrap' style={{ direction: 'ltr' }}>
      <div>{value.exec.id}</div>
      <div className='ml-2 text-xs text-gray-400 text-ellipsis whitespace-nowrap'>
        {value.symt !== null && `-> ${value.symt.id}`}
        {value.symt === null && value.exec.type === 'binary' && 'bin'}
        {value.symt === null && value.exec.type === 'script' && 'script'}
      </div>
    </div>
  )
}

function Vendor ({ cRef, dms, value }) {
  return (
    <div ref={cRef} className={classNames('flex items-center justify-center w-6 h-6', value > 0 && 'text-slate-900 bg-slate-300')}>
      {value > 0 && <div className='text-sm font-bold text-slate-900 bg-slate-300'>V</div>}
    </div>
  )
}

export default function BinariesTableCell ({ colId, value }) {
  const [ref, dms] = useChartDimensions(getSettings(colId))
  if (colId === 'binary') return <Binary cRef={ref} dms={dms} value={value} />
  if (colId === 'cve') return <Square cRef={ref} dms={dms} value={value} colorScale={cveScoreColor} />
  if (colId === 'cwe') return <Square cRef={ref} dms={dms} value={value} colorScale={cveScoreColor} />
  if (['prop'].indexOf(colId) >= 0) return <Vendor cRef={ref} dms={dms} value={value} />
  if (['listen', 'border', 'withinRead', 'withinWrite'].indexOf(colId) >= 0) return <Bar cRef={ref} dms={dms} value={value} colorScale={channelScoreColor} />
  /*
  return (
    <div ref={ref} className='w-20 h-6'>
      <svg width={dms.width} height={dms.height}>
        <g transform={`translate(${[
          0,
          dms.marginTop
        ].join(',')})`}
        >
          <text x={0} y={dms.boundedHeight / 2} dominantBaseline='central' className='text-sm fill-gray-400'>{value}</text>
        </g>
        <g transform={`translate(${[
          dms.marginLeft,
          dms.marginTop
        ].join(',')})`}
        >
          <rect x={0} y={0} width={value * dms.boundedWidth} height={dms.boundedHeight} fill={interpolateViridis(value)} />
        </g>
      </svg>
    </div>
  )
  */
}
