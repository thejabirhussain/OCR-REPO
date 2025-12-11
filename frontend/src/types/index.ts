export interface Job {
  job_id: string
  status: string
  original_filename: string
  created_at: string
  updated_at: string
  stats?: JobStats
  error_message?: string
  processing_stages: ProcessingStages
}

export interface JobStats {
  total_pages?: number
  total_blocks?: number
  total_characters_arabic?: number
  total_characters_english?: number
}

export interface ProcessingStages {
  extraction: string
  ocr: string
  translation: string
}

export interface Block {
  block_id: string
  type: string
  metadata: BlockMetadata
  text: string
}

export interface BlockMetadata {
  bbox?: number[]
  is_heading?: boolean
  heading_level?: number
  list_level?: number
  table?: TableMetadata
  confidence?: number
}

export interface TableMetadata {
  row?: number
  col?: number
  table_id?: string
}

export interface Page {
  page_index: number
  blocks: Block[]
}

export interface StructuredDocument {
  document_id: string
  language: string
  pages: Page[]
  metadata: DocumentMetadata
}

export interface DocumentMetadata {
  source_filename: string
  total_pages: number
  extraction_timestamp: string
  ocr_engine?: string
  processing_time_seconds?: number
}

export interface JobResult {
  job_id: string
  arabic?: StructuredDocument
  english?: StructuredDocument
}




