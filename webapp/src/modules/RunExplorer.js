import ReactFlow from 'reactflow'

import { useRunData, useRunExecutableFilesInteractionsGraph, useBorderBinaries } from '@/hooks/data'
import useChartDimensions from '@/hooks/useChartDimensions'

import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { useSelectedRun } from '@/hooks/store/selectedRun'

const chartSettings = {
  marginLeft: 0,
  marginTop: 0,
  marginRight: 0,
  marginBottom: 0
}

export default function RunExplorer ({ className }) {
  const [ref, dms] = useChartDimensions(chartSettings)
  const selectedFirmware = useSelectedFirmware()
  const selectedRun = useSelectedRun()
  const runData = useRunData(selectedFirmware, selectedRun)
  const runExecutableFilesInteractionsGraph = useRunExecutableFilesInteractionsGraph(selectedFirmware, selectedRun)
  const borderBinaries = useBorderBinaries(selectedFirmware, selectedRun)
  console.log(runData)
  console.log('runExecutableFilesInteractionsGraph')
  console.log(runExecutableFilesInteractionsGraph)
  console.log('borderBinaries')
  console.log(borderBinaries)
  return (
    <div ref={ref} className={className}>
      <div style={{ width: dms.width, height: dms.height }}>
        {dms.height > 0 && <ReactFlow nodes={runExecutableFilesInteractionsGraph.nodes} edges={runExecutableFilesInteractionsGraph.edges} fitView />}
      </div>
    </div>
  )
}
