import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Alert,
  Button,
  Chip,
  CircularProgress,
} from '@mui/material'
import { CheckCircle, Error as ErrorIcon, ArrowBack } from '@mui/icons-material'
import { getJob } from '../services/api'
import { useJobPolling } from '../hooks/useJobPolling'
import type { Job } from '../types'

const JobStatusPage = () => {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const [job, setJob] = useState<Job | null>(null)
  const [error, setError] = useState<string | null>(null)

  const { stopPolling } = useJobPolling({
    jobId: jobId || '',
    enabled: !!jobId,
    onUpdate: (updatedJob) => {
      setJob(updatedJob)
    },
    onComplete: (completedJob) => {
      setJob(completedJob)
      setTimeout(() => {
        navigate(`/result/${jobId}`)
      }, 1000)
    },
    onError: (err) => {
      setError(err.message)
    },
  })

  useEffect(() => {
    if (jobId) {
      getJob(jobId)
        .then(setJob)
        .catch((err) => setError(err.message))
    }

    return () => {
      stopPolling()
    }
  }, [jobId, stopPolling])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'failed':
        return 'error'
      case 'processing':
      case 'extracting':
      case 'ocr':
      case 'translating':
        return 'info'
      default:
        return 'default'
    }
  }

  const getProgress = () => {
    if (!job) return 0
    if (job.status === 'completed') return 100
    if (job.status === 'failed') return 0

    let progress = 0
    const stages = [
      job.processing_stages.extraction,
      job.processing_stages.ocr,
      job.processing_stages.translation,
    ]

    stages.forEach((stage) => {
      if (stage === 'completed') {
        progress += 33.33
      } else if (stage === 'in_progress') {
        progress += 11.11
      }
    })

    return Math.min(progress, 99)
  }

  if (error && !job) {
    return (
      <Box>
        <Alert severity="error">{error}</Alert>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/')} sx={{ mt: 2 }}>
          Back to Upload
        </Button>
      </Box>
    )
  }

  if (!job) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Button startIcon={<ArrowBack />} onClick={() => navigate('/')} sx={{ mb: 2 }}>
        Back to Upload
      </Button>

      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Typography variant="h5">Job Status</Typography>
          <Chip
            label={job.status.toUpperCase()}
            color={getStatusColor(job.status) as any}
            icon={
              job.status === 'completed' ? (
                <CheckCircle />
              ) : job.status === 'failed' ? (
                <ErrorIcon />
              ) : undefined
            }
          />
        </Box>

        <Typography variant="body1" gutterBottom>
          <strong>File:</strong> {job.original_filename}
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          <strong>Created:</strong> {new Date(job.created_at).toLocaleString()}
        </Typography>
        {job.updated_at && (
          <Typography variant="body2" color="text.secondary" gutterBottom>
            <strong>Last Updated:</strong> {new Date(job.updated_at).toLocaleString()}
          </Typography>
        )}

        <Box sx={{ mt: 3 }}>
          <Typography variant="body2" gutterBottom>
            Progress
          </Typography>
          <LinearProgress variant="determinate" value={getProgress()} sx={{ height: 8, borderRadius: 4 }} />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
            {Math.round(getProgress())}%
          </Typography>
        </Box>

        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Processing Stages:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
            <Chip
              label={`Extraction: ${job.processing_stages.extraction}`}
              size="small"
              color={job.processing_stages.extraction === 'completed' ? 'success' : 'default'}
            />
            <Chip
              label={`OCR: ${job.processing_stages.ocr}`}
              size="small"
              color={job.processing_stages.ocr === 'completed' ? 'success' : 'default'}
            />
            <Chip
              label={`Translation: ${job.processing_stages.translation}`}
              size="small"
              color={job.processing_stages.translation === 'completed' ? 'success' : 'default'}
            />
          </Box>
        </Box>

        {job.stats && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Statistics:
            </Typography>
            <Typography variant="body2">
              Pages: {job.stats.total_pages || 0} | Blocks: {job.stats.total_blocks || 0} | Arabic
              Characters: {job.stats.total_characters_arabic || 0} | English Characters:{' '}
              {job.stats.total_characters_english || 0}
            </Typography>
          </Box>
        )}

        {job.error_message && (
          <Alert severity="error" sx={{ mt: 3 }}>
            <Typography variant="subtitle2">Error:</Typography>
            {job.error_message}
          </Alert>
        )}

        {job.status === 'completed' && (
          <Button
            variant="contained"
            onClick={() => navigate(`/result/${jobId}`)}
            sx={{ mt: 3 }}
          >
            View Results
          </Button>
        )}
      </Paper>
    </Box>
  )
}

export default JobStatusPage




