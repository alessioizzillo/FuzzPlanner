import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/20/solid'
import { flexRender } from '@tanstack/react-table'

export default function TableHeadSort ({ table }) {
  return (
    <thead>{table.getHeaderGroups().map(hg => (
      <tr key={hg.id} className='text-sm font-bold border-y-2 border-gray-500 dark:border-slate-100 bg-gray-200 dark:bg-transparent text-black dark:text-gray-200'>
        {hg.headers.map(h => (
          <th key={h.id} className='p-2'>
            {h.isPlaceholder
              ? null
              : (
                <div
                  {...{
                    className: h.column.getCanSort()
                      ? 'flex items-center cursor-pointer select-none hover:text-blue-800 dark:hover:text-blue-400'
                      : '',
                    onClick: h.column.getToggleSortingHandler()
                  }}
                >
                  {flexRender(
                    h.column.columnDef.header,
                    h.getContext()
                  )}
                  {{
                    asc: <ChevronUpIcon className='w-4 h-4 ml-1 text-blue-800 dark:text-blue-400' />,
                    desc: <ChevronDownIcon className='w-4 h-4 ml-1 text-blue-800 dark:text-blue-400' />
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
