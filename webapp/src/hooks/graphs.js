import Graph from 'graphology'
import { allSimpleEdgePaths } from 'graphology-simple-path'

import { useRunData, useValidInteractions } from '@/hooks/data'
import { inputPathsLength } from '@/constants'
import { useMemo } from 'react'

export function useBinariesView (fwId, runId, ix) {
  const runData = useRunData(fwId, runId)
  const validInteractions = useValidInteractions(fwId, runId, ix)
  const { binaries, graph } = useMemo(() => {
    const binaries = {}
    const graph = new Graph({
      allowSelfLoops: false,
      multi: false,
      type: 'directed'
    })
    graph.mergeNode('border-source', {
      id: 'border-source',
      type: 'aux'
    })
    const data = {
      out: {
        maxOpenScore: 0,
        maxOpenBinariesLenght: 0,
        maxPropScore: 0,
        maxPropBinariesLength: 0,
        maxScore: 0,
        maxBinariesLength: 0
      }
    }
    const internalInteractions = {}
    const outTreeDepth = 4
    function handleBinary (b) {
      if (!binaries[b]) {
        binaries[b.id] = {
          id: b.id,
          data: {
            ...b
          },
          in_paths: [],
          in_score: 0,
          out_tree: {},
          out_score: 0,
          out_prop: {
            propScore: 0,
            openScore: 0,
            propBinaries: [],
            openBinaries: []
          },
          out_levels: Array(outTreeDepth).fill().map(() => ({
            propScore: 0,
            openScore: 0,
            propBinaries: [],
            openBinaries: []
          })),
          processes: {}
        }
      }
      graph.mergeNode(b.id, {
        id: b.id,
        type: 'binary',
        data: {
          ...b
        }
      })
    }
    function handleDataChannel (c) {
      graph.mergeNode(c.id, {
        id: c.id,
        type: 'channel',
        data: {
          ...c
        }
      })
    }
    function handleInternal (dataChannel, sourceEx, sinkEx) {
      if (internalInteractions[`${sinkEx.id}--${dataChannel.id}--${sourceEx.id}`]) return
      if (!graph.hasEdge(sourceEx.id, sinkEx.id)) {
        graph.addEdge(sourceEx.id, sinkEx.id, { channels: {} })
      }
      graph.updateEdgeAttribute(sourceEx.id, sinkEx.id, 'channels', channels => {
        if (!channels[dataChannel.id]) channels[dataChannel.id] = { ...dataChannel, counts: 0 }
        channels[dataChannel.id].counts += 1
        return channels
      })
      internalInteractions[`${sourceEx.id}--${dataChannel.id}--${sinkEx.id}`] = true
    }
    function handleBorder (dataChannel, sinkEx) {
      if (!graph.hasEdge('border-source', sinkEx.id)) {
        graph.addEdge('border-source', sinkEx.id, { channels: {} })
      }
      graph.updateEdgeAttribute('border-source', sinkEx.id, 'channels', channels => {
        if (!channels[dataChannel.id]) channels[dataChannel.id] = { ...dataChannel, counts: 0 }
        channels[dataChannel.id].counts += 1
        return channels
      })
    }
    function subtree (node, attr, depth) {
      const res = {
        ...attr,
        children: []
      }
      if (depth > 0) {
        graph.forEachOutNeighbor(node, (neig, neigAttr) => {
          if (neigAttr.type === 'binary') {
            const chanAttr = graph.getEdgeAttributes(node, neig)
            res.children.push(subtree(neig, { ...neigAttr, channel: chanAttr }, depth - 1))
          }
        })
      }
      return res
    }
    validInteractions.forEach(intId => {
      const interaction = runData.interactionsById[intId]
      const dataChannel = runData.dataChannelsById[interaction.channel]
      if (interaction.sources.length > 0) {
        interaction.sources.forEach(source => {
          const sourcePr = runData.processesById[source.pid]
          const sourceEx = runData.executableFilesById[sourcePr.executable]
          handleBinary(sourceEx)
          interaction.sinks.forEach(sink => {
            const sinkPr = runData.processesById[sink.pid]
            const sinkEx = runData.executableFilesById[sinkPr.executable]
            handleBinary(sinkEx)
            handleInternal(dataChannel, sourceEx, sinkEx)
          })
        })
      } else {
        interaction.sinks.forEach(sink => {
          const sinkPr = runData.processesById[sink.pid]
          const sinkEx = runData.executableFilesById[sinkPr.executable]
          handleBinary(sinkEx)
          handleBorder(dataChannel, sinkEx)
        })
      }
    })
    graph.forEachNode((node, attr) => {
      if (attr.type === 'binary') {
        const edgePaths = allSimpleEdgePaths(graph, 'border-source', node, { maxDepth: inputPathsLength })
        const paths = []
        edgePaths.forEach((p, ix) => {
          const path = {
            id: `${node}-p-${ix}`,
            score: 0,
            steps: []
          }
          for (let i = 0; i < p.length; i++) {
            const edgeAttr = graph.getEdgeAttributes(p[i])
            path.steps.push({
              id: `${node}-p-${ix}-s-${path.steps.length}`,
              ...edgeAttr,
              binarySource: graph.getNodeAttributes(graph.source(p[i])),
              top_channel: Object.values(edgeAttr.channels).reduce((p, c) => (p.score > c.score) ? p : c, 1)
            })
            path.score = Math.max(path.score, path.steps.slice(-1)[0].top_channel.score / (p.length - i))
          }
          paths.push(path)
          binaries[node].in_score = Math.max(binaries[node].in_score, path.score)
        })
        binaries[node].in_paths = paths.sort((p1, p2) => {
          if (p1.score < p2.score) return 1
          else if (p1.score > p2.score) return -1
          else if (p1.steps.length > p2.steps.length) return 1
          else if (p1.steps.length < p2.steps.length) return -1
          return 0
        })
        binaries[node].out_tree = subtree(node, attr, outTreeDepth)
        function handleOutTreeBinary (binary, depth) {
          const propScore = Math.max(...Object.values(binary.channel.channels).map(c => c.score))
          if (binary.data.is_proprietary) {
            binaries[node].out_levels[depth].propBinaries.push(binary)
            binaries[node].out_prop.propBinaries.push(binary)
            binaries[node].out_levels[depth].propScore += propScore
            binaries[node].out_prop.propScore += propScore
          } else {
            binaries[node].out_levels[depth].openBinaries.push(binary)
            binaries[node].out_prop.openBinaries.push(binary)
            binaries[node].out_levels[depth].openScore += propScore
            binaries[node].out_prop.openScore += propScore
          }
          binaries[node].out_score += propScore / (depth + 1)
          binary.children.forEach(bin => { handleOutTreeBinary(bin, depth + 1) })
        }
        binaries[node].out_tree.children.forEach(binary => {
          handleOutTreeBinary(binary, 0)
        })
      }
    })
    console.log('binaries', binaries)
    return { binaries, graph }
  }, [runData.id])
  return {
    binaries,
    graph
  }
}
