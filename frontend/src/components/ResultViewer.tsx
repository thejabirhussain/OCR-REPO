import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  TextField,
  Chip,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  ArrowBack,
  Download,
  Search,
  FilterList,
} from '@mui/icons-material'
import { getJobResult, downloadJobResult } from '../services/api'
import type { StructuredDocument, Block } from '../types'
import DownloadOptions from './DownloadOptions'
import BlockHighlighter from './BlockHighlighter'

const ResultViewer = () => {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const [arabicDoc, setArabicDoc] = useState<StructuredDocument | null>(null)
  const [englishDoc, setEnglishDoc] = useState<StructuredDocument | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<string>('all')
  const [highlightedBlockId, setHighlightedBlockId] = useState<string | null>(null)
  const arabicScrollRef = useRef<HTMLDivElement>(null)
  const englishScrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (jobId) {
      getJobResult(jobId)
        .then((result) => {
          setArabicDoc(result.arabic || null)
          setEnglishDoc(result.english || null)
          setLoading(false)
        })
        .catch((err) => {
          setError(err.message)
          setLoading(false)
        })
    }
  }, [jobId])

  const handleBlockClick = (blockId: string) => {
    setHighlightedBlockId(blockId)
    // Scroll to block in both panels
    const arabicElement = document.getElementById(`block-ar-${blockId}`)
    const englishElement = document.getElementById(`block-en-${blockId}`)
    arabicElement?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    englishElement?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  const filterBlocks = (blocks: Block[]) => {
    let filtered = blocks

    // Filter by type
    if (filterType !== 'all') {
      filtered = filtered.filter((block) => block.type === filterType)
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter((block) =>
        block.text.toLowerCase().includes(query)
      )
    }

    return filtered
  }

  const renderBlocks = (doc: StructuredDocument, language: 'ar' | 'en') => {
    if (!doc) return null

    return doc.pages.map((page) => (
      <Box key={page.page_index} sx={{ mb: 4 }}>
        <Typography variant="h6" gutterBottom color="primary">
          Page {page.page_index + 1}
        </Typography>
        {filterBlocks(page.blocks).map((block) => (
          <BlockHighlighter
            key={block.block_id}
            block={block}
            language={language}
            highlighted={highlightedBlockId === block.block_id}
            onClick={() => handleBlockClick(block.block_id)}
            searchQuery={searchQuery}
          />
        ))}
      </Box>
    ))
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error">{error}</Alert>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/')} sx={{ mt: 2 }}>
          Back to Upload
        </Button>
      </Box>
    )
  }

  if (!arabicDoc && !englishDoc) {
    return (
      <Box>
        <Alert severity="warning">No results available for this job.</Alert>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/')} sx={{ mt: 2 }}>
          Back to Upload
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/')}>
          Back to Upload
        </Button>
        {jobId && <DownloadOptions jobId={jobId} />}
      </Box>

      {/* Search and Filter Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search in text..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                label="All"
                onClick={() => setFilterType('all')}
                color={filterType === 'all' ? 'primary' : 'default'}
                clickable
              />
              <Chip
                label="Paragraphs"
                onClick={() => setFilterType('paragraph')}
                color={filterType === 'paragraph' ? 'primary' : 'default'}
                clickable
              />
              <Chip
                label="Headings"
                onClick={() => setFilterType('heading')}
                color={filterType === 'heading' ? 'primary' : 'default'}
                clickable
              />
              <Chip
                label="Tables"
                onClick={() => setFilterType('table_cell')}
                color={filterType === 'table_cell' ? 'primary' : 'default'}
                clickable
              />
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Side-by-side Viewer */}
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper
            sx={{
              p: 3,
              height: '70vh',
              overflow: 'auto',
              direction: 'rtl',
            }}
            ref={arabicScrollRef}
          >
            <Typography variant="h5" gutterBottom sx={{ direction: 'ltr', textAlign: 'left' }}>
              Arabic Text
            </Typography>
            {arabicDoc ? (
              renderBlocks(arabicDoc, 'ar')
            ) : (
              <Alert severity="info">Arabic document not available</Alert>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper
            sx={{
              p: 3,
              height: '70vh',
              overflow: 'auto',
            }}
            ref={englishScrollRef}
          >
            <Typography variant="h5" gutterBottom>
              English Translation
            </Typography>
            {englishDoc ? (
              renderBlocks(englishDoc, 'en')
            ) : (
              <Alert severity="info">English document not available</Alert>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Statistics */}
      {(arabicDoc || englishDoc) && (
        <Paper sx={{ p: 2, mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Document Statistics:
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            {arabicDoc && (
              <>
                <Chip label={`Arabic Pages: ${arabicDoc.metadata.total_pages}`} />
                <Chip
                  label={`Arabic Blocks: ${arabicDoc.pages.reduce((acc, p) => acc + p.blocks.length, 0)}`}
                />
              </>
            )}
            {englishDoc && (
              <>
                <Chip label={`English Pages: ${englishDoc.metadata.total_pages}`} />
                <Chip
                  label={`English Blocks: ${englishDoc.pages.reduce((acc, p) => acc + p.blocks.length, 0)}`}
                />
              </>
            )}
          </Box>
        </Paper>
      )}
    </Box>
  )
}

export default ResultViewer

