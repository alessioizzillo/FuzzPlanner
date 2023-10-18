import { makeId, sanitizeId } from '@/utils'
import { checkInteractionValidity } from './hooks/data'
import Graph from 'graphology'
import { eventTypes, groupedEventTypes, getDataChannelKind, timeBins, groupedEventTypesMapping } from './constants'
import { scaleQuantize } from 'd3-scale'
import dagre from '@dagrejs/dagre'
import { getHighestBaseScore } from './cveUtils'

// RUN DATA
export function getRunData ({ executableFiles, processes, dataChannels, interactions }) {
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
  executableFiles.forEach(e => {
    data.executableFilesById[e.id] = {
      ...e
    }
    data.executableFiles.push(e.id)
  })
  processes.forEach(p => {
    data.processesById[p.id] = {
      ...p
    }
    data.processes.push(p.id)
  })
  dataChannels.forEach(d => {
    console.log(d)
    if (d.id.length > 5 && d.id[d.id.length - 4] >= '0' && d.id[d.id.length - 4] <= '9') {
      data.dataChannelsById[d.id] = {
        ...d,
        score: Math.min(d.score, 0.7)
      }
    } else {
      data.dataChannelsById[d.id] = {
        ...d
      }
    }
    data.dataChannels.push(d.id)
  })
  interactions.forEach(i => {
    data.interactionsById[i.id] = {
      ...i
    }
    data.interactions.push(i.id)
  })
  return data
}

// RUN LOGS
export function getRunLogs ({ runData }) {
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
      if (parentExec.id === exec.id) {
        log.type = 'fork'
      } else {
        log.type = 'spawn'
      }
      log.parent = {
        proc: parent,
        exec: parentExec,
        symt: parentExec.type === 'symlink' ? runData.executableFilesById[parentExec.symlink_target] : null
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
  // Interactions
  runData.interactions.forEach(intId => {
    const inter = runData.interactionsById[intId]
    const chann = runData.dataChannelsById[inter.channel]
    if (checkInteractionValidity(runData, inter, chann)) {
      const log = {
        time: Math.max(...inter.sources.map(s => s.time), ...inter.sinks.map(s => s.time))
      }
      if (inter.sources.length > 0) {
        log.type = 'within'
        log.sources = inter.sources.toReversed().filter((value, index, self) =>
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
      log.sinks = inter.sinks.toReversed().filter((value, index, self) =>
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
  let timeOffset
  logs.sort((a, b) => a.time - b.time).forEach((log, lix) => {
    if (lix === 0) timeOffset = log.time
    log.time -= timeOffset
  })
  // console.log('runLogs', logs.sort((a, b) => a.time - b.time))
  console.log('listen', logs.filter(l => l.type === 'listen'))
  console.log('spawn', logs.filter(l => l.type === 'spawn'))
  console.log('init', logs.filter(l => l.type === 'init'))
  console.log('fork', logs.filter(l => l.type === 'fork'))
  console.log('border', logs.filter(l => l.type === 'border'))
  console.log('within', logs.filter(l => l.type === 'within'))
  return logs
}

// RUN GRAPH
export function getRunGraph ({ runData, runLogs }) {
  const graph = new Graph({
    type: 'directed',
    multi: true,
    allowSelfLoops: false
  })
  //
  function handleExecutableFile (eId) {
    if (graph.hasNode(eId)) { return }
    const exec = runData.executableFilesById[eId]
    if (exec.type === 'binary') {
      graph.addNode(eId, {
        type: 'executable',
        subtype: 'binary',
        data: exec
      })
    } else if (exec.type === 'script') {
      graph.addNode(eId, {
        type: 'executable',
        subtype: 'script',
        data: exec
      })
    } else if (exec.type === 'symlink') {
      graph.addNode(eId, {
        type: 'executable',
        subtype: 'symlink',
        data: exec
      })
      handleExecutableFile(exec.symlink_target)
      graph.addDirectedEdgeWithKey(
        `symbolink-${eId}-${exec.symlink_target}`,
        eId,
        exec.symlink_target,
        {
          type: 'symbolink',
          subtype: null,
          data: {}
        }
      )
    }
  }
  //
  function handleDataChannel (cId) {
    if (graph.hasNode(cId)) { return }
    const chann = runData.dataChannelsById[cId]
    graph.addNode(cId, {
      type: 'channel',
      subtype: getDataChannelKind(cId),
      data: chann
    })
  }
  //
  function handleProcess (pId) {
    if (graph.hasNode(pId)) { return }
    const proc = runData.processesById[pId]
    graph.addNode(pId, {
      type: 'process',
      subtype: null,
      data: proc
    })
    handleExecutableFile(proc.executable)
    graph.addDirectedEdgeWithKey(
      `execute-${pId}-${proc.executable}`,
      pId,
      proc.executable,
      {
        type: 'execute',
        subtype: null,
        data: {}
      }
    )
  }
  // Static graph
  for (const eId of runData.executableFiles) {
    handleExecutableFile(eId)
  }
  for (const cId of runData.dataChannels) {
    handleDataChannel(cId)
  }
  //
  graph.addNode('ext', {
    type: 'aux',
    subtype: null,
    data: {}
  })
  graph.addNode('root', {
    type: 'aux',
    subtype: null,
    data: {}
  })
  //
  function getEventEdgeArray (logix, log, src, trg, data) {
    const { time, type } = log
    const edgeId = `${logix}-${type}-${src}-${trg}`
    return [
      edgeId,
      src,
      trg,
      {
        type: 'event',
        subtype: type,
        logix,
        time,
        data: { ...data }
      }]
  }
  // Logs graph
  for (const [logix, log] of runLogs.entries()) {
    if (log.type === 'init') {
      // INIT
      const { child } = log
      const pId = child.proc.id
      if (graph.hasNode(pId)) {
        console.log(`Process '${pId}' already exists`, log)
        continue
      }
      handleProcess(pId)
      graph.addDirectedEdgeWithKey(...getEventEdgeArray(logix, log, 'root', pId, { child }))
    } else if (log.type === 'spawn' || log.type === 'fork') {
      // SPAWN || FORK
      const { child, parent } = log
      const chPid = child.proc.id
      const paPid = parent.proc.id
      if (graph.hasNode(chPid)) {
        console.log(`Process '${chPid}' already exists`, log)
        continue
      }
      if (!graph.hasNode(paPid)) {
        console.log(`Parent process '${paPid}' doesn't yet exists`, log)
        continue
        // handleProcess(paPid)
      }
      handleProcess(chPid)
      graph.addDirectedEdgeWithKey(...getEventEdgeArray(logix, log, chPid, paPid, { child, parent }))
    } else if (log.type === 'fork') {
      // FORK
    } else if (log.type === 'listen') {
      // LISTEN
      const { chann, listener } = log
      if (!graph.hasNode(listener.proc.id)) {
        console.log(`Process '${listener.proc.id}' doesn't yet exists`, log)
        continue
      }
      graph.addDirectedEdgeWithKey(...getEventEdgeArray(logix, log, chann.id, listener.proc.id, { channel: chann, listener }))
    } else if (log.type === 'border') {
      // BORDER
      const { chann, sinks } = log
      const sink = sinks[0]
      if (!graph.hasNode(sink.proc.id)) {
        console.log(`Process '${sink.proc.id}' doesn't yet exists`, log)
        handleProcess(sink.proc.id)
        // continue
      }
      graph.addDirectedEdgeWithKey(...getEventEdgeArray(logix, { ...log, type: 'border_write' }, 'ext', chann.id, { channel: chann, sink }))
      graph.addDirectedEdgeWithKey(...getEventEdgeArray(logix, { ...log, type: 'border_read' }, chann.id, sink.proc.id, { channel: chann, sink }))
    } else if (log.type === 'within') {
      // WITHIN
      const { chann, sinks, sources } = log
      const sink = sinks[0]
      const source = sources[0]
      if (!graph.hasNode(sink.proc.id)) {
        console.log(`Process '${sink.proc.id}' doesn't yet exists`, log)
        continue
      }
      if (!graph.hasNode(source.proc.id)) {
        console.log(`Process '${source.proc.id}' doesn't yet exists`, log)
        continue
      }
      graph.addDirectedEdgeWithKey(...getEventEdgeArray(logix, { ...log, type: 'within_write' }, source.proc.id, chann.id, { channel: chann, source, sink }))
      graph.addDirectedEdgeWithKey(...getEventEdgeArray(logix, { ...log, type: 'within_read' }, chann.id, sink.proc.id, { channel: chann, source, sink }))
    }
  }
  //
  // getBorderBinaries({ runData, runGraph: graph })
  return graph
}

// RUN METADATA
export function getRunMetadata ({ runLogs }) {
  const minTime = runLogs[0].time || 0
  const maxTime = runLogs.slice(-1)[0].time || 0
  const metadata = {
    timeScale: scaleQuantize()
      .domain([minTime, maxTime])
      .range([...Array(timeBins)].map((_e, ix) => ix)),
    bins: [...Array(timeBins)].map((_e, ix) => ({
      id: ix,
      types: groupedEventTypes.reduce((a, v) => ({ ...a, [v.id]: [] }), {})
    })),
    binsMax: {
      types: groupedEventTypes.reduce((a, v) => ({ ...a, [v.id]: 0 }), {})
    },
    binsMaxScore: {
      types: groupedEventTypes.reduce((a, v) => ({ ...a, [v.id]: 0 }), {})
    },
    binariesBinsById: {}
  }
  function updateBinsMax (ev, bin) {
    const m = bin.types[ev.id].length
    if (m > metadata.binsMax.types[ev.id]) {
      metadata.binsMax.types[ev.id] = m
    }
  }
  function updateBinsMaxScore (ev, bin) {
    console.log(ev.id, bin.types[ev.id])
    let m
    if (['listen', 'within', 'border'].indexOf(ev.id) >= 0) {
      m = Math.max(...bin.types[ev.id].map(d => d.chann.score))
    } else if (['init-fork', 'spawn'].indexOf(ev.id) >= 0) {
      m = Math.max(...bin.types[ev.id].map(d => getHighestBaseScore(d.child.exec.cves)))
    }
    if (m > metadata.binsMax.types[ev.id]) {
      metadata.binsMax.types[ev.id] = m
    }
  }
  function updateBinariesBins (log) {
    function updateBinary (bin, log) {
      if (!metadata.binariesBinsById[bin.exec.id]) {
        metadata.binariesBinsById[bin.exec.id] = {
          bins: [...Array(timeBins)].map((_e, ix) => ({
            id: ix,
            types: groupedEventTypes.reduce((a, v) => ({ ...a, [v.id]: [] }), {})
          }))
        }
      }
      metadata.binariesBinsById[bin.exec.id].bins[metadata.timeScale(log.time)].types[groupedEventTypesMapping[log.type]].push(log)
    }
    if (log.type === 'init') {
      updateBinary(log.child, log)
    } else if (log.type === 'fork') {
      updateBinary(log.child, log)
    } else if (log.type === 'spawn') {
      updateBinary(log.parent, log)
      updateBinary(log.child, log)
    } else if (log.type === 'listen') {
      updateBinary(log.listener, log)
    } else if (log.type === 'border') {
      updateBinary(log.sinks[0], log)
    } else if (log.type === 'within') {
      updateBinary(log.sources[0], log)
      updateBinary(log.sinks[0], log)
    }
  }
  for (const log of runLogs.values()) {
    metadata.bins[metadata.timeScale(log.time)].types[groupedEventTypesMapping[log.type]].push(log)
    updateBinariesBins(log)
  }
  for (const bin of metadata.bins) {
    for (const ev of groupedEventTypes) {
      updateBinsMax(ev, bin)
      updateBinsMaxScore(ev, bin)
    }
  }
  console.log(metadata)
  return metadata
}

// RUN VIEW
function getEdges (runGraph, timeSpan, conf) {
  const { min, max } = timeSpan
  const { borderThreshold, listenThreshold, withinThreshold } = conf
  return runGraph.filterEdges((_id, attr) => (
    attr.type === 'event' &&
    (min >= 0 ? attr.time >= min : true) &&
    (max >= 0 ? attr.time <= max : true) &&
    (((attr.subtype === 'border_read' || attr.subtype === 'border_write') ? attr.data.channel.score >= borderThreshold : true)) &&
    ((attr.subtype === 'listen' ? attr.data.channel.score >= listenThreshold : true)) &&
    (((attr.subtype === 'within_read' || attr.subtype === 'within_write') ? attr.data.channel.score >= withinThreshold : true))
  )).sort((a, b) => a.logix - b.logix)
}

export function getRunView ({ runGraph, timeSpan, conf }) {
  const data = {
    binariesById: {},
    metadata: {
      maxProcessLogs: 0
    },
    timeSpan,
    conf
  }
  if (Object.keys(runGraph).length === 0) return data
  const edges = getEdges(runGraph, timeSpan, conf)
  function handleExecutable (ex) {
    const id = ex.exec.id
    if (!data.binariesById[id]) {
      data.binariesById[id] = {
        id,
        data: ex,
        listenChannelsById: {},
        borderChannelsById: {},
        withinReadChannelsById: {},
        spawnParentExecsById: {},
        withinWriteChannelsById: {},
        spawnChildExecsById: {},
        processesById: {}
      }
    }
  }
  function handleProcess (ex, edge) {
    const binId = ex.exec.id
    const procId = ex.proc.id
    if (!data.binariesById[binId].processesById[procId]) {
      data.binariesById[binId].processesById[procId] = {
        id: procId,
        data: ex,
        logs: []
      }
    }
    data.binariesById[binId].processesById[procId].logs.push(edge)
    if (data.binariesById[binId].processesById[procId].logs.length > data.metadata.maxProcessLogs) data.metadata.maxProcessLogs = data.binariesById[binId].processesById[procId].logs.length
  }
  function updateProperty (ex, attr, trgEx = null, trgCh = null, edge) {
    const bin = data.binariesById[ex.exec.id]
    if (trgEx !== null && trgCh === null) {
      if (!bin[attr][trgEx.exec.id]) bin[attr][trgEx.exec.id] = { id: trgEx.exec.id, data: trgEx, entries: [] }
      bin[attr][trgEx.exec.id].entries.push(edge)
    } else if (trgEx === null && trgCh !== null) {
      if (!bin[attr][trgCh.id]) bin[attr][trgCh.id] = { id: trgCh.id, data: trgCh, entries: [] }
      bin[attr][trgCh.id].entries.push(edge)
    } else if (trgEx !== null && trgCh !== null) {
      if (!bin[attr][trgCh.id]) bin[attr][trgCh.id] = { id: trgCh.id, data: trgCh, binariesById: {} }
      if (!bin[attr][trgCh.id].binariesById[trgEx.exec.id]) bin[attr][trgCh.id].binariesById[trgEx.exec.id] = { id: trgEx.exec.id, data: trgEx, entries: [] }
      bin[attr][trgCh.id].binariesById[trgEx.exec.id].entries.push(edge)
    }
  }
  function handleEdge (edgeId) {
    const edge = runGraph.getEdgeAttributes(edgeId)
    if (edge.subtype === 'init') {
      //
    } else if (edge.subtype === 'spawn') {
      //
      const { parent, child } = edge.data
      handleExecutable(parent)
      handleExecutable(child)
      handleProcess(parent, edge)
      handleProcess(child, edge)
      updateProperty(child, 'spawnParentExecsById', parent, null, edge)
      updateProperty(parent, 'spawnChildExecsById', child, null, edge)
    } else if (edge.subtype === 'listen') {
      //
      const { channel, listener } = edge.data
      handleExecutable(listener)
      handleProcess(listener, edge)
      updateProperty(listener, 'listenChannelsById', null, channel, edge)
    } else if (edge.subtype === 'border_write') {
      //
    } else if (edge.subtype === 'border_read') {
      //
      const { channel, sink } = edge.data
      handleExecutable(sink)
      handleProcess(sink, edge)
      updateProperty(sink, 'borderChannelsById', null, channel, edge)
    } else if (edge.subtype === 'within_write') {
      //
      const { channel, source, sink } = edge.data
      handleExecutable(source)
      handleProcess(source, edge)
      updateProperty(source, 'withinWriteChannelsById', sink, channel, edge)
    } else if (edge.subtype === 'within_read') {
      //
      const { channel, source, sink } = edge.data
      handleExecutable(sink)
      handleProcess(sink, edge)
      updateProperty(sink, 'withinReadChannelsById', source, channel, edge)
    }
  }
  edges.forEach(handleEdge)
  console.log(data)
  return data
}

// BINARY GRAPH
export function getBinaryGraph ({ binId, binariesById, depth = { inProc: 1, inData: 1, outProc: 1, outData: 1 }, entriesThreshold = -1 }) {
  const g = new dagre.graphlib.Graph()
  g.setGraph({
    rankdir: 'TB',
    ranker: 'network-simplex'
  })
  const nodesById = {
    binaries: {},
    channels: {}
  }
  const edgesById = {
    border: {},
    listen: {},
    spawn: {},
    read: {},
    write: {},
    rw: {},
    pc: {}
  }
  let maxEdgesEntries = 0
  function visitBinary (id, depth) {
    updateBinary(id)
    const d = { inProc: depth.inProc - 1, inData: depth.inData - 1, outProc: depth.outProc - 1, outData: depth.outData - 1 }
    const bin = binariesById[id]
    for (const spawned of Object.values(bin.spawnChildExecsById)) {
      updateBinary(spawned.id)
      updateSpawn(id, spawned.id, spawned.entries)
      if (depth.outProc > 0) visitBinary(spawned.id, d)
    }
    for (const spawner of Object.values(bin.spawnParentExecsById)) {
      updateBinary(spawner.id)
      updateSpawn(spawner.id, id, spawner.entries)
      if (depth.inProc > 0) visitBinary(spawner.id, d)
    }
    for (const readChan of Object.values(bin.withinReadChannelsById)) {
      updateChannel(readChan)
      for (const writer of (Object.values(readChan.binariesById))) {
        updateBinary(writer.id)
        updateWithin(writer.id, id, readChan.id, writer.entries)
        if (depth.inData > 0) visitBinary(writer.id, d)
      }
    }
    for (const writeChan of Object.values(bin.withinWriteChannelsById)) {
      updateChannel(writeChan)
      for (const reader of (Object.values(writeChan.binariesById))) {
        updateBinary(reader.id)
        updateWithin(id, reader.id, writeChan.id, reader.entries)
        if (depth.outData > 0) visitBinary(reader.id, d)
      }
    }
    for (const borderChan of Object.values(bin.borderChannelsById)) {
      updateChannel(borderChan)
      updateBorder(id, borderChan.id, borderChan.entries)
    }
  }
  function updateBinary (id) {
    const bin = binariesById[id]
    const { exec, symt } = bin.data
    if (!nodesById.binaries[id]) {
      nodesById.binaries[id] = {
        id,
        label: id,
        width: 160,
        height: 40,
        type: 'binary',
        data: { exec, symt }
      }
    }
  }
  function updateChannel (chann) {
    const { id, data } = chann
    if (!nodesById.channels[id]) {
      nodesById.channels[id] = {
        id,
        label: id,
        width: 40,
        height: 40,
        type: 'channel',
        data: { ...data, type: getDataChannelKind(data.kind) }
      }
    }
  }
  function updateSpawn (idParent, idChild, entries) {
    const id = `${idParent}-${idChild}`
    const backId = `${idChild}-${idParent}`
    if (!edgesById.spawn[id] && !edgesById.spawn[backId]) {
      edgesById.spawn[id] = [
        idParent,
        idChild,
        { entries: [], type: 'spawn' }
      ]
      edgesById.spawn[id][2].entries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.spawn[id][2].entries.length)
    } else if (edgesById.spawn[backId]) {
      const { entries: spEntries } = edgesById.spawn[backId][2]
      delete edgesById.spawn[backId]
      edgesById.pc[backId] = [
        idChild,
        idParent,
        { entries: spEntries, backEntries: [], type: 'pc' }
      ]
      edgesById.pc[backId][2].backEntries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.pc[backId][2].entries.length + edgesById.pc[backId][2].backEntries.length)
    } else if (edgesById.pc[id]) {
      edgesById.pc[id][2].entries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.pc[id][2].entries.length + edgesById.pc[id][2].backEntries.length)
    } else if (edgesById.pc[backId]) {
      edgesById.pc[backId][2].backEntries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.pc[backId][2].entries.length + edgesById.pc[backId][2].backEntries.length)
    } else if (edgesById.spawn[id]) {
      edgesById.spawn[id][2].entries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.spawn[id][2].entries.length)
    }
  }
  function updateWithin (idWriter, idReader, idChannel, entries) {
    const idw = `${idWriter}-${idChannel}`
    const backIdw = `${idChannel}-${idWriter}`
    const idr = `${idChannel}-${idReader}`
    const backIdr = `${idReader}-${idChannel}`
    //
    if (!edgesById.write[idw] && !edgesById.read[backIdw]) {
      edgesById.write[idw] = [
        idWriter,
        idChannel,
        { entries: [], type: 'write' }
      ]
      edgesById.write[idw][2].entries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.write[idw][2].entries.length)
    } else if (edgesById.read[backIdw]) {
      const { entries: readEntries } = edgesById.read[backIdw][2]
      delete edgesById.read[backIdw]
      edgesById.rw[idw] = [
        idWriter,
        idChannel,
        { readEntries, writeEntries: [], type: 'rw' }
      ]
      edgesById.rw[idw][2].writeEntries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.rw[idw][2].writeEntries.length + edgesById.rw[idw][2].readEntries.length)
    } else if (edgesById.rw[idw]) {
      edgesById.rw[idw][2].writeEntries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.rw[idw][2].writeEntries.length + edgesById.rw[idw][2].readEntries.length)
    } else if (edgesById.write[idw]) {
      edgesById.write[idw][2].entries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.write[idw][2].entries.length)
    }
    //
    if (!edgesById.read[idr] && !edgesById.write[backIdr]) {
      edgesById.read[idr] = [
        idChannel,
        idReader,
        { entries: [], type: 'read' }
      ]
      edgesById.read[idr][2].entries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.read[idr][2].entries.length)
    } else if (edgesById.write[backIdr]) {
      const { entries: writeEntries } = edgesById.write[backIdr][2]
      delete edgesById.write[backIdr]
      edgesById.rw[backIdr] = [
        idReader,
        idChannel,
        { readEntries: [], writeEntries, type: 'rw' }
      ]
      edgesById.rw[backIdr][2].readEntries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.rw[backIdr][2].writeEntries.length + edgesById.rw[backIdr][2].readEntries.length)
    } else if (edgesById.rw[backIdr]) {
      edgesById.rw[backIdr][2].readEntries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.rw[backIdr][2].writeEntries.length + edgesById.rw[backIdr][2].readEntries.length)
    } else if (edgesById.read[idr]) {
      edgesById.read[idr][2].entries.push(...entries)
      maxEdgesEntries = Math.max(maxEdgesEntries, edgesById.read[idr][2].entries.length)
    }
  }
  function updateBorder (idReader, idChannel, entries) {
    const idr = `${idChannel}-${idReader}`
    if (!edgesById.read[idr]) {
      edgesById.read[idr] = [
        idChannel,
        idReader,
        { entries: [], type: 'border' }
      ]
    }
    edgesById.read[idr][2].entries.push(...entries)
  }
  if (binariesById[binId]) visitBinary(binId, depth)
  else {
    return {
      nodes: [],
      edges: []
    }
  }
  // maxEdgesEntries = Math.max(100, maxEdgesEntries)
  for (const [id, obj] of Object.entries(nodesById.binaries)) { g.setNode(id, obj) }
  for (const [id, obj] of Object.entries(nodesById.channels)) { g.setNode(id, obj) }
  for (const [idSrc, idTrg, obj] of Object.values(edgesById.spawn)) { g.setEdge(idSrc, idTrg, obj) }
  for (const [idSrc, idTrg, obj] of Object.values(edgesById.write)) { g.setEdge(idSrc, idTrg, obj) }
  for (const [idSrc, idTrg, obj] of Object.values(edgesById.read)) { g.setEdge(idSrc, idTrg, obj) }
  for (const [idSrc, idTrg, obj] of Object.values(edgesById.border)) { g.setEdge(idSrc, idTrg, obj) }
  for (const [idSrc, idTrg, obj] of Object.values(edgesById.pc)) { g.setEdge(idSrc, idTrg, obj) }
  for (const [idSrc, idTrg, obj] of Object.values(edgesById.rw)) { g.setEdge(idSrc, idTrg, obj) }
  // dagre.layout(g)
  const e = g.edges()
    .map(v => ({ ...g.edge(v), idSrc: v.v, idTrg: v.w }))
    .filter(d => {
      if (getEdgeEntriesLength(d) < entriesThreshold) {
        g.removeEdge(d.idSrc, d.idTrg)
        return false
      }
      return true
    })
    .map(d => ({
      id: `${sanitizeId(d.idSrc)}-${sanitizeId(d.idTrg)}`,
      source: sanitizeId(d.idSrc),
      target: sanitizeId(d.idTrg),
      type: 'smoothstep',
      sourceHandle: getHandleId(d, 'src'),
      targetHandle: getHandleId(d, 'trg'),
      style: getStyle(d, maxEdgesEntries),
      animated: getAnimated(d),
      data: d
    }))
  const notFilteredNodesById = {}
  e.forEach(e => {
    notFilteredNodesById[e.source] = true
    notFilteredNodesById[e.target] = true
  })
  dagre.layout(g)
  return {
    nodes: g.nodes()
      .map(v => g.node(v))
      .filter(d => notFilteredNodesById[sanitizeId(d.id)] !== undefined)
      .map(d => ({
        id: sanitizeId(d.id),
        label: d.label,
        type: d.type,
        position: { x: d.x - d.width / 2, y: d.y - d.height / 2 },
        data: d
      })),
    edges: e,
    maxEdgesEntries
  }
}
function getHandleId (edge, dir = 'src') {
  if (edge.type === 'border' && dir === 'src') return 'write-src'
  if (edge.type === 'border' && dir === 'trg') return 'read-trg'
  return `${edge.type}-${dir}`
}
function getEdgeEntriesLength (edge) {
  if (edge.type === 'rw') return edge.readEntries.length + edge.writeEntries.length
  else if (edge.type === 'pc') return edge.entries.length + edge.backEntries.length
  else return edge.entries.length
}
function getStyle (edge, maxEntries) {
  const style = {}
  if (edge.type === 'spawn' || edge.type === 'pc') {
    style.stroke = '#A3CCE4'
  } else {
    style.stroke = '#F9694C'
  }
  style.strokeWidth = Math.max(getEdgeEntriesLength(edge) / maxEntries * 15, 2)
  return style
}
function getAnimated (edge) {
  if (edge.type === 'rw' || edge.type === 'pc') return false
  return true
}
