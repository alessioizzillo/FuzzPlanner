import { dataChannelKinds, dataChannelKindsById } from '@/constants'

import { useRunData, useBorderBinaries } from '@/hooks/data'
import { useBinariesView } from '@/hooks/graphs'
import useChartDimensions from '@/hooks/useChartDimensions'

import { useSelectedFirmware } from '@/hooks/store/selectedFirmware'
import { useSelectedRun } from '@/hooks/store/selectedRun'

const chartSettings = {
  marginLeft: 0,
  marginTop: 0,
  marginRight: 0,
  marginBottom: 0
}

export default function BorderBinaries ({ className }) {
  const [ref, dms] = useChartDimensions(chartSettings)
  const selectedFirmware = useSelectedFirmware()
  const selectedRun = useSelectedRun()
  const runData = useRunData(selectedFirmware, selectedRun)
  const borderBinaries = useBorderBinaries(selectedFirmware, selectedRun)
  const binariesView = useBinariesView(selectedFirmware, selectedRun, -1)
  console.log(runData)
  console.log(borderBinaries)
  console.log(binariesView)
  return (
    <div ref={ref} className={className}>
      <div className='flex my-4 font-bold'>
        <svg className='w-12 h-8'>
          {dataChannelKinds.map((cid, ix) => (
            <rect
              key={cid}
              x={Math.floor(ix / 2) * 16}
              y={ix % 2 === 0 ? 0 : 16}
              width={16}
              height={16}
              stroke='gray'
              fill={dataChannelKindsById[cid].color}
              onMouseEnter={() => console.log(cid)}
            />
          ))}
        </svg>
        <div className='flex ml-2 align-middle w-60'>Executable</div>
        <div className='flex w-16 mx-1 align-middle'>Score</div>
        <div className='flex w-16 mx-1 align-middle'>Max</div>
        <div className='flex w-16 mx-1 align-middle'>Vendor</div>
      </div>
      {borderBinaries.map(b => (
        <div key={b.id} className='flex my-1'>
          <svg className='w-12 h-8'>
            {b.inputChannelsKinds.map((c, ix) => (
              <rect
                key={c.id}
                x={Math.floor(ix / 2) * 16}
                y={ix % 2 === 0 ? 0 : 16}
                width={16}
                height={16}
                stroke='gray'
                fill={c.count > 0 ? dataChannelKindsById[c.id].color : 'white'}
                onMouseEnter={() => console.log(c)}
              />
            ))}
          </svg>
          <div className='flex ml-2 align-middle w-60'>{b.id}</div>
          <div className='flex w-16 mx-1 align-middle'>{b.score.toFixed(1)}</div>
          <div className='flex w-16 mx-1 align-middle'>{b.max.toFixed(1)}</div>
          <div className='flex w-16 mx-1 align-middle'>{b.executableFile.is_proprietary ? 'T' : 'F'}</div>
        </div>
      ))}
    </div>
  )
}
