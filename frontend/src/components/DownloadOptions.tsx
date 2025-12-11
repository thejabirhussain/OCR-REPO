import { useState } from 'react'
import {
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material'
import {
  Download,
  Description,
  TextFields,
  Code,
} from '@mui/icons-material'
import { downloadJobResult } from '../services/api'

interface DownloadOptionsProps {
  jobId: string
}

const DownloadOptions = ({ jobId }: DownloadOptionsProps) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [downloading, setDownloading] = useState<string | null>(null)

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleDownload = async (language: 'ar' | 'en', format: 'json' | 'txt' | 'docx') => {
    setDownloading(`${language}-${format}`)
    try {
      const blob = await downloadJobResult(jobId, language, format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      
      const extension = format === 'json' ? 'json' : format === 'txt' ? 'txt' : 'docx'
      const langLabel = language === 'ar' ? 'arabic' : 'english'
      a.download = `document_${langLabel}.${extension}`
      
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download failed:', error)
      alert('Download failed. Please try again.')
    } finally {
      setDownloading(null)
      handleClose()
    }
  }

  return (
    <>
      <Button
        variant="contained"
        startIcon={<Download />}
        onClick={handleClick}
      >
        Download
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
      >
        <MenuItem disabled>
          <ListItemText primary="Arabic" />
        </MenuItem>
        <MenuItem
          onClick={() => handleDownload('ar', 'json')}
          disabled={downloading === 'ar-json'}
        >
          <ListItemIcon>
            <Code fontSize="small" />
          </ListItemIcon>
          <ListItemText primary="JSON" />
        </MenuItem>
        <MenuItem
          onClick={() => handleDownload('ar', 'txt')}
          disabled={downloading === 'ar-txt'}
        >
          <ListItemIcon>
            <TextFields fontSize="small" />
          </ListItemIcon>
          <ListItemText primary="TXT" />
        </MenuItem>
        <MenuItem
          onClick={() => handleDownload('ar', 'docx')}
          disabled={downloading === 'ar-docx'}
        >
          <ListItemIcon>
            <Description fontSize="small" />
          </ListItemIcon>
          <ListItemText primary="DOCX" />
        </MenuItem>
        <Divider />
        <MenuItem disabled>
          <ListItemText primary="English" />
        </MenuItem>
        <MenuItem
          onClick={() => handleDownload('en', 'json')}
          disabled={downloading === 'en-json'}
        >
          <ListItemIcon>
            <Code fontSize="small" />
          </ListItemIcon>
          <ListItemText primary="JSON" />
        </MenuItem>
        <MenuItem
          onClick={() => handleDownload('en', 'txt')}
          disabled={downloading === 'en-txt'}
        >
          <ListItemIcon>
            <TextFields fontSize="small" />
          </ListItemIcon>
          <ListItemText primary="TXT" />
        </MenuItem>
        <MenuItem
          onClick={() => handleDownload('en', 'docx')}
          disabled={downloading === 'en-docx'}
        >
          <ListItemIcon>
            <Description fontSize="small" />
          </ListItemIcon>
          <ListItemText primary="DOCX" />
        </MenuItem>
      </Menu>
    </>
  )
}

export default DownloadOptions




