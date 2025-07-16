import { dataChannelKinds, getDataChannelKind, dataChannelKindsById } from '@/constants'

import { useGetExecutableFiles, useGetProcesses, useGetDataChannels, useGetInteractions } from '@/hooks/queries'
import { useGraphLayout } from '@/hooks/layouts'
import { useMemo } from 'react'
import { makeId } from '@/utils'

export function useRunData (brandId, fwId, runId) {
  const getExecutableFiles = useGetExecutableFiles(brandId, fwId, runId)
  const getProcesses = useGetProcesses(brandId, fwId, runId)
  const getDataChannels = useGetDataChannels(brandId, fwId, runId)
  const getInteractions = useGetInteractions(brandId, fwId, runId)
  const data = useMemo(() => {
    const data = {
      id: makeId(16),
      executableFiles: [],
      executableFilesById: {},
      processes: [],
      processesById: {},
      dataChannels: [],
      dataChannelsById: {},
      interactions: [],
      interactionsById: {}
    }
    if (!getExecutableFiles.isSuccess || !getProcesses.isSuccess || !getDataChannels.isSuccess || !getInteractions.isSuccess) {
      return data
    }
    getExecutableFiles.data.forEach(e => {
      data.executableFilesById[e.id] = {
        ...e
      }
      data.executableFiles.push(e.id)
    })
    getProcesses.data.forEach(p => {
      data.processesById[p.id] = {
        ...p
      }
      data.processes.push(p.id)
    })
    getDataChannels.data.forEach(d => {
      data.dataChannelsById[d.id] = {
        ...d
      }
      data.dataChannels.push(d.id)
    })
    getInteractions.data.forEach(i => {
      data.interactionsById[i.id] = {
        ...i
      }
      data.interactions.push(i.id)
    })
    console.log('runData', data)
    return data
  }, [runId, !getExecutableFiles.isSuccess || !getProcesses.isSuccess || !getDataChannels.isSuccess || !getInteractions.isSuccess])
  return data
}

export function useRunLogs (brandId, fwId, runId) {
  const runData = useRunData(brandId, fwId, runId)
  const runLogs = useMemo(() => {
    const logs = []
    // Processes
    runData.processes.forEach(procId => {
      const proc = runData.processesById[procId]
      const exec = runData.executableFilesById[proc.executable]
      const log = {
        time: proc.start_time
      }
      const parent = runData.processesById[proc.parent]
      if (parent) {
        const parentExec = runData.executableFilesById[parent.executable]
        if (parent.id === proc.id) {
          log.type = 'fork'
        } else {
          log.type = 'spawn'
          log.parent = {
            proc: parent,
            exec: parentExec,
            symt: parentExec.type === 'symlink' ? runData.executableFilesById[parentExec.symlink_target] : null
          }
        }
      } else {
        log.type = 'init'
      }
      log.child = {
        proc,
        exec,
        symt: exec.type === 'symlink' ? runData.executableFilesById[exec.symlink_target] : null
      }
      logs.push(log)
    })
    // Interactions
    runData.interactions.forEach(intId => {
      const inter = runData.interactionsById[intId]
      const chann = runData.dataChannelsById[inter.channel]
      if (checkInteractionValidity(runData, inter, chann)) {
        const log = {
          time: Math.min(...inter.sources.map(s => s.time), ...inter.sinks.map(s => s.time))
        }
        if (inter.sources.length > 0) {
          log.type = 'internal'
          log.sources = inter.sources.filter((value, index, self) =>
            index === self.findIndex((t) => (
              t.pid === value.pid
            ))
          ).map(s => {
            const proc = runData.processesById[s.pid]
            const exec = runData.executableFilesById[proc.executable]
            return {
              proc,
              exec,
              symt: exec.type === 'symlink' ? runData.executableFilesById[exec.symlink_target] : null
            }
          })
        } else {
          log.type = 'border'
        }
        log.sinks = inter.sinks.filter((value, index, self) =>
          index === self.findIndex((t) => (
            t.pid === value.pid
          ))
        ).map(s => {
          const proc = runData.processesById[s.pid]
          const exec = runData.executableFilesById[proc.executable]
          return {
            proc,
            exec,
            symt: exec.type === 'symlink' ? runData.executableFilesById[exec.symlink_target] : null
          }
        })
        log.chann = chann
        logs.push(log)
      }
    })
    // Listens
    runData.dataChannels.forEach(chaId => {
      const chann = runData.dataChannelsById[chaId]
      chann.listening_pids.forEach(lsn => {
        const proc = runData.processesById[lsn.pid]
        const exec = runData.executableFilesById[proc.executable]
        const log = {
          time: lsn.time,
          type: 'listen',
          chann,
          listener: {
            proc,
            exec,
            symt: exec.type === 'symlink' ? runData.executableFilesById[exec.symlink_target] : null
          }
        }
        logs.push(log)
      })
    })
    console.log('runLogs', logs.sort((a, b) => a.time - b.time))
    console.log('listen', logs.filter(l => l.type === 'listen'))
    console.log('spawn', logs.filter(l => l.type === 'spawn'))
    console.log('init', logs.filter(l => l.type === 'init'))
    console.log('fork', logs.filter(l => l.type === 'fork'))
    console.log('border', logs.filter(l => l.type === 'border'))
    console.log('internal', logs.filter(l => l.type === 'internal'))
    return logs
  }, [runData.id])
  return runLogs
}

export function checkInteractionValidity (runData, interaction, dataChannel, log = { errors: [] }) {
  let val = true
  if (!dataChannel.used && interaction.sources.length > 0) {
    log.errors.push(`Error ${interaction.id}: sources and not used`)
    val = false
  }
  if (interaction.sources.length === 0 && interaction.sinks.length === 0) {
    log.errors.push(`Error ${interaction.id}: empty interaction`)
    val = false
  }
  interaction.sources.forEach(source => {
    if (!runData.processesById[source.pid]) {
      log.errors.push(`Error ${interaction.id}: invalid source process ${source.pid}`)
      val = false
    } else if (!runData.processesById[source.pid].executable) {
      log.errors.push(`Error ${interaction.id}: invalid source executable for process ${source.pid}`)
      val = false
    }
    interaction.sinks.forEach(sink => {
      const sourcePr = runData.processesById[source.pid]
      const sourceEx = runData.executableFilesById[sourcePr.executable]
      const sinkPr = runData.processesById[sink.pid]
      const sinkEx = runData.executableFilesById[sinkPr.executable]
      if (source.pid === sink.pid || sourceEx.id === sinkEx.id) {
        log.errors.push(`Error ${interaction.id}: source == sink`)
        val = false
      }
    })
  })
  interaction.sinks.forEach(sink => {
    if (!runData.processesById[sink.pid]) {
      log.errors.push(`Error ${interaction.id}: invalid sink process ${sink.pid}`)
      val = false
    } else if (!runData.processesById[sink.pid].executable) {
      log.errors.push(`Error ${interaction.id}: invalid sink executable for process ${sink.pid}`)
      val = false
    }
  })
  return val
}

export function useValidInteractions (fwId, runId, ix = -1) {
  const runData = useRunData(fwId, runId)
  const validInteractions = []
  runData.interactions.forEach(intId => {
    const interaction = runData.interactionsById[intId]
    const dataChannel = runData.dataChannelsById[interaction.channel]
    const val = checkInteractionValidity(runData, interaction, dataChannel)
    if (val) validInteractions.push(intId)
  })
  if (ix >= 0) return validInteractions.slice(0, ix)
  return validInteractions
}

export function useBorderBinaries (fwId, runId) {
  const runData = useRunData(fwId, runId)
  const validInteractions = useValidInteractions(fwId, runId)
  const binariesById = {}
  validInteractions.forEach(intId => {
    const interaction = runData.interactionsById[intId]
    const dataChannel = runData.dataChannelsById[interaction.channel]
    if (interaction.sources.length === 0) {
      interaction.sinks.forEach(sink => {
        const sinkPr = runData.processesById[sink.pid]
        const sinkEx = runData.executableFilesById[sinkPr.executable]
        if (!binariesById[sinkEx.id]) {
          binariesById[sinkEx.id] = {
            id: sinkEx.id,
            executableFile: sinkEx,
            inputChannelsKinds: dataChannelKinds.map(c => ({ id: c, count: 0 })),
            inputChannels: [],
            max: 0,
            score: 0
          }
        }
        let ix = binariesById[sinkEx.id].inputChannels.map(c => c.id).indexOf(dataChannel.id)
        if (ix < 0) {
          binariesById[sinkEx.id].inputChannels.push({
            ...dataChannel,
            count: 0
          })
          ix = binariesById[sinkEx.id].inputChannels.length - 1
        }
        binariesById[sinkEx.id].inputChannels[ix].count += 1
        binariesById[sinkEx.id].inputChannelsKinds[dataChannelKinds.indexOf(getDataChannelKind(dataChannel.kind))].count += 1
        binariesById[sinkEx.id].score += dataChannel.score
        binariesById[sinkEx.id].max = Math.max(dataChannel.score, binariesById[sinkEx.id].max)
      })
    }
  })
  return Object.values(binariesById).sort((a, b) => b.max - a.max)
}

export function useRunExecutableFilesInteractionsGraph (fwId, runId) {
  const runData = useRunData(fwId, runId)
  const nodesById = {}
  const edgesById = {}
  const log = {
    errors: []
  }
  function createNode (id, data) {
    if (!nodesById[id]) {
      nodesById[id] = {
        id,
        data: {
          ...data,
          label: id
        }
      }
    }
  }
  function getEdgeId (idSrc, idTrg) {
    return `${idSrc}---${idTrg}`
  }
  function createEdge (idSrc, idTrg, data) {
    const id = getEdgeId(idSrc, idTrg)
    if (!edgesById[id]) {
      edgesById[id] = {
        id,
        source: idSrc,
        target: idTrg,
        data: {
          ...data
        }
      }
    }
  }
  runData.interactions.forEach(intId => {
    const interaction = runData.interactionsById[intId]
    const dataChannel = runData.dataChannelsById[interaction.channel]
    const val = checkInteractionValidity(runData, interaction, dataChannel, log)
    if (val) {
      if (!dataChannel.used) {
        if (interaction.sources.length > 0) log.errors.push(`Error ${intId}: sources and not used`)
        else if (interaction.sinks.length === 0) log.errors.push(`Error ${intId}: empty interaction`)
        else { // LISTEN - distinguere canali raggiungibili dall'esterno e non raggiungibili
          /*
          interaction.sinks.forEach(sink => {
            const sinkPr = runData.processesById[sink.pid]
            const sinkEx = runData.executableFilesById[sinkPr.executable]
            createNode(dataChannel.id, { ...dataChannel, nodeType: 'dataChannel' })
            createNode(sinkEx.id, { ...sinkEx, nodeType: 'executableFile' })
            createEdge(dataChannel.id, sinkEx.id, { processes: [] })
            const edgeId = getEdgeId(dataChannel.id, sinkEx.id)
            edgesById[edgeId].data.processes.push(sinkPr)
          })
          */
        }
      } else {
        if (interaction.sources.length === 0) { // READ-ONLY - non possibile se kind of ['unix_socket', 'pipe']
          interaction.sinks.forEach(sink => {
            const sinkPr = runData.processesById[sink.pid]
            const sinkEx = runData.executableFilesById[sinkPr.executable]
            // createNode(dataChannel.id, { ...dataChannel, nodeType: 'dataChannel' })
            createNode(sinkEx.id, { ...sinkEx, nodeType: 'executableFile' })
            // createEdge(dataChannel.id, sinkEx.id, { processes: [] })
            // const edgeId = getEdgeId(dataChannel.id, sinkEx.id)
            // edgesById[edgeId].data.processes.push(sinkPr)
          })
        } else if (interaction.sinks.length === 0) { // WRITE-ONLY
          /*
          interaction.sources.forEach(source => {
            const sourcePr = runData.processesById[source.pid]
            const sourceEx = runData.executableFilesById[sourcePr.executable]
            createNode(dataChannel.id, { ...dataChannel, nodeType: 'dataChannel' })
            createNode(sourceEx.id, { ...sourceEx, nodeType: 'executableFile' })
            createEdge(sourceEx.id, dataChannel.id, { processes: [] })
            const edgeId = getEdgeId(sourceEx.id, dataChannel.id)
            edgesById[edgeId].data.processes.push(sourcePr)
          })
          */
        } else { // WRITE-READ
          /*
          interaction.sources.forEach(source => {
            interaction.sinks.forEach(sink => {
              const sourcePr = runData.processesById[source.pid]
              const sourceEx = runData.executableFilesById[sourcePr.executable]
              const sinkPr = runData.processesById[sink.pid]
              const sinkEx = runData.executableFilesById[sinkPr.executable]
              createNode(dataChannel.id, { ...dataChannel, nodeType: 'dataChannel' })
              createNode(sourceEx.id, { ...sourceEx, nodeType: 'executableFile' })
              createNode(sinkEx.id, { ...sinkEx, nodeType: 'executableFile' })
              createEdge(sourceEx.id, dataChannel.id, { processes: [] })
              createEdge(dataChannel.id, sinkEx.id, { processes: [] })
              let edgeId = getEdgeId(sourceEx.id, dataChannel.id)
              edgesById[edgeId].data.processes.push(sourcePr)
              edgeId = getEdgeId(dataChannel.id, sinkEx.id)
              edgesById[edgeId].data.processes.push(sinkPr)
            })
          })
          */
        }
      }
    }
  })
  const data = {
    nodes: Object.values(nodesById),
    edges: Object.values(edgesById)
  }
  console.log(log)
  console.log('Executable', data.nodes.filter(n => n.data.nodeType === 'executableFile' && n.data.symlink_target === null).length)
  console.log('Symlinks', data.nodes.filter(n => n.data.nodeType === 'executableFile' && n.data.symlink_target !== null).length)
  console.log('Channels', data.nodes.filter(n => n.data.nodeType === 'dataChannel').length)
  if (data.nodes.length > 0) return useGraphLayout(data.nodes, data.edges)
  return data
}

export function useRunGroupedInteractionsGraph (fwId, runId) {
  const runData = useRunData(fwId, runId)
  const nodesById = {}
  const edgesById = {}
  const log = {
    errors: []
  }
  function createNode (id, data) {
    if (!nodesById[id]) {
      nodesById[id] = {
        id,
        data: {
          ...data,
          label: id
        }
      }
    }
  }
  function getEdgeId (idSrc, idTrg) {
    return `${idSrc}---${idTrg}`
  }
  function createEdge (idSrc, idTrg, data) {
    const id = getEdgeId(idSrc, idTrg)
    if (!edgesById[id]) {
      edgesById[id] = {
        id,
        source: idSrc,
        target: idTrg,
        data: {
          ...data
        }
      }
    }
  }
  runData.interactions.forEach(intId => {
    const interaction = runData.interactionsById[intId]
    const dataChannel = runData.dataChannelsById[interaction.channel]
    const val = checkInteractionValidity(runData, interaction, log)
    if (val && dataChannel.used) { // val && dataChannel.used && interaction.sources.length === 0
      interaction.sinks.forEach(sink => {
        const sinkPr = runData.processesById[sink.pid]
        const sinkEx = runData.executableFilesById[sinkPr.executable]
        createNode(dataChannel.kind, { nodeType: 'dataChannel' })
        if (sinkEx.symlink_target === null) {
          createNode(sinkEx.id, { ...sinkEx, nodeType: 'executableFile' })
          createEdge(dataChannel.kind, sinkEx.id, { processes: [] })
          edgesById[getEdgeId(dataChannel.kind, sinkEx.id)].data.processes.push(sinkPr)
        } else {
          const sinkTargetEx = runData.executableFilesById[sinkEx.symlink_target]
          createNode(sinkTargetEx.id, { ...sinkTargetEx, nodeType: 'executableFile' })
          createEdge(dataChannel.kind, sinkTargetEx.id, { processes: [] })
          createNode(sinkEx.id, { ...sinkEx, nodeType: 'executableFile' })
          createEdge(sinkTargetEx.id, sinkEx.id, { processes: [] })
          edgesById[getEdgeId(dataChannel.kind, sinkTargetEx.id)].data.processes.push(sinkPr)
          edgesById[getEdgeId(sinkTargetEx.id, sinkEx.id)].data.processes.push(sinkPr)
        }
        interaction.sources.forEach(src => {
          const srcPr = runData.processesById[src.pid]
          const srcEx = runData.executableFilesById[srcPr.executable]
          if (srcEx.symlink_target === null) {
            createNode(srcEx.id, { ...srcEx, nodeType: 'executableFile' })
            createEdge(srcEx.id, dataChannel.kind, { processes: [] })
            edgesById[getEdgeId(srcEx.id, dataChannel.kind)].data.processes.push(srcPr)
          } else {
            const srcTargetEx = runData.executableFilesById[srcEx.symlink_target]
            createNode(srcTargetEx.id, { ...srcTargetEx, nodeType: 'executableFile' })
            createEdge(srcEx.id, srcTargetEx.id, { processes: [] })
            createNode(srcEx.id, { ...srcEx, nodeType: 'executableFile' })
            createEdge(srcTargetEx.id, dataChannel.kind, { processes: [] })
            edgesById[getEdgeId(srcEx.id, srcTargetEx.id)].data.processes.push(sinkPr)
            edgesById[getEdgeId(srcTargetEx.id, dataChannel.kind)].data.processes.push(sinkPr)
          }
        })
      })
    }
  })
  const data = {
    nodes: Object.values(nodesById),
    edges: Object.values(edgesById)
  }
  console.log(log)
  console.log('Executable', data.nodes.filter(n => n.data.nodeType === 'executableFile' && n.data.symlink_target === null).length)
  console.log('Symlinks', data.nodes.filter(n => n.data.nodeType === 'executableFile' && n.data.symlink_target !== null).length)
  console.log('Channels', data.nodes.filter(n => n.data.nodeType === 'dataChannel').length)
  if (data.nodes.length > 0) return useGraphLayout(data.nodes, data.edges, 'LR')
  return data
}

export function useRunBinariesInteractionsGraph2 (fwId, runId) {
  const runData = useRunData(fwId, runId)
  const nodesById = {}
  const edgesById = {}
  const log = {
    errors: []
  }
  function createNode (id, data) {
    if (!nodesById[id]) {
      nodesById[id] = {
        id,
        data: {
          ...data,
          label: id
        }
      }
    }
  }
  function getEdgeId (idSrc, idTrg) {
    return `${idSrc}---${idTrg}`
  }
  function createEdge (idSrc, idTrg, data) {
    const id = getEdgeId(idSrc, idTrg)
    if (!edgesById[id]) {
      edgesById[id] = {
        id,
        source: idSrc,
        target: idTrg,
        data: {
          ...data
        }
      }
    }
  }
  runData.interactions.forEach(intId => {
    const interaction = runData.interactionsById[intId]
    const dataChannel = runData.dataChannelsById[interaction.channel]
    const val = checkInteractionValidity(runData, interaction, log)
    if (val && dataChannel.used) { // val && dataChannel.used && interaction.sources.length === 0
      interaction.sinks.forEach(sink => {
        const sinkPr = runData.processesById[sink.pid]
        const sinkEx = runData.executableFilesById[sinkPr.executable]
        createNode(sinkEx.id, { ...sinkEx, nodeType: 'executableFile' })
        interaction.sources.forEach(src => {
          const srcPr = runData.processesById[src.pid]
          const srcEx = runData.executableFilesById[srcPr.executable]
          createNode(srcEx.id, { ...srcEx, nodeType: 'executableFile' })
          createEdge(srcEx.id, sinkEx.id, { processes: [] })
          edgesById[getEdgeId(srcEx.id, sinkEx.id)].data.processes.push({ src: srcPr, snk: sinkPr })
        })
      })
    }
  })
  const data = {
    nodes: Object.values(nodesById),
    edges: Object.values(edgesById)
  }
  console.log(log)
  console.log('Executable', data.nodes.filter(n => n.data.nodeType === 'executableFile' && n.data.symlink_target === null).length)
  console.log('Symlinks', data.nodes.filter(n => n.data.nodeType === 'executableFile' && n.data.symlink_target !== null).length)
  console.log('Channels', data.nodes.filter(n => n.data.nodeType === 'dataChannel').length)
  if (data.nodes.length > 0) return useGraphLayout(data.nodes, data.edges, 'LR')
  return data
}

export function useRunBinariesInteractionsGraph (fwId, runId) {
  const runData = useRunData(fwId, runId)
  const nodesById = {}
  const edgesById = {}
  const log = {
    errors: []
  }
  function createNode (id, data) {
    if (!nodesById[id]) {
      console.log(data)
      nodesById[id] = {
        id,
        data: {
          ...data,
          label: id
        },
        style: { color: data.isProprietary ? 'red' : 'black' }
      }
    }
  }
  function getEdgeId (idSrc, idTrg) {
    return `${idSrc}---${idTrg}`
  }
  function createEdge (idSrc, idTrg, data) {
    const id = getEdgeId(idSrc, idTrg)
    if (!edgesById[id]) {
      edgesById[id] = {
        id,
        source: idSrc,
        target: idTrg,
        data: {
          ...data
        }
      }
    }
  }
  runData.interactions.forEach(intId => {
    const interaction = runData.interactionsById[intId]
    const dataChannel = runData.dataChannelsById[interaction.channel]
    const val = checkInteractionValidity(runData, interaction, log)
    let src
    let snk
    if (val && dataChannel.used) { // val && dataChannel.used && interaction.sources.length === 0
      interaction.sinks.forEach(sink => {
        const sinkPr = runData.processesById[sink.pid]
        const sinkEx = runData.executableFilesById[sinkPr.executable]
        if (sinkEx.symlink_target === null) {
          createNode(sinkEx.id, { ...sinkEx, nodeType: 'executableFile' })
          snk = sinkEx
        } else {
          const sinkTargetEx = runData.executableFilesById[sinkEx.symlink_target]
          createNode(sinkTargetEx.id, { ...sinkTargetEx, nodeType: 'executableFile' })
          // createNode(sinkEx.id, { ...sinkEx, nodeType: 'executableFile' })
          // createEdge(sinkTargetEx.id, sinkEx.id, { processes: [] })
          snk = sinkTargetEx
        }
        interaction.sources.forEach(src => {
          const srcPr = runData.processesById[src.pid]
          const srcEx = runData.executableFilesById[srcPr.executable]
          if (srcEx.symlink_target === null) {
            createNode(srcEx.id, { ...srcEx, nodeType: 'executableFile' })
            src = srcEx
          } else {
            const srcTargetEx = runData.executableFilesById[srcEx.symlink_target]
            createNode(srcTargetEx.id, { ...srcTargetEx, nodeType: 'executableFile' })
            // createNode(srcEx.id, { ...srcEx, nodeType: 'executableFile' })
            // createEdge(srcTargetEx.id, srcEx.id, { processes: [] })
            src = srcTargetEx
          }
          createEdge(src.id, snk.id, { processes: [] })
        })
      })
    }
  })
  const data = {
    nodes: Object.values(nodesById),
    edges: Object.values(edgesById)
  }
  console.log(log)
  console.log('Executable', data.nodes.filter(n => n.data.nodeType === 'executableFile' && n.data.symlink_target === null).length)
  console.log('Symlinks', data.nodes.filter(n => n.data.nodeType === 'executableFile' && n.data.symlink_target !== null).length)
  console.log('Channels', data.nodes.filter(n => n.data.nodeType === 'dataChannel').length)
  if (data.nodes.length > 0) return useGraphLayout(data.nodes, data.edges, 'LR')
  return data
}

export function useRunBorderInteractionsGraph (fwId, runId) {
  const runData = useRunData(fwId, runId)
  const nodesById = {}
  const edgesById = {}
  const log = {
    errors: []
  }
  function createNode (id, data) {
    if (!nodesById[id]) {
      nodesById[id] = {
        id,
        data: {
          ...data,
          label: id
        }
      }
    }
  }
  function getEdgeId (idSrc, idTrg) {
    return `${idSrc}---${idTrg}`
  }
  function createEdge (idSrc, idTrg, data) {
    const id = getEdgeId(idSrc, idTrg)
    if (!edgesById[id]) {
      edgesById[id] = {
        id,
        source: idSrc,
        target: idTrg,
        data: {
          ...data
        }
      }
    }
  }
  runData.interactions.forEach(intId => {
    const interaction = runData.interactionsById[intId]
    const dataChannel = runData.dataChannelsById[interaction.channel]
    const val = checkInteractionValidity(runData, interaction, log)
    if (val && dataChannel.used) { // val && dataChannel.used && interaction.sources.length === 0
      if (interaction.sources.length === 0) {
        interaction.sinks.forEach(sink => {
          const sinkPr = runData.processesById[sink.pid]
          const sinkEx = runData.executableFilesById[sinkPr.executable]
          createNode(dataChannel.kind, { nodeType: 'dataChannel' })
          if (sinkEx.symlink_target === null) {
            createNode(sinkEx.id, { ...sinkEx, nodeType: 'executableFile' })
            createEdge(dataChannel.kind, sinkEx.id, { processes: [] })
            edgesById[getEdgeId(dataChannel.kind, sinkEx.id)].data.processes.push(sinkPr)
          } else {
            const sinkTargetEx = runData.executableFilesById[sinkEx.symlink_target]
            createNode(sinkTargetEx.id, { ...sinkTargetEx, nodeType: 'executableFile' })
            createEdge(dataChannel.kind, sinkTargetEx.id, { processes: [] })
            createNode(sinkEx.id, { ...sinkEx, nodeType: 'executableFile' })
            createEdge(sinkTargetEx.id, sinkEx.id, { processes: [] })
            edgesById[getEdgeId(dataChannel.kind, sinkTargetEx.id)].data.processes.push(sinkPr)
            edgesById[getEdgeId(sinkTargetEx.id, sinkEx.id)].data.processes.push(sinkPr)
          }
        })
      }
    }
  })
  const data = {
    nodes: Object.values(nodesById),
    edges: Object.values(edgesById)
  }
  console.log(log)
  console.log('Executable', data.nodes.filter(n => n.data.nodeType === 'executableFile' && n.data.symlink_target === null).length)
  console.log('Symlinks', data.nodes.filter(n => n.data.nodeType === 'executableFile' && n.data.symlink_target !== null).length)
  console.log('Channels', data.nodes.filter(n => n.data.nodeType === 'dataChannel').length)
  if (data.nodes.length > 0) return useGraphLayout(data.nodes, data.edges, 'LR')
  return data
}
