import { useQuery } from '@tanstack/react-query'
import { api } from '@/hooks/queries'

async function fetchFuzzExperiments({ queryKey }) {
  const [, brandId, firmwareId] = queryKey
  const res = await api.get('/fuzz_experiments', {
    params: { brandId, firmwareId }
  })
  return res.data
}

export function useFuzzExperimentsPolling(brandId, firmwareId) {
  return useQuery(
    ['fuzzExperiments', brandId, firmwareId],
    fetchFuzzExperiments,
    {
      enabled: !!brandId && !!firmwareId,
      refetchInterval: 2000,
    }
  )
}
