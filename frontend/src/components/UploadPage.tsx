import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import { CloudUpload } from '@mui/icons-material'
import { createJob } from '../services/api'

const UploadPage = () => {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [ocrEngine, setOcrEngine] = useState('paddleocr')

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      // Validate file type
      const allowedTypes = ['.pdf', '.docx', '.jpg', '.jpeg', '.png', '.tiff', '.tif']
      const fileExt = '.' + selectedFile.name.split('.').pop()?.toLowerCase()
      
      if (!allowedTypes.includes(fileExt)) {
        setError(`File type not allowed. Allowed types: ${allowedTypes.join(', ')}`)
        return
      }

      // Validate file size (50MB)
      if (selectedFile.size > 50 * 1024 * 1024) {
        setError('File size exceeds 50MB limit')
        return
      }

      setFile(selectedFile)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setError(null)

    try {
      const result = await createJob(file, {
        ocr_engine: ocrEngine,
      })
      navigate(`/job/${result.job_id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Upload failed')
      setUploading(false)
    }
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const droppedFile = event.dataTransfer.files[0]
    if (droppedFile) {
      const input = document.createElement('input')
      input.type = 'file'
      input.files = event.dataTransfer.files
      handleFileSelect({ target: input } as any)
    }
  }

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Arabic Text Extraction & Translation
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload a document (PDF, DOCX, or image) containing Arabic text to extract and translate it.
      </Typography>

      <Paper
        sx={{
          p: 4,
          mt: 3,
          border: '2px dashed',
          borderColor: 'primary.main',
          textAlign: 'center',
          cursor: 'pointer',
          '&:hover': {
            borderColor: 'primary.dark',
            backgroundColor: 'action.hover',
          },
        }}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <input
          type="file"
          id="file-upload"
          style={{ display: 'none' }}
          onChange={handleFileSelect}
          accept=".pdf,.docx,.jpg,.jpeg,.png,.tiff,.tif"
        />
        <label htmlFor="file-upload">
          <CloudUpload sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {file ? file.name : 'Drag and drop a file here, or click to select'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Supported formats: PDF, DOCX, JPEG, PNG, TIFF (Max 50MB)
          </Typography>
        </label>
      </Paper>

      <Box sx={{ mt: 3, maxWidth: 300 }}>
        <FormControl fullWidth>
          <InputLabel>OCR Engine</InputLabel>
          <Select
            value={ocrEngine}
            label="OCR Engine"
            onChange={(e) => setOcrEngine(e.target.value)}
          >
            <MenuItem value="paddleocr">PaddleOCR</MenuItem>
            <MenuItem value="tesseract">Tesseract</MenuItem>
            <MenuItem value="ensemble">Ensemble</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {file && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="body2" color="text.secondary">
            File: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
          </Typography>
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {uploading && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress />
          <Typography variant="body2" sx={{ mt: 1 }}>
            Uploading...
          </Typography>
        </Box>
      )}

      <Button
        variant="contained"
        size="large"
        onClick={handleUpload}
        disabled={!file || uploading}
        sx={{ mt: 3 }}
      >
        Upload and Process
      </Button>
    </Box>
  )
}

export default UploadPage




