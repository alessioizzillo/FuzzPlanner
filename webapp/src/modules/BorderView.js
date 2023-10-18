import { ChevronDownIcon, ChevronRightIcon, ChevronUpIcon } from '@heroicons/react/20/solid'
import { createColumnHelper, flexRender, getCoreRowModel, getSortedRowModel, getExpandedRowModel, useReactTable } from '@tanstack/react-table'
import { Fragment, useState } from 'react'

function Expander ({ row }) {
  return (
    <button {...{ onClick: row.getToggleExpandedHandler() }}>
      {row.getIsExpanded() ? <ChevronDownIcon className='w-4 h-4 mr-1' /> : <ChevronRightIcon className='w-4 h-4 mr-1' />}
    </button>
  )
}

const columnHelper = createColumnHelper()
const binariesColumns = [
  columnHelper.display({
    id: 'expander',
    header: () => null,
    cell: ({ row }) => <Expander row={row} />
  }),
  columnHelper.accessor('id', {
    id: 'id',
    header: 'Binary',
    cell: v => v.getValue()
  }),
  columnHelper.accessor('maxBorderScore', {
    id: 'border',
    header: 'Border',
    cell: v => v.getValue()
  }),
  columnHelper.accessor(row => row.borderChannels.length, {
    id: 'numBorderChannels',
    header: '# Border Ch.',
    cell: v => v.getValue()
  }),
  columnHelper.accessor('maxListenScore', {
    id: 'listen',
    header: 'Listen',
    cell: v => v.getValue()
  }),
  columnHelper.accessor(row => row.listenChannels.length, {
    id: 'numListenChannels',
    header: '# Listen Ch.',
    cell: v => v.getValue()
  })
]

function BinariesTable ({ binaries, sorting, setSorting }) {
  const table = useReactTable({
    data: binaries,
    columns: binariesColumns,
    state: { sorting },
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    getCoreRowModel: getCoreRowModel(),
    getRowCanExpand: () => true,
    getExpandedRowModel: getExpandedRowModel()
  })
  return (
    <table className='p-2 text-left'>
      <BinariesTableHead table={table} />
      <tbody>
        {table.getRowModel().rows.map(row => (
          <Fragment key={row.id}>
            <tr key={row.id} className='border-y border-slate-500' onClick={() => console.log(row.original)}>
              {row.getVisibleCells().map(cell => (
                <td key={cell.id} className='p-2 cursor-pointer'>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
            {row.getIsExpanded() && (
              <tr>{row.id}</tr>
            )}
          </Fragment>
        ))}
      </tbody>
    </table>
  )
}

function BinariesTableHead ({ table }) {
  return (
    <thead>{table.getHeaderGroups().map(hg => (
      <tr key={hg.id} className='border-y-2 border-slate-100'>
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
function BinaryComponent () {

}

export default function BorderView ({ borderBinaries }) {
  const [sorting, setSorting] = useState([])
  console.log(borderBinaries)
  return (
    <div>
      BorderView
      <BinariesTable binaries={borderBinaries} sorting={sorting} setSorting={setSorting} />
    </div>
  )
}
