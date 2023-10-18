import { scaleQuantize, scaleSequential } from 'd3-scale'
import { interpolateBlues, interpolateCividis, interpolateCool, interpolateCubehelixDefault, interpolateGnBu, interpolateGreens, interpolateOranges, interpolatePuBuGn, interpolateReds, interpolateYlOrBr } from 'd3-scale-chromatic'

export const procSpawnNumColor = scaleSequential(interpolateBlues).domain([0, 1])

export const channelScoreColor = scaleSequential(interpolateCool).domain([0, 1])
export const channelListenColor = scaleSequential(interpolateCool).domain([0, 1])
export const cveScoreColor = scaleSequential(interpolateCividis).domain([0, 10])

export const discreteIntervals = scaleQuantize()
  .domain([0, 1])
  .range([...Array(4)].map((_e, i) => ((i + 1) / 4)))
