import { initialState } from './store'

// BORDER BINARIES
function addBinary (bin) {
  return {
    id: bin.id,
    data: bin,
    borderChannelsById: {},
    listenChannelsById: {},
    symlinksById: {},
    maxBorderScore: 0,
    maxListenScore: 0
  }
}
function addSymlink (bin) {
  return {
    id: bin.id,
    data: bin,
    borderChannelsById: {},
    listenChannelsById: {},
    maxBorderScore: 0,
    maxListenScore: 0
  }
}
function addProcess (proc) {
  return {
    id: proc.id,
    data: proc
  }
}
function addChannel (chann) {
  return {
    id: chann.id,
    data: chann,
    processesById: {}
  }
}
function getEdges (graph, minTime, maxTime, conf) {
  const {
    borderChannelThreshold,
    listenChannelThreshold,
    withinChannelThreshold
  } = conf
  return graph.filterEdges((_id, attr) => (
    attr.type === 'event' &&
    (minTime ? attr.time >= minTime : true) &&
    (maxTime ? attr.time <= maxTime : true) &&
    (((attr.subtype === 'border_read' || attr.subtype === 'border_write') ? attr.data.channel.score >= borderChannelThreshold : true)) &&
    ((attr.subtype === 'listen' ? attr.data.channel.score >= listenChannelThreshold : true)) &&
    (((attr.subtype === 'within_read' || attr.subtype === 'within_write') ? attr.data.channel.score >= withinChannelThreshold : true))
  )).sort((a, b) => a.logix - b.logix)
}
export function getBorderBinaries ({ runGraph, logix }) {
  if (runGraph === initialState.selectedRunGraph) return []
  getDataView(runGraph, 0, 300000, {
    borderChannelThreshold: 0.1,
    listenChannelThreshold: 0,
    withinChannelThreshold: 0.1,
    timeBins: 20
  })
  if (true) return []
  const binaries = {}
  function getEdges (subtype) {
    if (logix !== undefined) return runGraph.filterEdges((_id, attributes) => attributes.logix <= logix && (attributes.subtype === subtype))
    return runGraph.filterEdges((_id, attributes) => attributes.subtype === subtype)
  }
  function handleBorderEdge (edgeId) {
    const edge = runGraph.getEdgeAttributes(edgeId)
    const { channel, sink } = edge.data
    const { exec, symt, proc } = sink
    if (!symt) {
      //
      if (!binaries[exec.id]) binaries[exec.id] = addBinary(exec)
      if (!binaries[exec.id].borderChannelsById[channel.id]) binaries[exec.id].borderChannelsById[channel.id] = addChannel(channel)
      if (!binaries[exec.id].borderChannelsById[channel.id].processesById[proc.id]) binaries[exec.id].borderChannelsById[channel.id].processesById[proc.id] = addProcess(proc)
      binaries[exec.id].maxBorderScore = Math.max(binaries[exec.id].maxBorderScore, channel.score)
    } else {
      //
      if (!binaries[symt.id]) binaries[symt.id] = addBinary(symt)
      if (!binaries[symt.id].borderChannelsById[channel.id]) binaries[symt.id].borderChannelsById[channel.id] = addChannel(channel)
      if (!binaries[symt.id].borderChannelsById[channel.id].processesById[proc.id]) binaries[symt.id].borderChannelsById[channel.id].processesById[proc.id] = addProcess(proc)
      binaries[symt.id].maxBorderScore = Math.max(binaries[symt.id].maxBorderScore, channel.score)
      //
      if (!binaries[symt.id].symlinksById[exec.id]) binaries[symt.id].symlinksById[exec.id] = addSymlink(exec)
      if (!binaries[symt.id].symlinksById[exec.id].borderChannelsById[channel.id]) binaries[symt.id].symlinksById[exec.id].borderChannelsById[channel.id] = addChannel(channel)
      if (!binaries[symt.id].symlinksById[exec.id].borderChannelsById[channel.id].processesById[proc.id]) binaries[symt.id].symlinksById[exec.id].borderChannelsById[channel.id].processesById[proc.id] = addProcess(proc)
      binaries[symt.id].symlinksById[exec.id].maxBorderScore = Math.max(binaries[symt.id].symlinksById[exec.id].maxBorderScore, channel.score)
    }
    const { binId, bin } = sink.symt ? { binId: sink.symt.id, bin: sink.symt } : { binId: sink.exec.id, bin: sink.exec }
    if (!binaries[binId]) {
      binaries[binId] = {
        ...bin
      }
    }
  }
  function handleListenEdge (edgeId) {
    const edge = runGraph.getEdgeAttributes(edgeId)
    const { channel, listener } = edge.data
    const { exec, symt, proc } = listener
    if (!symt) {
      if (!binaries[exec.id]) binaries[exec.id] = addBinary(exec)
      //
      if (!binaries[exec.id].borderChannelsById[channel.id]) {
        if (!binaries[exec.id].listenChannelsById[channel.id]) binaries[exec.id].listenChannelsById[channel.id] = addChannel(channel)
        if (!binaries[exec.id].listenChannelsById[channel.id].processesById[proc.id]) binaries[exec.id].listenChannelsById[channel.id].processesById[proc.id] = addProcess(proc)
        binaries[exec.id].maxListenScore = Math.max(binaries[exec.id].maxListenScore, channel.score)
      }
    } else {
      if (!binaries[symt.id]) binaries[symt.id] = addBinary(symt)
      //
      if (!binaries[symt.id].borderChannelsById[channel.id]) {
        if (!binaries[symt.id].listenChannelsById[channel.id]) binaries[symt.id].listenChannelsById[channel.id] = addChannel(channel)
        if (!binaries[symt.id].listenChannelsById[channel.id].processesById[proc.id]) binaries[symt.id].listenChannelsById[channel.id].processesById[proc.id] = addProcess(proc)
        binaries[symt.id].maxListenScore = Math.max(binaries[symt.id].maxListenScore, channel.score)
        //
        if (!binaries[symt.id].symlinksById[exec.id]) binaries[symt.id].symlinksById[exec.id] = addSymlink(exec)
        if (!binaries[symt.id].symlinksById[exec.id].listenChannelsById[channel.id]) binaries[symt.id].symlinksById[exec.id].listenChannelsById[channel.id] = addChannel(channel)
        if (!binaries[symt.id].symlinksById[exec.id].listenChannelsById[channel.id].processesById[proc.id]) binaries[symt.id].symlinksById[exec.id].listenChannelsById[channel.id].processesById[proc.id] = addProcess(proc)
        binaries[symt.id].symlinksById[exec.id].maxListenScore = Math.max(binaries[symt.id].symlinksById[exec.id].maxListenScore, channel.score)
      }
    }
    console.log(edge)
  }
  //
  const listenEdges = getEdges('listen')
  const borderEdges = getEdges('border_read')
  //
  borderEdges.forEach(handleBorderEdge)
  listenEdges.forEach(handleListenEdge)
  // return binaries
  return Object.values(binaries).map(bin => ({
    ...bin,
    borderChannels: Object.values(bin.borderChannelsById).map(ch => ({
      ...ch,
      processes: Object.values(ch.processesById)
    })).sort((a, b) => b.data.score - a.data.score),
    listenChannels: Object.values(bin.listenChannelsById).map(ch => ({
      ...ch,
      processes: Object.values(ch.processesById)
    })).sort((a, b) => b.data.score - a.data.score),
    symlinks: Object.values(bin.symlinksById).map(sym => ({
      ...sym,
      borderChannels: Object.values(sym.borderChannelsById).map(ch => ({
        ...ch,
        processes: Object.values(ch.processesById)
      })).sort((a, b) => b.data.score - a.data.score),
      listenChannels: Object.values(sym.listenChannelsById).map(ch => ({
        ...ch,
        processes: Object.values(ch.processesById)
      })).sort((a, b) => b.data.score - a.data.score)
    }))
  })).sort((a, b) => b.maxBorderScore - a.maxBorderScore)
}

// DATA VIEW
export function getDataView ({ graph, minTime, maxTime, conf }) {
  const edges = getEdges(graph, minTime, maxTime, conf)
  const data = {
    binariesById: {}
  }
  const attrs = {
    listenChannelsById: {},
    borderChannelsById: {},
    withinReadChannelsById: {},
    spawnParentExecsById: {},
    withinWriteChannelsById: {},
    spawnChildExecsById: {},
    processesById: {}
  }
  function updateProperty (attr, ex, obj) {
    const { exec, symt, proc } = ex
    let binId = obj.id
    let symId = obj.id
    if (attr === 'listenChannelsById' || attr === 'borderChannelsById') {
      binId = symId = obj.channel.id
    } else if (attr === 'spawnParentExecsById') {
      binId = obj.parent.symt === null ? obj.parent.exec.id : obj.parent.symt.id
      symId = obj.parent.symt === null ? `${obj.parent.exec.id}-null` : `${obj.parent.symt.id}-${obj.parent.exec.id}`
    } else if (attr === 'spawnChildExecsById') {
      binId = obj.child.symt === null ? obj.child.exec.id : obj.child.symt.id
      symId = obj.child.symt === null ? `${obj.child.exec.id}-null` : `${obj.child.symt.id}-${obj.child.exec.id}`
    } else if (attr === 'withinWriteChannSinksById') {
      binId = obj.sink.symt === null ? `${obj.sink.exec.id}-${obj.channel.id}` : `${obj.sink.symt.id}-${obj.channel.id}`
      symId = obj.sink.symt === null ? `${obj.sink.exec.id}-null-${obj.channel.id}` : `${obj.sink.symt.id}-${obj.sink.exec.id}-${obj.channel.id}`
    } else if (attr === 'withinReadChannSourcesById') {
      binId = obj.source.symt === null ? `${obj.source.exec.id}-${obj.channel.id}` : `${obj.source.symt.id}-${obj.channel.id}`
      symId = obj.source.symt === null ? `${obj.source.exec.id}-null-${obj.channel.id}` : `${obj.source.symt.id}-${obj.source.exec.id}-${obj.channel.id}`
    }
    if (ex.symt === null) {
      if (!data.binariesById[exec.id][attr][binId]) data.binariesById[exec.id][attr][binId] = { ...obj, id: binId }
    } else {
      if (!data.binariesById[symt.id][attr][binId]) data.binariesById[symt.id][attr][binId] = { ...obj, id: binId }
      if (!data.binariesById[symt.id].symlinksById[exec.id][attr][symId]) data.binariesById[symt.id].symlinksById[exec.id][attr][symId] = { ...obj, id: symId }
    }
  }
  function updateProp (ex, attr, trgEx = null, trgCh = null, edge) {
    const { exec, symt, proc } = ex
    const exObj = ex.symt === null
      ? data.binariesById[exec.id]
      : data.binariesById[symt.id].symlinksById[exec.id]
    if (trgCh === null && trgEx !== null) {
      if (trgEx.symt === null) {
        if (!exObj[attr][trgEx.exec.id]) exObj[attr][trgEx.exec.id] = { id: trgEx.exec.id, data: trgEx.exec, symlinksById: {}, entries: [] }
        exObj[attr][trgEx.exec.id].entries.push(edge)
      } else {
        if (!exObj[attr][trgEx.symt.id]) exObj[attr][trgEx.symt.id] = { id: trgEx.symt.id, data: trgEx.symt, symlinksById: {}, entries: [] }
        if (!exObj[attr][trgEx.symt.id].symlinksById[trgEx.exec.id]) exObj[attr][trgEx.symt.id].symlinksById[trgEx.exec.id] = { id: trgEx.exec.id, data: trgEx.exec, entries: [] }
        exObj[attr][trgEx.symt.id].symlinksById[trgEx.exec.id].entries.push(edge)
      }
    } else if (trgCh !== null && trgEx === null) {
      if (!exObj[attr][trgCh.id]) exObj[attr][trgCh.id] = { id: trgCh.id, data: trgCh, entries: [] }
      exObj[attr][trgCh.id].entries.push(edge)
    } else if (trgCh !== null && trgEx !== null) {
      if (!exObj[attr][trgCh.id]) exObj[attr][trgCh.id] = { id: trgCh.id, data: trgCh, binariesById: {} }
      if (trgEx.symt === null) {
        if (!exObj[attr][trgCh.id].binariesById[trgEx.exec.id]) exObj[attr][trgCh.id].binariesById[trgEx.exec.id] = { id: trgEx.exec.id, data: trgEx.exec, symlinksById: {}, entries: [] }
        exObj[attr][trgCh.id].binariesById[trgEx.exec.id].entries.push(edge)
      } else {
        if (!exObj[attr][trgCh.id].binariesById[trgEx.symt.id]) exObj[attr][trgCh.id].binariesById[trgEx.symt.id] = { id: trgEx.symt.id, data: trgEx.symt, symlinksById: {}, entries: [] }
        if (!exObj[attr][trgCh.id].binariesById[trgEx.symt.id].symlinksById[trgEx.exec.id]) exObj[attr][trgCh.id].binariesById[trgEx.symt.id].symlinksById[trgEx.exec.id] = { id: trgEx.exec.id, data: trgEx.exec, entries: [] }
        exObj[attr][trgCh.id].binariesById[trgEx.symt.id].symlinksById[trgEx.exec.id].entries.push(edge)
      }
    }
  }
  function addBinary (bin) {
    if (!data.binariesById[bin.id]) {
      data.binariesById[bin.id] = {
        id: bin.id,
        data: bin,
        symlinksById: {},
        ...JSON.parse(JSON.stringify(attrs))
      }
    }
  }
  function addSymlink (exec, symt) {
    addBinary(symt)
    if (!data.binariesById[symt.id].symlinksById[exec.id]) {
      data.binariesById[symt.id].symlinksById[exec.id] = {
        id: exec.id,
        data: exec,
        ...JSON.parse(JSON.stringify(attrs))
      }
    }
  }
  function addExecutable (ex) {
    if (ex.symt === null) {
      addBinary(ex.exec)
    } else {
      addSymlink(ex.exec, ex.symt)
    }
  }
  function handleEdge (edgeId) {
    const edge = graph.getEdgeAttributes(edgeId)
    if (edge.subtype === 'init') {
      //
    } else if (edge.subtype === 'spawn') {
      //
      const { parent, child } = edge.data
      addExecutable(parent)
      addExecutable(child)
      updateProp(child, 'spawnParentExecsById', parent, null, edge)
      updateProp(parent, 'spawnChildExecsById', child, null, edge)
      // updateProperty('spawnParentExecsById', child, { parent, child })
      // updateProperty('spawnChildExecsById', parent, { child, parent })
    } else if (edge.subtype === 'listen') {
      //
      const { channel, listener } = edge.data
      addExecutable(listener)
      updateProp(listener, 'listenChannelsById', null, channel, edge)
      // updateProperty('listenChannelsById', listener, { channel })
    } else if (edge.subtype === 'border_write') {
      //
    } else if (edge.subtype === 'border_read') {
      //
      const { channel, sink } = edge.data
      addExecutable(sink)
      updateProp(sink, 'borderChannelsById', null, channel, edge)
      // updateProperty('borderChannelsById', sink, { channel })
    } else if (edge.subtype === 'within_write') {
      //
      const { channel, source, sink } = edge.data
      addExecutable(source)
      updateProp(source, 'withinWriteChannelsById', sink, channel, edge)
      // updateProperty('withinWriteChannSinksById', source, { sink, channel })
    } else if (edge.subtype === 'within_read') {
      //
      const { channel, source, sink } = edge.data
      addExecutable(sink)
      updateProp(sink, 'withinReadChannelsById', source, channel, edge)
      // updateProperty('withinReadChannSourcesById', sink, { source, channel })
    }
  }
  edges.forEach(handleEdge)
  return data
}
