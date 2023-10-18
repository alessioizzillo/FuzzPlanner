import { interpolateViridis } from 'd3-scale-chromatic'

export function Square ({ cRef, dms, value, colorScale = interpolateViridis }) {
  return (
    <div ref={cRef} className='w-6 h-6'>
      <svg width={dms.width} height={dms.height}>
        <g transform={`translate(${[
          dms.marginLeft,
          dms.marginTop
        ].join(',')})`}
        >
          <rect x={0} y={0} width={dms.boundedWidth} height={value ? dms.boundedHeight : 0} fill={colorScale(value)} />
        </g>
      </svg>
    </div>
  )
}
