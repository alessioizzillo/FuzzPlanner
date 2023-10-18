import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/20/solid'

export default function Expander ({ row, onClick = row.getToggleExpandedHandler(), expanded = row.getIsExpanded() }) {
  return (
    <button {...{ onClick }}>
      {expanded ? <ChevronDownIcon className='w-4 h-4 mr-1' /> : <ChevronRightIcon className='w-4 h-4 mr-1' />}
    </button>
  )
}
