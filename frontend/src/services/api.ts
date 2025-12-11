import axios from 'axios'
import type { Job, JobResult } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const createJob = async (file: File, options?: {
  source_language?: string
  target_language?: string
  ocr_engine?: string
  translation_model?: string
}): Promise<{ job_id: string; status: string; created_at: string }> => {
  const formData = new FormData()
  formData.append('file', file)
  
  if (options?.source_language) {
    formData.append('source_language', options.source_language)
  }
  if (options?.target_language) {
    formData.append('target_language', options.target_language)
  }
  if (options?.ocr_engine) {
    formData.append('ocr_engine', options.ocr_engine)
  }
  if (options?.translation_model) {
    formData.append('translation_model', options.translation_model)
  }

  const response = await api.post('/api/jobs', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const getJob = async (jobId: string): Promise<Job> => {
  const response = await api.get(`/api/jobs/${jobId}`)
  return response.data
}

export const getJobResult = async (jobId: string): Promise<JobResult> => {
  const response = await api.get(`/api/jobs/${jobId}/result`)
  return response.data
}

export const downloadJobResult = async (
  jobId: string,
  language: 'ar' | 'en',
  format: 'json' | 'txt' | 'docx'
): Promise<Blob> => {
  const response = await api.get(`/api/jobs/${jobId}/download`, {
    params: { language, format },
    responseType: 'blob',
  })
  return response.data
}

export const healthCheck = async (): Promise<any> => {
  const response = await api.get('/api/health')
  return response.data
}

export default api




