import { Fragment } from 'react'
import { createColumnHelper, flexRender, getCoreRowModel, getExpandedRowModel, getSortedRowModel, useReactTable } from '@tanstack/react-table'
import { accessorChannel, accessorKind, accessorRole, accessorScore } from './accessors'
import ChannelsTableCell from './ChannelsTableCell'
import TableHeadSort from '@/components/TableHeadSort'

const columnHelper = createColumnHelper()
const channelsColumns = [
  columnHelper.accessor(accessorRole, {
    id: 'role',
    header: 'Role',
    cell: v => <ChannelsTableCell colId='role' value={v.getValue()} />
  }),
  columnHelper.accessor(accessorKind, {
    id: 'kind',
    header: 'Kind',
    cell: v => <ChannelsTableCell colId='kind' value={v.getValue()} />
  }),
  columnHelper.accessor(accessorScore, {
    id: 'score',
    header: 'Score',
    cell: v => <ChannelsTableCell colId='score' value={v.getValue()} />
  }),
  columnHelper.accessor(accessorChannel, {
    id: 'channel',
    header: 'Channel',
    cell: v => <ChannelsTableCell colId='channel' value={v.getValue()} />
  }),
  columnHelper.display({
    id: 'select',
    header: '',
    cell: (props) => <ChannelsTableCell colId='select' value={{ role: props.row.original.role, channel: props.row.original, binary: props.table.options.meta.binary }} />
  })
]

export default function ChannelsTable ({ className, binary, channels, sorting, setSorting }) {
  const table = useReactTable({
    data: channels,
    columns: channelsColumns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    state: { sorting },
    onSortingChange: setSorting,
    getExpandedRowModel: getExpandedRowModel(),
    getRowCanExpand: () => true,
    meta: { binary }
  })
  return (
    <table className={className}>
      <TableHeadSort table={table} />
      <tbody>
        {table.getRowModel().rows.map(row => (
          <Fragment key={row.id}>
            <tr key={row.id} className='border-y border-slate-500'>
              {row.getVisibleCells().map(cell => (
                <td key={cell.id} className='p-2 cursor-pointer'>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
            {row.getIsExpanded() && (
              <tr>
                <td className='bg-gray-900' colSpan={row.getVisibleCells().length} onClick={() => console.log(row.original)}>
                  {row.original.id}
                </td>
              </tr>
            )}
          </Fragment>
        ))}
      </tbody>
    </table>
  )
}
