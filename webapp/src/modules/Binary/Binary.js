import { useMemo, useState } from 'react'
import ChannelsTable from './ChannelsTable'
import CveTable from './CveTable'

export default function Binary ({ className, binary }) {
  const [channelsSorting, setChannelsSorting] = useState([{ id: 'score', desc: true }])
  const [cveSorting, setCveSorting] = useState([{ id: 'base', desc: true }])
  const [listenChecked, setListenChecked] = useState(true)
  const [borderChecked, setBorderChecked] = useState(true)
  const [readChecked, setReadChecked] = useState(true)
  const [writeChecked, setWriteChecked] = useState(true)
  const channels = useMemo(() => {
    let ch = []
    if (listenChecked) ch = ch.concat(Object.values(binary.listenChannelsById).map(c => ({ ...c, role: 'listen' })))
    if (borderChecked) ch = ch.concat(Object.values(binary.borderChannelsById).map(c => ({ ...c, role: 'border' })))
    if (readChecked && writeChecked) {
      Object.values(binary.withinReadChannelsById).forEach(c => {
        if (binary.withinWriteChannelsById[c.id]) ch.push({ ...c, role: 'rw' })
        else ch.push({ ...c, role: 'read' })
      })
      Object.values(binary.withinWriteChannelsById).forEach(c => {
        if (!binary.withinReadChannelsById[c.id]) ch.push({ ...c, role: 'write' })
      })
    } else {
      if (readChecked) ch = ch.concat(Object.values(binary.withinReadChannelsById).map(c => ({ ...c, role: 'read' })))
      if (writeChecked) ch = ch.concat(Object.values(binary.withinWriteChannelsById).map(c => ({ ...c, role: 'write' })))
    }
    return ch
  }, [listenChecked, borderChecked, readChecked, writeChecked])
  const handleOnChangeListen = (id) => { setListenChecked(!listenChecked) }
  const handleOnChangeBorder = (id) => { setBorderChecked(!borderChecked) }
  const handleOnChangeRead = (id) => { setReadChecked(!readChecked) }
  const handleOnChangeWrite = (id) => { setWriteChecked(!writeChecked) }
  return (
    <div className='flex overflow-y-auto h-120'>
      <div className='px-2'>
        <div className='flex items-center h-12 text-sm'>
          <input className='' type='checkbox' id='listen' name='listen' checked={listenChecked} onChange={handleOnChangeListen} />
          <label className='w-20 pl-2' htmlFor='listen'>Listen</label>
          <input className='' type='checkbox' id='border' name='border' checked={borderChecked} onChange={handleOnChangeBorder} />
          <label className='w-20 pl-2' htmlFor='border'>Border</label>
          <input className='' type='checkbox' id='read' name='read' checked={readChecked} onChange={handleOnChangeRead} />
          <label className='w-20 pl-2' htmlFor='read'>Read</label>
          <input className='' type='checkbox' id='write' name='write' checked={writeChecked} onChange={handleOnChangeWrite} />
          <label className='w-20 pl-2' htmlFor='write'>Write</label>
        </div>
        <ChannelsTable
          binary={binary}
          channels={channels}
        // channels={[...(true ? Object.values(binary.listenChannelsById) : [])]}
          sorting={channelsSorting}
          setSorting={setChannelsSorting}
        />
      </div>
      <div className='ml-8'>
        <CveTable
          cves={binary.data.exec.cves}
          sorting={cveSorting}
          setSorting={setCveSorting}
        />
      </div>
    </div>
  )
}
