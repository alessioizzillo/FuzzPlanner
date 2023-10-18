export function getCVSS (cve) {
  if (cve.metrics.cvssMetricV31) {
    return {
      baseScore: cve.metrics.cvssMetricV31[0].cvssData.baseScore,
      expScore: cve.metrics.cvssMetricV2[0].exploitabilityScore
    }
  }
  if (cve.metrics.cvssMetricV2) {
    return {
      baseScore: cve.metrics.cvssMetricV2[0].cvssData.baseScore,
      expScore: cve.metrics.cvssMetricV2[0].exploitabilityScore
    }
  }
  return {
    baseScore: 0
  }
}

export function getHighestBaseScore (cves) {
  let max = 0
  cves.forEach(cve => {
    max = Math.max(max, getCVSS(cve).baseScore)
  })
  return max
}
