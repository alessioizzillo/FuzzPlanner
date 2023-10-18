import { dataChannelKindsById, getDataChannelKind } from '@/constants'
import { useSelectedEntries } from '@/hooks/store/selectedEntries'
import classNames from 'classnames'

export default function SelectedEntries ({ className }) {
  const selectedEntries = useSelectedEntries()
  console.log(selectedEntries)
  return (
    <div className={classNames('', className)}>
      {Object.values(selectedEntries).map(e => {
        const Icon = dataChannelKindsById[getDataChannelKind(e.channel.kind)].Icon
        return (
          <div className='pb-2 mb-2 overflow-hidden text-sm border-b text-ellipsis' key={e.id}>
            <div>{e.binary.id}</div>
            <div className='flex items-center justify-center'>
              <div className='pr-2'><Icon /></div>
              <div>{e.channel.id}</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
