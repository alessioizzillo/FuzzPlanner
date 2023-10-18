import Slider from '@/components/Slider'
import { dataChannelKindsById } from '@/constants'
import { getBinaryGraph, getRunView } from '@/data'
import { useSelectedEntries } from '@/hooks/store/selectedEntries'
import { useSelectedRunGraph, useSelectedRunView } from '@/hooks/store/selectedRun'
import useChartDimensions from '@/hooks/useChartDimensions'
import { channelScoreColor } from '@/scales'
import { initialState } from '@/store'
import classNames from 'classnames'
import { interpolateViridis } from 'd3-scale-chromatic'
import { useCallback, useMemo, useState } from 'react'
import ReactFlow, { Handle, Position, Background, Controls, MiniMap, NodeToolbar } from 'reactflow'
import { Tooltip } from 'react-tooltip'
import { scaleQuantize } from 'd3-scale'

const TooltipChannel = ({ data }) => {
  const [isVisible, setVisible] = useState(false)
  return (
    <div onMouseEnter={() => setVisible(true)} onMouseLeave={() => setVisible(false)}>
      <NodeToolbar isVisible={isVisible} position={data.toolbarPosition}>
        <div>This is a tooltip</div>
      </NodeToolbar>
      <div style={{ padding: 20 }}>{data.label}</div>
      <Handle type='target' position={Position.Left} />
      <Handle type='source' position={Position.Right} />
    </div>
  )
}

const chartSettings = {
  marginLeft: 0,
  marginTop: 0,
  marginRight: 0,
  marginBottom: 0
}

function BinaryNode ({ selectedBinaryId, data, onClick }) {
  return (
    <>
      <Handle type='target' position={Position.Top} id='spawn-trg' style={{ left: 40 }} />
      <Handle type='target' position={Position.Top} id='read-trg' style={{ left: 'auto', right: 40 }} />
      <Handle type='target' position={Position.Left} id='pc-trg' />
      <Handle type='source' position={Position.Left} id='pc-src' />
      <Handle type='target' position={Position.Right} id='rw-trg' />
      <Handle type='source' position={Position.Right} id='rw-src' />
      <div
        className={classNames('flex items-center justify-center overflow-hidden text-ellipsis', selectedBinaryId === data.id ? 'bg-slate-100 text-slate-900' : 'bg-slate-500')}
        style={{ width: `${data.width}px`, height: `${data.height}px` }}
      >
        {data.label}
      </div>
      <Handle type='source' position={Position.Bottom} id='spawn-src' style={{ left: 40 }} />
      <Handle type='source' position={Position.Bottom} id='write-src' style={{ left: 'auto', right: 40 }} />
    </>
  )
}

function ChannelNode ({ data }) {
  const Ic = useMemo(() => dataChannelKindsById[data.data.type].Icon, [data.id])
  const [isTooltip, setTooltip] = useState(false)
  return (
    <>
      <Handle type='target' position={Position.Top} id='read-src' />
      <div
        onMouseEnter={() => setTooltip(true)} onMouseLeave={() => setTooltip(false)}
        id={`channel-node-${data.id}`}
        className='flex items-center justify-center text-slate-200'
        style={{ background: channelScoreColor(data.data.score), width: `${data.width}px`, height: `${data.height}px` }}
      >
        <Ic className='w-6 h-6' />
      </div>
      <Handle type='source' position={Position.Bottom} id='write-trg' />
      <NodeToolbar isVisible={isTooltip} position={Position.Top}>
        <div className='p-2 text-sm bg-cyan-950'>
          {data.id}
        </div>
      </NodeToolbar>
    </>

  )
}

export default function BinaryGraph ({ className, binary, setSelectedBinary }) {
  const BinNode = (props) => <BinaryNode selectedBinaryId={binary.id} onClick={setSelectedBinary} {...props} />
  const [ref, dms] = useChartDimensions(chartSettings)
  const runGraph = useSelectedRunGraph()
  const selectedRunView = useSelectedRunView()
  const setSelectedEntries = useSelectedEntries()
  const { timeSpan, binariesById, conf } = selectedRunView
  const [entriesThreshold, setEntriesThreshold] = useState(0)
  const [depth, setDepth] = useState({ inProc: 0, inData: 0, outProc: 0, outData: 0 })
  const binaryView = useMemo(() => getRunView({ runGraph, timeSpan, conf: initialState.selectedRunView.conf }), [])
  const allBinariesById = binaryView.binariesById
  const binId = binary.id
  const [graph, setGraph] = useState(getBinaryGraph({ binId, binariesById, depth }))
  const updateDepth = useCallback(({ id, v }) => {
    setDepth({ ...depth, [id]: v })
    setGraph(getBinaryGraph({ binId, binariesById, depth: { ...depth, [id]: v }, entriesThreshold }))
  }, [depth, binId, entriesThreshold])
  const interactionsScale = useMemo(() => (
    scaleQuantize()
      .domain([0, graph.maxEdgesEntries])
      .range([...Array(100)].map((_v, i) => i))), [graph.maxEdgesEntrie])
  const updateEntriesThreshold = useCallback(({ id, v }) => {
    const t = interactionsScale.invertExtent(v)[0]
    setEntriesThreshold(t)
    setGraph(getBinaryGraph({ binId, binariesById, depth, entriesThreshold: t }))
  }, [depth, binId, entriesThreshold])

  // const gr = useMemo(() => getBinaryGraph({ binId, binariesById, depth }), [binId, timeSpan, conf, depth])
  const nodeTypes = useMemo(() => ({ channel: ChannelNode, binary: BinNode }), [binary.id])

  return (
    <div className={classNames('flex flex-col', className)}>
      <div className='flex flex-none pl-2 mx-2'>
        <Slider className='flex-auto pr-2' id='inProc' label='Parents depth' currentValue={depth.inProc} setCurrentValue={updateDepth} max={4} step={1} />
        <Slider className='flex-auto pr-2' id='outProc' label='Children depth' currentValue={depth.outProc} setCurrentValue={updateDepth} max={4} step={1} />
        <Slider className='flex-auto pr-2' id='inData' label='Data reads depth' currentValue={depth.inData} setCurrentValue={updateDepth} max={4} step={1} />
        <Slider className='flex-auto' id='outData' label='Data writes depth' currentValue={depth.outData} setCurrentValue={updateDepth} max={4} step={1} />
      </div>
      <div className='flex-none pl-2 mx-2'>
        <Slider id='interactions' label='Interactions threshold' currentValue={entriesThreshold} setCurrentValue={updateEntriesThreshold} max={interactionsScale(graph.maxEdgesEntries)} step={1} />
      </div>
      <div ref={ref} className='flex-auto'>
        <div style={{ width: dms.width, height: dms.height }}>
          {dms.height > 0 &&
            <ReactFlow
              id={binId}
              nodes={graph.nodes}
              edges={graph.edges}
              nodeTypes={nodeTypes}
              proOptions={{ hideAttribution: true }}
              minZoom={0.05}
              fitView
            >
              <Background />
              <Controls />
              <MiniMap nodeStrokeWidth={3} nodeColor='gray' zoomable pannable />
            </ReactFlow>}
        </div>
      </div>
    </div>
  )
}
