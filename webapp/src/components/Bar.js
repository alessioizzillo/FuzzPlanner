import { interpolateViridis } from 'd3-scale-chromatic'

export default function Bar ({ cRef, dms, value, colorScale = interpolateViridis }) {
  return (
    <div ref={cRef} className='w-20 h-6'>
      <svg width={dms.width} height={dms.height}>
        <g transform={`translate(${[
          0,
          dms.marginTop
        ].join(',')})`}
        >
          <text x={0} y={dms.boundedHeight / 2} dominantBaseline='central' className='text-sm fill-gray-400'>{value}</text>
        </g>
        <g transform={`translate(${[
          dms.marginLeft,
          dms.marginTop
        ].join(',')})`}
        >
          <rect x={0} y={0} width={value * dms.boundedWidth} height={dms.boundedHeight} fill={colorScale(value)} />
        </g>
      </svg>
    </div>
  )
}
