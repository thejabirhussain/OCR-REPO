import { useEffect, useRef } from 'react'
import { getJob } from '../services/api'
import type { Job } from '../types'

interface UseJobPollingOptions {
  jobId: string
  enabled?: boolean
  interval?: number
  onUpdate?: (job: Job) => void
  onComplete?: (job: Job) => void
  onError?: (error: Error) => void
}

export const useJobPolling = ({
  jobId,
  enabled = true,
  interval = 2000,
  onUpdate,
  onComplete,
  onError,
}: UseJobPollingOptions) => {
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!enabled || !jobId) return

    const poll = async () => {
      try {
        const job = await getJob(jobId)
        
        if (onUpdate) {
          onUpdate(job)
        }

        if (job.status === 'completed' || job.status === 'failed') {
          if (intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
          }
          
          if (job.status === 'completed' && onComplete) {
            onComplete(job)
          } else if (job.status === 'failed' && onError) {
            onError(new Error(job.error_message || 'Job failed'))
          }
        }
      } catch (error) {
        if (onError) {
          onError(error as Error)
        }
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
          intervalRef.current = null
        }
      }
    }

    // Initial poll
    poll()

    // Set up polling
    intervalRef.current = setInterval(poll, interval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [jobId, enabled, interval, onUpdate, onComplete, onError])

  return { stopPolling: () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }}
}




