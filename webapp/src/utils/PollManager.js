/**
 * Centralized Polling Manager with ETag support and smart backoff
 * Optimizes API polling by avoiding duplicate requests and using HTTP caching
 */

class SmartPoller {
  constructor(endpoint, params, options) {
    this.endpoint = endpoint
    this.params = params
    this.options = options
    this.interval = options.initialInterval || 2000
    this.maxInterval = options.maxInterval || 30000
    this.minInterval = options.minInterval || 1000
    this.consecutiveUnchanged = 0
    this.etag = null
    this.isRunning = false
    this.timeoutId = null
    this.lastData = null

    this.start()
  }

  start() {
    if (this.isRunning) return
    this.isRunning = true
    this.poll()
  }

  stop() {
    this.isRunning = false
    if (this.timeoutId) {
      clearTimeout(this.timeoutId)
      this.timeoutId = null
    }
  }

  async poll() {
    if (!this.isRunning) return

    try {
      const headers = {}
      if (this.etag) {
        headers['If-None-Match'] = this.etag
      }

      const url = new URL(`http://localhost:4000${this.endpoint}`)
      Object.entries(this.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, value)
        }
      })

      const response = await fetch(url.toString(), { headers })

      if (response.status === 304) {
        // No changes detected, increase polling interval
        this.consecutiveUnchanged++
        this.adjustInterval(false)
        this.scheduleNextPoll()
        return
      }

      if (!response.ok) {
        console.error(`[PollManager] HTTP ${response.status} for URL: ${url.toString()}`)
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      this.etag = response.headers.get('ETag')

      // Reset interval on data change
      const dataChanged = JSON.stringify(data) !== JSON.stringify(this.lastData)
      if (dataChanged) {
        this.consecutiveUnchanged = 0
        this.adjustInterval(true)
        this.lastData = data
        this.options.onData?.(data)
      } else {
        this.consecutiveUnchanged++
        this.adjustInterval(false)
      }

    } catch (error) {
      console.error('Polling error:', error)
      this.options.onError?.(error)
      // Increase interval on error
      this.consecutiveUnchanged++
      this.adjustInterval(false)
    }

    this.scheduleNextPoll()
  }

  adjustInterval(hasChanges) {
    if (hasChanges) {
      // Reset to fast polling when data changes
      this.interval = this.minInterval
    } else if (this.consecutiveUnchanged > 2) {
      // Exponential backoff when no changes
      this.interval = Math.min(this.interval * 1.4, this.maxInterval)
    }

    // Custom interval calculation based on data state
    if (this.options.getInterval && this.lastData) {
      const customInterval = this.options.getInterval(this.lastData)
      if (customInterval) {
        this.interval = Math.max(customInterval, this.minInterval)
      }
    }
  }

  scheduleNextPoll() {
    if (!this.isRunning) return

    this.timeoutId = setTimeout(() => {
      this.poll()
    }, this.interval)
  }

  updateParams(newParams) {
    const paramsChanged = JSON.stringify(this.params) !== JSON.stringify(newParams)
    if (paramsChanged) {
      this.params = newParams
      this.etag = null // Reset ETag when params change
      this.consecutiveUnchanged = 0
      this.interval = this.options.initialInterval || 2000

      // Trigger immediate poll for new params
      if (this.timeoutId) {
        clearTimeout(this.timeoutId)
      }
      this.poll()
    }
  }
}

class PollManager {
  constructor() {
    this.subscriptions = new Map()
    this.activePolls = new Map()
  }

  subscribe(endpoint, params, callback, options = {}) {
    const key = this.getKey(endpoint, params)

    if (!this.subscriptions.has(key)) {
      this.subscriptions.set(key, new Set())
    }
    this.subscriptions.get(key).add(callback)

    if (!this.activePolls.has(key)) {
      this.startPolling(key, endpoint, params, options)
    } else {
      // Update existing poller with new params
      const poller = this.activePolls.get(key)
      poller.updateParams(params)
    }

    return () => this.unsubscribe(key, callback)
  }

  unsubscribe(key, callback) {
    const callbacks = this.subscriptions.get(key)
    if (callbacks) {
      callbacks.delete(callback)
      if (callbacks.size === 0) {
        this.subscriptions.delete(key)
        const poller = this.activePolls.get(key)
        if (poller) {
          poller.stop()
          this.activePolls.delete(key)
        }
      }
    }
  }

  startPolling(key, endpoint, params, options) {
    const poller = new SmartPoller(endpoint, params, {
      onData: (data) => {
        const callbacks = this.subscriptions.get(key)
        if (callbacks) {
          callbacks.forEach(callback => {
            try {
              callback(data, null) // data, error
            } catch (error) {
              console.error('Callback error:', error)
            }
          })
        }
      },
      onError: (error) => {
        const callbacks = this.subscriptions.get(key)
        if (callbacks) {
          callbacks.forEach(callback => {
            try {
              callback(null, error) // data, error
            } catch (callbackError) {
              console.error('Callback error:', callbackError)
            }
          })
        }
      },
      ...options
    })

    this.activePolls.set(key, poller)
  }

  getKey(endpoint, params) {
    // Create a stable key from endpoint and params
    const sortedParams = Object.keys(params || {})
      .sort()
      .reduce((result, key) => {
        result[key] = params[key]
        return result
      }, {})

    return `${endpoint}:${JSON.stringify(sortedParams)}`
  }

  // Debug method to see active polls
  getActivePolls() {
    return Array.from(this.activePolls.keys())
  }

  // Method to force refresh all polls
  refreshAll() {
    this.activePolls.forEach(poller => {
      poller.etag = null
      poller.consecutiveUnchanged = 0
      poller.interval = poller.options.initialInterval || 2000
    })
  }

  // Method to force immediate poll for all active polls
  forceRefresh() {
    this.activePolls.forEach(poller => {
      poller.etag = null
      poller.consecutiveUnchanged = 0
      poller.interval = poller.options.initialInterval || 2000

      // Cancel current timeout and poll immediately
      if (poller.timeoutId) {
        clearTimeout(poller.timeoutId)
      }
      poller.poll()
    })
  }
}

// Global instance
export const pollManager = new PollManager()

// Export for testing
export { SmartPoller, PollManager }