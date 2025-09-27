import { useState, useEffect } from 'react'

export function useSelectProgress(containerName) {
  const [progress, setProgress] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!containerName) {
      setProgress(null)
      setError(null)
      return
    }

    setLoading(true)
    setError(null)

    const fetchProgress = async () => {
      try {
        const response = await fetch(`http://localhost:4000/select_progress/${containerName}`)
        if (response.ok) {
          const data = await response.json()
          setProgress(data)
        } else if (response.status === 404) {
          // No progress data available - analysis may have completed
          setProgress(null)
        } else {
          throw new Error(`HTTP ${response.status}`)
        }
      } catch (err) {
        setError(err.message)
        setProgress(null)
      } finally {
        setLoading(false)
      }
    }

    // Fetch immediately
    fetchProgress()

    // Poll every 2 seconds for updates
    const interval = setInterval(fetchProgress, 2000)

    return () => clearInterval(interval)
  }, [containerName])

  return { progress, loading, error }
}