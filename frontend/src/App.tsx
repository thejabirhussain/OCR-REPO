import { Routes, Route } from 'react-router-dom'
import { Container } from '@mui/material'
import UploadPage from './components/UploadPage'
import JobStatusPage from './components/JobStatusPage'
import ResultViewer from './components/ResultViewer'

function App() {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/job/:jobId" element={<JobStatusPage />} />
        <Route path="/result/:jobId" element={<ResultViewer />} />
      </Routes>
    </Container>
  )
}

export default App

