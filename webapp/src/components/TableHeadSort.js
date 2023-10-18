import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/20/solid'
import { flexRender } from '@tanstack/react-table'

export default function TableHeadSort ({ table }) {
  return (
    <thead>{table.getHeaderGroups().map(hg => (
      <tr key={hg.id} className='text-sm  border-y-2 border-slate-100'>
        {hg.headers.map(h => (
          <th key={h.id} className='p-2'>
            {h.isPlaceholder
              ? null
              : (
                <div
                  {...{
                    className: h.column.getCanSort()
                      ? 'flex items-center cursor-pointer select-none'
                      : '',
                    onClick: h.column.getToggleSortingHandler()
                  }}
                >
                  {flexRender(
                    h.column.columnDef.header,
                    h.getContext()
                  )}
                  {{
                    asc: <ChevronUpIcon className='w-4 h-4 ml-1' />,
                    desc: <ChevronDownIcon className='w-4 h-4 ml-1' />
                  }[h.column.getIsSorted()] ?? null}
                </div>
                )}
          </th>
        ))}
      </tr>
    ))}
    </thead>
  )
}
