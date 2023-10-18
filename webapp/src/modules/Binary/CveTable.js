import { Fragment } from 'react'
import { createColumnHelper, flexRender, getCoreRowModel, getExpandedRowModel, getSortedRowModel, useReactTable } from '@tanstack/react-table'
import { accessorChannel, accessorKind, accessorRole, accessorScore } from './accessors'
import ChannelsTableCell from './ChannelsTableCell'
import TableHeadSort from '@/components/TableHeadSort'
import useChartDimensions from '@/hooks/useChartDimensions'
import Bar from '@/components/Bar'
import { cveScoreColor } from '@/scales'
import { getCVSS } from '@/cveUtils'

function getSettings (colId) {
  if (['base', 'exp'].indexOf(colId) >= 0) {
    return {
      marginLeft: 30,
      marginTop: 0,
      marginRight: 0,
      marginBottom: 0
    }
  }
  return {
    marginLeft: 10,
    marginTop: 0,
    marginRight: 0,
    marginBottom: 0
  }
}

function Cell ({ colId, value }) {
  const [ref, dms] = useChartDimensions(getSettings(colId))
  if (['base', 'exp'].indexOf(colId) >= 0) return <Bar cRef={ref} dms={dms} value={value} colorScale={cveScoreColor} />
  if (colId === 'id') return <div ref={ref} className='text-xs'>{value}</div>
}

const columnHelper = createColumnHelper()
const cveColumns = [
  columnHelper.accessor(row => row.id, {
    id: 'id',
    header: 'CVE',
    cell: v => <Cell colId='id' value={v.getValue()} />
  }),
  columnHelper.accessor(row => getCVSS(row).baseScore, {
    id: 'base',
    header: 'Base',
    cell: v => <Cell colId='base' value={v.getValue()} />
  }),
  columnHelper.accessor(row => getCVSS(row).expScore, {
    id: 'exp',
    header: 'Exploitability',
    cell: v => <Cell colId='exp' value={v.getValue()} />
  })
]

export default function CveTable ({ className, cves, sorting, setSorting }) {
  const table = useReactTable({
    data: cves,
    columns: cveColumns,
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
