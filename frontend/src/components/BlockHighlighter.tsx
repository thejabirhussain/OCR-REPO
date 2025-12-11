import { Box, Paper, Typography, Chip } from '@mui/material'
import type { Block } from '../types'

interface BlockHighlighterProps {
  block: Block
  language: 'ar' | 'en'
  highlighted?: boolean
  onClick?: () => void
  searchQuery?: string
}

const BlockHighlighter = ({
  block,
  language,
  highlighted = false,
  onClick,
  searchQuery = '',
}: BlockHighlighterProps) => {
  const getBlockStyle = () => {
    const baseStyle: any = {
      p: 2,
      mb: 1,
      cursor: onClick ? 'pointer' : 'default',
      transition: 'all 0.2s',
      border: '1px solid transparent',
    }

    if (highlighted) {
      baseStyle.borderColor = 'primary.main'
      baseStyle.backgroundColor = 'action.selected'
      baseStyle.boxShadow = 2
    }

    return baseStyle
  }

  const highlightText = (text: string, query: string) => {
    if (!query) return text

    const parts = text.split(new RegExp(`(${query})`, 'gi'))
    return parts.map((part, index) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={index} style={{ backgroundColor: '#ffeb3b', padding: '2px 0' }}>
          {part}
        </mark>
      ) : (
        part
      )
    )
  }

  const getBlockTypeLabel = () => {
    if (block.metadata.is_heading) {
      return `H${block.metadata.heading_level || 1}`
    }
    if (block.type === 'table_cell') {
      return 'Table'
    }
    if (block.metadata.list_level !== null && block.metadata.list_level !== undefined) {
      return 'List'
    }
    return 'Paragraph'
  }

  return (
    <Paper
      id={`block-${language === 'ar' ? 'ar' : 'en'}-${block.block_id}`}
      sx={getBlockStyle()}
      onClick={onClick}
      onMouseEnter={(e) => {
        if (!highlighted) {
          e.currentTarget.style.backgroundColor = 'action.hover'
        }
      }}
      onMouseLeave={(e) => {
        if (!highlighted) {
          e.currentTarget.style.backgroundColor = 'background.paper'
        }
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
        <Chip label={getBlockTypeLabel()} size="small" color="primary" variant="outlined" />
        {block.metadata.confidence !== null && block.metadata.confidence !== undefined && (
          <Chip
            label={`${Math.round(block.metadata.confidence * 100)}%`}
            size="small"
            color={block.metadata.confidence > 0.9 ? 'success' : 'warning'}
            variant="outlined"
          />
        )}
      </Box>
      <Typography
        variant={
          block.metadata.is_heading
            ? `h${Math.min(block.metadata.heading_level || 1, 6)}` as any
            : 'body1'
        }
        sx={{
          direction: language === 'ar' ? 'rtl' : 'ltr',
          textAlign: language === 'ar' ? 'right' : 'left',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {highlightText(block.text, searchQuery)}
      </Typography>
    </Paper>
  )
}

export default BlockHighlighter

