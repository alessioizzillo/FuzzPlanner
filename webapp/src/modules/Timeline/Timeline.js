import { eventTypes, groupedEventTypes } from '@/constants'
import { useSelectedRunMetadata, useSelectedRunView, useSetSelectedRunView } from '@/hooks/store/selectedRun'
import useChartDimensions from '@/hooks/useChartDimensions'
import { scaleBand, scaleLinear } from 'd3-scale'
import { useCallback, useEffect, useMemo, useRef } from 'react'
import { brushX } from 'd3-brush'
import { select, selectAll } from 'd3-selection'
import { channelListenColor, channelScoreColor, cveScoreColor, discreteIntervals, procSpawnNumColor } from '@/scales'
import { getHighestBaseScore } from '@/cveUtils'

const chartSettings = {
  marginLeft: 70,
  marginTop: 4,
  marginRight: 0,
  marginBottom: 4
}

function closest (ar, el) {
  return ar.reduce(function (prev, curr) {
    return (Math.abs(curr - el) < Math.abs(prev - el) ? curr : prev)
  })
}

function Brush ({ brushRef, dms, timeScale, xScale, timeSpan, updateTimeSpan }) {
  const xTimeScale = useMemo(() => (
    scaleLinear()
      .domain(xScale.range())
      .range(timeScale.domain())
  ), [xScale.range(), timeScale.domain()])
  const draw = useCallback(() => {
    const gen = brushX()
      .extent([[0, 0], [dms.boundedWidth, dms.boundedHeight]])
      .on('end', brushended)
    function brushended (event) {
      const selection = event.selection
      if (!event.sourceEvent || !selection) {
        updateTimeSpan({ min: -1, max: -1 })
        return
      }
      const [x0, x1] = selection.map(d => closest([timeScale.range()[0], ...timeScale.thresholds(), timeScale.range()[1]], xTimeScale(d)))
      updateTimeSpan({ min: x0, max: x1 })
    }
    if (brushRef.current) {
      selectAll(brushRef.current).selectAll('*').remove()
      select(brushRef.current).call(gen)
      if (timeSpan.min >= 0 && timeSpan.max >= 0) select(brushRef.current).call(gen.move, timeSpan.max > timeSpan.min ? [timeSpan.min, timeSpan.max].map(x => xTimeScale.invert(x)) : null)
      else select(brushRef.current).call(gen.move, null)
    }
  }, [timeSpan, brushRef.current])
  useEffect(() => {
    draw()
  }, [brushRef.current])
  return null
}

function setStroke ({ binariesBinsById, currentBinary, selectedBinary, b, e }) {
  if (selectedBinary !== null) {
    const sel = binariesBinsById[selectedBinary.id].bins[b.id].types[e.id].length > 0
    if (sel) return '#FFF'
    else return ''
  } else if (currentBinary !== null) {
    const cur = binariesBinsById[currentBinary.id].bins[b.id].types[e.id].length > 0
    if (cur) return '#FFF'
    else return ''
  }
  /*
  const cur = currentBinary !== null && binariesBinsById[currentBinary.id].bins[b.id].types[e.id].length > 0
  const sel = selectedBinary !== null && binariesBinsById[selectedBinary.id].bins[b.id].types[e.id].length > 0
  if (cur && !sel) return '' // '#C8A2C8'
  if (!cur && sel) return '#000' // '#86EFAB'
  if (cur && sel) return '#000' // '#FFDB58'
  return ''
  */
}

function setFill (bin, grType) {
  if (['within', 'border'].indexOf(grType) >= 0) {
    const v = Math.max(...bin.types[grType].map(d => d.chann.score))
    return channelScoreColor(v)
  } else if (grType === 'listen') {
    const v = Math.max(...bin.types[grType].map(d => d.chann.score))
    return channelListenColor(v)
  } else if (['init-fork', 'spawn'].indexOf(grType) >= 0) {
    const v = Math.max(...bin.types[grType].map(d => getHighestBaseScore(d.child.exec.cves)))
    return cveScoreColor(v)
  }
}

function setHeight (bin, grType, vMax) {
  const v = bin.types[grType].length
  if (v === 0) return 0
  return discreteIntervals(v / vMax)
}

export default function Timeline ({ className, currentBinary, selectedBinary }) {
  const [ref, dms] = useChartDimensions(chartSettings)
  const brushRef = useRef()
  const { bins, binsMax, binsMaxScore, timeScale } = useSelectedRunMetadata()
  const runView = useSelectedRunView()
  const runMetadata = useSelectedRunMetadata()
  const setRunView = useSetSelectedRunView()
  const updateTimeSpan = useCallback((timeSpan) => {
    setRunView({ timeSpan })
  }, [])
  const xScale = useMemo(() => (
    scaleBand()
      .domain(bins.map(b => b.id))
      .range([0, dms.boundedWidth])
      .paddingInner(0.15)
  ), [bins, dms.width])
  const yScale = useMemo(() => (
    scaleBand()
      .domain(groupedEventTypes.map(t => t.id))
      .range([0, dms.boundedHeight])
      .paddingInner(0.15)
  ), [bins, dms.height])
  return (
    <div ref={ref} className={className}>
      <svg width={dms.width} height={dms.height}>
        <g transform={`translate(${[
          0,
          dms.marginTop
        ].join(',')})`}
        >
          {groupedEventTypes.map(e => (
            <text key={e.id} x={0} y={yScale(e.id) + yScale.bandwidth() / 2} dominantBaseline='middle' className='fill-slate-300'>{e.label}</text>
          ))}
        </g>
        <g transform={`translate(${[
          dms.marginLeft,
          dms.marginTop
        ].join(',')})`}
        >
          {groupedEventTypes.slice(0, -1).map(e => (
            <line
              key={e.id}
              x1={0}
              x2={dms.boundedWidth}
              y1={yScale(e.id) + yScale.bandwidth()}
              y2={yScale(e.id) + yScale.bandwidth()}
              className='stroke-gray-600'
            />
          ))}
          {bins.map(b => (groupedEventTypes.map(e => {
            return (
              <rect
                key={`${b}-${e.id}`}
                x={xScale(b.id)}
                y={yScale(e.id) + (1 - setHeight(b, e.id, binsMax.types[e.id])) * yScale.bandwidth()}
                width={xScale.bandwidth()}
                height={yScale.bandwidth() * setHeight(b, e.id, binsMax.types[e.id])}
                fill={setFill(b, e.id)}
                fillOpacity={b.types[e.id].length > 0 ? 1 : 0.1}
                stroke={setStroke({ binariesBinsById: runMetadata.binariesBinsById, selectedBinary, currentBinary, e, b })}
                strokeWidth={2}
              />
            )
          })))}

        </g>
        <g
          id='timeline-brush'
          ref={brushRef}
          transform={`translate(${[
          dms.marginLeft,
          dms.marginTop
        ].join(',')})`}
        />
        <Brush brushRef={brushRef} dms={dms} timeScale={timeScale} xScale={xScale} timeSpan={runView.timeSpan} updateTimeSpan={updateTimeSpan} />
      </svg>
    </div>
  )
}
