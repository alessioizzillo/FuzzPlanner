import { Fragment, useCallback } from 'react'
import { createColumnHelper, flexRender, getCoreRowModel, getExpandedRowModel, getSortedRowModel, useReactTable } from '@tanstack/react-table'
import { accessorListen, accessorBorder, accessorWithinRead, accessorSpawnParent, accessorWithinWrite, accessorSpawnChild, accessorBinary, accessorCve, accessorCwe, accessorProprietary } from './accessors'
import Expander from '@/components/Expander'
import BinariesTableCell from './BinariesTableCell'
import Binary from '@/modules/Binary/Binary'
import TableHeadSort from '@/components/TableHeadSort'
import classNames from 'classnames'

const columnHelper = createColumnHelper()
const binariesColumns = [
  columnHelper.display({
    id: 'expander',
    header: () => null,
    cell: ({ row, selectedBinary, setSelectedBinary }) => (
      <Expander
        row={row}
        onClick={() => setSelectedBinary(selectedBinary?.id === row.original.id ? null : row.original)}
        expanded={selectedBinary?.id === row.original.id}
      />)
  }),
  columnHelper.accessor(accessorListen, {
    id: 'listen',
    header: 'Listen',
    cell: v => <BinariesTableCell colId='listen' value={v.getValue()} />
  }),
  columnHelper.accessor(accessorBorder, {
    id: 'border',
    header: 'Border',
    cell: v => <BinariesTableCell colId='border' value={v.getValue()} />
  }),
  columnHelper.accessor(accessorWithinRead, {
    id: 'withinRead',
    header: 'Read',
    cell: v => <BinariesTableCell colId='withinRead' value={v.getValue()} />
  }),
  /* columnHelper.accessor(accessorSpawnParent, {
    id: 'spawnParent',
    header: 'Parents',
    cell: v => v.getValue()
  }), */
  columnHelper.accessor(accessorCve, {
    id: 'cve',
    header: () => <div className='m-auto text-xs'>CVE</div>,
    cell: v => <BinariesTableCell colId='cve' value={v.getValue()} />
  }),
  /* columnHelper.accessor(accessorCwe, {
    id: 'cwe',
    header: () => <div className='m-auto text-xs'>CWE</div>,
    cell: v => <BinariesTableCell colId='cwe' value={v.getValue()} />
  }), */
  columnHelper.accessor(accessorProprietary, {
    id: 'prop',
    header: () => <div className='m-auto' />,
    cell: v => <BinariesTableCell colId='prop' value={v.getValue()} />
  }),
  columnHelper.accessor(accessorBinary, {
    id: 'binary',
    header: 'Binary',
    cell: v => <BinariesTableCell colId='binary' value={v.getValue()} />
  }),
  columnHelper.accessor(accessorWithinWrite, {
    id: 'withinWrite',
    header: 'Write',
    cell: v => <BinariesTableCell colId='withinWrite' value={v.getValue()} />
  })
  /* columnHelper.accessor(accessorSpawnChild, {
    id: 'spawnChild',
    header: 'Children',
    cell: v => v.getValue()
  }) */
]

export default function BinariesTable ({ className, binaries, sorting, setSorting, currentBinary, setCurrentBinary, selectedBinary, setSelectedBinary }) {
  const table = useReactTable({
    data: binaries,
    columns: binariesColumns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    state: { sorting },
    onSortingChange: setSorting,
    getExpandedRowModel: getExpandedRowModel(),
    getRowCanExpand: () => true
  })
  return (
    <table className={className}>
      <TableHeadSort table={table} />
      <tbody>
        {table.getRowModel().rows.map(row => (
          <Fragment key={row.id}>
            <tr
              key={row.id}
              className={classNames('border-y border-slate-500', currentBinary?.id === row.original.id ? 'bg-slate-700' : '')}
              onMouseEnter={() => { setCurrentBinary(row.original) }}
              onMouseLeave={() => { setCurrentBinary(null) }}
            >
              {row.getVisibleCells().map(cell => (
                <td key={cell.id} className='p-2 cursor-pointer'>
                  {flexRender(cell.column.columnDef.cell, { ...cell.getContext(), setSelectedBinary, selectedBinary })}
                </td>
              ))}
            </tr>
            {selectedBinary?.id === row.original.id && (
              <tr>
                <td className='bg-gray-900' colSpan={row.getVisibleCells().length} onClick={() => console.log(row.original)}>
                  <Binary binary={row.original} />
                </td>
              </tr>
            )}
          </Fragment>
        ))}
      </tbody>
    </table>
  )
}
